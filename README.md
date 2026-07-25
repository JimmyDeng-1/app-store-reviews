# Phase I: Data Ingestion & Infrastructure - Apple App Store

## Project Purpose
[cite_start]This repository contains the foundational ingestion engine designed to collect, clean, and structure user-generated text data from the open web[cite: 529]. [cite_start]The goal of this pipeline is to support downstream sentiment analysis and machine learning models for Sciencia AI[cite: 529].

## Data Collection Methodology
[cite_start]Data is programmatically collected using the **Official Apple iTunes RSS API**[cite: 530]. [cite_start]This provides an un-gated, highly stable stream of structured JSON data[cite: 531]. [cite_start]Using the official API allows the pipeline to completely bypass the need for brittle HTML scraping or CAPTCHA management, ensuring a maintainable automated process[cite: 531]. 
Data is then structured and stored locally using a normalized SQLite relational database schema.

## Main Findings & API Limitations
[cite_start]Following feasibility testing and Exploratory Data Analysis (EDA) on a 2,650-review sample, the following constraints and findings were identified[cite: 532]:

* [cite_start]**Volume Cap & Pagination:** The Apple API enforces a strict limit of 500 recent reviews per application, per regional storefront (e.g., US, GB, CA)[cite: 533]. Furthermore, not all storefronts reach this maximum limit.
* [cite_start]**Data Health & Completeness:** The structural payload is highly reliable with 0 missing fields or duplicates found during testing[cite: 536]. [cite_start]However, to ensure modeling integrity, content-level quality flags (e.g., non-English content, low-signal text, missing fields) have been implemented directly into the database schema[cite: 518, 536].

## Strategic Recommendation
[cite_start]Due to the strict 500-review volume caps per storefront, **this source cannot be used for deep historical review collection**[cite: 534]. 

[cite_start]However, because the data is highly structured, rich in text, and reliably accessible without blocking, this API is highly recommended and optimized for **recurring recent-review monitoring** (e.g., daily or weekly automated ingestion pipelines)[cite: 535].
