# Finova

![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green)
![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-red)
![Database](https://img.shields.io/badge/Database-PostgreSQL-lightgrey)
![AI](https://img.shields.io/badge/AI-Prophet%20%7C%20Isolation%20Forest-orange)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Project-Active-yellowgreen)

Finova is a personal finance tracker that helps you manage spending, correct AI predictions, detect anomalies, and review financial insights in one place.The system provides a clean dashboard for real-time insights while leveraging advanced Machine Learning models in the background.  

---  

## Overview  

Traditional finance trackers rely on manual entry and basic pie charts. This project elevates personal finance by integrating Machine Learning directly into the data pipeline.  

The system allows users to input transactions which are automatically categorized via NLP. It then processes historical data through an Isolation Forest algorithm to flag highly unusual purchases, and utilizes Facebook's Prophet model to project a 30-day spending forecast. The application is built as a highly responsive monolithic architecture using Streamlit and SQLite.  

---  

## Key Features  

- Interactive financial dashboard with real-time monthly metric filtering  
- NLP-based automatic transaction categorization  
- Unsupervised anomaly detection (Isolation Forest) for unusual spending  
- Time-series forecasting (Prophet) for 30-day budget projection  
- "Human-in-the-loop" UI for correcting AI categorization guesses  
- High-volume synthetic data seeder for ML model stress-testing  
- Secure, local SQLite database management  

---  

## System Architecture  

The application is modularized to separate the UI from heavy data processing:  

1. **Presentation Layer** — Streamlit UI (filtered to current calendar month to prevent memory bloat)  
2. **Business & ML Logic Layer** — Pandas data manipulation, Scikit-learn, and Prophet modeling  
3. **Data Access Layer** — Python SQLite3 integration  
4. **Database Layer** — Local SQLite relational database  

*(For detailed data flow and scaling plans, see [ARCHITECTURE.md](ARCHITECTURE.md))*  

---  

## Technology Stack  

| Component            | Technology              |
|---------------------|-------------------------|
| Programming Language | Python                  |
| Web Framework        | Streamlit               |
| Data Manipulation    | Pandas, NumPy           |
| Machine Learning     | Scikit-learn, Prophet   |
| Visualization        | Plotly Express & Graph  |
| Database             | SQLite3                 |

---  
## Project Structure

```
Finova/
│
├── dashboard.py         # Main entry point for the Streamlit UI
├── requirements.txt     # Python dependencies
├── README.md            # Project documentation and setup
├── ARCHITECTURE.md      # System design and data flow details
│
├── api/                 # (V2.0) Planned FastAPI routing
├── core/                # Core business logic and NLP configurations
├── ml/                  # Machine learning models (Anomaly & Forecast)
├── analysis/            # Data processing and UI metric calculations
│
├── data/                # Local database storage (Git-ignored)
│   └── expenses.db      # SQLite database file
│
└── scripts/             # Utility scripts
    └── seed_db.py       # Generates 20,000 synthetic records for ML training
```    
---  

## Installation  

Clone the repository:  

git clone https://github.com/smaharx/Finova.git  
cd Finova 

Set up a virtual environment and install dependencies:  

python -m venv .venv  

# Activate on Windows  
.venv\Scripts\activate  

# Activate on Mac/Linux  
source .venv/bin/activate  

pip install -r requirements.txt  

---  

## Configuration  

The application uses environment variables for secure configuration.  

- Locate the .env.example file in the root directory  
- Duplicate it and rename the copy to .env  
- Fill in any required local configuration variables  

(Note: The database requires no manual setup; expenses.db will auto-generate on the first run)  

---  

## Running the Application  

To launch the dashboard locally, run:  

streamlit run dashboard.py  

Alternatively, on Windows, you can use the batch script:  

./run_app.bat  

---  

## Generating Mock Data (For ML Testing)  

Machine Learning models require significant historical data to function accurately. To test the Prophet forecasting and Isolation Forest models, run the database seeder script to inject 20,000 realistic transactions:  

python scripts/seed_db.py  

---  

## Future Improvements (V2.0 SaaS Roadmap)  

- Microservices architecture: Decoupling the frontend by introducing a FastAPI backend  
- Cloud database integration: Migrating from local SQLite to PostgreSQL (Supabase)  
- Multi-tenant authentication: Implementing JWT-based user login sessions  

---  

## Authors  

Shahzaib Mahar (@smaharx)

---  

## License  

This project is licensed under the MIT License. See the LICENSE file for details.
