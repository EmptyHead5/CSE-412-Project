from flask import Flask, request, redirect, render_template, session
import psycopg2
from collections import defaultdict

app = Flask(__name__)

app.secret_key = 'any_random_string'

conn = psycopg2.connect(
    dbname="cse412",
    user="nickogle", 
    host="localhost",
    port="8888" 
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
        ORDER BY e.event_id DESC
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

    # check if the event is at max capacity
    cur.execute("""
        SELECT 
            (SELECT COUNT(*) FROM Attendance WHERE event_id = %s),
            (SELECT max_attendees FROM Event WHERE event_id = %s)
    """, (event_id, event_id))
    
    current_count, max_cap = cur.fetchone()

    if max_cap is not None and current_count >= max_cap:
        cur.close()
        return redirect((request.referrer or '/') + '?error=event_full')

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
        return redirect((request.referrer or '/') + '?error=already_registered')

    cur.execute(
        "INSERT INTO Attendance (asurite_id, event_id) VALUES (%s, %s)",
        (asurite_id, event_id)
    )

    session['user_asurite'] = asurite_id

    conn.commit()
    cur.close()
    return redirect(request.referrer or '/')

@app.route('/cancel_registration', methods=['POST'])
def cancel_registration():
    asurite_id = session.get('user_asurite')
    event_id = request.form.get('event_id')
    
    if asurite_id and event_id:
        cur = conn.cursor()
        cur.execute("DELETE FROM Attendance WHERE asurite_id = %s AND event_id = %s", (asurite_id, event_id))
        conn.commit()
        cur.close()
    
    return redirect(request.referrer or '/user')

@app.route('/add_event', methods=['POST'])
def add_event():
    name = request.form['name'].strip()
    status = request.form['status'].strip()
    organizer_name = request.form.get('organizer_name', '').strip()
    location = request.form.get('location', '').strip()
    room = request.form.get('room', '').strip()
    
    start_time = request.form.get('start_time', '09:00')

    max_limit = request.form.get('max_limit', '').strip()

    if max_limit == "":
        max_limit = None

    if not organizer_name or not location:
        return "Organizer and Location are required."

    cur = conn.cursor()

    cur.execute("SELECT organizer_id FROM Organizer WHERE name=%s", (organizer_name,))
    result = cur.fetchone()
    if result is None:
        cur.execute("INSERT INTO Organizer (name) VALUES (%s) RETURNING organizer_id", (organizer_name,))
        organizer_id = cur.fetchone()[0]
    else:
        organizer_id = result[0]

    cur.execute("SELECT venue_id FROM Venue WHERE building=%s AND room=%s", (location, room))
    venue = cur.fetchone()
    if venue is None:
        cur.execute("INSERT INTO Venue (building, room) VALUES (%s, %s) RETURNING venue_id", (location, room))
        venue_id = cur.fetchone()[0]
    else:
        venue_id = venue[0]

    cur.execute("""
        INSERT INTO Event (name, status, organizer_id, venue_id, max_attendees)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING event_id
    """, (name, status, organizer_id, venue_id, max_limit))
    event_id = cur.fetchone()[0]

    cur.execute("""
        INSERT INTO Schedule (event_id, event_date, start_time, end_time)
        VALUES (%s, CURRENT_DATE, %s, '23:59')
    """, (event_id, start_time))

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

    cur.execute("""
        DELETE FROM Attendee 
        WHERE asurite_id NOT IN (SELECT asurite_id FROM Attendance)
    """)

    conn.commit()
    cur.close()
    return redirect('/')

@app.route('/edit/<int:event_id>', methods=['GET', 'POST'])
def edit_event(event_id):
    cur = conn.cursor()

    if request.method == 'POST':
        name = request.form['name']
        status = request.form['status']
        location = request.form['location']
        room = request.form['room']
        max_limit = request.form.get('max_limit', '').strip()
        max_limit = int(max_limit) if max_limit else None

        cur.execute("SELECT venue_id FROM Event WHERE event_id = %s", (event_id,))
        venue_id = cur.fetchone()[0]
        
        cur.execute("UPDATE Venue SET building=%s, room=%s WHERE venue_id=%s", (location, room, venue_id))
        
        cur.execute("""
            UPDATE Event 
            SET name=%s, status=%s, max_attendees=%s 
            WHERE event_id=%s
        """, (name, status, max_limit, event_id))

        conn.commit()
        cur.close()
        return redirect('/')

    cur.execute("""
        SELECT e.name, e.status, v.building, v.room, e.max_attendees 
        FROM Event e 
        JOIN Venue v ON e.venue_id = v.venue_id 
        WHERE e.event_id = %s
    """, (event_id,))
    event = cur.fetchone()
    cur.close()
    return render_template('edit_event.html', event=event, event_id=event_id)

@app.route('/user')
def user_index():
    cur = conn.cursor()
    cur.execute("""
        SELECT e.event_id, e.name, v.building, v.room, s.event_date, s.start_time 
        FROM Event e
        JOIN Venue v ON e.venue_id = v.venue_id
        JOIN Schedule s ON e.event_id = s.event_id
        WHERE e.status = 'Active'
    """)
    events = cur.fetchall()

    user_asurite = session.get('user_asurite')
    my_event_ids = []
    if user_asurite:
        cur.execute("SELECT event_id FROM Attendance WHERE asurite_id = %s", (user_asurite,))
        my_event_ids = [row[0] for row in cur.fetchall()]

    cur.close()
    return render_template('user_index.html', events=events, my_event_ids=my_event_ids)

if __name__ == '__main__':
    app.run(debug=True)