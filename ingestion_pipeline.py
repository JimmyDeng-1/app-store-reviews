import sqlite3
import requests
import json

def run_ingestion(app_id, storefront, page_limit):
    print(f"--- Starting Ingestion Run for App: {app_id} | Storefront: {storefront} | Pages: {page_limit} ---")
    
    # Connect to DB
    conn = sqlite3.connect('app_store_pipeline.db')
    cursor = conn.cursor()
    
    # 1. Create Ingestion Run Record & Get Lineage ID
    cursor.execute('''
        INSERT INTO ingestion_runs (app_id, storefront, page_limit)
        VALUES (?, ?, ?)
    ''', (app_id, storefront, page_limit))
    run_id = cursor.lastrowid
    
    # Initialize Metrics
    fetched_count = 0
    inserted_count = 0
    skipped_count = 0
    failed_count = 0
    
    # 2. Controlled Pagination Loop
    for page in range(1, page_limit + 1):
        print(f"Fetching page {page}...")
        url = f"https://itunes.apple.com/{storefront}/rss/customerreviews/page={page}/id={app_id}/sortby=mostrecent/json"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            print(f"Failed or blocked on page {page}: {e}")
            break # Stop pagination if the API errors out
            
        entries = data.get('feed', {}).get('entry', [])
        if not entries:
            print("No more reviews found.")
            break
            
        # The Apple RSS API often includes app metadata as the first entry on page 1. We skip it.
        if page == 1 and isinstance(entries, list) and len(entries) > 0 and 'im:name' in entries[0]:
            entries = entries[1:]
            
        # 3. Process and Track Reviews
        for entry in entries:
            fetched_count += 1
            try:
                # Save Raw Payload for Lineage
                raw_payload_str = json.dumps(entry)
                cursor.execute('''
                    INSERT INTO raw_reviews (run_id, raw_payload)
                    VALUES (?, ?)
                ''', (run_id, raw_payload_str))
                
                # Extract Normalized Fields
                review_id = entry.get('id', {}).get('label', '')
                date = entry.get('updated', {}).get('label', '')
                rating = int(entry.get('im:rating', {}).get('label', 0))
                title = entry.get('title', {}).get('label', '')
                review_text = entry.get('content', {}).get('label', '')
                version = entry.get('im:version', {}).get('label', 'Unknown')
                
                # Quality Flags
                is_low_signal = len(review_text) < 10
                has_missing_fields = not all([review_id, date, rating, title, review_text])
                
                # Insert Normalized Record
                cursor.execute('''
                    INSERT INTO normalized_reviews 
                    (review_id, app_id, storefront, run_id, date, rating, title, review_text, version, is_low_signal, has_missing_fields)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (review_id, app_id, storefront, run_id, date, rating, title, review_text, version, is_low_signal, has_missing_fields))
                
                inserted_count += 1
                
            except sqlite3.IntegrityError:
                # Composite Uniqueness violation (this review was already inserted)
                skipped_count += 1
            except Exception:
                failed_count += 1
                
    # 4. Finalize Execution Metrics
    cursor.execute('''
        UPDATE ingestion_runs 
        SET fetched_count = ?, inserted_count = ?, skipped_count = ?, failed_count = ?
        WHERE run_id = ?
    ''', (fetched_count, inserted_count, skipped_count, failed_count, run_id))
    
    conn.commit()
    conn.close()
    
    print("\n--- Ingestion Run Complete ---")
    print(f"Run ID: {run_id}")
    print(f"Fetched: {fetched_count}")
    print(f"Inserted: {inserted_count}")
    print(f"Skipped (Duplicates): {skipped_count}")
    print(f"Failed: {failed_count}")

if __name__ == "__main__":
    # Parameterized Inputs
    TARGET_APP_ID = "324684580"  # Spotify
    TARGET_STOREFRONT = "us"
    TARGET_PAGES = 3  # Testing controlled pagination
    
    run_ingestion(TARGET_APP_ID, TARGET_STOREFRONT, TARGET_PAGES)