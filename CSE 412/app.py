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
        SELECT a.name, e.name, a.phone
        FROM Attendee a
        JOIN Student s ON a.attendee_id = s.attendee_id
        LEFT JOIN Attendance at ON a.attendee_id = at.attendee_id
        LEFT JOIN Event e ON at.event_id = e.event_id
    """)
    students_raw = cur.fetchall()
    cur.close()

    student_dict = defaultdict(list)
    for name, event, phone in students_raw:
        key = (name, phone)
        if event:
            student_dict[key].append(event)
        else:
            student_dict[key].append("None")

    return render_template("index.html", events=events, students=student_dict)


@app.route('/register', methods=['POST'])
def register():
    name = request.form['name']
    phone = request.form['phone']
    event_id = request.form['event_id']

    cur = conn.cursor()

    cur.execute(
        "INSERT INTO Attendee (name, phone) VALUES (%s, %s) RETURNING attendee_id",
        (name, phone)
    )
    attendee_id = cur.fetchone()[0]

    cur.execute(
        "INSERT INTO Student (attendee_id, major, graduating_year) VALUES (%s, %s, %s)",
        (attendee_id, "Computer Science", 2026)
    )

    cur.execute(
        "INSERT INTO Attendance (attendee_id, event_id) VALUES (%s, %s)",
        (attendee_id, event_id)
    )

    conn.commit()
    cur.close()

    return redirect('/')


@app.route('/add_event', methods=['POST'])
def add_event():
    name = request.form['name']
    status = request.form['status']
    organizer_name = request.form.get('organizer_name')
    location = request.form.get('location')
    room = request.form.get('room')

    if not organizer_name or not organizer_name.strip():
        return "Organizer name cannot be empty"

    if not location or not location.strip():
        return "Location cannot be empty"

    cur = conn.cursor()


    cur.execute(
        "SELECT organizer_id FROM Organizer WHERE name=%s",
        (organizer_name,)
    )
    result = cur.fetchone()

    if result is None:
        cur.execute(
            "INSERT INTO Organizer (name) VALUES (%s) RETURNING organizer_id",
            (organizer_name,)
        )
        organizer_id = cur.fetchone()[0]
    else:
        organizer_id = result[0]

  
    cur.execute(
        "SELECT venue_id FROM Venue WHERE building=%s AND room=%s",
        (location, room)
    )
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
    cur.execute(
        "UPDATE Event SET status='Active' WHERE event_id=%s",
        (event_id,)
    )
    conn.commit()
    cur.close()
    return redirect('/')


@app.route('/cancel/<int:event_id>')
def cancel(event_id):
    cur = conn.cursor()
    cur.execute(
        "UPDATE Event SET status='Cancelled' WHERE event_id=%s",
        (event_id,)
    )
    conn.commit()
    cur.close()
    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True)