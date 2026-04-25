"""Tests for KamaAI context injection — ask_stream_with_context and _build_messages changes."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from unittest.mock import MagicMock


class TestBuildContext:
    """Test _build_messages with context parameter."""

    def test_context_injected_into_system_message(self, test_db_path):
        from core.ai.kama import KamaAI, ConversationMemory

        kama = KamaAI.__new__(KamaAI)
        kama.SYSTEM_PROMPT = "You are Kama."
        conversation = ConversationMemory(session_id="test")

        messages = kama._build_messages(
            "What is Chun Blue?", conversation, context="## Reference Data\nSome data"
        )
        system_msg = messages[0]["content"]
        assert "You are Kama." in system_msg
        assert "## Reference Data" in system_msg
        assert "Some data" in system_msg

    def test_no_context_when_no_match(self, test_db_path):
        from core.ai.kama import KamaAI, ConversationMemory

        kama = KamaAI.__new__(KamaAI)
        kama.SYSTEM_PROMPT = "You are Kama."
        conversation = ConversationMemory(session_id="test")

        messages = kama._build_messages("Hello", conversation)
        system_msg = messages[0]["content"]
        assert system_msg == "You are Kama."
        assert "Reference Data" not in system_msg

    def test_conversation_history_included(self, test_db_path):
        from core.ai.kama import KamaAI, ConversationMemory

        kama = KamaAI.__new__(KamaAI)
        kama.SYSTEM_PROMPT = "You are Kama."
        conversation = ConversationMemory(session_id="test")
        conversation.add_turn("user", "Previous question")
        conversation.add_turn("assistant", "Previous answer")

        messages = kama._build_messages("New question", conversation)
        # messages[0] = system, [1] = user history, [2] = assistant history, [3] = current user
        assert len(messages) == 4
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "Previous question"
        assert messages[2]["role"] == "assistant"
        assert messages[3]["role"] == "user"
        assert messages[3]["content"] == "New question"

    def test_backward_compatible_build_messages(self, test_db_path):
        """Calling without context param still works."""
        from core.ai.kama import KamaAI, ConversationMemory

        kama = KamaAI.__new__(KamaAI)
        kama.SYSTEM_PROMPT = "You are Kama."
        conversation = ConversationMemory(session_id="test")

        messages = kama._build_messages("Hello", conversation)
        assert len(messages) == 2  # system + user
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"


class TestAskStreamWithContext:
    """Test ask_stream_with_context method."""

    def test_yields_content_dicts(self, test_db_path):
        from core.ai.kama import KamaAI, ConversationMemory, _conversation_store
        from core.ai.context import ContextRetriever

        kama = KamaAI.__new__(KamaAI)
        kama.SYSTEM_PROMPT = "You are Kama."
        kama.conversation_store = _conversation_store
        kama._get_conversation = lambda sid=None, uid=None: ConversationMemory(
            session_id="test"
        )
        kama._stream_request = MagicMock(return_value=["chunk1", "chunk2"])

        retriever = ContextRetriever(test_db_path)
        events = list(
            kama.ask_stream_with_context(
                "Tell me about Chun Blue", context_retriever=retriever
            )
        )
        assert len(events) == 2
        assert events[0] == {"type": "content", "content": "chunk1"}
        assert events[1] == {"type": "content", "content": "chunk2"}

    def test_saves_conversation(self, test_db_path):
        from core.ai.kama import KamaAI, ConversationMemory
        from core.ai.context import ContextRetriever

        conversation = ConversationMemory(session_id="test-session")
        kama = KamaAI.__new__(KamaAI)
        kama.SYSTEM_PROMPT = "You are Kama."
        kama._get_conversation = lambda sid=None, uid=None: conversation
        kama._stream_request = MagicMock(return_value=["Hello from Kama"])

        retriever = ContextRetriever(test_db_path)
        list(
            kama.ask_stream_with_context(
                "What is pottery?", context_retriever=retriever
            )
        )

        assert len(conversation.turns) == 2
        assert conversation.turns[0].role == "user"
        assert conversation.turns[0].content == "What is pottery?"
        assert conversation.turns[1].role == "assistant"
        assert conversation.turns[1].content == "Hello from Kama"

    def test_context_in_system_message_via_stream(self, test_db_path):
        """Verify context from retriever appears in the messages sent to LLM."""
        from core.ai.kama import KamaAI, ConversationMemory
        from core.ai.context import ContextRetriever

        captured_messages = []
        conversation = ConversationMemory(session_id="test")

        def mock_stream(messages):
            captured_messages.extend(messages)
            return iter(["response"])

        kama = KamaAI.__new__(KamaAI)
        kama.SYSTEM_PROMPT = "You are Kama."
        kama._get_conversation = lambda sid=None, uid=None: conversation
        kama._stream_request = mock_stream

        retriever = ContextRetriever(test_db_path)
        list(
            kama.ask_stream_with_context(
                "Tell me about Chun Blue", context_retriever=retriever
            )
        )

        system_content = captured_messages[0]["content"]
        assert "## Reference Data" in system_content
        assert "Chun Blue" in system_content

    def test_no_context_still_streams(self, test_db_path):
        """When no context matches, streaming still works normally."""
        from core.ai.kama import KamaAI, ConversationMemory
        from core.ai.context import ContextRetriever

        captured_messages = []
        conversation = ConversationMemory(session_id="test")

        def mock_stream(messages):
            captured_messages.extend(messages)
            return iter(["response"])

        kama = KamaAI.__new__(KamaAI)
        kama.SYSTEM_PROMPT = "You are Kama."
        kama._get_conversation = lambda sid=None, uid=None: conversation
        kama._stream_request = mock_stream

        retriever = ContextRetriever(test_db_path)
        list(
            kama.ask_stream_with_context(
                "What is the meaning of life?", context_retriever=retriever
            )
        )

        system_content = captured_messages[0]["content"]
        assert "## Reference Data" not in system_content
        assert system_content == "You are Kama."
