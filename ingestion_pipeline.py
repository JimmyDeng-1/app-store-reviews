import sqlite3
import requests
import json
from datetime import datetime

def run_ingestion(app_id, storefront, page_limit):
    print(f"--- Starting Ingestion Run for App: {app_id} | Storefront: {storefront} | Pages: {page_limit} ---")
    
    # Connect to DB
    conn = sqlite3.connect('app_store_pipeline.db')
    cursor = conn.cursor()
    
    # 1. Create Ingestion Run Record (Status: running)
    cursor.execute('''
        INSERT INTO ingestion_runs (app_id, storefront, page_limit, status)
        VALUES (?, ?, ?, 'running')
    ''', (app_id, storefront, page_limit))
    run_id = cursor.lastrowid
    
    # Initialize Metrics
    fetched_count = 0
    inserted_count = 0
    skipped_count = 0
    failed_count = 0
    run_status = 'completed'
    error_msg = None
    
    try:
        # 2. Controlled Pagination Loop
        for page in range(1, page_limit + 1):
            print(f"Fetching page {page}...")
            url = f"https://itunes.apple.com/{storefront}/rss/customerreviews/page={page}/id={app_id}/sortby=mostrecent/json"
            
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()
            except Exception as e:
                # Log API error and determine if partial or completely failed
                error_msg = f"Failed on page {page}: {str(e)}"
                print(error_msg)
                run_status = 'partial' if (fetched_count > 0) else 'failed'
                break # Stop pagination safely
                
            entries = data.get('feed', {}).get('entry', [])
            if not entries:
                print("No more reviews found.")
                break
                
            # Skip the first entry if it is app metadata
            if page == 1 and isinstance(entries, list) and len(entries) > 0 and 'im:name' in entries[0]:
                entries = entries[1:]
                
            # 3. Process and Track Reviews
            for entry in entries:
                fetched_count += 1
                try:
                    # EXACT LINEAGE: Save Raw Payload FIRST to get the raw_id
                    raw_payload_str = json.dumps(entry)
                    cursor.execute('''
                        INSERT INTO raw_reviews (run_id, raw_payload)
                        VALUES (?, ?)
                    ''', (run_id, raw_payload_str))
                    raw_id = cursor.lastrowid 
                    
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
                    
                    # EXACT LINEAGE: Insert Normalized Record WITH raw_id
                    cursor.execute('''
                        INSERT INTO normalized_reviews 
                        (review_id, app_id, storefront, run_id, raw_id, date, rating, title, review_text, version, is_low_signal, has_missing_fields)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (review_id, app_id, storefront, run_id, raw_id, date, rating, title, review_text, version, is_low_signal, has_missing_fields))
                    
                    inserted_count += 1
                    
                except sqlite3.IntegrityError:
                    # Composite Uniqueness violation (duplicate)
                    skipped_count += 1
                except Exception as row_error:
                    failed_count += 1
                    print(f"Row insertion failed: {row_error}")
                    
        # Commit all successful inserts
        conn.commit()

    except Exception as critical_error:
        # 4. Transaction Protection: Rollback on unexpected DB crashes
        conn.rollback()
        run_status = 'failed'
        error_msg = f"Critical Database Error: {str(critical_error)}"
        print(error_msg)
        
    finally:
        # 5. Finalize Execution Metrics and Safely Close Connection
        try:
            cursor.execute('''
                UPDATE ingestion_runs 
                SET fetched_count = ?, inserted_count = ?, skipped_count = ?, failed_count = ?,
                    status = ?, error_message = ?, finished_at = CURRENT_TIMESTAMP
                WHERE run_id = ?
            ''', (fetched_count, inserted_count, skipped_count, failed_count, run_status, error_msg, run_id))
            conn.commit()
        except Exception as cleanup_error:
            print(f"Failed to update run status: {cleanup_error}")
        finally:
            conn.close()
        
        print("\n--- Ingestion Run Complete ---")
        print(f"Run ID: {run_id} | Status: {run_status.upper()}")
        print(f"Fetched: {fetched_count} | Inserted: {inserted_count} | Skipped: {skipped_count} | Failed: {failed_count}")

if __name__ == "__main__":
    # Parameterized Inputs
    TARGET_APP_ID = "324684580"  # Spotify
    TARGET_STOREFRONT = "us"
    TARGET_PAGES = 3  
    
    run_ingestion(TARGET_APP_ID, TARGET_STOREFRONT, TARGET_PAGES)