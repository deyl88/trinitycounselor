"""Privacy Mediator — orchestrates SAP signal processing and RKG sync.

The Privacy Mediator is the gatekeeper between the private and shared layers.
It:
  1. Pulls unprocessed SAP signals from the staging table (sap_signals_staging)
  2. Aggregates signals into relational patterns and needs
  3. Writes abstracted patterns to the Neo4j RKG via rkg/queries.py
  4. Marks staging records as processed

Crucially, the Mediator NEVER passes raw private content to the RKG.
It only uses the abstracted SAPSignal objects that were already
extracted by the SAP module.

Status: STUB — interfaces fully defined, orchestration logic stubbed
with clear TODO markers. The SAP extraction path (used inline by
agents) is fully implemented in sap.py.

Trigger paths
─────────────
1. Async background sync — POST /v1/relationships/{id}/sync
2. Inline during store_memory node (via sap.py + stage_sap_signals)
   → Mediator picks up staged signals on next sync call
"""

from __future__ import annotations

import json

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.privacy.schemas import SAPSignal, SyncResult
from app.rkg import queries as rkg

logger = get_logger(__name__)


class PrivacyMediator:
    """Orchestrates the flow of abstracted patterns from private agents to the RKG.

    Args:
        db: Async SQLAlchemy session for reading the staging table.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def trigger_sap_sync(self, relationship_id: str) -> SyncResult:
        """Pull all unprocessed SAP signals for a relationship and sync to RKG.

        This is the primary entry point for the insight sync endpoint.
        It reads the staging table, aggregates signals, writes to Neo4j,
        and marks staging records as processed.

        Args:
            relationship_id: UUID of the relationship to sync.

        Returns:
            SyncResult with counts of what was written.
        """
        result = SyncResult(
            relationship_id=relationship_id,
            signals_processed=0,
            patterns_upserted=0,
            needs_upserted=0,
            events_recorded=0,
        )
        try:
            staged = await self._fetch_unprocessed_signals(relationship_id)
            if not staged:
                logger.debug("sap_sync_nothing_to_process", relationship_id=relationship_id)
                return result

            all_signals: list[SAPSignal] = []
            staging_ids: list[str] = []

            for row in staged:
                staging_ids.append(str(row["id"]))
                raw_signals = row["signals"]
                if isinstance(raw_signals, str):
                    raw_signals = json.loads(raw_signals)
                for raw in raw_signals:
                    try:
                        all_signals.append(SAPSignal(**raw))
                    except Exception as exc:
                        logger.warning("mediator_signal_parse_error", error=str(exc))

            result.signals_processed = len(all_signals)

            # Aggregate and write to RKG
            patterns_count, needs_count = await self._write_patterns_to_rkg(
                relationship_id, all_signals
            )
            result.patterns_upserted = patterns_count
            result.needs_upserted = needs_count

            # Mark staging records as processed
            await self._mark_processed(staging_ids)

            logger.info(
                "sap_sync_complete",
                relationship_id=relationship_id,
                signals=result.signals_processed,
                patterns=result.patterns_upserted,
            )
        except Exception as exc:
            logger.error("sap_sync_failed", relationship_id=relationship_id, error=str(exc))
            result.errors.append(str(exc))

        return result

    async def extract_patterns(
        self,
        user_id: str,
        recent_turns: list[dict],
        source_agent: str,
    ) -> list[SAPSignal]:
        """On-demand SAP extraction from recent conversation turns.

        Used when you need signals without a full staged-sync cycle —
        e.g., to prime the RKG after onboarding intake.

        Args:
            user_id: UUID of the user whose turns to process.
            recent_turns: List of {'user_message': str, 'ai_response': str} dicts.
            source_agent: "agent_a" or "agent_b".

        Returns:
            List of extracted SAPSignal objects.

        TODO: Implement aggregation logic (currently returns empty list).
        """
        from app.privacy.sap import SignalAbstractionProtocol

        sap = SignalAbstractionProtocol()
        all_signals: list[SAPSignal] = []

        for turn in recent_turns:
            signals = await sap.extract(
                user_message=turn.get("user_message", ""),
                ai_response=turn.get("ai_response", ""),
                source_agent=source_agent,
            )
            all_signals.extend(signals)

        return all_signals

    async def _fetch_unprocessed_signals(self, relationship_id: str) -> list[dict]:
        """Fetch unprocessed staging records for a relationship."""
        result = await self._db.execute(
            text(
                "SELECT id, source_agent, signals, created_at "
                "FROM sap_signals_staging "
                "WHERE relationship_id = :rel_id AND processed = false "
                "ORDER BY created_at ASC "
                "LIMIT 500"
            ),
            {"rel_id": relationship_id},
        )
        rows = result.fetchall()
        return [dict(r._mapping) for r in rows]

    async def _write_patterns_to_rkg(
        self,
        relationship_id: str,
        signals: list[SAPSignal],
    ) -> tuple[int, int]:
        """Aggregate signals and write to Neo4j RKG.

        TODO: Implement full aggregation logic:
          - Group signals by type and theme
          - Compute aggregate intensity (weighted average by recency)
          - Map signal themes to canonical RelationalPattern names
          - Detect NeedCluster from attachment_need signals
          - Create Events for crisis_indicator and connection_moment signals

        Currently writes one pattern per unique (signal_type, primary_theme) pair.
        """
        if not signals:
            return 0, 0

        patterns_count = 0
        needs_count = 0

        # Group signals by category for aggregation
        by_category: dict[str, list[SAPSignal]] = {}
        for signal in signals:
            key = f"{signal.signal_type}:{signal.themes[0] if signal.themes else 'unknown'}"
            by_category.setdefault(key, []).append(signal)

        for key, group in by_category.items():
            avg_intensity = sum(s.intensity for s in group) / len(group)
            primary_signal = max(group, key=lambda s: s.intensity)

            pattern_id = f"{relationship_id}:{key}"
            try:
                await rkg.upsert_pattern(
                    relationship_id=relationship_id,
                    pattern_id=pattern_id,
                    name=key.replace(":", " — ").replace("_", " ").title(),
                    category=primary_signal.category,
                    intensity=avg_intensity,
                )
                patterns_count += 1
            except Exception as exc:
                logger.warning("rkg_pattern_write_failed", error=str(exc))

            # Extract needs from attachment_need signals
            if primary_signal.signal_type == "attachment_need":
                for theme in primary_signal.themes:
                    need_id = f"{relationship_id}:{primary_signal.source_tag}:{theme}"
                    try:
                        await rkg.upsert_need_cluster(
                            pattern_id=pattern_id,
                            need_id=need_id,
                            theme=theme,
                            priority=avg_intensity,
                            partner_tag=primary_signal.source_tag,
                        )
                        needs_count += 1
                    except Exception as exc:
                        logger.warning("rkg_need_write_failed", error=str(exc))

        return patterns_count, needs_count

    async def _mark_processed(self, staging_ids: list[str]) -> None:
        """Mark staging records as processed so they aren't synced again."""
        if not staging_ids:
            return
        await self._db.execute(
            text("UPDATE sap_signals_staging SET processed = true WHERE id = ANY(:ids)"),
            {"ids": staging_ids},
        )
        await self._db.commit()
