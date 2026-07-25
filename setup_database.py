import sqlite3

def init_db(db_path="app_store_pipeline.db"):
    # Connects to database (creates the file automatically if missing)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON;")

    # 1. Ingestion Runs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ingestion_runs (
        run_id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        target_app_id TEXT NOT NULL,
        target_storefront TEXT NOT NULL,
        api_page_limit INTEGER DEFAULT 10,
        api_review_limit INTEGER DEFAULT 500,
        status TEXT DEFAULT 'pending'
    );
    """)

    # 2. Raw Source Reviews Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS raw_reviews (
        raw_id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id INTEGER,
        app_id TEXT NOT NULL,
        storefront TEXT NOT NULL,
        raw_json_payload TEXT NOT NULL,
        ingested_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (run_id) REFERENCES ingestion_runs(run_id)
    );
    """)

    # 3. Normalized Reviews Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS normalized_reviews (
        db_id INTEGER PRIMARY KEY AUTOINCREMENT,
        review_id TEXT NOT NULL,
        app_id TEXT NOT NULL,
        storefront TEXT NOT NULL,
        app_version TEXT,
        rating INTEGER CHECK (rating >= 1 AND rating <= 5),
        title TEXT,
        review_text TEXT,
        review_timestamp DATETIME,
        
        -- Quality & Data Health Flags
        is_non_english INTEGER DEFAULT 0,
        is_low_signal INTEGER DEFAULT 0,
        is_repeated INTEGER DEFAULT 0,
        has_missing_fields INTEGER DEFAULT 0,
        
        -- Deduplication Constraint
        UNIQUE (review_id, app_id, storefront)
    );
    """)

    conn.commit()
    conn.close()
    print(f"✅ Database created successfully at '{db_path}'!")

if __name__ == "__main__":
    init_db()