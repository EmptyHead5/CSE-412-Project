import psycopg2

conn = psycopg2.connect(
    dbname="cse412",
    user="postgres",
    password="1234",
    host="localhost"
)

cur = conn.cursor()

cur.execute("""
INSERT INTO Organizer (name, type, phone)
VALUES 
('ASU CS Dept', 'Department', '123456'),
('Google', 'Company', '999999'),
('Microsoft', 'Company', '888888')
RETURNING organizer_id;
""")
organizers = cur.fetchall()

cur.execute("""
INSERT INTO Venue (building, room, resources)
VALUES
('Brickyard', '101', 'Projector'),
('BYAC', '205', 'Whiteboard'),
('Zoom', 'Online', 'Virtual')
RETURNING venue_id;
""")
venues = cur.fetchall()

events = []
event_data = [
    ('Tech Talk', 'Active'),
    ('AI Workshop', 'Active'),
    ('Cloud Seminar', 'Cancelled')
]

for i, (name, status) in enumerate(event_data):
    cur.execute("""
        INSERT INTO Event (name, status, organizer_id, venue_id)
        VALUES (%s, %s, %s, %s)
        RETURNING event_id;
    """, (
        name,
        status,
        organizers[i][0],
        venues[i][0]
    ))
    events.append(cur.fetchone())

for i, e in enumerate(events):
    cur.execute("""
        INSERT INTO Schedule (event_id, event_date, start_time, end_time)
        VALUES (%s, CURRENT_DATE + %s, '10:00', '12:00')
    """, (e[0], i))

cur.execute("""
INSERT INTO Attendee (name, phone)
VALUES
('Alice', '111111'),
('Bob', '222222'),
('Charlie', '333333')
RETURNING attendee_id;
""")
attendees = cur.fetchall()

for a in attendees:
    cur.execute("""
        INSERT INTO Student (attendee_id, major, graduating_year)
        VALUES (%s, 'Computer Science', 2026)
    """, (a[0],))

for i, a in enumerate(attendees):
    event_id = events[i % len(events)][0]
    cur.execute("""
        INSERT INTO Attendance (attendee_id, event_id)
        VALUES (%s, %s)
    """, (a[0], event_id))

conn.commit()
cur.close()
conn.close()

print("Database initialized successfully!")