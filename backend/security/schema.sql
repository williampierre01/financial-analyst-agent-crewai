CREATE TABLE IF NOT EXISTS auth_schema (version integer PRIMARY KEY);
CREATE TABLE IF NOT EXISTS app_users (
    firebase_uid varchar(128) PRIMARY KEY,
    role text NOT NULL CHECK (role IN ('user', 'admin')) DEFAULT 'user',
    active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS app_sessions (
    token_hash char(64) PRIMARY KEY,
    firebase_uid varchar(128) NOT NULL REFERENCES app_users(firebase_uid) ON DELETE CASCADE,
    auth_time bigint NOT NULL,
    mfa boolean NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    last_seen timestamptz NOT NULL DEFAULT now(),
    expires_at timestamptz NOT NULL DEFAULT now() + interval '8 hours'
);
CREATE INDEX IF NOT EXISTS app_sessions_user_idx ON app_sessions(firebase_uid);
CREATE TABLE IF NOT EXISTS security_events (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    event text NOT NULL,
    firebase_uid varchar(128),
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS security_events_time_idx ON security_events(created_at);
INSERT INTO auth_schema(version) VALUES (1) ON CONFLICT DO NOTHING;
