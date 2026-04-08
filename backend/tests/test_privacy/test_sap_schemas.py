"""SAP schema validation tests — verifies the privacy firewall's data contracts."""

import pytest
from pydantic import ValidationError

from app.privacy.schemas import SAPSignal


def test_valid_sap_signal():
    signal = SAPSignal(
        signal_type="emotional_state",
        themes=["feeling_unheard", "emotional_exhaustion"],
        intensity=0.75,
        category="connection_deficit",
        valence="negative",
        source_tag="partner_a",
    )
    assert signal.intensity == 0.75
    assert signal.source_tag == "partner_a"


def test_sap_signal_intensity_bounds():
    with pytest.raises(ValidationError):
        SAPSignal(
            signal_type="emotional_state",
            themes=["test"],
            intensity=1.5,  # > 1.0 — should fail
            category="test",
            valence="negative",
            source_tag="partner_a",
        )


def test_sap_signal_requires_themes():
    with pytest.raises(ValidationError):
        SAPSignal(
            signal_type="emotional_state",
            themes=[],  # empty — min_length=1
            intensity=0.5,
            category="test",
            valence="negative",
            source_tag="partner_a",
        )


def test_sap_signal_rejects_overly_specific_theme():
    """Themes that are too long (>4 words) should be rejected — they're likely too specific."""
    with pytest.raises(ValidationError):
        SAPSignal(
            signal_type="emotional_state",
            themes=["partner said they feel abandoned because of work travel schedule"],
            intensity=0.5,
            category="test",
            valence="negative",
            source_tag="partner_a",
        )


def test_sap_signal_invalid_source_tag():
    with pytest.raises(ValidationError):
        SAPSignal(
            signal_type="emotional_state",
            themes=["test_theme"],
            intensity=0.5,
            category="test",
            valence="negative",
            source_tag="partner_c",  # invalid
        )


def test_sync_result_has_crisis_detector():
    from app.privacy.schemas import SAPExtractionResult

    result = SAPExtractionResult(
        signals=[
            SAPSignal(
                signal_type="crisis_indicator",
                themes=["self_harm_ideation"],
                intensity=0.9,
                category="safety_concern",
                valence="negative",
                source_tag="partner_a",
            )
        ],
        source_agent="agent_a",
        relationship_id="test-rel-id",
    )
    assert result.has_crisis_indicator is True


def test_namespace_access_enforcement():
    from app.core.exceptions import UnauthorizedNamespaceAccess
    from app.memory.pgvector_store import ConversationMemoryStore

    store = ConversationMemoryStore(
        user_id="user-a",
        agent_role="agent_a",
        relationship_id="rel-1",
        db=None,  # type: ignore — not needed for this test
    )
    with pytest.raises(UnauthorizedNamespaceAccess):
        store._validate_namespace_access("agent_b:rel-1")
