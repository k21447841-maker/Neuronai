from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class LLMResponse:
    content: str
    model: str
    input_tokens: int
    output_tokens: int
    raw: Dict[str, Any]


class BaseLLMProvider(ABC):
    slug: str

    @abstractmethod
    async def test_connection(self, api_key: str, model: str, timeout: int = 30) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def generate_text(
        self, api_key: str, model: str, system_prompt: str, user_prompt: str,
        temperature: float = 0.7, max_tokens: int = 4096, timeout: int = 60,
    ) -> LLMResponse:
        pass
