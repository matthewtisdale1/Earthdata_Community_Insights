import os

from app.main_matches import app


@app.get("/system/context")
def system_context():
    return {
        "dataset_mode": os.environ.get("DATASET_MODE", "full").lower(),
        "database_name": os.environ.get("APP_DATABASE", ""),
    }
