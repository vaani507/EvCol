# Weekly Progress Journal — Jaskaran Singh (Roll No: 1024160033)

**Project Name:** Event Collision Detector: Predictive Launch-Window Intelligence

## Week 1 (Aug 3 - Aug 9): Collision Scoring & Project Research

* Participated in group brainstorming sessions for project selection.
* Researched heuristic collision scoring methods and evaluated blind-spot scheduling issues to identify the key factors affecting launch-window conflicts.
* Studied temporal proximity, industry relevance, audience overlap, event magnitude, and media friction as potential scoring factors.

## Week 2 (Aug 10 - Aug 16): Backend Architecture Feasibility

* Researched methods to analyze event data and compute collision risk using Python, Pandas, and Scikit-learn utilities.
* Investigated FastAPI for developing launch-date submission and risk-scoring endpoints.
* Evaluated PostgreSQL and Elasticsearch as storage solutions for user/session data and external event data.

## Week 3 (Aug 17 - Aug 23): Proposal Text Drafting

* Drafted sections on the Problem Statement, Project Scope, and Evaluation Metrics, including Collision Score Latency (CSL), in the LaTeX project proposal.
* Formulated the theoretical logic for the collision analysis engine by considering temporal proximity, industry relevance, audience overlap, event magnitude, and media friction.
* Contributed to defining the proposed workflow for event retrieval, risk calculation, and alternative-date recommendations.

## Week 4 (Aug 24 - Aug 30): Document Review & Proofreading

* Collaborated on proofreading the project proposal and supporting LaTeX files.
* Assisted in checking the system logic and reviewing the DFD and Use Case diagrams.
* Reviewed the event ingestion and backend workflow for consistency with the proposed architecture.
* Cleaned up document formatting and adjusted author metadata according to instructor instructions.

## Week 5 (Aug 31 - Sep 6): Event Ingestion & Collision Analysis

* Worked on the initial event ingestion workflow for retrieving external event information.
* Studied the required event attributes for calculating collision risk around a proposed launch date.
* Worked on implementing the initial **±7-day event retrieval window** for identifying nearby competing events.
* Began developing the explainable heuristic scoring logic for classifying collision risk as High, Medium, or Low.

## Week 6 (Sep 7 - Sep 13): Risk Scoring & Recommendation Logic

* Continued development of the collision-risk scoring component.
* Worked on identifying the primary events contributing to the calculated risk score.
* Contributed to the logic for identifying lower-risk alternative launch dates around the proposed date.
* Worked on connecting event retrieval, scoring, and recommendation components with the backend workflow.
* Reviewed the risk-scoring API requirements in preparation for end-to-end integration.
