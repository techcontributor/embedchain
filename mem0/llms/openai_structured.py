import json
import os
from typing import Dict, List, Optional

from openai import OpenAI

from mem0.configs.llms.base import BaseLlmConfig
from mem0.llms.base import LLMBase


class OpenAIStructuredLLM(LLMBase):
    """
    A class for interacting with OpenAI's structured language models using the specified configuration.
    """

    def __init__(self, config: Optional[BaseLlmConfig] = None):
        """
        Initializes the OpenAIStructuredLLM instance with the given configuration.

        Args:
            config (Optional[BaseLlmConfig]): Configuration settings for the language model.
        """
        super().__init__(config)

        if not self.config.model:
            self.config.model = "gpt-4o-2024-08-06"

        api_key = self.config.api_key or os.getenv("OPENAI_API_KEY")
        base_url = (
            self.config.openai_base_url
            or os.getenv("OPENAI_API_BASE")
            or "https://api.openai.com/v1"
        )
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def _parse_response(self, response, tools):
        """
        Process the response based on whether tools are used or not.
        Args:
            response: The raw response from API.
            tools (list, optional): List of tools that the model can call.
        Returns:
            str or dict: The processed response.
        """

        if tools:
            processed_response = {
                "content": response.choices[0].message.content,
                "tool_calls": [],
            }

            if response.choices[0].message.tool_calls:
                for tool_call in response.choices[0].message.tool_calls:
                    processed_response["tool_calls"].append(
                        {
                            "name": tool_call.function.name,
                            "arguments": json.loads(tool_call.function.arguments),
                        }
                    )

            return processed_response

        else:
            return response.choices[0].message.content

    def generate_response(
        self,
        messages: List[Dict[str, str]],
        response_format: Optional[str] = None,
        tools: Optional[List[Dict]] = None,
        tool_choice: str = "auto",
    ) -> str:
        """
        Generates a response using OpenAI based on the provided messages.

        Args:
            messages (List[Dict[str, str]]): A list of dictionaries, each containing a 'role' and 'content' key.
            response_format (Optional[str]): The desired format of the response. Defaults to None.
            tools (Optional[List[Dict]]): A list of dictionaries, each containing a 'name' and 'arguments' key.
            tool_choice (str): The choice of tool to use. Defaults to "auto".

        Returns:
            str: The generated response from the model.
        """
        params = {
            "model": self.config.model,
            "messages": messages,
            "temperature": self.config.temperature,
        }

        if response_format:
            params["response_format"] = response_format
        if tools:
            params["tools"] = tools
            params["tool_choice"] = tool_choice

        response = self.client.beta.chat.completions.parse(**params)
        return self._parse_response(response, tools)
