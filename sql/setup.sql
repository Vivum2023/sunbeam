CREATE TABLE IF NOT EXISTS resources (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    url TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL UNIQUE,
    role_name TEXT NOT NULL,
    is_hod BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS finance_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL,
    role_name TEXT NOT NULL,
    is_hod BOOLEAN NOT NULL,
    name TEXT NOT NULL,
    note TEXT NOT NULL,
    amount BIGINT NOT NULL, -- Negative for cost, positive for revenue, value in paise
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    valid BOOLEAN NOT NULL DEFAULT TRUE,
    live_note TEXT NOT NULL DEFAULT ''
);