# Finova Architecture

## 1. High-Level Overview
Finova is currently designed as a monolithic data application (Version 1.0). It processes user financial data, stores it locally, and runs advanced Machine Learning pipelines to generate predictive forecasting and anomaly detection. 

The architecture is built prioritizing mathematical accuracy and UI responsiveness, separating the heavy Machine Learning dataframes from the front-end rendering logic.

## 2. Technology Stack
* **Frontend / UI:** Streamlit
* **Data Processing:** Pandas, NumPy
* **Machine Learning:** * `Prophet` (Time-series forecasting)
  * `scikit-learn` / Isolation Forest (Anomaly detection)
* **Database:** SQLite (Local)
* **Visualization:** Plotly

## 3. Directory Structure
```text
Finova/
│
├── dashboard.py         # Main entry point for the Streamlit UI
├── requirements.txt     # Dependency management
├── README.md            # Project documentation and setup
├── ARCHITECTURE.md      # System design and data flow details
│
├── api/                 # (V2.0) FastAPI routing and endpoints
├── core/                # Core business logic and configurations
├── ml/                  # Machine learning models and training scripts
├── analysis/            # Data analysis and processing modules
│
├── data/                # Local database storage (Git-ignored)
│   └── expenses.db      # SQLite database file
│
└── scripts/             # Standalone database and utility scripts
    ├── seed_db.py       # Generates synthetic load-testing data
    ├── migrate_db.py    # Database schema migrations
    └── import_csv.py    # Legacy data ingestion

    ## 4. Data Flow & Execution
### A. Data Ingestion
* Users input data via the Streamlit frontend.
* The system uses NLP logic to automatically categorize the transaction before saving it to the SQLite database.

### B. Machine Learning Pipeline
* **Anomaly Detection:** The Isolation Forest model loads the complete historical dataset and flags statistical outliers (contamination set to 0.05).
* **Forecasting:** The Prophet model aggregates historical daily spending to project a 30-day forward-looking trendline.

### C. UI Rendering Optimization
* To prevent memory bloat, the frontend UI strictly limits rendering to the current calendar month. The heavy ML models operate on the full historical dataset in the background.

## 5. Future Roadmap (V2.0 SaaS)
* **Backend API:** Implement FastAPI to act as a secure middleman, decoupling the Streamlit frontend from direct database access.
* **Database Migration:** Transition from local SQLite to cloud-hosted PostgreSQL (e.g., Supabase) for connection pooling and scalability.