# EvCol Architecture & Codebase Guide

This document outlines the structure of the EvCol (Event Collision Detector) codebase, explaining where everything is located, what each component does, and detailing the internal and external APIs used.

## 1. Codebase Structure

The project is split into two primary components: the **Frontend (`app`)** and the **Backend (`backend`)**.

### Frontend (`/code/app/`)
The frontend is a vanilla JavaScript Single Page Application (SPA) that communicates with the backend APIs to display collision analysis and event data.

- **`index.html`**: The main entry point for the frontend. It contains all the HTML markup for the different views (Analyze Date, Event Radar, Results, Calendar, History). 
- **`styles.css`**: The central stylesheet implementing the custom EvCol theme (dark forest green, warm orange, cream) and responsive glassmorphic UI without any external CSS framework.
- **`app.js`**: The core frontend logic. It handles:
  - Client-side routing between pages (`navigate()` function).
  - Submitting launch details to the backend API (`/api/analyze`).
  - Fetching external events from the backend (`/api/events`).
  - Dynamically injecting API responses (risk scores, overlapping events, recommended alternatives) into the DOM.

### Backend (`/code/backend/`)
The backend is powered by Python and FastAPI, serving as the central nervous system that orchestrates database interactions, event ingestion, and risk calculation.

- **`main.py`**: The entry point for the FastAPI server. It defines all the API routes (`/api/analyze`, `/api/events`, `/api/ingest`, etc.) and handles the application lifecycle (such as seeding the database on startup).
- **`models.py`**: Defines the SQLAlchemy ORM models (e.g., `Event`, `AnalysisReport`, `AlternativeDate`) mapping Python objects to SQLite database tables.
- **`database.py`**: Configures the SQLAlchemy database engine and connection session for the SQLite database (`evcol.db`).
- **`scoring.py`**: Contains the heuristic engine (`compute_score`). This is the core algorithm that calculates the risk score based on audience overlap, industry relevance, and temporal proximity to other events.
- **`ingestion.py`**: Handles external data ingestion. It reaches out to third-party APIs to pull live event data into the local database.
- **`seed.py`**: Contains fallback/initial static event data to ensure the platform has a rich dataset to test against upon the first launch.
- **`evcol.db`**: The local SQLite database file where all events and analyses are stored.

---

## 2. APIs Used (External and Internal)

### External APIs
**What:** [Nager.Date API](https://date.nager.at/)
**Where:** Used in `backend/ingestion.py`.
**Why:** To dynamically ingest real-world public holidays across different countries (like the US) into the `evcol.db` database. Launching on major public holidays drastically impacts audience availability and PR reach, so EvCol treats these as high-risk collision events.


### Internal APIs (FastAPI Endpoints)
The frontend communicates entirely via these internal REST endpoints exposed by `main.py`:

#### `POST /api/analyze`
- **What it does:** Receives launch parameters (Launch Name, Proposed Date, Industry, Audience Tags), runs the heuristic scoring algorithm against the events in the database, and returns a detailed risk breakdown.
- **Where it is used:** Called by `app.js` when a user clicks the "Analyze Collision Risk" button on the frontend.
- **Why it is used:** To provide the user with a quantitative risk score, specific conflicting events, and alternative date recommendations.

#### `GET /api/events`
- **What it does:** Retrieves a list of events currently stored in the database, with optional filtering parameters (industry, date range).
- **Where it is used:** Called by `app.js` to populate the "Event Radar" grid on the frontend.
- **Why it is used:** To allow users to manually explore the competitive landscape and see what's happening around their proposed launch dates.

#### `POST /api/ingest`
- **What it does:** Triggers the ingestion pipeline to fetch the latest public holidays from the Nager.Date API and stores them locally.
- **Where it is used:** Automatically triggered in the FastAPI `lifespan` event on server startup in `main.py`, and can be triggered manually if needed.
- **Why it is used:** To ensure the local database stays up-to-date with relevant real-world temporal constraints without manually hardcoding them.
