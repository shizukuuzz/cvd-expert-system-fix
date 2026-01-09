#!/usr/bin/env python3
"""
CVD Expert System - Azure Functions Entry Point
Uses Azure Functions HTTP Trigger with Flask WSGI integration.
Saves diagnosis results to Cosmos DB with flat CSV-like structure.
"""

import azure.functions as func
from app_deploy import app as flask_app

# Create Azure Functions app with WSGI support for Flask
# Variable MUST be named 'app' for Azure Functions v4
app = func.WsgiFunctionApp(app=flask_app.wsgi_app, http_auth_level=func.AuthLevel.ANONYMOUS)
