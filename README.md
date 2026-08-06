# App Store Review Ingestion Pipeline (Phase I)

**Sciencia AI - Data Ingestion & Infrastructure**

This repository contains an automated data ingestion pipeline that fetches, normalizes, and stores customer reviews from the Apple App Store. This pipeline serves as the foundational ingestion layer for downstream feature engineering, product feedback analysis, and AI-powered sentiment modeling.

## Project Purpose & Methodology
The goal of this pipeline is to reliably acquire user-generated textual data, transform it into a usable structure, and maintain strict data lineage. 

* **Collection Methodology:** Data is collected using the official Apple iTunes RSS API with controlled, dynamic pagination.
* **Limitations:** The Apple API enforces a 500-review-per-app-per-storefront limit. While this restricts deep historical collection, the structural completeness of the payload provides an excellent foundation for recent app review monitoring.

## 🏗️ Architecture & Database Schema
The pipeline uses a local SQLite database (`app_store_pipeline.db`) structured to enforce exact row-level lineage and idempotency.

* **`ingestion_runs`**: Logs execution parameters and metrics (`fetched_count`, `inserted_count`, `skipped_count`, `failed_count`). It includes execution state tracking (`status`: running, completed, partial, failed) and captures precise error messages if API limits or timeouts are hit.
* **`raw_reviews`**: Stores the exact, untouched JSON payloads returned by the Apple API.
* **`normalized_reviews`**: Stores the cleaned fields. Uses a composite primary key (`review_id`, `app_id`, `storefront`) to prevent duplicates. Features **exact row-level lineage** via a `raw_id` foreign key, tracing every cleaned review directly to its original JSON payload.

## Setup & Execution

### 1. Prerequisites
Ensure you have Python 3 installed. The only external dependency required is `requests`.
```bash
pip install requests