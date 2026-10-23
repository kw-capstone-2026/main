-- Existing databases: run before starting the updated backend.
-- schema.sql changes alone do not update existing Docker volumes.
BEGIN;
ALTER TABLE shap_features ADD COLUMN IF NOT EXISTS feature_value NUMERIC;
COMMIT;
