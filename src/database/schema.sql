CREATE TABLE IF NOT EXISTS users (
  email TEXT PRIMARY KEY, name TEXT NOT NULL, picture TEXT,
  created_at BIGINT NOT NULL, updated_at BIGINT NOT NULL);
CREATE TABLE IF NOT EXISTS children (
  id TEXT PRIMARY KEY, parent_email TEXT NOT NULL REFERENCES users(email) ON DELETE CASCADE,
  name TEXT NOT NULL, age INT NOT NULL, grade INT NOT NULL, preferred_color TEXT,
  birthday DATE, created_at BIGINT NOT NULL, updated_at BIGINT NOT NULL);
CREATE INDEX IF NOT EXISTS children_parent_idx ON children(parent_email);
CREATE TABLE IF NOT EXISTS sessions (
  token TEXT PRIMARY KEY, user_email TEXT NOT NULL REFERENCES users(email) ON DELETE CASCADE,
  expires_at BIGINT NOT NULL);
CREATE TABLE IF NOT EXISTS worksheets (
  id TEXT PRIMARY KEY, child_id TEXT NOT NULL REFERENCES children(id) ON DELETE CASCADE,
  serial TEXT NOT NULL, problems JSONB NOT NULL, answers JSONB,
  completed BOOLEAN NOT NULL DEFAULT FALSE, incorrect_problems JSONB NOT NULL DEFAULT '[]',
  correct_answers JSONB, created_at BIGINT NOT NULL, updated_at BIGINT NOT NULL);
CREATE INDEX IF NOT EXISTS worksheets_child_idx ON worksheets(child_id, created_at DESC);
CREATE INDEX IF NOT EXISTS worksheets_serial_idx ON worksheets(serial);
CREATE TABLE IF NOT EXISTS device_tokens (
  id TEXT PRIMARY KEY, name TEXT NOT NULL, token_hash TEXT NOT NULL UNIQUE,
  created_at BIGINT NOT NULL, last_used_at BIGINT, revoked_at BIGINT);
