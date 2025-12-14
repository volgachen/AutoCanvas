"""
Baseline ReAct Agent - Standalone implementation using ReAct framework.

ReAct Format:
    Thought: [reasoning about what to do next]
    Action: search[query text] or submit[answer text]
    Observation: [result from action]

"""

import asyncio
import os
import json
import logging
import requests
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from openai import AsyncOpenAI
from app.services.database import db
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)


# Mode configurations
MODE_CONFIGS = {
    "chat": {
        "description": "Normal conversation mode",
        "instruction": "Now, your valid function is 'chat[The message you want to say in this conversation]', to provide your response to the current conversation.",
        "actions": ["chat"],
        "action_descriptions": {
            "chat": "chat[message] - Send a message in the conversation"
        }
    },
    "edit": {
        "description": "File editing mode - make edits to files",
        "instruction": """You can use the following actions:
- read_file[filename] - Read the contents of a file
- write_file[filename|content] - Write content to a file (use | as separator)
- edit_file[filename|old_text|new_text] - Replace old_text with new_text in a file (use | as separator)
- chat[message] - Send a message in the conversation

Important: When using actions that require multiple arguments, separate them with |""",
        "actions": ["read_file", "write_file", "edit_file", "chat"],
        "action_descriptions": {
            "read_file": "read_file[filename] - Read the contents of a file",
            "write_file": "write_file[filename|content] - Write content to a file",
            "edit_file": "edit_file[filename|old_text|new_text] - Replace old_text with new_text in a file",
            "chat": "chat[message] - Send a message in the conversation"
        }
    }
}


class ReActParser:
    """Parser for ReAct-style output (Thought/Action/Observation)."""

    @staticmethod
    def parse_action(text: str) -> Optional[Tuple[str, str]]:
        """
        Parse action from text in format: Action: tool_name[arguments]

        Args:
            text: Text containing action

        Returns:
            Tuple of (tool_name, arguments) or None if not found
        """
        # Pattern: Action: tool_name[arguments]
        pattern = r'Action:\s*(\w+)\[(.*?)\]'
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)

        if match:
            tool_name = match.group(1).strip()
            arguments = match.group(2).strip()
            return (tool_name, arguments)

        return None

    @staticmethod
    def extract_thought(text: str) -> Optional[str]:
        """
        Extract thought from text.

        Args:
            text: Text containing thought

        Returns:
            Thought text or None if not found
        """
        pattern = r'Thought:\s*(.+?)(?=\n(?:Action|Observation|$))'
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)

        if match:
            return match.group(1).strip()

        return None


class BaselineReActAgent:
    """
    Baseline HotpotQA agent using ReAct framework.

    This agent uses text-based reasoning traces with explicit Thought/Action/Observation
    steps instead of function calling.
    """

    def __init__(
        self,
        name: str = "Alice",
        model: str = "gpt-4.1-mini",
        temperature: float = 0.2,
        mode: str = "chat",
    ):
        """
        Initialize the baseline ReAct agent.

        Args:
            name: Agent name
            model: OpenAI model name
            temperature: Sampling temperature
            mode: Default agent mode ('chat' or 'edit')
        """
        self.name = name
        self.model = model
        self.temperature = temperature

        # Validate and set mode
        if mode not in MODE_CONFIGS:
            raise ValueError(f"Invalid mode: {mode}. Available modes: {list(MODE_CONFIGS.keys())}")
        self.mode = mode

        # Initialize OpenAI client
        self.client = AsyncOpenAI(
            base_url=os.environ.get("OPENAI_BASE_URL", ""),
            api_key=os.environ.get("OPENAI_API_KEY", "")
        )

        # Parser
        self.parser = ReActParser()

        # System prompt (mode-agnostic)
        self.system_prompt = f"""You are {self.name}, an expert in coding and creative writing.

You should follow the ReAct (Reasoning + Acting) framework:
1. Thought: Think step by step about what information you need
2. Action: Take one of the available actions
3. Observation: You will receive the result of your action

Format your response EXACTLY as:
Thought: [your reasoning here]
Action: [action_name[arguments]]

After each action, you will receive an Observation with the results.

Important:
- Always start with "Thought:" followed by your reasoning
- Always follow with "Action:" and the specific action
- Only use the actions provided in the instructions
"""

        self.messages = [{
            "role": "system",
            "content": self.system_prompt,
        }]
        self.last_retrieve_time = None

    def set_mode(self, mode: str):
        """Change the agent's mode."""
        if mode not in MODE_CONFIGS:
            raise ValueError(f"Invalid mode: {mode}. Available modes: {list(MODE_CONFIGS.keys())}")
        self.mode = mode
        logger.info(f"Agent {self.name} mode changed to: {mode}")

    async def __call__(self, session_id) -> str:
        """
        Run the agent on a question.

        Args:
            question: The question to answer

        Returns:
            The final answer
        """

        # TODO: get all messages after xxx and append that to self.messages
        new_messages = db.get_session_messages(session_id=session_id, start_from=self.last_retrieve_time)
        self.last_retrieve_time = datetime.now()
        if new_messages:
            # TODO: append new messages to self.messages
            self.messages.append({
                "role": "user",
                "content": "Here are some newly coming messages: \n"
                           + "\n".join([f"【{m['role']}】{m['content']}" for m in new_messages])
            })

        # Add mode-specific instruction message
        mode_config = MODE_CONFIGS[self.mode]
        instruction_message = {
            "role": "user",
            "content": mode_config["instruction"]
        }

        try:
            # Call LLM for reasoning and action
            resp = await self.client.chat.completions.create(
                model=self.model,
                messages=self.messages + [instruction_message],
                temperature=self.temperature,
            )

            llm_output = resp.choices[0].message.content
            logger.info(f"LLM Output:\n{llm_output}")

        except Exception as e:
            logger.warning(f"LLM call failed: {e}, retrying after 5s...")
            await asyncio.sleep(5)
            return

        if not llm_output:
            logger.warning("Empty LLM output, continuing...")
            return

        # Parse action from output
        action_result = self.parser.parse_action(llm_output)

        if action_result is None:
            logger.warning("No valid action found in LLM output")
            return

        action_name, arguments = action_result
        logger.info(f"Action: {action_name}[{arguments}]")

        # Execute action based on current mode
        try:
            observation = await self._execute_action(session_id, action_name, arguments)
            logger.info(f"Action executed successfully: {observation[:100]}...")
        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            observation = f"Error: {str(e)}"

    async def _execute_action(self, session_id: str, action_name: str, arguments: str) -> str:
        """
        Execute an action based on the action name.

        Args:
            session_id: Current session ID
            action_name: Name of the action to execute
            arguments: Arguments for the action

        Returns:
            Observation string
        """
        action_name_lower = action_name.lower()

        # Chat action (available in all modes)
        if action_name_lower == "chat":
            return await self._action_chat(session_id, arguments)

        # Edit mode actions
        elif action_name_lower == "read_file":
            return await self._action_read_file(arguments)

        elif action_name_lower == "write_file":
            return await self._action_write_file(arguments)

        elif action_name_lower == "edit_file":
            return await self._action_edit_file(arguments)

        else:
            return f"Unknown action: {action_name}. Available actions: {MODE_CONFIGS[self.mode]['actions']}"

    async def _action_chat(self, session_id: str, message: str) -> str:
        """Send a chat message."""
        db.create_message(
            session_id=session_id,
            content=message,
            role=self.name,
            metadata={
                "source": "agent",
                "mode": self.mode
            }
        )
        return f"Message sent: {message[:50]}..."

    async def _action_edit_file(self, arguments: str) -> str:
        """Edit a file by replacing old_text with new_text."""
        # Split by | separator
        raise NotImplementedError
