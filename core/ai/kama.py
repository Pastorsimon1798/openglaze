"""
Kama - The Kiln God AI Assistant
Provides glaze consulting with chemistry knowledge and layering predictions.
Security-hardened with per-user conversation memory (March 2026).
"""

import os
import json
import time
import hashlib
import logging
import threading
from pathlib import Path
from typing import Generator, Optional, List, Dict, Any
from dataclasses import dataclass, field
import requests
from requests.exceptions import Timeout, ConnectionError

logger = logging.getLogger(__name__)


class AIServiceError(Exception):
    """AI service is unavailable."""

    pass


class RateLimitError(Exception):
    """Rate limit exceeded."""

    pass


@dataclass
class ConversationTurn:
    """A single turn in the conversation."""

    role: str
    content: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class ConversationMemory:
    """Conversation memory for a single user/session."""

    session_id: str
    turns: List[ConversationTurn] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)

    def add_turn(self, role: str, content: str) -> None:
        """Add a turn to the conversation."""
        self.turns.append(ConversationTurn(role=role, content=content))
        self.last_accessed = time.time()

        # Trim old turns if exceeds max (keep last 20)
        if len(self.turns) > 20:
            self.turns = self.turns[-20:]

    def get_messages(self) -> List[Dict[str, str]]:
        """Get messages in API format."""
        return [{"role": t.role, "content": t.content} for t in self.turns]

    def is_expired(self, max_age_hours: int = 24) -> bool:
        """Check if conversation has expired."""
        return time.time() - self.last_accessed > (max_age_hours * 3600)


class ConversationStore:
    """
    Thread-safe conversation store with automatic cleanup.

    Security features:
    - Per-user/session isolation
    - Automatic expiration
    - Memory limits
    """

    def __init__(self, max_age_hours: int = 24, cleanup_interval: int = 3600):
        self._conversations: Dict[str, ConversationMemory] = {}
        self._lock = threading.RLock()
        self.max_age_hours = max_age_hours
        self.cleanup_interval = cleanup_interval
        self._last_cleanup = time.time()

    def _session_key(self, session_id: Optional[str], user_id: Optional[str]) -> str:
        """Generate a unique key for session isolation."""
        if user_id:
            # In cloud mode, isolate by user
            return hashlib.sha256(f"user:{user_id}".encode()).hexdigest()[:32]
        elif session_id:
            # Session-based isolation
            return hashlib.sha256(f"session:{session_id}".encode()).hexdigest()[:32]
        else:
            # Anonymous (no persistence)
            return "anonymous"

    def get(
        self, session_id: Optional[str] = None, user_id: Optional[str] = None
    ) -> ConversationMemory:
        """Get or create conversation for session/user."""
        key = self._session_key(session_id, user_id)

        with self._lock:
            if key not in self._conversations:
                self._conversations[key] = ConversationMemory(session_id=key)

            self._conversations[key].last_accessed = time.time()

            # Periodic cleanup
            if time.time() - self._last_cleanup > self.cleanup_interval:
                self._cleanup_expired()

            return self._conversations[key]

    def clear(
        self, session_id: Optional[str] = None, user_id: Optional[str] = None
    ) -> None:
        """Clear conversation for session/user."""
        key = self._session_key(session_id, user_id)

        with self._lock:
            if key in self._conversations:
                del self._conversations[key]

    def clear_all(self) -> None:
        """Clear all conversations."""
        with self._lock:
            self._conversations.clear()

    def _cleanup_expired(self) -> None:
        """Remove expired conversations."""
        with self._lock:
            expired_keys = [
                k
                for k, v in self._conversations.items()
                if v.is_expired(self.max_age_hours)
            ]
            for key in expired_keys:
                del self._conversations[key]
            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} expired conversations")
            self._last_cleanup = time.time()

    def get_stats(self) -> Dict[str, Any]:
        """Get store statistics."""
        with self._lock:
            return {
                "total_conversations": len(self._conversations),
                "total_turns": sum(len(c.turns) for c in self._conversations.values()),
            }


# Global conversation store
_conversation_store = ConversationStore()


class KamaAI:
    """
    Kama is the kiln god - a glaze consultant AI.
    Analyzes and predicts glaze combinations based on chemistry.

    Security features (March 2026):
    - Per-user conversation isolation
    - Request timeouts
    - Rate limiting awareness
    - Error handling
    """

    # Default fallback prompt (used if config file doesn't exist)
    # Ceramics knowledge comes from the database via ContextRetriever (RAG),
    # NOT from this prompt. Keep this minimal — personality and formatting only.
    _DEFAULT_SYSTEM_PROMPT = """You are Kama — the kiln god, a glaze consultant who has watched potters fire for centuries.

FORMATTING: Always use markdown formatting:
- **bold** for glaze names and key terms
- Bullet points (-) for lists
- Numbered lists (1. 2. 3.) for steps
- ## headings for sections
- Blank lines between paragraphs
- Concise — 2-4 paragraphs unless asked for detail

"A OVER B" means A is the TOP layer (applied LAST), B is the BASE (applied FIRST).

Use the reference data provided with each question to ground your answers in specific glaze chemistry, combinations, and rules from the database. If the context doesn't contain enough information, say so.

ANALYZE and PREDICT — don't just approve or deny. Warn about risks with qualified language ("may", "tends to", "high risk"), not absolutes. Suggest alternatives. Happy accidents are real.
"""

    def __init__(
        self,
        endpoint: str = None,
        model: str = None,
        provider: str = "lmstudio",
        timeout: int = 90,
        max_retries: int = 3,
    ):
        """
        Initialize Kama AI.

        Args:
            endpoint: API endpoint URL
            model: Model name to use
            provider: AI provider ('lmstudio', 'ollama', or 'anthropic')
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
        """
        self.provider = provider
        self.timeout = timeout
        self.max_retries = max_retries
        self.conversation_store = _conversation_store

        # Resolve endpoint by provider
        if provider == "lmstudio":
            self.endpoint = endpoint or os.environ.get(
                "LM_STUDIO_URL",
                os.environ.get("LMSTUDIO_BASE_URL", "http://127.0.0.1:1234/v1"),
            )
            self.model = model or os.environ.get(
                "LM_STUDIO_MODEL",
                os.environ.get("LMSTUDIO_MODEL", ""),
            )
            self.api_key = os.environ.get("LM_STUDIO_API_KEY", "")
        elif provider == "ollama":
            self.endpoint = endpoint or os.environ.get(
                "OLLAMA_API", "http://localhost:11434/api/chat"
            )
            self.model = model or os.environ.get("OLLAMA_MODEL", "kimi-k2.5:cloud")
            self.api_key = ""
        elif provider == "anthropic":
            self.endpoint = endpoint or os.environ.get(
                "ANTHROPIC_API", "https://api.anthropic.com/v1/messages"
            )
            self.model = model or os.environ.get(
                "ANTHROPIC_MODEL", "claude-sonnet-4-20250514"
            )
            self.api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not self.api_key:
                logger.warning("ANTHROPIC_API_KEY not set - cloud AI will not work")
        else:
            raise ValueError(f"Unknown provider: {provider}")

        # Load system prompt from config file, fallback to class default
        self.SYSTEM_PROMPT = self._load_system_prompt()

    def _load_system_prompt(self) -> str:
        """Load system prompt from config file, fallback to default."""
        prompt_path = (
            Path(__file__).parent.parent.parent / "config" / "kama-system-prompt.txt"
        )
        try:
            if prompt_path.exists():
                with open(prompt_path, "r") as f:
                    prompt = f.read().strip()
                    if prompt:
                        logger.info(f"Loaded system prompt from {prompt_path}")
                        return prompt
        except Exception as e:
            logger.warning(f"Failed to load system prompt from file: {e}")
        logger.info("Using default system prompt")
        return self._DEFAULT_SYSTEM_PROMPT

    def _get_conversation(
        self, session_id: Optional[str] = None, user_id: Optional[str] = None
    ) -> ConversationMemory:
        """Get conversation memory for current session."""
        return self.conversation_store.get(session_id, user_id)

    def _build_messages(
        self,
        question: str,
        conversation: ConversationMemory,
        images: Optional[List[str]] = None,
        context: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """Build messages list with system prompt and history."""
        system_content = self.SYSTEM_PROMPT
        if context:
            system_content += f"\n\n## Reference Data\n{context}"
        messages = [{"role": "system", "content": system_content}]

        # Add conversation history
        messages.extend(conversation.get_messages())

        # Add current question (with images if provided - Ollama vision format)
        if images:
            messages.append({"role": "user", "content": question, "images": images})
        else:
            messages.append({"role": "user", "content": question})

        return messages

    def ask(
        self,
        question: str,
        context: dict = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        images: Optional[List[str]] = None,
    ) -> str:
        """
        Ask Kama a question (non-streaming).

        Args:
            question: The question to ask
            context: Optional context (glazes, combinations, etc.)
            session_id: Session ID for conversation isolation
            user_id: User ID for cloud mode isolation
            images: Optional list of base64-encoded image strings

        Returns:
            Kama's response text
        """
        conversation = self._get_conversation(session_id, user_id)
        messages = self._build_messages(question, conversation, images=images)

        try:
            response = self._make_request(messages, stream=False)
            response_text = response.get("message", {}).get("content", "No response")

            # Save to conversation
            conversation.add_turn("user", question)
            conversation.add_turn("assistant", response_text)

            return response_text

        except Timeout:
            raise AIServiceError("AI service timed out. Please try again.")
        except ConnectionError:
            raise AIServiceError("Cannot connect to AI service. Is Ollama running?")
        except Exception as e:
            logger.error(f"AI request failed: {e}")
            raise AIServiceError(f"AI service error: {str(e)}")

    def ask_stream(
        self,
        question: str,
        context: dict = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        images: Optional[List[str]] = None,
    ) -> Generator[str, None, None]:
        """
        Ask Kama a question with streaming response.

        Args:
            question: The question to ask
            context: Optional context
            session_id: Session ID for conversation isolation
            user_id: User ID for cloud mode isolation
            images: Optional list of base64-encoded image strings

        Yields:
            Chunks of Kama's response
        """
        conversation = self._get_conversation(session_id, user_id)
        messages = self._build_messages(question, conversation, images=images)
        full_response = ""

        try:
            for chunk in self._stream_request(messages):
                full_response += chunk
                yield chunk

            # Save to conversation after streaming completes
            if full_response:
                conversation.add_turn("user", question)
                conversation.add_turn("assistant", full_response)

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"\n\n[Error: {str(e)}]"

    def ask_stream_with_context(
        self,
        question: str,
        context_retriever,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        images: Optional[List[str]] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Ask Kama with RAG-style context injection.

        Retrieves relevant context from the database, injects it into
        the system prompt, and makes a single LLM call.

        Yields dicts: {"type": "content", "content": ...}
        """
        conversation = self._get_conversation(session_id, user_id)
        context = context_retriever.retrieve(question)
        messages = self._build_messages(
            question, conversation, images=images, context=context
        )
        full_response = ""

        for chunk in self._stream_request(messages):
            full_response += chunk
            yield {"type": "content", "content": chunk}

        if full_response:
            conversation.add_turn("user", question)
            conversation.add_turn("assistant", full_response)

    def _make_request(self, messages: List[Dict], stream: bool = False) -> Dict:
        """Make request to AI provider."""
        if self.provider == "lmstudio":
            return self._lmstudio_request(messages, stream)
        elif self.provider == "ollama":
            return self._ollama_request(messages, stream)
        elif self.provider == "anthropic":
            return self._anthropic_request(messages, stream)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    def _lmstudio_request(self, messages: List[Dict], stream: bool) -> Dict:
        """Make request to LM Studio (OpenAI-compatible)."""
        base = self.endpoint.rstrip("/")
        url = f"{base}/chat/completions"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "max_tokens": 4096,
        }

        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    url, json=payload, headers=headers, timeout=self.timeout
                )
                if response.status_code == 429:
                    raise RateLimitError("Rate limited by LM Studio")
                if response.status_code != 200:
                    raise AIServiceError(
                        f"LM Studio error: {response.status_code} {response.text[:200]}"
                    )
                return response.json()
            except (Timeout, ConnectionError):
                if attempt < self.max_retries - 1:
                    time.sleep(2**attempt)
                    continue
                raise

    def _ollama_request(self, messages: List[Dict], stream: bool) -> Dict:
        """Make request to Ollama."""
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
        }

        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    self.endpoint, json=payload, timeout=self.timeout
                )

                if response.status_code == 429:
                    raise RateLimitError("Rate limited by Ollama")

                if response.status_code != 200:
                    raise AIServiceError(f"Ollama error: {response.status_code}")

                return response.json()

            except (Timeout, ConnectionError):
                if attempt < self.max_retries - 1:
                    time.sleep(2**attempt)  # Exponential backoff
                    continue
                raise

    def _stream_request(self, messages: List[Dict]) -> Generator[str, None, None]:
        """Stream request to AI provider."""
        if self.provider == "lmstudio":
            yield from self._lmstudio_stream(messages)
        elif self.provider == "ollama":
            yield from self._ollama_stream(messages)
        elif self.provider == "anthropic":
            yield from self._anthropic_stream(messages)

    def _lmstudio_stream(self, messages: List[Dict]) -> Generator[str, None, None]:
        """Stream from LM Studio (OpenAI-compatible SSE)."""
        base = self.endpoint.rstrip("/")
        url = f"{base}/chat/completions"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "max_tokens": 4096,
        }

        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                stream=True,
                timeout=self.timeout,
            )
            if response.status_code != 200:
                raise AIServiceError(
                    f"LM Studio stream error: {response.status_code} {response.text[:200]}"
                )
            for line in response.iter_lines():
                if not line:
                    continue
                text = line.decode("utf-8", errors="replace")
                if not text.startswith("data: "):
                    continue
                data = text[6:]
                if data.strip() == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        yield content
                except json.JSONDecodeError:
                    pass
        except (Timeout, ConnectionError) as e:
            logger.error(f"LM Studio stream error: {e}")
            raise AIServiceError(f"LM Studio stream error: {e}")

    def _ollama_stream(self, messages: List[Dict]) -> Generator[str, None, None]:
        """Stream from Ollama."""
        try:
            response = requests.post(
                self.endpoint,
                json={"model": self.model, "messages": messages, "stream": True},
                stream=True,
                timeout=self.timeout,
            )

            for line in response.iter_lines():
                if line.strip():
                    try:
                        data = json.loads(line)
                        if "message" in data:
                            content = data["message"].get("content", "")
                            if content:
                                yield content
                    except json.JSONDecodeError:
                        pass

        except Exception as e:
            logger.error(f"Ollama stream error: {e}")
            raise AIServiceError(f"Ollama stream error: {e}")

    def _anthropic_request(self, messages: List[Dict], stream: bool) -> Dict:
        """Make request to Anthropic API."""
        if not self.api_key:
            raise AIServiceError("ANTHROPIC_API_KEY not configured")

        # Convert messages format for Anthropic
        system = messages[0]["content"]
        anthropic_messages = messages[1:]

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json={
                "model": self.model,
                "max_tokens": 4096,
                "system": system,
                "messages": anthropic_messages,
            },
            timeout=self.timeout,
        )

        if response.status_code != 200:
            raise AIServiceError(f"Anthropic error: {response.status_code}")

        return response.json()

    def _anthropic_stream(self, messages: List[Dict]) -> Generator[str, None, None]:
        """Stream from Anthropic API using SSE."""
        if not self.api_key:
            raise AIServiceError("ANTHROPIC_API_KEY not configured")

        system = messages[0]["content"]
        anthropic_messages = messages[1:]

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "max_tokens": 4096,
            "system": system,
            "messages": anthropic_messages,
            "stream": True,
        }

        try:
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=payload,
                timeout=self.timeout,
                stream=True,
            )

            if response.status_code != 200:
                raise AIServiceError(f"Anthropic stream error: {response.status_code}")

            for line in response.iter_lines():
                if not line:
                    continue
                line = line.decode("utf-8") if isinstance(line, bytes) else line
                if not line.startswith("data: "):
                    continue
                data_str = line[6:]
                if data_str.strip() == "[DONE]":
                    break
                try:
                    data = json.loads(data_str)
                    if data.get("type") == "content_block_delta":
                        delta = data.get("delta", {})
                        text = delta.get("text", "")
                        if text:
                            yield text
                except json.JSONDecodeError:
                    pass

        except AIServiceError:
            raise
        except Exception as e:
            logger.error(f"Anthropic stream error: {e}")
            raise AIServiceError(f"Anthropic stream error: {e}")

    def clear_conversation(
        self, session_id: Optional[str] = None, user_id: Optional[str] = None
    ) -> None:
        """Clear conversation for a session/user."""
        self.conversation_store.clear(session_id, user_id)


# Convenience functions
_default_kama: Optional[KamaAI] = None


def get_kama() -> KamaAI:
    """Get or create default Kama instance."""
    global _default_kama
    if _default_kama is None:
        provider = os.environ.get("AI_PROVIDER", "lmstudio")
        _default_kama = KamaAI(provider=provider)
    return _default_kama


def ask_kama(
    question: str,
    context: dict = None,
    clear: bool = False,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    images: Optional[List[str]] = None,
) -> str:
    """
    Ask Kama a question (convenience function).

    Args:
        question: The question to ask
        context: Optional context
        clear: Clear conversation memory before asking
        session_id: Session ID for conversation isolation
        user_id: User ID for cloud mode isolation
        images: Optional list of base64-encoded image strings

    Returns:
        Kama's response
    """
    kama = get_kama()
    if clear:
        kama.clear_conversation(session_id, user_id)
    return kama.ask(question, context, session_id, user_id, images=images)


def ask_kama_stream(
    question: str,
    context: dict = None,
    clear: bool = False,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    images: Optional[List[str]] = None,
) -> Generator[str, None, None]:
    """
    Ask Kama with streaming (convenience function).

    Args:
        question: The question to ask
        context: Optional context
        clear: Clear conversation memory before asking
        session_id: Session ID for conversation isolation
        user_id: User ID for cloud mode isolation
        images: Optional list of base64-encoded image strings

    Yields:
        Response chunks
    """
    kama = get_kama()
    if clear:
        kama.clear_conversation(session_id, user_id)
    yield from kama.ask_stream(question, context, session_id, user_id, images=images)
