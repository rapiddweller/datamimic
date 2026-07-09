-- Explicit sequence= test setup: a non-default schema plus a DBA-pre-created sequence,
-- mirroring the Benerator migration case (zsv.t_angebote_id_seq: existing, arbitrarily named).
CREATE SCHEMA IF NOT EXISTS migrated_schema;

-- Idempotency across test runs
DROP SEQUENCE IF EXISTS functional.custom_seq_name;
DROP SEQUENCE IF EXISTS migrated_schema.legacy_seq;

-- Pre-created at 500: generated ids must come from the 500-region, proving the generator FOUND
-- this sequence instead of minting a fresh one at 1 (which is what the pre-fix schema handling
-- would have done, if it didn't fail on the malformed 3-part identifier outright).
CREATE SEQUENCE migrated_schema.legacy_seq START 500;
