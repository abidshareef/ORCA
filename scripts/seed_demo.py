"""Seed the checked-in ORCA demo scenarios into PostgreSQL.

Run from the repository root after applying backend/database/schema.sql:
    python scripts/seed_demo.py
"""
import json
from datetime import datetime, timezone
from pathlib import Path

from backend.database.db_manager import db

ROOT = Path(__file__).resolve().parents[1]
SCENARIO_FILE = ROOT / "data" / "demo" / "scenarios.json"


def main() -> None:
    payload = json.loads(SCENARIO_FILE.read_text(encoding="utf-8"))
    seeded = 0
    for scenario in payload.get("scenarios", []):
        if not scenario.get("locations"):
            continue
        location = scenario["locations"][0]
        state = location["state"]
        row = db.fetch_one(
            """
            INSERT INTO locations (name, geom, depth)
            VALUES (%s, ST_SetSRID(ST_MakePoint(%s, %s, %s), 4326), %s)
            ON CONFLICT (name) DO UPDATE
                SET geom = EXCLUDED.geom, depth = EXCLUDED.depth
            RETURNING id
            """,
            (
                scenario["name"],
                location["longitude"],
                location["latitude"],
                location.get("depth", 0.0),
                location.get("depth", 0.0),
            ),
        )
        location_id = row["id"]
        # Keep the seeder repeatable: replace the previous observation for this scenario.
        db.execute_query(
            "DELETE FROM ecosystem_observations WHERE location_id = %s",
            (location_id,),
        )
        db.execute_query(
            """
            INSERT INTO ecosystem_observations (
                location_id, timestamp, temperature, salinity, dissolved_oxygen,
                ph, chlorophyll, turbidity, pollution, biodiversity, fisheries, current
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                location_id,
                datetime.now(timezone.utc),
                state.get("temperature"),
                state.get("salinity"),
                state.get("dissolved_oxygen"),
                state.get("ph"),
                state.get("chlorophyll"),
                state.get("turbidity"),
                state.get("pollution"),
                state.get("biodiversity"),
                state.get("fisheries"),
                state.get("current"),
            ),
        )
        seeded += 1
    print(f"Seeded {seeded} ORCA scenarios into PostgreSQL.")


if __name__ == "__main__":
    main()
