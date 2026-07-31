import unittest
import sqlite3

class TestPipelineDatabase(unittest.TestCase):
    def setUp(self):
        # Connect to your local database
        self.conn = sqlite3.connect('app_store_pipeline.db')
        self.cursor = self.conn.cursor()

    def test_ingestion_runs_logged(self):
        # Verify that the pipeline actually logged ingestion runs
        self.cursor.execute("SELECT COUNT(*) FROM ingestion_runs")
        count = self.cursor.fetchone()[0]
        self.assertGreater(count, 0, "Test Failed: No ingestion runs found in the database.")

    def test_composite_uniqueness(self):
        # Verify that the composite uniqueness rule successfully blocked duplicates
        self.cursor.execute('''
            SELECT review_id, app_id, storefront, COUNT(*)
            FROM normalized_reviews
            GROUP BY review_id, app_id, storefront
            HAVING COUNT(*) > 1
        ''')
        duplicates = self.cursor.fetchall()
        self.assertEqual(len(duplicates), 0, f"Test Failed: Found {len(duplicates)} duplicate reviews!")

    def tearDown(self):
        self.conn.close()

if __name__ == '__main__':
    unittest.main()