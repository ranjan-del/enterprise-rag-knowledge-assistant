"""LLM client wrapper.

MEMORY.md checklist:
- [ ] Answer generation with confidence, citations, highlighted text, source document
"""

from __future__ import annotations


class LLMClient:
    """Abstraction over the configured LLM provider.

    TODO: initialise the provider client from settings (llm_provider, llm_api_key).
    """

    def complete(self, prompt: str, context: list[str]) -> str:
        # TODO: build a RAG prompt with retrieved context and call the LLM.
        raise NotImplementedError
