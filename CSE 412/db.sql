-- Organizer
CREATE TABLE Organizer (
 organizer_id SERIAL PRIMARY KEY,
 name TEXT NOT NULL,
 type TEXT,
 phone TEXT
);
-- Venue
CREATE TABLE Venue (
 venue_id SERIAL PRIMARY KEY,
 building TEXT,
 room TEXT,
 resources TEXT
);
-- Event
CREATE TABLE Event (
 event_id SERIAL PRIMARY KEY,
 name TEXT NOT NULL,
 category TEXT,
 is_public BOOLEAN,
 status TEXT,
 max_attendees INT,
 organizer_id INT REFERENCES Organizer(organizer_id),
 venue_id INT REFERENCES Venue(venue_id)
);
-- Schedule
CREATE TABLE Schedule (
 schedule_id SERIAL PRIMARY KEY,
 event_id INT UNIQUE REFERENCES Event(event_id),
 event_date DATE,
 start_time TIME,
 end_time TIME
);
-- Attendee
CREATE TABLE Attendee (
 attendee_id SERIAL PRIMARY KEY,
 name TEXT,
 phone TEXT
);
-- Student
CREATE TABLE Student (
 attendee_id INT PRIMARY KEY REFERENCES Attendee(attendee_id),
 major TEXT,
 graduating_year INT
);
-- Attendance
CREATE TABLE Attendance (
 attendee_id INT REFERENCES Attendee(attendee_id),
 event_id INT REFERENCES Event(event_id),
 PRIMARY KEY (attendee_id, event_id)
);
