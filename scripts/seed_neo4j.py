#!/usr/bin/env python3
"""
Bootstrap the Neo4j Relational Knowledge Graph (RKG).

1. Applies uniqueness constraints
2. Creates indexes
3. Optionally creates a test couple for local development

Run once on a fresh Neo4j instance:
  python scripts/seed_neo4j.py
  python scripts/seed_neo4j.py --seed-test-data
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse
import uuid

from neo4j import AsyncGraphDatabase

from backend.config import settings


SCHEMA_FILE = Path(__file__).parent.parent / "backend" / "graph" / "schema.cypher"


def parse_cypher_statements(cypher: str) -> list[str]:
    """Split a .cypher file into individual statements (split on ';')."""
    return [
        stmt.strip()
        for stmt in cypher.split(";")
        if stmt.strip() and not stmt.strip().startswith("//")
    ]


async def apply_schema(driver) -> None:
    print("  → Applying schema constraints and indexes...")
    cypher = SCHEMA_FILE.read_text()
    statements = parse_cypher_statements(cypher)

    async with driver.session() as session:
        for stmt in statements:
            if stmt.upper().startswith(("CREATE CONSTRAINT", "CREATE INDEX")):
                try:
                    await session.run(stmt)
                except Exception as e:
                    print(f"    ⚠ Skipped: {e}")
    print(f"  ✓ {len(statements)} schema statements processed.")


async def seed_test_data(driver) -> None:
    """Create a test couple for local development."""
    print("  → Seeding test data...")
    partner_a_id = str(uuid.uuid4())
    partner_b_id = str(uuid.uuid4())
    couple_id = str(uuid.uuid4())

    async with driver.session() as session:
        await session.run(
            """
            MERGE (pa:Person {user_id: $pa_id})
            SET pa.attachment_style = 'anxious', pa.couple_id = $couple_id
            MERGE (pb:Person {user_id: $pb_id})
            SET pb.attachment_style = 'avoidant', pb.couple_id = $couple_id
            MERGE (c:Couple {couple_id: $couple_id})
            SET c.primary_cycle = 'pursue-withdraw', c.eft_stage = 'de-escalation'
            MERGE (pa)-[:PARTNER_IN]->(c)
            MERGE (pb)-[:PARTNER_IN]->(c)
            """,
            pa_id=partner_a_id,
            pb_id=partner_b_id,
            couple_id=couple_id,
        )
    print(f"  ✓ Test couple created: {couple_id}")
    print(f"    Partner A: {partner_a_id}")
    print(f"    Partner B: {partner_b_id}")


async def main(seed: bool = False) -> None:
    print("🔧 Seeding Trinity RKG (Neo4j)...")

    driver = AsyncGraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )

    try:
        await driver.verify_connectivity()
        print("  ✓ Connected to Neo4j.")

        await apply_schema(driver)

        if seed:
            await seed_test_data(driver)

    finally:
        await driver.close()

    print("\n✅ RKG seeding complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed-test-data", action="store_true")
    args = parser.parse_args()
    asyncio.run(main(seed=args.seed_test_data))
