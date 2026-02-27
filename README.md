# SurveyMonkey Apply to Affinity CRM Pipeline

## Overview
This project is a serverless ETL (Extract, Transform, Load) pipeline built to synchronize grant application data from SurveyMonkey Apply (SMA) into Affinity CRM for the Innovation Voucher Fund (IVF) program. It is designed to run as a scheduled Azure Function. 

The pipeline employs a Delta Sync architecture, fetching only applications that have been modified since the last successful execution, minimizing API payload sizes and preventing rate-limiting issues.

## Architecture & Data Flow



1. **Authentication & State Retrieval:** * The pipeline authenticates with Azure Blob Storage to retrieve the previous execution's high-water mark timestamp (`sync_state.json`) and the dynamic SMA OAuth tokens (`program_info.json`).
   * If the SMA token has expired, the script negotiates a refresh and immediately commits the new token back to Blob Storage.
2. **Delta Extraction (SMA):**
   * Queries the SMA API for the IVF program, filtering for applications where the `last_updated` timestamp is strictly greater than the high-water mark.
3. **Data Transformation:**
   * Deeply nested JSON task payloads from SMA are flattened into standard Python dictionaries.
   * Cleans and formats specific fields (e.g., email addresses) and maps external index values to internal standardized strings (e.g., Provinces, Sectors).
4. **Entity Resolution & Caching (Affinity):**
   * Extracts the Principal Investigator (Person) and Company (Organization) from the application.
   * Checks a local in-memory cache to see if the entity's Affinity ID was already resolved during the current run.
   * If not cached, it queries the Affinity API. If the entity does not exist, it creates a new record and caches the resulting ID.
5. **Upsert (Affinity):**
   * Maps the SMA Application ID to existing Opportunity List Entries in Affinity.
   * Creates a new Opportunity if one does not exist.
   * Compares the transformed SMA payload against the current Affinity custom fields and pushes updates only for fields that have changed.
6. **State Persistence:**
   * Upon successful completion, the current UTC timestamp is written to `sync_state.json` in Azure Blob Storage, acting as the high-water mark for the next execution.

## Directory Structure

* `/affinity/`: Modules for interacting with the Affinity API (`get.py`, `update.py`, `find_or_create.py`). Includes the in-memory entity cache logic.
* `/pipeline/`: Core orchestration logic (`sync.py`) and helper functions (`helpers.py`) for routing data and building payloads.
* `/smapply/`: Modules for authenticating with SMA (`client.py`), querying programs (`program.py`), and transforming raw JSON data (`tables.py`, `mapping.py`, `utils.py`).
* `/tests/`: The `pytest` suite containing unit tests and mocked API responses to validate transformation logic.
* `main.py` / `function_app.py`: The primary entry points for local execution and the Azure Function runtime, respectively.

## Cloud Infrastructure Requirements

This pipeline requires an Azure Storage Account to maintain state across ephemeral serverless executions. 

You must manually create a blob container named **`pipeline-state`**. Inside this container, seed a file named `program_info.json` with valid SMA tokens:
```json
{
    "access_token": "your_initial_access_token",
    "refresh_token": "your_initial_refresh_token"
}
```

## Environment Variables

The pipeline relies on the following environment variables. Locally, these are managed via a .env file (ignored by Git). In production, these must be configured in the Azure Function App Settings.

| Variable | Description |
| --- | --- |
|SMA_CLIENT_ID | SurveyMonkey Apply API Client ID|
|SMA_CLIENT_SECRET | SurveyMonkey Apply API Client Secret |
| AFFINITY_BASE_URL | Defaults to https://api.affinity.co |
| AFFINITY_ACCESS_TOKEN | Affinity API Key |
| AFFINITY_IVF_LIST_ID | The specific integer ID of the Affinity list being updated |
| AZURE_STORAGE_CONNECTION_STRING | Connection string for the Storage Account hosting the state blob |

## Local Development & Testing
### Installation
1. Clone the repository.
2. Install the development requirements:
`pip install  -r requirements-dev.txt`

### Running Locally
To execute the pipeline manually from your terminal, run:
`func start`

### Running Tests
The project uses `pytest` for validation, relying on `unittest.mock` to simulate API payloads without executing external HTTP requests. To run the test suite:
`python -m pytest`

## Deployment Notes (Azure Functions)
### Trigger:
Configured as a Timer Trigger via function_app.py.
### Logging:
`host.json` is configured to suppress verbose Information level HTTP logs from the azure.core libraries to prevent log flooding.
### Dependencies:
Azure will automatically install packages defined in requirements.txt during deployment.
