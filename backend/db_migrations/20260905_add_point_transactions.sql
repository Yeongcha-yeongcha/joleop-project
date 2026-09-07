CREATE TABLE IF NOT EXISTS point_transactions (
    transaction_id BIGSERIAL PRIMARY KEY,
    profile_id BIGINT NOT NULL REFERENCES child_profiles(profile_id) ON DELETE RESTRICT,
    transaction_type VARCHAR(20) NOT NULL,
    amount INTEGER NOT NULL,
    label VARCHAR(180) NOT NULL,
    reference_type VARCHAR(40),
    reference_id BIGINT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_point_transactions_profile_id
    ON point_transactions(profile_id);

CREATE INDEX IF NOT EXISTS ix_point_transactions_profile_created
    ON point_transactions(profile_id, created_at DESC);
