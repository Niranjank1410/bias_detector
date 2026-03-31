# backend/scheduler.py
"""
Lightweight scheduler entry point for Render Cron Job.
This script runs the full pipeline once and exits.
It does NOT load ML models — those run on your local machine.
The Render cron job only triggers a fetch + bias recompute.
"""

import os
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import requests

# Trigger the pipeline via the API health endpoint
# In production, you'd add a protected /admin/run-pipeline endpoint
# For now, we run the pipeline locally on a schedule using the system cron

if __name__ == "__main__":
    print("Scheduler: pipeline should be run locally via cron")
    print("See README for setup instructions")