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
    building TEXT NOT NULL,
    room TEXT,
    resources TEXT
);

-- Event
CREATE TABLE Event (
    event_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT,
    is_public BOOLEAN,
    status TEXT NOT NULL DEFAULT 'Active',
    max_attendees INT,
    organizer_id INT REFERENCES Organizer(organizer_id) ON DELETE SET NULL,
    venue_id INT REFERENCES Venue(venue_id) ON DELETE SET NULL
);

-- Schedule
CREATE TABLE Schedule (
    schedule_id SERIAL PRIMARY KEY,
    event_id INT UNIQUE REFERENCES Event(event_id) ON DELETE CASCADE,
    event_date DATE,
    start_time TIME,
    end_time TIME
);

-- Attendee
CREATE TABLE Attendee (
    asurite_id VARCHAR(20) PRIMARY KEY,
    name TEXT NOT NULL,
    phone TEXT NOT NULL
);

-- Student (ISA)
CREATE TABLE Student (
    asurite_id VARCHAR(20) PRIMARY KEY REFERENCES Attendee(asurite_id) ON DELETE CASCADE,
    major TEXT,
    graduating_year INT
);

-- Attendance (many-to-many)
CREATE TABLE Attendance (
    asurite_id VARCHAR(20) REFERENCES Attendee(asurite_id) ON DELETE CASCADE,
    event_id INT REFERENCES Event(event_id) ON DELETE CASCADE,
    PRIMARY KEY (asurite_id, event_id)
);
