"""Tests for system prompt — ensure tool references are removed and context guidance added."""

import pytest
from pathlib import Path


@pytest.fixture
def prompt_text():
    prompt_path = Path(__file__).parent.parent / "config" / "kama-system-prompt.txt"
    return prompt_path.read_text()


class TestNoToolReferences:
    def test_no_call_tools(self, prompt_text):
        assert "call tools" not in prompt_text.lower()

    def test_no_use_tools(self, prompt_text):
        assert "use tools" not in prompt_text.lower()

    def test_no_tool_call(self, prompt_text):
        assert "tool call" not in prompt_text.lower()

    def test_no_database_tools(self, prompt_text):
        assert "database tools" not in prompt_text.lower()


class TestContextGuidance:
    def test_has_context_or_reference_data(self, prompt_text):
        lower = prompt_text.lower()
        assert "reference data" in lower or "context" in lower

    def test_no_chemistry_tool_instructions(self, prompt_text):
        """The old prompt said 'Use your tools to look up chemistry'."""
        lower = prompt_text.lower()
        assert "use your tools to look up" not in lower


class TestPersonalityPreserved:
    def test_has_who_you_are(self, prompt_text):
        assert "WHO YOU ARE" in prompt_text

    def test_has_voice(self, prompt_text):
        assert "VOICE" in prompt_text

    def test_has_over_semantics(self, prompt_text):
        assert '"OVER" SEMANTICS' in prompt_text

    def test_has_personality_rules(self, prompt_text):
        assert "RULES FOR PERSONALITY" in prompt_text

    def test_has_chemistry_knowledge_section(self, prompt_text):
        assert "CHEMISTRY KNOWLEDGE" in prompt_text
