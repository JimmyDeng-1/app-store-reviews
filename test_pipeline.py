import unittest
import sqlite3
import tempfile
import os
from unittest.mock import patch, MagicMock
import ingestion_pipeline

class TestPipelineDatabase(unittest.TestCase):
    def setUp(self):
        # 1. Create a temporary, isolated database file for testing
        self.test_db_fd, self.test_db_path = tempfile.mkstemp()
        self.conn = sqlite3.connect(self.test_db_path)
        self.cursor = self.conn.cursor()
        
        # 2. Build the fresh schema
        self.cursor.execute('''
            CREATE TABLE ingestion_runs (
                run_id INTEGER PRIMARY KEY AUTOINCREMENT, app_id TEXT, storefront TEXT, page_limit INTEGER,
                run_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, finished_at DATETIME, status TEXT DEFAULT 'running',
                error_message TEXT, fetched_count INTEGER DEFAULT 0, inserted_count INTEGER DEFAULT 0,
                skipped_count INTEGER DEFAULT 0, failed_count INTEGER DEFAULT 0
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE raw_reviews (
                raw_id INTEGER PRIMARY KEY AUTOINCREMENT, run_id INTEGER, raw_payload JSON,
                FOREIGN KEY (run_id) REFERENCES ingestion_runs(run_id)
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE normalized_reviews (
                review_id TEXT, app_id TEXT, storefront TEXT, run_id INTEGER, raw_id INTEGER,
                date TEXT, rating INTEGER, title TEXT, review_text TEXT, version TEXT,
                is_low_signal BOOLEAN, has_missing_fields BOOLEAN,
                PRIMARY KEY (review_id, app_id, storefront),
                FOREIGN KEY (run_id) REFERENCES ingestion_runs(run_id),
                FOREIGN KEY (raw_id) REFERENCES raw_reviews(raw_id)
            )
        ''')
        self.conn.commit()

       # 3. Intercept the pipeline's DB connection to use our temp DB instead
        # We save the original sqlite3.connect function before we mock it
        original_connect = sqlite3.connect
        
        def mock_connect(db_path, *args, **kwargs):
            # We use the original function here so it doesn't infinite loop!
            return original_connect(self.test_db_path, *args, **kwargs)
        
        self.db_patcher = patch('ingestion_pipeline.sqlite3.connect', side_effect=mock_connect)
        self.db_patcher.start()

        # 4. Create a Fake API Response Fixture
        self.mock_payload = {
            "feed": {
                "entry": [
                    {"im:name": {"label": "Spotify"}}, # App metadata (should be skipped)
                    {
                        "id": {"label": "REV_001"}, "updated": {"label": "2023-10-01"},
                        "im:rating": {"label": "5"}, "title": {"label": "Great App"},
                        "content": {"label": "This app is absolutely wonderful!"}, "im:version": {"label": "8.8"}
                    },
                    {
                        "id": {"label": "REV_002"}, "updated": {"label": "2023-10-02"},
                        "im:rating": {"label": "1"}, "title": {"label": ""}, # Missing title
                        "content": {"label": "Bad."}, # <10 chars (low signal)
                        "im:version": {"label": "8.8"}
                    }
                ]
            }
        }

    def tearDown(self):
        # Clean up the isolated database
        self.db_patcher.stop()
        self.conn.close()
        os.close(self.test_db_fd)
        os.remove(self.test_db_path)

    @patch('ingestion_pipeline.requests.get')
    def test_1_first_run_inserts_and_lineage(self, mock_get):
        mock_get.return_value = MagicMock(json=lambda: self.mock_payload)
        ingestion_pipeline.run_ingestion('123', 'us', 1)
        
        self.cursor.execute("SELECT inserted_count, skipped_count, status FROM ingestion_runs")
        run = self.cursor.fetchone()
        self.assertEqual(run[0], 2, "Failed: Should insert exactly 2 valid reviews.")
        self.assertEqual(run[2], 'completed', "Failed: Run status should be 'completed'.")
        
        self.cursor.execute("SELECT raw_id FROM normalized_reviews")
        raw_ids = [row[0] for row in self.cursor.fetchall()]
        self.assertTrue(all(raw_ids), "Failed: Exact row-level lineage (raw_id) is missing!")

    @patch('ingestion_pipeline.requests.get')
    def test_2_idempotency_duplicate_skipping(self, mock_get):
        mock_get.return_value = MagicMock(json=lambda: self.mock_payload)
        ingestion_pipeline.run_ingestion('123', 'us', 1) # Run 1
        ingestion_pipeline.run_ingestion('123', 'us', 1) # Run 2
        
        self.cursor.execute("SELECT inserted_count, skipped_count FROM ingestion_runs ORDER BY run_id DESC LIMIT 1")
        run2 = self.cursor.fetchone()
        self.assertEqual(run2[0], 0, "Failed: Second run should insert 0 new reviews.")
        self.assertEqual(run2[1], 2, "Failed: Second run should flag 2 skipped duplicates.")

    @patch('ingestion_pipeline.requests.get')
    def test_3_cross_storefront_rule(self, mock_get):
        mock_get.return_value = MagicMock(json=lambda: self.mock_payload)
        ingestion_pipeline.run_ingestion('123', 'us', 1)
        ingestion_pipeline.run_ingestion('123', 'gb', 1) # Same reviews, different storefront
        
        self.cursor.execute("SELECT COUNT(*) FROM normalized_reviews")
        self.assertEqual(self.cursor.fetchone()[0], 4, "Failed: Cross-storefront uniqueness blocked valid inserts.")

    @patch('ingestion_pipeline.requests.get')
    def test_4_malformed_fields_processing(self, mock_get):
        mock_get.return_value = MagicMock(json=lambda: self.mock_payload)
        ingestion_pipeline.run_ingestion('123', 'us', 1)
        
        self.cursor.execute("SELECT is_low_signal, has_missing_fields FROM normalized_reviews WHERE review_id = 'REV_002'")
        flags = self.cursor.fetchone()
        self.assertTrue(flags[0], "Failed: Did not flag <10 char review as low signal.")
        self.assertTrue(flags[1], "Failed: Did not flag missing title.")

    @patch('ingestion_pipeline.requests.get')
    def test_5_failed_page_request(self, mock_get):
        mock_get.side_effect = Exception("API Timeout Simulation")
        ingestion_pipeline.run_ingestion('123', 'us', 1)
        
        self.cursor.execute("SELECT status, error_message FROM ingestion_runs")
        run = self.cursor.fetchone()
        self.assertEqual(run[0], 'failed', "Failed: Crash did not result in 'failed' status.")
        self.assertIn("API Timeout", run[1], "Failed: Error message not preserved.")

if __name__ == '__main__':
    unittest.main()