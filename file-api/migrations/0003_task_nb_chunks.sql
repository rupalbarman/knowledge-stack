-- Records how many chunks an upsert_vectors task wrote to Milvus once it
-- completes. Null until completion, and not meaningful for delete_vectors
-- tasks. Read via files.latest_task_id (see analytics summary), the same
-- indirection already used for indexing_status - never mutated in place.
ALTER TABLE tasks ADD COLUMN nb_chunks INTEGER;
