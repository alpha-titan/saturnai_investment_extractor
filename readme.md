# Django Financial Data Extraction Application

This Django application allows users to upload transcript files containing financial conversations. The application processes the uploaded transcripts, extracts financial information such as assets, expenditures, and income using the OpenAI model, and stores the extracted information in a database. The application also provides a REST API for uploading files and retrieving the extracted financial data.

## Features

- Upload `.txt` files containing financial conversation transcripts.
- Extracts financial information from the uploaded transcripts.
- Handles large files by splitting them into manageable chunks while maintaining context.
- Stores extracted financial data in a database.
- Provides a REST API for file upload and data retrieval.
- Displays financial data on the frontend.

## Prerequisites

- Python 3.8+
- Django 3.2+
- Node.js (for frontend dependencies if any)
- OpenAI API Key

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/alpha-titan/saturnai_investment_extractor.git
   cd saturnai_investment_extractor
    ```

2. **Setup the Virtual Env**:
   ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3. **Setup the Virtual Env**:
   ```bash
    pip install -r requirements.txt
    ```