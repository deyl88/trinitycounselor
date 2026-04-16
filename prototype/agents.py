"""
Trinity Counselor — Agent Definitions

Three agents. One relational intelligence system.
"""

import json
import random
import time

import anthropic

client = anthropic.Anthropic(timeout=120.0)


def _call_with_retry(max_retries: int = 3, base_delay: float = 1.0, **kwargs):
    """
    Wrap client.messages.create() with exponential backoff retry.

    Retries on transient errors: APITimeoutError, APIConnectionError,
    InternalServerError. Does not retry 4xx client errors.
    """
    last_exc = None
    for attempt in range(max_retries):
        try:
            return client.messages.create(**kwargs)
        except (
            anthropic.APITimeoutError,
            anthropic.APIConnectionError,
            anthropic.InternalServerError,
        ) as exc:
            last_exc = exc
            if attempt < max_retries - 1:
                delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), 30.0)
                time.sleep(delay)
    raise last_exc

# ── System Prompts ────────────────────────────────────────────────────────────

PARTNER_AGENT_SYSTEM = """
You are a private, compassionate AI counselor supporting {partner_name}.
You hold a completely confidential space — nothing shared here is ever shown to their partner.

Your approach:
- Deep, unhurried listening. You never rush toward solutions.
- Therapist-style questions that invite reflection rather than debate.
- You reflect patterns and themes back gently, without judgment.
- You hold both compassion and honest insight in balance.
- You speak in plain, warm language — never clinical jargon.

You are informed by (but not rigidly bound to):
- Emotionally Focused Therapy (EFT) — understanding attachment needs beneath surface conflict
- Gottman Method — recognizing Four Horsemen patterns, celebrating repair attempts
- Internal Family Systems — helping {partner_name} understand their own parts and protective behaviors
- Attachment Theory — understanding their relational patterns and style

Your goal is not to fix the relationship. Your goal is to help {partner_name}:
1. Understand their own emotional experience clearly
2. Connect their current feelings to underlying needs
3. Find language for things that feel unspeakable
4. Develop capacity for self-reflection

Current therapeutic context for {partner_name}:
{therapeutic_summary}
"""

RELATIONSHIP_COUNSELOR_SYSTEM = """
You are the Relationship Counselor in the Trinity system.
Your client is the relationship itself — not either individual partner.

You hold both partners with equal compassion and strict neutrality.
You are never an advocate for either partner's position.

Your role:
- See the relational system, not just individual perspectives
- Translate between partners' different emotional languages
- Surface blind spots and circular patterns neither partner can see alone
- Guide repair conversations with care and structure
- Celebrate growth and reconnection

Critical constraint — Privacy:
You have access only to abstracted relational themes, not private disclosures.
You must NEVER reveal or reference private content.
When you reference patterns, you speak in collective terms:
  WRONG: "One of you has expressed feeling unheard."
  RIGHT: "Feeling heard and understood seems like an important theme in your relationship right now."

You are informed by:
- EFT — attachment cycles and the underlying question "Are you there for me?"
- Gottman Method — the architecture of relationship health and repair
- Family Systems Theory — the relationship as a self-regulating system
- Esther Perel — desire, distance, aliveness, and the long game of intimate partnership

Current state of the relationship:
{relational_model}

Active themes surfaced from both partners (abstracted):
{active_themes}
"""

# ── Signal Abstraction Protocol (SAP) ────────────────────────────────────────

SAP_SYSTEM = """
You extract relational themes from personal conversation transcripts.

Rules:
- Extract ONLY categorical themes, emotional patterns, and need states
- NEVER quote, paraphrase, or reference specific statements
- NEVER include names, identifying details, or specific events
- Output must be a valid JSON array only — no other text

Output format:
[
  {
    "theme": "short descriptive label",
    "category": "one of: connection|trust|communication|intimacy|safety|shared_purpose|resentment|grief|respect|autonomy",
    "intensity": 0.0-1.0,
    "valence": "positive|negative|mixed"
  }
]
"""


# ── Agent Classes ─────────────────────────────────────────────────────────────

class PartnerAgent:
    """
    Private counselor for one partner.
    Has full access to that partner's context.
    Emits only abstracted signals to the RIL.
    """

    def __init__(self, partner_name: str):
        self.partner_name = partner_name
        self.conversation_history: list[dict] = []
        self.therapeutic_summary: str = "No prior sessions. This is the beginning."
        self.recent_messages_buffer: list[str] = []

    def _build_system(self) -> str:
        return PARTNER_AGENT_SYSTEM.format(
            partner_name=self.partner_name,
            therapeutic_summary=self.therapeutic_summary,
        )

    def respond(self, user_message: str) -> str:
        self.conversation_history.append({"role": "user", "content": user_message})
        self.recent_messages_buffer.append(user_message)

        response = _call_with_retry(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=self._build_system(),
            messages=self.conversation_history,
        )

        reply = response.content[0].text
        self.conversation_history.append({"role": "assistant", "content": reply})

        # Auto-compress context every 10 exchanges
        if len(self.conversation_history) > 20:
            self._compress_context()

        return reply

    def _compress_context(self):
        """Compress old conversation into therapeutic summary to manage context window."""
        history_text = "\n".join(
            f"{m['role'].upper()}: {m['content']}"
            for m in self.conversation_history[:-6]  # keep last 6 turns fresh
        )

        compression_prompt = f"""
        You are updating a therapeutic summary for an ongoing counseling relationship.

        EXISTING SUMMARY:
        {self.therapeutic_summary}

        NEW CONVERSATION:
        {history_text}

        Write an updated therapeutic summary (max 400 words) covering:
        - Key emotional themes and patterns observed
        - Apparent attachment style and relational tendencies
        - Recurring needs and pain points
        - Growth edges and strengths
        - Current therapeutic direction and open threads

        Do not include specific quotes. Write in third person ("The client...").
        """

        response = _call_with_retry(
            model="claude-sonnet-4-6",
            max_tokens=600,
            system="You maintain therapeutic summaries. Be precise, compassionate, and pattern-focused.",
            messages=[{"role": "user", "content": compression_prompt}],
        )

        self.therapeutic_summary = response.content[0].text
        # Keep only last 6 turns after compression
        self.conversation_history = self.conversation_history[-6:]

    def extract_ril_signals(self) -> list[dict]:
        """
        Privacy-preserving signal extraction.
        This is the ONLY data that leaves the private context.
        """
        if not self.recent_messages_buffer:
            return []

        messages_text = "\n".join(self.recent_messages_buffer)
        self.recent_messages_buffer = []  # clear buffer after extraction

        response = _call_with_retry(
            model="claude-sonnet-4-6",
            max_tokens=512,
            system=SAP_SYSTEM,
            messages=[{"role": "user", "content": f"Extract themes from:\n{messages_text}"}],
        )

        try:
            signals = json.loads(response.content[0].text)
            # Tag source without content
            for signal in signals:
                signal["source"] = self.partner_name.lower().replace(" ", "_")
            return signals
        except json.JSONDecodeError:
            return []


class RelationshipCounselor:
    """
    The third presence. Holds the relationship as its client.
    Operates only from abstracted relational model — never private data.
    """

    def __init__(self):
        self.conversation_history: list[dict] = []
        self.relational_model: str = "Early relationship — context being established."
        self.active_themes: list[dict] = []

    def update_from_ril(self, signals: list[dict]):
        """Receive abstracted signals from both private agents via RIL."""
        self.active_themes.extend(signals)
        # Keep only most recent 20 signals
        self.active_themes = self.active_themes[-20:]
        self._refresh_relational_model()

    def _refresh_relational_model(self):
        if not self.active_themes:
            return

        themes_text = "\n".join(
            f"- {s['theme']} ({s['category']}, intensity: {s['intensity']:.1f})"
            for s in self.active_themes
        )

        refresh_prompt = f"""
        Update the relational dynamic summary based on these abstracted signals:

        {themes_text}

        Current model: {self.relational_model}

        Write a concise updated model (max 200 words) describing:
        - Dominant relational themes right now
        - Apparent dynamic patterns
        - Health dimensions (connection, trust, communication, safety, intimacy)
        - Recommended focus for counseling

        Write in observational, non-attributive language.
        """

        response = _call_with_retry(
            model="claude-sonnet-4-6",
            max_tokens=300,
            system="You model relational dynamics from abstracted signals. No attribution to individuals.",
            messages=[{"role": "user", "content": refresh_prompt}],
        )

        self.relational_model = response.content[0].text

    def _build_system(self) -> str:
        themes_summary = (
            "\n".join(f"- {s['theme']} ({s['category']})" for s in self.active_themes[-10:])
            or "No signals yet — relationship context building."
        )
        return RELATIONSHIP_COUNSELOR_SYSTEM.format(
            relational_model=self.relational_model,
            active_themes=themes_summary,
        )

    def respond(self, speaker: str, message: str) -> str:
        """Respond in a session where speaker is identified but context is relational."""
        contextualized_message = f"[{speaker}]: {message}"
        self.conversation_history.append({"role": "user", "content": contextualized_message})

        response = _call_with_retry(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=self._build_system(),
            messages=self.conversation_history,
        )

        reply = response.content[0].text
        self.conversation_history.append({"role": "assistant", "content": reply})
        return reply


# ── Trinity System Orchestrator ───────────────────────────────────────────────

class TrinitySystem:
    """
    Top-level orchestrator for the three-agent system.
    Manages session modes and RIL signal flow.
    """

    def __init__(self, partner_a_name: str, partner_b_name: str):
        self.agent_a = PartnerAgent(partner_a_name)
        self.agent_b = PartnerAgent(partner_b_name)
        self.relationship_counselor = RelationshipCounselor()
        self.partner_a_name = partner_a_name
        self.partner_b_name = partner_b_name

    def solo_session(self, partner: str, message: str) -> str:
        """Private session with one partner's counselor."""
        if partner == "a":
            return self.agent_a.respond(message)
        elif partner == "b":
            return self.agent_b.respond(message)
        raise ValueError(f"Unknown partner: {partner}")

    def sync_to_ril(self):
        """Push abstracted signals from both private agents to relationship counselor."""
        signals_a = self.agent_a.extract_ril_signals()
        signals_b = self.agent_b.extract_ril_signals()
        all_signals = signals_a + signals_b
        if all_signals:
            self.relationship_counselor.update_from_ril(all_signals)

    def joint_session(self, speaker_partner: str, message: str) -> str:
        """Joint session mediated by the Relationship Counselor."""
        speaker_name = (
            self.partner_a_name if speaker_partner == "a" else self.partner_b_name
        )
        return self.relationship_counselor.respond(speaker_name, message)
