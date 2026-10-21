"""Small PostgreSQL repository. Connections are short lived to allow Neon to idle."""
from contextlib import contextmanager
from pathlib import Path
import os

import certifi
import psycopg
from psycopg.rows import dict_row


class Database:
    def __init__(self, url=None):
        self.url = url or os.environ.get("DATABASE_URL", "")
        if not self.url:
            raise RuntimeError("DATABASE_URL is required")

    @contextmanager
    def connect(self):
        # Never log the connection string. Verify both TLS and server identity.
        # Use an explicit CA bundle: binary libpq may not find the host trust store.
        with psycopg.connect(self.url, sslmode="verify-full", sslrootcert=certifi.where(), connect_timeout=10,
                             row_factory=dict_row) as conn:
            # Poolers reject startup options; LOCAL stays within this transaction.
            conn.execute("SET LOCAL statement_timeout = '10s'")
            yield conn

    def check(self):
        with self.connect() as conn:
            row = conn.execute("SELECT version FROM auth_schema WHERE version = 1").fetchone()
            if row is None:
                raise RuntimeError("Apply the authentication database migration first")

    def migrate(self):
        sql = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")
        with self.connect() as conn:
            conn.execute("SELECT pg_advisory_xact_lock(46190319)")
            conn.execute(sql)

    def user(self, uid):
        with self.connect() as conn:
            return conn.execute("SELECT * FROM app_users WHERE firebase_uid = %s", (uid,)).fetchone()

    def allow_user(self, uid, role):
        with self.connect() as conn:
            conn.execute("""INSERT INTO app_users(firebase_uid, role) VALUES (%s, %s)
                ON CONFLICT (firebase_uid) DO UPDATE SET role = EXCLUDED.role, active = true""", (uid, role))
            conn.execute("DELETE FROM app_sessions WHERE firebase_uid = %s", (uid,))
            conn.execute("INSERT INTO security_events(event, firebase_uid) VALUES ('account_authorized', %s)", (uid,))

    def disable_user(self, uid):
        with self.connect() as conn:
            conn.execute("UPDATE app_users SET active = false WHERE firebase_uid = %s", (uid,))
            conn.execute("DELETE FROM app_sessions WHERE firebase_uid = %s", (uid,))
            conn.execute("INSERT INTO security_events(event, firebase_uid) VALUES ('account_disabled', %s)", (uid,))

    def create_session(self, digest, uid, auth_time, mfa):
        with self.connect() as conn:
            conn.execute("DELETE FROM app_sessions WHERE expires_at <= now() OR last_seen <= now() - interval '30 minutes'")
            conn.execute("""INSERT INTO app_sessions(token_hash, firebase_uid, auth_time, mfa)
                VALUES (%s, %s, %s, %s)""", (digest, uid, auth_time, mfa))
            conn.execute("INSERT INTO security_events(event, firebase_uid) VALUES ('login', %s)", (uid,))
            conn.execute("DELETE FROM security_events WHERE created_at < now() - interval '30 days'")

    def session(self, digest):
        with self.connect() as conn:
            return conn.execute("""UPDATE app_sessions s SET last_seen = now()
                FROM app_users u WHERE s.token_hash = %s AND u.firebase_uid = s.firebase_uid
                AND u.active AND s.expires_at > now() AND s.last_seen > now() - interval '30 minutes'
                RETURNING s.*, u.role""", (digest,)).fetchone()

    def revoke(self, digest):
        with self.connect() as conn:
            row = conn.execute("DELETE FROM app_sessions WHERE token_hash = %s RETURNING firebase_uid", (digest,)).fetchone()
            if row:
                conn.execute("INSERT INTO security_events(event, firebase_uid) VALUES ('logout', %s)", (row["firebase_uid"],))

    def audit(self, event, uid=None):
        with self.connect() as conn:
            conn.execute("INSERT INTO security_events(event, firebase_uid) VALUES (%s, %s)", (event, uid))
