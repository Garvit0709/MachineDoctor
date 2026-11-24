# MachineDoctor — Powered by AURA

**An experimental motor-bearing diagnostic and condition-monitoring research platform.**

MachineDoctor is a full-stack software application designed to analyze vibration signals, manage motor and bearing records, and store diagnostic results using the experimental AURA algorithm.

The platform combines signal processing, condition-aware diagnostic inference, secure administrator access, and persistent diagnostic history.

**Live Application:** https://machinedoctor-zm4t.onrender.com/

**Source Code:** https://github.com/Garvit0709/MachineDoctor

## Key Features

- **Motor Registry:** Create, update, and manage motors and associated bearings.
- **Signal Explorer:** Upload vibration CSV files and inspect extracted signal characteristics.
- **AURA Intelligence:** Analyze compatible precomputed feature sequences using the experimental AURA v0.1 model.
- **Diagnostic History:** Store and retrieve diagnostic sessions and window-level predictions.
- **Administrator Authentication:** JWT-based authentication with Argon2 password hashing.
- **API Security:** Login rate limiting, upload validation, protected endpoints, and database integrity safeguards.
- **Responsive Dashboard:** React interface with lazy-loaded modules, connection monitoring, and error handling.

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React, TypeScript, Vite, Tailwind CSS |
| Backend | Python, FastAPI |
| Database | PostgreSQL |
| ORM and migrations | SQLAlchemy, Alembic |
| Authentication | JWT, Argon2 |
| Scientific computing | NumPy, pandas, SciPy, scikit-learn |
| Deployment | Render |
| Version control | Git and GitHub |

## AURA — Experimental Diagnostic Algorithm

AURA v0.1 processes compatible feature-window sequences using vibration characteristics and operating conditions.

### Diagnostic Features

- RMS
- Standard deviation
- Peak-to-peak amplitude
- Crest factor
- Kurtosis
- Dominant frequency
- Spectral centroid

### Operating Conditions

- RPM
- RPM acceleration

The current model produces window-level diagnostic states:

- `NORMAL`
- `WARNING`
- `UNKNOWN`

Diagnostic sessions can be associated with registered motors and bearings and saved in PostgreSQL.

**Research limitation:** AURA v0.1 is an experimental model developed using synthetic calibration data. Its diagnostic predictions are not certified or validated for industrial safety-critical decisions. Additional real-world testing, calibration, and scientific validation are required.

## System Architecture

```text
React + TypeScript Dashboard
           |
           | HTTPS / REST API
           v
       FastAPI Backend
           |
     +-----+------+
     |            |
     v            v
 AURA Engine   Authentication
     |            |
     +-----+------+
           |
           v
       PostgreSQL
           |
    Diagnostic History
```

## Local Development

### Backend

Clone the repository:

```bash
git clone https://github.com/Garvit0709/MachineDoctor.git
cd MachineDoctor
```

Create a Python virtual environment and install dependencies:

```bash
python -m venv .venv
```

Activate the environment and run:

```bash
pip install -r requirements.txt
```

Configure the required database and JWT environment variables using `.env.production.example` as a reference. Use local development values rather than production credentials.

Apply migrations:

```bash
python -m alembic upgrade head
```

Start FastAPI:

```bash
python -m uvicorn backend.main:app --reload
```

API documentation: http://127.0.0.1:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open the URL displayed by Vite.

## Testing

Run backend tests:

```bash
python -m pytest tests -q
```

Run frontend checks:

```bash
npm --prefix frontend run build
npm --prefix frontend run lint
```

The project has passed a 91-test Python regression suite, along with hosted AURA inference, diagnostic persistence, authentication, and API-security verification.

## Deployment

MachineDoctor uses Render-hosted services for:

- React frontend
- FastAPI backend
- PostgreSQL database

Deployment secrets must be configured through the hosting provider's environment-variable settings. Real `.env` files must never be committed to Git.

## Security

The platform includes administrator authentication, password hashing, protected API routes, request rate limiting, CSV upload restrictions, and referential-integrity safeguards.

Production security depends on correct deployment configuration, secure secrets, database access controls, and continued maintenance.

## Project Status

**MachineDoctor v1.0 — Research Prototype**

Core software development and initial cloud deployment are complete. Scientific validation and further production hardening remain ongoing.

## Creator

**GM — Garvit Maheshwari**

Created and developed by Garvit Maheshwari.

*MachineDoctor — Powered by AURA*