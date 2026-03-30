# backend/api/main.py
"""
FastAPI application entry point.

This file creates the app, registers all routers, and configures
CORS (Cross-Origin Resource Sharing) so the frontend can call the API.
"""

import os
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import stories, sources, categories

app = FastAPI(
    title="Bias Detector API",
    description="News bias detection and analysis API",
    version="1.0.0",
)

# CORS configuration.
# CORS controls which domains are allowed to call your API from a browser.
# Without this, your Next.js frontend would be blocked by the browser
# when it tries to fetch from a different domain (e.g. your-app.vercel.app
# calling your-api.render.com).

app.add_middleware(
    CORSMiddleware,
    # In production, replace "*" with actual frontend url
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#Register routers - each router handles a group of related endpoints
app.include_router(stories.router)
app.include_router(sources.router)
app.include_router(categories.router)

@app.get("/")
def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "Bias Detector API is running"}

@app.get("/health")
def health():
    """Health check for Render's uptime monitoring."""
    return {"status": "healthy"}