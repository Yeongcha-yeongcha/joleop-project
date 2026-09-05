ALTER TABLE learning_attempts
ADD COLUMN IF NOT EXISTS word_results JSONB;
