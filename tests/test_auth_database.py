"""Runs against disposable PostgreSQL in CI, never a developer/Neon database."""
from contextlib import contextmanager
import os
import unittest
from unittest.mock import patch


@unittest.skipUnless(os.environ.get("AUTH_TEST_DATABASE_URL"), "PostgreSQL integration runs in CI")
class DatabaseTests(unittest.TestCase):
    def test_production_timeout_is_transaction_local(self):
        import psycopg
        from backend.security.database import Database

        real_connect = psycopg.connect
        url = os.environ["AUTH_TEST_DATABASE_URL"]

        def ci_connect(connection_url, **kwargs):
            self.assertNotIn("options", kwargs)
            # Only TLS is replaced for CI's disposable local PostgreSQL.
            kwargs.pop("sslmode")
            kwargs.pop("sslrootcert")
            return real_connect(connection_url, **kwargs)

        with patch("backend.security.database.psycopg.connect", side_effect=ci_connect):
            with Database(url).connect() as conn:
                self.assertEqual(
                    conn.execute("SHOW statement_timeout").fetchone()["statement_timeout"], "10s"
                )
                conn.commit()
                self.assertEqual(
                    conn.execute("SHOW statement_timeout").fetchone()["statement_timeout"], "0"
                )

    def setUp(self):
        import psycopg
        from psycopg.rows import dict_row
        from backend.security.database import Database

        class TestDatabase(Database):
            @contextmanager
            def connect(self):
                with psycopg.connect(self.url, row_factory=dict_row) as conn:
                    yield conn

        self.db = TestDatabase(os.environ["AUTH_TEST_DATABASE_URL"])
        self.db.migrate()
        self.db.migrate()
        self.db.check()
        with self.db.connect() as conn:
            conn.execute("TRUNCATE app_sessions, app_users, security_events RESTART IDENTITY")

    def test_migration_sessions_expiry_roles_and_revocation(self):
        self.db.allow_user("alice", "user")
        self.db.create_session("a" * 64, "alice", 123, False)
        self.assertEqual(self.db.session("a" * 64)["role"], "user")
        self.db.revoke("a" * 64)
        self.assertIsNone(self.db.session("a" * 64))
        for column in ("expires_at", "last_seen"):
            self.db.create_session("b" * 64, "alice", 123, False)
            with self.db.connect() as conn:
                # column is a fixed test literal, not external input.
                conn.execute(f"UPDATE app_sessions SET {column} = now() - interval '1 day'")
            self.assertIsNone(self.db.session("b" * 64))
        self.db.create_session("c" * 64, "alice", 123, False)
        self.db.allow_user("alice", "admin")
        self.assertIsNone(self.db.session("c" * 64))
        self.db.create_session("d" * 64, "alice", 123, True)
        self.db.disable_user("alice")
        self.assertIsNone(self.db.session("d" * 64))

    def test_foreign_key_and_parameterized_uid(self):
        import psycopg
        with self.assertRaises(psycopg.errors.ForeignKeyViolation):
            self.db.create_session("x" * 64, "unknown", 123, False)
        uid = "name'; DROP TABLE app_users; --"
        self.db.allow_user(uid, "user")
        self.assertEqual(self.db.user(uid)["firebase_uid"], uid)
        self.db.check()
