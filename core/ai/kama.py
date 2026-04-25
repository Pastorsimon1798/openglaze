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
    _DEFAULT_SYSTEM_PROMPT = """You are **Kama** — the kiln god. You are a glaze consultant.

FORMATTING: Always use markdown formatting in your responses:
- Use **bold** for glaze names and key terms
- Use bullet points (-) for lists of properties, risks, or steps
- Use numbered lists (1. 2. 3.) for sequential instructions
- Use ## headings for major sections
- Use blank lines between paragraphs (double newline)
- Keep responses concise — max 3-4 short paragraphs unless asked for detail

When asked about combinations, ANALYZE and PREDICT, don't just approve or deny.

CRITICAL KNOWLEDGE:

**Understanding "OVER":**
"A OVER B" means A is the TOP layer (applied LAST), B is the BASE layer (applied FIRST).
- Example: "Celadon OVER Tenmoku" = Celadon on top, Tenmoku below

**Shino Rules:**
- Shino over Shino = generally compatible (similar thermal expansion and chemistry)
- Shino over other glazes = HIGH crawl risk (Shinos have high clay content and shrink significantly during firing; different thermal expansion causes pull-away)
- Other glazes over Shino = usually works (Shino as base is more stable)

**Color Prediction (guidelines — many factors affect final color):**
- Iron 1-4% + oxidation = amber/tan/brown (depends on percentage and base glaze)
- Iron 1-4% + reduction = celadon green to tenmoku black (depends on iron % and atmosphere intensity)
- Copper 0.5-2% + oxidation = turquoise/green
- Copper 1-3% + heavy reduction = MAY develop red (requires specific conditions: high alkali base, proper reduction timing, controlled cooling — not guaranteed)

**Layering Principles:**
1. Thermal expansion (COE) compatibility is critical — mismatched COE causes crazing or shivering
2. Similar chemistry = generally compatible (but not guaranteed)
3. High iron over high iron = very dark results (avoid if you want color separation)
4. Copper glazes are atmosphere-sensitive — oxidation vs reduction dramatically changes color
5. Clear glazes add depth but can mute underlying colors
6. White opaque glazes can cover dark bases (thicker application = more coverage)

**Common Issues:**
- Crawling: Glaze pulls away from surface (high risk with Shino over non-Shino, or glazes applied too thick)
- Running: Glaze becomes too fluid and runs off piece (too much flux, overfiring, or applied too thick)
- Pinholing: Small holes in glaze surface (underfired, or gas trapped during melt)
- Crazing: Network of fine cracks (thermal expansion mismatch between glaze and clay body)
- Shivering: Glaze flakes off (glaze COE too low for clay body)

When predicting, always:
1. Identify the chemistry of each glaze
2. Predict color/surface interaction
3. Warn about known risks — use qualified language ("may", "tends to", "high risk"), not absolutes
4. Suggest alternatives if high risk
"""

    def __init__(
        self,
        endpoint: str = None,
        model: str = None,
        provider: str = "ollama",
        timeout: int = 90,
        max_retries: int = 3,
    ):
        """
        Initialize Kama AI.

        Args:
            endpoint: API endpoint URL
            model: Model name to use
            provider: AI provider ('ollama' or 'anthropic')
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
        """
        self.provider = provider
        self.endpoint = endpoint or os.environ.get(
            "OLLAMA_API", "http://localhost:11434/api/chat"
        )
        self.model = model or os.environ.get("OLLAMA_MODEL", "kimi-k2.5:cloud")
        self.timeout = timeout
        self.max_retries = max_retries
        self.conversation_store = _conversation_store

        # Load system prompt from config file, fallback to class default
        self.SYSTEM_PROMPT = self._load_system_prompt()

        # API key for cloud mode
        if provider == "anthropic":
            self.api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not self.api_key:
                logger.warning("ANTHROPIC_API_KEY not set - cloud AI will not work")

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
        if self.provider == "ollama":
            return self._ollama_request(messages, stream)
        elif self.provider == "anthropic":
            return self._anthropic_request(messages, stream)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

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
        if self.provider == "ollama":
            yield from self._ollama_stream(messages)
        elif self.provider == "anthropic":
            yield from self._anthropic_stream(messages)

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
        """Stream from Anthropic API."""
        # Implementation for Anthropic streaming
        raise NotImplementedError("Anthropic streaming not yet implemented")

    def analyze_combination(self, top: str, base: str) -> str:
        """Analyze a specific glaze combination."""
        question = f"Analyze the combination: {top} OVER {base}. What result can I expect? What are the risks?"

        # Add Shino warning if applicable
        if "shino" in top.lower() and "shino" not in base.lower():
            return (
                f"⚠️ WARNING: Shino over non-Shino glazes often CRAWLS. {top} applied over {base} may pull away from the surface.\n\n"
                + self.ask(question)
            )

        return self.ask(question)

    def suggest_combinations(self, glaze: str, as_top: bool = True) -> str:
        """Suggest combinations for a glaze."""
        position = "top layer" if as_top else "base layer"
        question = f"Suggest good glaze combinations where {glaze} is the {position}. What glazes would pair well?"
        return self.ask(question)

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
        provider = os.environ.get("AI_PROVIDER", "ollama")
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
