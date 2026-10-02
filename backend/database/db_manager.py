import psycopg2
from psycopg2.extras import RealDictCursor
import os
from typing import List, Dict, Any, Optional

class DatabaseManager:
    def __init__(self):
        # In a real production app, these would come from environment variables
        self.conn_params = {
            "dbname": os.getenv("ORCA_DB_NAME", "orca_db"),
            "user": os.getenv("ORCA_DB_USER", "postgres"),
            "password": os.getenv("ORCA_DB_PASSWORD", "postgres"),
            "host": os.getenv("ORCA_DB_HOST", "localhost"),
            "port": os.getenv("ORCA_DB_PORT", "5432")
        }

    def get_connection(self):
        return psycopg2.connect(**self.conn_params)

    def execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                if cur.description:
                    return cur.fetchall()
                conn.commit()
                return []

    def fetch_one(self, query: str, params: tuple = None) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                return cur.fetchone()

db = DatabaseManager()
