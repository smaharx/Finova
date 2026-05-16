from fastapi import FastAPI

# Initialize the API application
app = FastAPI(title="Finance Tracker API", version="2.0")

# Define our very first endpoint (Health Check)
@app.get("/")
def health_check():
    return {
        "status": "online",
        "message": "FastAPI backend is running successfully.",
        "version": "2.0"
    }
    