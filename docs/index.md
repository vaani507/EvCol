![Tiet Logo](assets/tiet-logo.svg){ .tiet-logo }

**UCS503: Software Engineering (Project)**  
**TIET Patiala**

# Event Collision Detector - Predictive Event Scheduling & Collision Analysis

**Author(s)**:

- Jaskaran Singh (Roll No: `1024160033`)
- Vaani Mehta (Roll No: `1024160123`)
- Parmeet Singh (Roll No: `1024160021`)

**Lab Instructor**: Jeelani Asif

---

## Project Overview

**Event Collision Detector** is a predictive scheduling system designed to help organizations identify potential conflicts around planned product launches, marketing campaigns, and major announcements.

The system collects information about external events such as competitor launches, industry conferences, calendars, and major public events. It analyzes these events against a proposed schedule to identify potential collisions, calculates a collision risk score, and provides recommendations for alternative launch windows.

The goal is to help teams avoid crowded time slots, reduce competition for audience attention and media coverage, and make more informed scheduling decisions.

## System Architecture

The Event Collision Detector follows a layered architecture consisting of the following major components:

1. **Event Organizer Interface**: Allows users to submit and manage planned event details.
2. **Event Collection & Storage**: Collects competing events from external calendars, APIs, and websites and stores relevant event information.
3. **Collision Analysis Engine**: Compares planned events with competing events and evaluates potential conflicts based on factors such as timing and relevance.
4. **Report & Recommendation System**: Generates collision reports, alerts, and recommendations for alternative launch windows.
5. **Event Management**: Allows system administrators to maintain and update event data.

## Data Flow

The system processes event information through the following flow:

```text
Event Organizer
      |
      v
Submit Event Details
      |
      v
Event Database
      |
      v
Analyze Event Collision <---- External Event Sources
      |                              |
      v                              v
Generate Report & Alert       External Events Database
      |
      v
Collision Report /
Recommendation
