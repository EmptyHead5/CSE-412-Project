from flask import Flask, request, redirect, render_template
import psycopg2
from collections import defaultdict

app = Flask(__name__)

conn = psycopg2.connect(
    dbname="cse412",
    user="postgres",
    password="1234",
    host="localhost"
)

@app.route('/')
def index():
    cur = conn.cursor()

    cur.execute("""
        SELECT e.event_id, e.name, e.status,
               v.building, v.room,
               s.event_date, s.start_time,
               o.name
        FROM Event e
        LEFT JOIN Venue v ON e.venue_id = v.venue_id
        LEFT JOIN Schedule s ON e.event_id = s.event_id
        LEFT JOIN Organizer o ON e.organizer_id = o.organizer_id
    """)
    events = cur.fetchall()

    cur.execute("""
        SELECT a.name, e.name, a.asurite_id
        FROM Attendee a
        JOIN Student s ON a.asurite_id = s.asurite_id
        LEFT JOIN Attendance at ON a.asurite_id = at.asurite_id
        LEFT JOIN Event e ON at.event_id = e.event_id
    """)
    students_raw = cur.fetchall()
    cur.close()

    student_dict = defaultdict(list)
    for name, event, asurite_id in students_raw:
        key = (name, asurite_id)
        student_dict[key].append(event if event else "None")

    return render_template("index.html", events=events, students=student_dict)


@app.route('/register', methods=['POST'])
def register():
    asurite_id = request.form['asurite_id'].strip().lower()
    name = request.form['name'].strip()
    phone = request.form['phone'].strip()
    event_id = request.form['event_id']

    if not asurite_id or not name or not phone:
        return "All fields are required."

    cur = conn.cursor()

    # Check if attendee already exists
    cur.execute("SELECT asurite_id FROM Attendee WHERE asurite_id=%s", (asurite_id,))
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO Attendee (asurite_id, name, phone) VALUES (%s, %s, %s)",
            (asurite_id, name, phone)
        )
        cur.execute(
            "INSERT INTO Student (asurite_id, major, graduating_year) VALUES (%s, %s, %s)",
            (asurite_id, "Computer Science", 2026)
        )

    # Check for duplicate registration
    cur.execute(
        "SELECT 1 FROM Attendance WHERE asurite_id=%s AND event_id=%s",
        (asurite_id, event_id)
    )
    if cur.fetchone():
        cur.close()
        return redirect('/?error=already_registered')

    cur.execute(
        "INSERT INTO Attendance (asurite_id, event_id) VALUES (%s, %s)",
        (asurite_id, event_id)
    )
    conn.commit()
    cur.close()
    return redirect('/')


@app.route('/add_event', methods=['POST'])
def add_event():
    name = request.form['name'].strip()
    status = request.form['status'].strip()
    organizer_name = request.form.get('organizer_name', '').strip()
    location = request.form.get('location', '').strip()
    room = request.form.get('room', '').strip()

    if not organizer_name:
        return "Organizer name cannot be empty."
    if not location:
        return "Location cannot be empty."

    cur = conn.cursor()

    cur.execute("SELECT organizer_id FROM Organizer WHERE name=%s", (organizer_name,))
    result = cur.fetchone()
    if result is None:
        cur.execute(
            "INSERT INTO Organizer (name) VALUES (%s) RETURNING organizer_id",
            (organizer_name,)
        )
        organizer_id = cur.fetchone()[0]
    else:
        organizer_id = result[0]

    cur.execute("SELECT venue_id FROM Venue WHERE building=%s AND room=%s", (location, room))
    venue = cur.fetchone()
    if venue is None:
        cur.execute(
            "INSERT INTO Venue (building, room) VALUES (%s, %s) RETURNING venue_id",
            (location, room)
        )
        venue_id = cur.fetchone()[0]
    else:
        venue_id = venue[0]

    cur.execute("""
        INSERT INTO Event (name, status, organizer_id, venue_id)
        VALUES (%s, %s, %s, %s)
        RETURNING event_id
    """, (name, status, organizer_id, venue_id))
    event_id = cur.fetchone()[0]

    cur.execute("""
        INSERT INTO Schedule (event_id, event_date, start_time, end_time)
        VALUES (%s, CURRENT_DATE, '10:00', '12:00')
    """, (event_id,))

    conn.commit()
    cur.close()
    return redirect('/')


@app.route('/active/<int:event_id>')
def active(event_id):
    cur = conn.cursor()
    cur.execute("UPDATE Event SET status='Active' WHERE event_id=%s", (event_id,))
    conn.commit()
    cur.close()
    return redirect('/')


@app.route('/cancel/<int:event_id>')
def cancel(event_id):
    cur = conn.cursor()
    cur.execute("UPDATE Event SET status='Cancelled' WHERE event_id=%s", (event_id,))
    conn.commit()
    cur.close()
    return redirect('/')


@app.route('/delete/<int:event_id>', methods=['POST'])
def delete(event_id):
    cur = conn.cursor()
    cur.execute("DELETE FROM Event WHERE event_id=%s", (event_id,))
    conn.commit()
    cur.close()
    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True)