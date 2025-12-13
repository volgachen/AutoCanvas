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
        name = "Alice",
        model: str = "gpt-4.1-mini",
        temperature: float = 0.2,
        max_rounds: int = 15,
    ):
        """
        Initialize the baseline ReAct agent.

        Args:
            model: OpenAI model name
            temperature: Sampling temperature
            max_rounds: Maximum conversation rounds
            search_api_base_url: Base URL for search API
        """
        self.name = name
        self.model = model
        self.temperature = temperature
        # Initialize OpenAI client
        self.client = AsyncOpenAI(
            base_url=os.environ.get("OPENAI_BASE_URL", ""),
            api_key=os.environ.get("OPENAI_API_KEY", "")
        )

        # Parser
        self.parser = ReActParser()

        # System prompt
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
"""

        self.messages = [{
            "role": "system",
            "content": self.system_prompt,
        }]
        self.last_retrieve_time = None

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

        # TODO: add final instructions after the final message.
        instruction_message = {
            "role": "user",
            "content": "Now, your valid function is 'chat[The message you want to say in this conversation]', to provide your response to the current conversation."
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

        # TODO: make actions
        if action_name == "chat":
            # Create message in database
            db.create_message(
                session_id=session_id,
                content=arguments,
                role=self.name,
                metadata={
                    "source": "api"
                }
            )
