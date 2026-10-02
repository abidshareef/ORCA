import json
import os
from backend.database.db_manager import db

def migrate_json_to_db():
    print("Starting migration of scenarios.json to database...")

    try:
        with open("data/demo/scenarios.json", "r") as f:
            data = json.load(f)

        for scenario in data["scenarios"]:
            print(f"Migrating scenario: {scenario['name']} ({scenario['id']})")

            for loc in scenario["locations"]:
                # 1. Insert Location
                # Note: we are simplifying geom as a point for now
                loc_query = """
                INSERT INTO locations (name, geom, depth)
                VALUES (%s, ST_SetSRID(ST_MakePoint(%s, %s), 4326), %s)
                RETURNING id
                """
                loc_params = (
                    scenario['name'],
                    loc['longitude'],
                    loc['latitude'],
                    loc['depth']
                )

                # The execute_query returns a list of dicts due to RealDictCursor
                loc_res = db.execute_query(loc_query, loc_params)
                if not loc_res:
                    print("Failed to insert location")
                    continue

                loc_id = loc_res[0]['id']

                # 2. Insert Observation
                obs_query = """
                INSERT INTO ecosystem_observations (
                    location_id, timestamp, temperature, salinity, dissolved_oxygen,
                    ph, chlorophyll, turbidity, pollution, biodiversity, fisheries, current
                ) VALUES (%s, NOW(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                state = loc['state']
                obs_params = (
                    loc_id,
                    state.get('temperature'),
                    state.get('salinity'),
                    state.get('dissolved_oxygen'),
                    state.get('ph'),
                    state.get('chlorophyll'),
                    state.get('turbidity'),
                    state.get('pollution'),
                    state.get('biodiversity'),
                    state.get('fisheries'),
                    state.get('current')
                )
                db.execute_query(obs_query, obs_params)

        print("Migration completed successfully.")

    except Exception as e:
        print(f"Migration failed: {str(e)}")

if __name__ == "__main__":
    migrate_json_to_db()
