# DataPilot

**DataPilot** is a Django-based data cleaning and reporting platform designed to transform raw datasets into clean, structured, and downloadable outputs.

It provides a modular pipeline for importing datasets, validating files, analyzing data, detecting issues, applying cleaning operations, and generating exportable results.

---

## Core Workflow

```text
Upload
   ↓
Detect
   ↓
Validate
   ↓
Import
   ↓
Analyze
   ↓
Clean
   ↓
Report
   ↓
Export
```

DataPilot separates each stage of the workflow so that individual components can evolve independently while remaining part of one consistent data-processing pipeline.

---

## Features

### Import System

* CSV support
* Excel (`.xlsx`) support
* Automatic file format detection
* File validation
* Dedicated readers
* Extensible reader registry

### Data Cleaning

* Missing value detection
* Duplicate row detection
* Cleaning findings
* Cleaning statistics
* Cleaning job tracking
* Structured cleaning pipeline

### Dataset Management

* Dataset metadata
* Dataset lifecycle management
* File ingestion
* Dataset analysis
* Dataset checksums
* Processing status tracking

### Export System

* CSV export
* Excel export
* PDF report generation
* Format-specific writers
* Extensible writer registry

### Reporting

* Cleaning reports
* Dataset summaries
* Detailed findings
* Generated output history
* Downloadable cleaned datasets
* Cleaning job history

---

## Supported Formats

| Format        | Import | Export |
| ------------- | :----: | :----: |
| CSV           |    ✓   |    ✓   |
| Excel `.xlsx` |    ✓   |    ✓   |
| PDF           |    —   |    ✓   |

The import and export systems are designed around registries, making it straightforward to introduce additional formats without restructuring the entire application.

---

## Architecture

DataPilot follows a modular service-oriented application structure.

```text
apps/
├── cleaner/
│   ├── services/
│   └── migrations/
│
├── datasets/
│   ├── services/
│   └── migrations/
│
├── importer/
│   ├── detectors/
│   ├── readers/
│   └── validators/
│
├── exporter/
│   └── writers/
│
└── reports/
    └── services/
```

Each application owns a specific responsibility:

* **Cleaner** — detects and resolves data-quality issues.
* **Datasets** — manages dataset lifecycle and analysis.
* **Importer** — detects, validates, and reads source files.
* **Exporter** — generates files in supported output formats.
* **Reports** — presents cleaning results and job history.

---

## Technology Stack

* **Backend:** Django
* **Data Processing:** Pandas
* **Database:** PostgreSQL
* **Frontend:** HTML, CSS, JavaScript
* **Testing:** Django Test Framework

The application is built with a strong separation between business logic, data processing, file handling, and presentation.

---

## Design Principles

DataPilot is being developed around several core principles:

* **Modularity** — services have clear responsibilities.
* **Extensibility** — new formats and processing capabilities can be added without rewriting the core pipeline.
* **Separation of concerns** — importing, cleaning, exporting, and reporting remain independent components.
* **Reliability** — critical functionality is covered by automated tests.
* **Maintainability** — application logic is organized into dedicated services rather than concentrated in views.
* **User-focused output** — cleaned data and reports are presented in practical, downloadable formats.

---

## Project Status

DataPilot is currently under active development.

The core CSV and Excel data workflow is established, including importing, validation, cleaning, exporting, and reporting. The project is now being refined toward a more complete and production-quality data platform.

---

## Author

**Amani Mugisha**

