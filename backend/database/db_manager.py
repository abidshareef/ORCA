import os
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import psycopg2
from psycopg2.extras import RealDictCursor


class DatabaseManager:
    """Small PostgreSQL adapter supporting DATABASE_URL or individual variables."""

    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL", "").strip()
        self.conn_params = {
            "dbname": os.getenv("ORCA_DB_NAME", "orca_ecosystem"),
            "user": os.getenv("ORCA_DB_USER", "orca_user"),
            "password": os.getenv("ORCA_DB_PASSWORD", "orca_password"),
            "host": os.getenv("ORCA_DB_HOST", "localhost"),
            "port": os.getenv("ORCA_DB_PORT", "5432"),
        }

    def get_connection(self):
        if self.database_url:
            return psycopg2.connect(self.database_url, connect_timeout=5)
        return psycopg2.connect(**self.conn_params, connect_timeout=5)

    def execute_query(
        self, query: str, params: Optional[tuple] = None
    ) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                if cursor.description:
                    return [dict(row) for row in cursor.fetchall()]
                return []

    def fetch_one(
        self, query: str, params: Optional[tuple] = None
    ) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                row = cursor.fetchone()
                return dict(row) if row else None


db = DatabaseManager()
