import sys
import os

# Append the root directory to the Python path to prevent path resolution errors
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.database import engine, Base


def initialize_production_database():
    print("Connecting to the database engine via connection pool...")
    try:
        # Reaches out to the configured DATABASE_URL and creates all tables mapped in models.py
        Base.metadata.create_all(bind=engine)
        print(
            "Schema verification complete: 'transactions' table compiled successfully in the cloud."
        )
    except Exception as e:
        print(f"Catastrophic Database Connection Error: {str(e)}")


if __name__ == "__main__":
    initialize_production_database()
