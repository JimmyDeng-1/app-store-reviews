import sqlite3

def setup_database():
    # Connect to the database (this will create a fresh one since you deleted the old one)
    conn = sqlite3.connect('app_store_pipeline.db')
    cursor = conn.cursor()

    # 1. Update ingestion_runs with status tracking and timestamps
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ingestion_runs (
        run_id INTEGER PRIMARY KEY AUTOINCREMENT,
        app_id TEXT,
        storefront TEXT,
        page_limit INTEGER,
        run_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        finished_at DATETIME,
        status TEXT DEFAULT 'running',
        error_message TEXT,
        fetched_count INTEGER DEFAULT 0,
        inserted_count INTEGER DEFAULT 0,
        skipped_count INTEGER DEFAULT 0,
        failed_count INTEGER DEFAULT 0
    )
    ''')

    # 2. Raw reviews (remains mostly the same, but now we will fetch its ID later)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS raw_reviews (
        raw_id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id INTEGER,
        raw_payload JSON,
        FOREIGN KEY (run_id) REFERENCES ingestion_runs(run_id)
    )
    ''')

    # 3. Update normalized_reviews with exact raw_id lineage
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS normalized_reviews (
        review_id TEXT,
        app_id TEXT,
        storefront TEXT,
        run_id INTEGER,
        raw_id INTEGER,
        date TEXT,
        rating INTEGER,
        title TEXT,
        review_text TEXT,
        version TEXT,
        is_low_signal BOOLEAN,
        has_missing_fields BOOLEAN,
        PRIMARY KEY (review_id, app_id, storefront),
        FOREIGN KEY (run_id) REFERENCES ingestion_runs(run_id),
        FOREIGN KEY (raw_id) REFERENCES raw_reviews(raw_id)
    )
    ''')

    conn.commit()
    conn.close()
    print("Database schema successfully updated with exact lineage and status tracking!")

if __name__ == "__main__":
    setup_database()