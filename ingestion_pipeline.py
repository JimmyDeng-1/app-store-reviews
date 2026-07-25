import sqlite3
import requests
import json
from datetime import datetime

# --- Configuration ---
DB_PATH = "app_store_pipeline.db"
APP_ID = "324684580"  # Spotify's App ID
STOREFRONT = "gb"
API_URL = f"https://itunes.apple.com/{STOREFRONT}/rss/customerreviews/page=1/id={APP_ID}/sortby=mostrecent/json"

def run_ingestion_pipeline():
    print(f"Starting ingestion pipeline for App ID: {APP_ID} | Region: {STOREFRONT}")
    
    # 1. Connect to local SQLite database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 2. Create a new Ingestion Run record
    cursor.execute("""
        INSERT INTO ingestion_runs (target_app_id, target_storefront, status)
        VALUES (?, ?, 'running')
    """, (APP_ID, STOREFRONT))
    run_id = cursor.lastrowid

    try:
        # 3. Fetch data from Apple's Official API
        response = requests.get(API_URL)
        response.raise_for_status()
        raw_json_data = response.json()

        # 4. Store the untouched JSON payload for traceability
        cursor.execute("""
            INSERT INTO raw_reviews (run_id, app_id, storefront, raw_json_payload)
            VALUES (?, ?, ?, ?)
        """, (run_id, APP_ID, STOREFRONT, json.dumps(raw_json_data)))

        # 5. Extract and Normalize Reviews
        entries = raw_json_data.get('feed', {}).get('entry', [])
        inserted_count = 0

        for entry in entries:
            # Skip the first entry if it is app metadata rather than a user review
            if 'author' not in entry:
                continue

            # Parse fields safely
            review_id = entry.get('id', {}).get('label', '')
            app_version = entry.get('im:version', {}).get('label', '')
            rating = int(entry.get('im:rating', {}).get('label', '0'))
            title = entry.get('title', {}).get('label', '')
            review_text = entry.get('content', {}).get('label', '')
            review_timestamp = entry.get('updated', {}).get('label', '')

            # Apply Quality Flags (Data Health)
            is_low_signal = 1 if len(review_text) < 10 else 0
            has_missing_fields = 1 if not title or not review_text else 0

            # 6. Insert into Normalized Table (Ignore duplicates automatically)
            cursor.execute("""
                INSERT OR IGNORE INTO normalized_reviews 
                (review_id, app_id, storefront, app_version, rating, title, review_text, review_timestamp, is_low_signal, has_missing_fields)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (review_id, APP_ID, STOREFRONT, app_version, rating, title, review_text, review_timestamp, is_low_signal, has_missing_fields))
            
            # Check if a new row was actually inserted (not ignored)
            if cursor.rowcount > 0:
                inserted_count += 1

        # 7. Mark run as completed
        cursor.execute("UPDATE ingestion_runs SET status = 'completed' WHERE run_id = ?", (run_id,))
        conn.commit()
        print(f"✅ Success! Pipeline ingested {inserted_count} new normalized reviews.")

    except Exception as e:
        # If anything fails, mark the run as failed
        cursor.execute("UPDATE ingestion_runs SET status = 'failed' WHERE run_id = ?", (run_id,))
        conn.commit()
        print(f"❌ Pipeline failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    run_ingestion_pipeline()