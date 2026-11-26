# Event Collision Detector

Event Collision Detector is a predictive scheduling platform designed to help teams identify crowded launch periods and choose better dates for product launches, campaigns, and major announcements.

## Overview

Users can enter a proposed launch date and receive a collision/risk score based on relevant external events such as competitor launches, industry conferences, and major public events.

The system:

* Collects relevant external events
* Builds a unified event timeline
* Detects conflicts around a proposed launch date
* Calculates a collision risk score
* Recommends lower-risk launch windows

The platform is designed to help teams make data-driven scheduling decisions and reduce competition for audience attention and media coverage.

## Key Features

* Cross-industry event radar
* Real-time collision scoring
* Launch date risk analysis
* Optimal launch recommendations
* Event timeline and search
* Competitor and industry event tracking
* Predictive scheduling
* Campus event registration and schedule-overlap checks

## Campus mode

Use the Campus mode toggle to register college team events with a college, team, event type, date, start/end time, and location. Event types are Cultural, Business, and Technical. Event boards are separated by college name. Events overlap when their time ranges intersect on the same date for the same college, even if they are at different locations; adjacent time ranges do not overlap. Campus events are only added when a team registers them—none are seeded.

Opening an event's **Risk analysis** shows its schedule risk score, overlap details, and safer same-day time slots when available. The campus score applies event-type multipliers (Cultural 1.0x, Business 1.15x, Technical 1.3x) to overlap count and duration; it does not use the normal launch model's audience or industry factors. Registered team events can be moved to a suggested slot; their date and duration are preserved. Imported Saturnalia events remain read-only.

The **Sync Saturnalia events** button imports the public schedule from [Saturnalia](https://www.saturnalia.in/events) onto the Thapar Institute board. Event times are converted to India local time. If the source has no valid end time, only events with the exact same start time are flagged. The location selector is populated from imported venues and registered campus events.

## Tech Stack

* Frontend: HTML/CSS/JavaScript
* Backend: Python
* Database: SQLite/SQLAlchemy
* Caching: Redis
* Authentication: JWT
* Data Sources: External event APIs
* Analytics: Python / Machine Learning
* Testing: Unit, integration and frontend testing
* CI/CD: Git-based continuous integration and deployment

## Architecture

The system follows a layered architecture:

```text
React Frontend
      |
   REST API
      |
Business Logic
      |
PostgreSQL + Redis
      |
Event / Market APIs
```

The system continuously collects external events, evaluates proposed launch dates against those events, and generates a collision score and recommended launch window.
