"""
Storage backends for mappings.json.

Supports:
- Local file (default)
- Supabase table (when SUPABASE_URL and SUPABASE_KEY are set)

To use Supabase:
1. Create a free project at https://supabase.com
2. Create a table named `mappings` with columns:
   - id (text, primary key) — e.g. "default"
   - data (jsonb) — the mappings object
   - updated_at (timestamptz)
3. Enable Row Level Security and allow appropriate access.
4. Set env vars:
   - SUPABASE_URL
   - SUPABASE_KEY
   - SUPABASE_TABLE (optional, default: mappings)
   - SUPABASE_ROW_ID (optional, default: default)
"""

import json
import os
from datetime import datetime, timezone
from typing import Optional


class StorageError(Exception):
    pass


class LocalFileStorage:
    def __init__(self, path: str):
        self.path = path

    def load(self) -> dict:
        abs_path = os.path.abspath(self.path)
        print(f"[storage] Looking for mappings at: {abs_path} (exists={os.path.exists(abs_path)})")
        if not os.path.exists(self.path):
            return {}
        with open(self.path, "r", encoding="utf-8") as f:
            data = json.load(f)
            print(f"[storage] Loaded {len(data)} mapping(s)")
            return data

    def save(self, mappings: dict):
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(mappings, f, indent=2)
            f.write("\n")


class SupabaseStorage:
    def __init__(self, url: str, key: str, table: str = "mappings", row_id: str = "default"):
        from supabase import create_client

        self.client = create_client(url, key)
        self.table = table
        self.row_id = row_id

    def load(self) -> dict:
        response = (
            self.client.table(self.table)
            .select("data")
            .eq("id", self.row_id)
            .execute()
        )

        if not response.data:
            return {}

        data = response.data[0].get("data")
        return data if isinstance(data, dict) else json.loads(data)

    def save(self, mappings: dict):
        payload = {
            "id": self.row_id,
            "data": mappings,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        existing = (
            self.client.table(self.table)
            .select("id")
            .eq("id", self.row_id)
            .execute()
        )

        if existing.data:
            response = (
                self.client.table(self.table)
                .update(payload)
                .eq("id", self.row_id)
                .execute()
            )
        else:
            response = self.client.table(self.table).insert(payload).execute()

        if hasattr(response, "error") and response.error:
            raise StorageError(f"Supabase error: {response.error}")


def get_storage(path: Optional[str] = None):
    """Return the appropriate storage backend based on environment variables."""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if supabase_url and supabase_key:
        table = os.getenv("SUPABASE_TABLE", "mappings")
        row_id = os.getenv("SUPABASE_ROW_ID", "default")
        return SupabaseStorage(supabase_url, supabase_key, table, row_id)

    default_path = os.path.join(os.path.dirname(__file__), "..", "mappings.json")
    return LocalFileStorage(path or os.getenv("MAPPINGS_FILE", default_path))
