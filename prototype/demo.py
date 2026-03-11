"""
Trinity Counselor — Interactive Demo

Run this to experience the system directly in your terminal.
Shows all three session modes and the privacy-preserving RIL sync.

Usage:
  python demo.py
"""

import os
from agents import TrinitySystem

def separator(title: str):
    print(f"\n{'═' * 60}")
    print(f"  {title}")
    print('═' * 60)

def demo():
    trinity = TrinitySystem(partner_a_name="Alex", partner_b_name="Jordan")

    # ── Phase 1: Private sessions ──────────────────────────────────

    separator("PRIVATE SESSION — Alex (Partner A)")
    print("Alex is speaking privately to their counselor.\n")

    alex_messages = [
        "I feel like Jordan and I have been disconnected lately. "
        "Every time I try to talk about it, they shut down or change the subject.",
        "I don't know if it's something I'm doing wrong. I just feel really lonely "
        "inside the relationship.",
    ]

    for msg in alex_messages:
        print(f"Alex: {msg}")
        response = trinity.solo_session("a", msg)
        print(f"\nCounselor A: {response}\n")
        input("  [press Enter to continue]")

    separator("PRIVATE SESSION — Jordan (Partner B)")
    print("Jordan is speaking privately to their counselor.\n")
    print("Note: Jordan's counselor has NO knowledge of what Alex said.\n")

    jordan_messages = [
        "I've been feeling overwhelmed at work and I think I've been pulling away "
        "from Alex. I feel guilty about it but I just don't have the emotional bandwidth.",
        "I can tell Alex is frustrated with me but when they bring it up "
        "I just don't know what to say so I go quiet.",
    ]

    for msg in jordan_messages:
        print(f"Jordan: {msg}")
        response = trinity.solo_session("b", msg)
        print(f"\nCounselor B: {response}\n")
        input("  [press Enter to continue]")

    # ── Phase 2: RIL Sync ──────────────────────────────────────────

    separator("RIL SYNC — Privacy-Preserving Signal Extraction")
    print("Extracting abstracted themes from both private sessions...")
    print("(No private content crosses this boundary)\n")

    trinity.sync_to_ril()

    print("Relational model updated:")
    print(f"\n{trinity.relationship_counselor.relational_model}\n")
    print("Active themes:")
    for theme in trinity.relationship_counselor.active_themes:
        print(f"  • {theme['theme']} [{theme['category']}] intensity: {theme.get('intensity', '?')}")

    input("\n  [press Enter to start joint session]")

    # ── Phase 3: Joint session ─────────────────────────────────────

    separator("JOINT SESSION — Relationship Counselor")
    print("Both partners are now in session together.")
    print("The Relationship Counselor works only from abstracted context.\n")

    joint_exchanges = [
        ("a", "Alex", "We wanted to come together because things have felt off between us."),
        ("b", "Jordan", "Yeah. I know I've been distant. I'm not sure how to explain it."),
        ("a", "Alex", "I've been feeling alone, even when we're in the same room."),
    ]

    for partner, name, msg in joint_exchanges:
        print(f"{name}: {msg}")
        response = trinity.joint_session(partner, msg)
        print(f"\nRelationship Counselor: {response}\n")
        input("  [press Enter to continue]")

    separator("DEMO COMPLETE")
    print("This demonstrated:")
    print("  1. Private counseling for each partner (no cross-contamination)")
    print("  2. Privacy-preserving RIL sync (themes only, no raw content)")
    print("  3. Joint session operating from abstracted relational model")
    print("\nThe relationship is the client.")


if __name__ == "__main__":
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: Set ANTHROPIC_API_KEY in your environment or .env file")
        exit(1)
    demo()
