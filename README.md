# App Store Review Ingestion Pipeline (Phase I)

**Sciencia AI - Data Ingestion & Infrastructure**

This repository contains an automated data ingestion pipeline that fetches, normalizes, and stores customer reviews from the Apple App Store. This pipeline serves as the foundational ingestion layer for downstream feature engineering, product feedback analysis, and AI-powered sentiment modeling.

## Project Purpose & Methodology
The goal of this pipeline is to reliably acquire user-generated textual data, transform it into a usable structure, and maintain strict data lineage. 

* **Collection Methodology:** Data is collected using the official Apple iTunes RSS API. The pipeline utilizes controlled pagination to iterate through available data payloads dynamically.
* **Limitations (EDA Findings):** Exploratory Data Analysis (EDA) revealed a strict **500-review-per-app-per-storefront limitation** imposed by Apple's API. While this restricts deep historical collection, the structural completeness of the payload (ratings, timestamps, version numbers) provides an excellent foundation for recent app review monitoring.

## Architecture & Database Schema
The pipeline uses a local SQLite database (`app_store_pipeline.db`) structured to enforce strict data lineage and idempotency.

* **`ingestion_runs`**: Logs every execution of the pipeline, recording parameters (App ID, Storefront, Page Limit) and execution metrics (`fetched_count`, `inserted_count`, `skipped_count`, `failed_count`).
* **`raw_reviews`**: Stores the exact, untouched JSON payloads returned by the Apple API, linked to the `run_id` for absolute traceability.
* **`normalized_reviews`**: Stores the cleaned, extracted fields (Review ID, Rating, Title, Text, Version, Date). Uses a composite primary key (`review_id`, `app_id`, `storefront`) to prevent duplicates while supporting cross-storefront ingestion.

## Setup & Execution

### 1. Prerequisites
Ensure you have Python 3 installed. The only external dependency required is the `requests` library.
```bash
pip install requests