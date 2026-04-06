# AEGIS

AI-Based Deployment Risk Prediction Platform

AEGIS is an AI-assisted platform designed to analyze software deployment changes and predict potential risks before a deployment occurs. The system integrates with CI/CD pipelines, analyzes commit and deployment characteristics, and produces a risk score that helps engineering teams make safer deployment decisions.

The platform provides a backend API capable of receiving deployment metadata from CI/CD systems, processing the data through a risk analysis engine, and storing deployment insights for further analysis and monitoring.

---

## System Architecture

The AEGIS platform follows a modular architecture designed for CI/CD integration and deployment intelligence.

CI/CD Pipeline
↓
Webhook Receiver
↓
Security Validation Layer
↓
Payload Normalization
↓
Deployment Risk Analysis Engine
↓
Database Storage
↓
API Response

The system can be integrated directly into CI/CD workflows such as GitHub Actions, GitLab CI, Jenkins, or other automation pipelines.

---

## Features

Deployment Risk Analysis
Evaluates deployments based on commit activity, code churn, testing metrics, and historical failure patterns.

CI/CD Webhook Integration
Receives deployment metadata directly from CI/CD pipelines using a webhook ingestion endpoint.

Security Layer
Token-based authentication for webhook ingestion and optional signature verification for external integrations.

Deployment Analytics API
Provides endpoints for analyzing deployments and retrieving deployment data.

Database Persistence
Stores deployment risk records and historical deployment data for monitoring and analytics.

Swagger API Documentation
Interactive API documentation for testing and validating endpoints.

---

## Tech Stack

### Backend

Python
FastAPI
Pydantic
SQLAlchemy
SQLite

### Frontend

Next.js
TypeScript

### DevOps

Docker
Docker Compose

---

## API Endpoints

### Analyze Deployment

POST /api/analysis/analyze

Analyzes a deployment and calculates a deployment risk score.

Example Request Body

{
"repo_name": "test/repo",
"commit_count": 2,
"files_changed": 4,
"commit_messages": ["test commit"],
"deployment_environment": "staging",
"deployment_frequency": 3,
"code_churn": 120,
"test_coverage": 75,
"rollback_plan": true,
"dependency_updates": 1,
"historical_failures": 0
}

---

### CI/CD Webhook Receiver

POST /api/integrations/webhook

Receives deployment data from CI/CD pipelines and automatically triggers risk analysis.

Authentication Header

X-AEGIS-TOKEN: <token>

---

### Get Deployment

GET /api/deployments/{deployment_id}

Retrieves stored deployment analysis data.

---

## Project Structure

AEGIS

backend
└── app
    ├── models
    ├── routers
    ├── schemas
    ├── services
    ├── config.py
    ├── database.py
    └── main.py

frontend
├── src
└── public

docker-compose.yml
Dockerfile
README.md

---

## Running the Project

### Backend

cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

Backend runs on:

http://localhost:8000

API documentation is available at:

http://localhost:8000/docs

---

### Frontend

cd frontend
npm install
npm run dev

Frontend runs on:

http://localhost:3000

---

## Current Implementation Status

Completed

Core Backend API
Deployment Risk Analysis Engine
CI/CD Webhook Integration
Security Token Authentication
Deployment Data Persistence
Swagger API Testing

Planned Enhancements

Machine learning-based deployment risk prediction models
Deployment risk analytics dashboard
Real-time CI/CD pipeline monitoring
Cloud provider integrations

---

## Author

Vishwas Desai
