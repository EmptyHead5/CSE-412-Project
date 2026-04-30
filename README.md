# Event Management System (CSE 412)

##  Project Overview
This project is a web-based Event Management System built using Flask and PostgreSQL.  
It demonstrates how a relational database schema (designed in Phase 2) can be integrated into a working application.

The system allows users to:
- Create events
- Register attendees for events
- Manage event status (Active / Cancelled)
- View which events each attendee has joined

---

##  Database Design
This project implements the following tables:

- Organizer
- Venue
- Event
- Schedule
- Attendee
- Student (ISA relationship)
- Attendance (many-to-many relationship)

Key features:
- Foreign key constraints
- One-to-many relationships
- Many-to-many relationships via Attendance
- ISA relationship (Student → Attendee)

---


##  Setup Instructions

### 1. Install dependencies

```bash
pip install -r requirements.txt
