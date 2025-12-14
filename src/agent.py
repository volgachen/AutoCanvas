"""
Baseline ReAct Agent - Standalone implementation using ReAct framework.

ReAct Format (XML-based):
    <thought>
    [reasoning about what to do next]
    </thought>
    <action>
    action_name
    </action>
    <inputs>
    [action inputs]
    </inputs>

"""

import asyncio
import os
import json
import logging
import requests
import re
import time
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
        "instruction": """You can use the following actions:

1. chat - Send a message in the conversation
   Format: <action>chat</action><inputs>Your message here</inputs>

2. enter_edit_mode - Enter edit mode to propose changes
   Format: <action>enter_edit_mode</action><inputs>Description of what you want to edit</inputs>

Always wrap your response in XML tags:
<thought>Your reasoning process</thought>
<action>action_name</action>
<inputs>action inputs</inputs>""",
        "actions": ["chat", "enter_edit_mode"],
        "action_descriptions": {
            "chat": "Send a message in the conversation",
            "enter_edit_mode": "Enter edit mode to make changes"
        }
    },
    "edit": {
        "description": "File editing mode - make edits to files",
        "instruction": """You can use the following actions:

1. search_and_replace - Perform a search and replace operation
   Format:
   <action>search_and_replace</action>
   <inputs>
   <<<<<<< SEARCH
   [Original code lines]
   =======
   [Modified code lines]
   >>>>>>> REPLACE
   </inputs>

2. exit_edit_mode - Exit edit mode and return to chat mode
   Format: <action>exit_edit_mode</action><inputs>Summary of changes made</inputs>

Always wrap your response in XML tags:
<thought>Your reasoning process</thought>
<action>action_name</action>
<inputs>action inputs</inputs>

Important: Each search_and_replace action should contain exactly ONE search/replace block.""",
        "actions": ["search_and_replace", "exit_edit_mode"],
        "action_descriptions": {
            "search_and_replace": "Perform a search and replace operation",
            "exit_edit_mode": "Exit edit mode and return to chat mode"
        }
    }
}


class ReActParser:
    """Parser for XML-based ReAct output."""

    @staticmethod
    def parse_action(text: str) -> Optional[Tuple[str, str]]:
        """
        Parse action from XML format:
        <action>action_name</action>
        <inputs>arguments</inputs>

        Args:
            text: Text containing XML tags

        Returns:
            Tuple of (action_name, inputs) or None if not found
        """
        # Pattern for <action>...</action>
        action_pattern = r'<action>\s*(.*?)\s*</action>'
        action_match = re.search(action_pattern, text, re.IGNORECASE | re.DOTALL)

        # Pattern for <inputs>...</inputs>
        inputs_pattern = r'<inputs>\s*(.*?)\s*</inputs>'
        inputs_match = re.search(inputs_pattern, text, re.IGNORECASE | re.DOTALL)

        if action_match:
            action_name = action_match.group(1).strip()
            inputs = inputs_match.group(1).strip() if inputs_match else ""
            return (action_name, inputs)

        return None

    @staticmethod
    def extract_thought(text: str) -> Optional[str]:
        """
        Extract thought from XML format: <thought>...</thought>

        Args:
            text: Text containing thought XML tag

        Returns:
            Thought text or None if not found
        """
        pattern = r'<thought>\s*(.*?)\s*</thought>'
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

You follow the ReAct (Reasoning + Acting) framework using XML tags.

Format your response EXACTLY as:
<thought>
[Your step-by-step reasoning about what to do]
</thought>
<action>
[action_name]
</action>
<inputs>
[The inputs/content for this action]
</inputs>

Important:
- Always include all three XML tags: <thought>, <action>, and <inputs>
- Only use actions that are provided in the mode-specific instructions
- Each response should contain exactly ONE action
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
        new_files = db.get_file_versions(session_id=session_id, start_from=self.last_retrieve_time)
        self.last_retrieve_time = datetime.now()
        if new_messages:
            # TODO: append new messages to self.messages
            self.messages.append({
                "role": "user",
                "content": "Here are some newly coming messages: \n"
                           + "\n".join([f"【{m['role']}】{m['content']}" for m in new_messages])
            })
        if new_files:
            self.messages.append({
                "role": "user",
                "content": "Here is the newest version:\n" + new_files[-1]["content"]
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

    async def _execute_action(self, session_id: str, action_name: str, inputs: str) -> str:
        """
        Execute an action based on the action name.

        Args:
            session_id: Current session ID
            action_name: Name of the action to execute
            inputs: Input content for the action

        Returns:
            Observation string
        """
        action_name_lower = action_name.lower()

        # Chat mode actions
        if action_name_lower == "chat":
            return await self._action_chat(session_id, inputs)

        elif action_name_lower == "enter_edit_mode":
            return await self._action_enter_edit_mode(session_id, inputs)

        # Edit mode actions
        elif action_name_lower == "search_and_replace":
            return await self._action_search_and_replace(session_id, inputs)

        elif action_name_lower == "exit_edit_mode":
            return await self._action_exit_edit_mode(session_id, inputs)

        else:
            return f"Unknown action: {action_name}. Available actions in {self.mode} mode: {MODE_CONFIGS[self.mode]['actions']}"

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
        return f"Message sent successfully"

    async def _action_enter_edit_mode(self, session_id: str, proposal: str) -> str:
        """Enter edit mode with a proposal."""
        # Switch to edit mode
        self.set_mode("edit")

        # Create a message with the edit proposal
        db.create_message(
            session_id=session_id,
            content=f"[Entering edit mode] {proposal}",
            role=self.name,
            metadata={
                "source": "agent",
                "mode": "edit",
                "action": "enter_edit_mode",
                "proposal": proposal
            }
        )
        return f"Entered edit mode. Proposal: {proposal}"

    async def _action_search_and_replace(self, session_id: str, inputs: str) -> str:
        """
        Perform a search and replace operation.

        Expects inputs in format:
        <<<<<<< SEARCH
        [original lines]
        =======
        [modified lines]
        >>>>>>> REPLACE
        """
        # Parse the search/replace block
        pattern = r'<<<<<<< SEARCH\s*(.*?)\s*=======\s*(.*?)\s*>>>>>>> REPLACE'
        match = re.search(pattern, inputs, re.DOTALL)

        if not match:
            return "Error: Invalid search/replace format. Expected format:\n<<<<<<< SEARCH\n...\n=======\n...\n>>>>>>> REPLACE"

        search_text = match.group(1).strip()
        replace_text = match.group(2).strip()

        # Get the latest file version
        latest_version = db.get_latest_file_version(session_id, "passage")

        if not latest_version:
            return "Error: No file found to edit. Please create a passage first."

        current_content = latest_version['content']

        # Check if search text exists
        if search_text not in current_content:
            return f"Error: Search text not found in current passage.\nSearching for:\n{search_text[:100]}..."

        # Perform replacement
        new_content = current_content.replace(search_text, replace_text, 1)

        # Save new version
        new_version = db.create_file_version(
            session_id=session_id,
            file_id="passage",
            content=new_content,
            editor=self.name,
            version_id=f"v-{int(time.time() * 1000)}",
        )

        return f"Successfully applied edit. New version: {new_version['version_id']}"

    async def _action_exit_edit_mode(self, session_id: str, summary: str) -> str:
        """Exit edit mode and return to chat mode."""
        # Switch back to chat mode
        self.set_mode("chat")

        # Create a message with the summary
        db.create_message(
            session_id=session_id,
            content=f"[Exiting edit mode] {summary}",
            role=self.name,
            metadata={
                "source": "agent",
                "mode": "chat",
                "action": "exit_edit_mode",
                "summary": summary
            }
        )
        return f"Exited edit mode. Summary: {summary}"
