import json
import asyncpg

from ..config import DB_URL, DB_NAME


class BroadcastDatabase:
    def __init__(self, conn):
        self.conn = conn

    @classmethod
    async def init(cls):
        conn = await asyncpg.create_pool(f'{DB_URL}/{DB_NAME}', min_size=3, max_size=3)
        return cls(conn)

    async def close(self):
        await self.conn.close()

    async def set_setting(self, key, value):
        await self.conn.execute(
            '''
            INSERT INTO settings (key, value) 
            VALUES ($1, $2)
            ON CONFLICT (key) DO UPDATE 
            SET value = $2
            ''',
            key, json.dumps(value),
        )

    async def get_setting(self, key, default=None):
        row = await self.conn.fetchrow('SELECT * FROM settings WHERE key = $1', key)
        if row:
            return json.loads(row['value'])
        return default
