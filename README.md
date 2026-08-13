# DataPilot

DataPilot is a Django-based data cleaning and analysis platform designed to help users upload CSV datasets, analyze their structure and quality, clean common data issues, and generate downloadable reports.

The project combines Django, Pandas, PostgreSQL, and ReportLab to provide a web-based workflow for dataset processing and data quality analysis.

## Features

- CSV file upload
- Dataset scanning and analysis
- Row and column statistics
- Missing-value detection
- Duplicate-row detection
- Automatic data cleaning
- Column-name standardization
- Missing-value handling
- Duplicate-row removal
- Empty-row removal
- Text normalization
- Cleaned CSV generation
- PDF cleaning reports
- Cleaning job tracking
- Dataset metadata storage
- Cleaning history
- Individual cleaning reports
- PostgreSQL database integration
- Django admin integration

## How It Works

DataPilot follows a simple data-processing workflow:

```text
Upload CSV
    ↓
Scan Dataset
    ↓
Analyze Data Quality
    ↓
Create Dataset Record
    ↓
Clean Dataset
    ↓
Generate Cleaned CSV
    ↓
Generate PDF Report
    ↓
Store Cleaning History
