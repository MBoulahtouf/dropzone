# Dropzone: A Production-Ready Document Intelligence Pipeline

![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)
![Framework](https://img.shields.io/badge/Framework-FastAPI-green)
![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)

Dropzone is a scalable, end-to-end framework for ingesting, understanding, and searching large volumes of unstructured documents. It's designed to process publicly available documents, such as scanned PDFs from official journals, and transform them into a queryable, AI-ready dataset.

## Key Features

This project demonstrates a full MLOps lifecycle, from raw data ingestion to a live, searchable API.

* **Modular Scraper Framework**: A robust scraper designed to systematically download document sets from web sources. It's built to be adaptable for different websites.
* **Parallelized OCR Engine**: A high-throughput OCR pipeline that leverages **Python's multiprocessing** to handle memory-intensive conversions of scanned PDFs to text, preventing OOM errors and maximizing CPU core utilization.
* **Intelligent Text Structuring**: A sophisticated, regex-based parsing module that identifies and extracts structured data (like titles, dates, authors, and articles) from unstructured, OCR-generated text.
* **AI-Ready Data Preparation**: The pipeline automatically classifies and prepares the data for modern AI applications. This includes:
    * **Classification**: Standardizing document types into clear categories.
    * **Chunking for RAG**: Breaking down large documents into small, semantically meaningful chunks, perfect for Retrieval-Augmented Generation.
* **Vector Database Ingestion**: A dedicated script uses **Sentence-Transformers** to generate vector embeddings for each text chunk and ingests the data into a database (SQLite for dev), ready for semantic search.
* **FastAPI-Powered Search API**: A high-performance, asynchronous API built with FastAPI that exposes the data through two key endpoints:
    * A `/search` endpoint for semantic, vector-based similarity search.
    * A `/documents/{file_name}` endpoint to retrieve full, structured documents.

## Architecture Overview

The project follows a clean, modular pipeline architecture, ensuring separation of concerns and maintainability.

`[Scanned PDFs] -> [Scraper] -> [OCR Engine] -> [Raw Text] -> [Parser & Classifier] -> [Structured JSON] -> [Chunker] -> [Vector DB] -> [FastAPI Backend] -> [User]`

## Tech Stack

* **Backend**: FastAPI, Uvicorn
* **Data Processing**: Tesseract (OCR), PDF2Image, NumPy
* **NLP & Search**: Sentence-Transformers
* **Orchestration**: Python Multiprocessing
* **Database**: SQLite (Development)
* **Dependency Management**: Poetry

## Local Setup and Usage

Follow these steps to get the pipeline and API running locally.

### 1. Prerequisites

Ensure you have the following system-level dependencies installed:

```bash
# On Debian/Ubuntu
sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-fra tesseract-ocr-ara poppler-utils

### 2. Installation

Clone the repository and install the Python dependencies using Poetry.

```bash
git clone [https://github.com/YourUsername/dropzone.git](https://github.com/YourUsername/dropzone.git)
cd dropzone
poetry install

### 3. Running the Data Pipeline

Execute the full pipeline to scrape the documents, perform OCR, parse them, and prepare the data for the database.

```bash
# Run the pipeline on a small sample first (e.g., 3 files from 2024)
poetry run python tools/run_full_pipeline.py --start-year 2024 --end-year 2024 --limit 3

### 4. Ingesting Data into the Database

This script creates the vector embeddings and populates the SQLite database.

```bash
poetry run python tools/ingest_to_db.py

### 5. Launching the API

Start the FastAPI server.

```bash 
poetry run uvicorn main:app --reload


The API will be live at http://127.0.0.1:8000. You can access the interactive documentation at http://127.0.0.1:8000/docs.

# Future Enhancements & Roadmap

- This project provides a solid foundation.
- The next steps involve scaling and building upon this core engine to create a full-featured, production-ready application.

## Build the User Interface

- **Action:**
  - Begin work in the `dz-scrap-ui` directory.
  - Use a framework like React or Vue to build a simple web page with a search bar and a results area.
- **Impact:**
  - This will be the most visible improvement, allowing non-technical users to interact with your powerful backend.

## Automate and Scale the Data Pipeline

- **Action:**
  - Schedule your `run_full_pipeline.py` script to run automatically (e.g., daily using a cron job).
- **Impact:**
  - Your application will stay perpetually up-to-date with the latest laws without any manual effort.

## Move to a Production Database

- **Action:**
  - Migrate from SQLite to a more powerful database like PostgreSQL with the `pgvector` extension.
- **Impact:**
  - This will allow your search to remain fast and efficient even as you scale to hundreds of thousands or millions of legal documents.

## Deploy to the Cloud

- **Action:**
  - Deploy your FastAPI application to a cloud server using a production-ready setup (e.g., Gunicorn with Nginx).
- **Impact:**
  - This makes your API publicly accessible, reliable, and ready to handle multiple simultaneous users.

