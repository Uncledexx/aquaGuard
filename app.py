from flask import Flask, render_template, jsonify
import serial, threading, time, re
import mysql.connector
import datetime
import serial.tools.list_ports

app = Flask(__name__)

water_level = 0
alert_triggered = False
last_db_insert = datetime.datetime.min

DB_NAME = "aquaguard"
TABLE_NAME = "water_level_data"


def init_db():
    conn = mysql.connector.connect(host="localhost", user="root", password="")
    cursor = conn.cursor()

    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
    conn.database = DB_NAME

    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            water_level INT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()


def log_to_db(level):
    global last_db_insert
    now = datetime.datetime.now()

    if (now - last_db_insert).total_seconds() >= 60:

        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database=DB_NAME
        )

        cursor = conn.cursor()

        cursor.execute(
            f"INSERT INTO {TABLE_NAME} (water_level) VALUES (%s)",
            (level,)
        )

        conn.commit()
        cursor.close()
        conn.close()

        last_db_insert = now


def get_recent_alerts(limit=10):

    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database=DB_NAME
    )

    cursor = conn.cursor()

    cursor.execute(
        f"SELECT water_level, timestamp FROM {TABLE_NAME} ORDER BY timestamp DESC LIMIT {limit}"
    )

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    alerts = []

    for r in rows:
        alerts.append({
            "level": r[0],
            "time": r[1].strftime("%Y-%m-%d %H:%M:%S")
        })

    return alerts


init_db()


def find_arduino():

    ports = serial.tools.list_ports.comports()

    for port in ports:
        if "Arduino" in port.description or "CH340" in port.description:
            return port.device

    return None


try:

    port = find_arduino()

    if port:
        ser = serial.Serial(port, 9600, timeout=1)
        time.sleep(2)
        print("Connected to", port)

    else:
        ser = None
        print("Arduino not detected")

except:
    ser = None


def read_serial():

    global water_level, alert_triggered

    while True:

        if ser:

            line = ser.readline().decode('ascii', errors='ignore').strip()

            match = re.search(r'Water Level: (\d+)%', line)

            if match:

                val = int(match.group(1))

                water_level = val
                alert_triggered = val >= 80

                if alert_triggered:
                    log_to_db(val)

        time.sleep(0.2)


threading.Thread(target=read_serial, daemon=True).start()


@app.route("/")
def home():

    alerts = get_recent_alerts()

    return render_template(
        "index.html",
        recent_alerts=alerts
    )


@app.route("/api/water_level")
def api_water_level():

    return jsonify({
        "water_level": water_level,
        "alert": alert_triggered
    })


@app.route("/api/recent_alerts")
def api_recent_alerts():

    return jsonify(get_recent_alerts())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)