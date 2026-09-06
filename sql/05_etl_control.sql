USE ecommerce;

-- ============================================================
-- ETL job execution record
-- ============================================================

CREATE TABLE IF NOT EXISTS etl_runs (
    run_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,

    job_name VARCHAR(100) NOT NULL,
    source_file VARCHAR(500) NOT NULL,

    status ENUM(
        'RUNNING',
        'SUCCESS',
        'FAILED'
    ) NOT NULL DEFAULT 'RUNNING',

    started_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    finished_at DATETIME(3) NULL,

    total_source_rows BIGINT UNSIGNED NOT NULL DEFAULT 0,
    total_staging_rows BIGINT UNSIGNED NOT NULL DEFAULT 0,
    total_events_loaded BIGINT UNSIGNED NOT NULL DEFAULT 0,
    total_duplicates BIGINT UNSIGNED NOT NULL DEFAULT 0,

    error_message TEXT NULL,

    PRIMARY KEY (run_id),

    KEY idx_etl_runs_job_name (job_name),
    KEY idx_etl_runs_status (status),
    KEY idx_etl_runs_started_at (started_at)
) ENGINE=InnoDB;


-- ============================================================
-- ETL batch checkpoint
-- ============================================================

CREATE TABLE IF NOT EXISTS etl_batches (
    batch_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,

    run_id BIGINT UNSIGNED NOT NULL,

    batch_no INT UNSIGNED NOT NULL,

    source_start_row BIGINT UNSIGNED NOT NULL,
    source_end_row BIGINT UNSIGNED NOT NULL,

    source_rows BIGINT UNSIGNED NOT NULL DEFAULT 0,
    staging_rows BIGINT UNSIGNED NOT NULL DEFAULT 0,
    events_loaded BIGINT UNSIGNED NOT NULL DEFAULT 0,
    duplicates_skipped BIGINT UNSIGNED NOT NULL DEFAULT 0,

    status ENUM(
        'RUNNING',
        'SUCCESS',
        'FAILED'
    ) NOT NULL DEFAULT 'RUNNING',

    started_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    finished_at DATETIME(3) NULL,

    error_message TEXT NULL,

    PRIMARY KEY (batch_id),

    UNIQUE KEY uk_etl_batch_run_no (
        run_id,
        batch_no
    ),

    KEY idx_etl_batches_status (status),

    CONSTRAINT fk_etl_batches_run
        FOREIGN KEY (run_id)
        REFERENCES etl_runs (run_id)
        ON DELETE CASCADE
) ENGINE=InnoDB;