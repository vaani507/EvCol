# EvCol - Event Collision Detector

EvCol is a predictive launch-window intelligence platform that helps teams make smarter launch decisions before the competition gets their audience's attention. Our AI-powered platform scans 1,248+ global events to surface conflicts before they cost you reach, press coverage, and conversions.

## Features Built & Fixed

1. **Brand New UI & Aesthetics:**
   - Designed a dark forest green, warm orange, and cream theme.
   - Designed a new "EvCol" logo with an animated sun motif.
   - Integrated `Shrikhand`, `Playfair Display`, `JetBrains Mono`, and `Inter` fonts.
   - Built a sleek responsive glassmorphic frontend UI without any external CSS frameworks.

2. **Frontend-Backend Integration:**
   - Rewrote the frontend JavaScript (`app.js`) to properly interface with the FastAPI backend.
   - Eliminated the mocked analysis data and connected the frontend to the `/api/analyze` endpoint.
   - The analysis form now collects all parameters (Launch Name, Proposed Date, Industry, and Audience Tags) and sends them to the backend for accurate heuristic risk scoring.
   - Connected the "Event Radar" and "Dashboard" views to the live `/api/events` endpoint to dynamically display seeded external events.
   
3. **Backend API Features:**
   - Set up the FastAPI backend powered by an SQLite database (`evcol.db`).
   - Populated the database using the `lifespan` hook which runs initial database creation, local static seeds, and dynamically ingests live holidays from the Nager.Date API.
   - Exposed endpoints for `health`, `ingest` (fetching Nager.Date events), `analyze` (collision risk score algorithm), `events` (listing filtered external events), and `reports` (retrieving previous reports).

4. **Dynamic Rendering & HTML Fixes:**
   - Modified `index.html` to add IDs to all relevant elements in the results section so `app.js` can inject dynamic API response data into the UI.
   - Ensured the dynamic factor breakdown, conflicting events, and alternative recommendations are properly populated.

## Tech Stack
- **Frontend:** Vanilla HTML, CSS, JavaScript
- **Backend:** Python, FastAPI, SQLAlchemy, Pydantic, SQLite
- **Environment:** Windows

---

## How to Run the Project

You need to run both the FastAPI Backend and the Frontend Server simultaneously for EvCol to work correctly.

### 1. Start the Backend

1. Open a new terminal and navigate to the backend directory:
   ```bash
   cd \software-engineering\code\backend
   ```
2. Install the required Python dependencies (if not already installed):
   ```bash
   pip install -r requirements.txt
   ```
3. Start the FastAPI server using Uvicorn:
   ```bash
   uvicorn main:app --reload --port 8000
   ```
4. *Note: The backend will automatically create the `evcol.db` SQLite database and seed it with external events on startup.*

### 2. Start the Frontend

1. Open another terminal and navigate to the frontend directory:
   ```bash
   \software-engineering\code\app
   ```
2. Start a simple local HTTP server. For example, using Python:
   ```bash
   python -m http.server 8765
   ```
3. Open your web browser and navigate to:
   **[http://localhost:8765](http://localhost:8765)**

---

## Testing the Platform

1. Navigate to the **Analyze Date** page via the top navigation bar.
2. Enter a **Launch Name**.
3. Select a **Proposed Launch Date** (e.g., `10/15/2026`).
4. Select an **Industry** and **Target Audience Tags**.
5. Click **Analyze Collision Risk**. 
6. Watch the loading sequence execute the request to the FastAPI backend and view the dynamic results rendered on the page, including collision factor breakdown and recommended alternatives.
