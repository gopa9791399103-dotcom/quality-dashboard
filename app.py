import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import mysql.connector

# ---------------- APP SETUP ----------------
app = Flask(__name__)
app.secret_key = "SujanQualityMonitoringSecureKey"

# ---------------- RAILWAY DB CONFIG ----------------
db_config = {
    "host": "trolley.proxy.rlwy.net",
    "port": 10817,
    "user": "root",
    "password": "cMEGSJPymiJQtUIuxAhmTooLPAjgYMhF",
    "database": "quality_input",
    "autocommit": True
}


# ---------------- DB CONNECTION FUNCTION ----------------
def get_db():
    return mysql.connector.connect(**db_config)


# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        if username == "Sujan" and password == "Maint":

            session["user"] = username
            return redirect(url_for("index"))

        else:
            return render_template("login.html",
                                   error="Invalid Username or Password")

    return render_template("login.html")


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():

    session.clear()
    return redirect(url_for("login"))


# ---------------- HOME ----------------
@app.route("/")
def index():

    if "user" not in session:
        return redirect(url_for("login"))

    return render_template("index.html")


# ---------------- COMMON FETCH FUNCTION ----------------
def fetch_section(section_name):

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT parameter, jan, feb, mar, apr, may, jun,
               jul, aug, sep, oct, nov, `dec`, ytd
        FROM quality_data
        WHERE section = %s
    """, (section_name,))

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    data = {row["parameter"]: row for row in rows}

    return data


# ---------------- ROUTES ----------------
@app.route("/customer_score_card")
def customer_score_card():
    data = fetch_section("Customer Score card")
    return render_template("customer_score_card.html", data=data)


@app.route("/customer_complaints")
def customer_complaints():
    data = fetch_section("No of Customer Complaints")
    return render_template("customer_complaints.html", data=data)


@app.route("/customer_ppm")
def customer_ppm():
    data = fetch_section("Customer PPM")
    return render_template("customer_ppm.html", data=data)


@app.route("/warranty_complaints")
def warranty_complaints():
    data = fetch_section("No of Warranty Complaints")
    return render_template("warranty_complaints.html", data=data)


@app.route("/warranty_chargeback")
def warranty_chargeback():
    data = fetch_section("Warranty Charge back")
    return render_template("warranty_chargeback.html", data=data)


@app.route("/sales_return")
def sales_return():
    data = fetch_section("Sales Return")
    return render_template("sales_return.html", data=data)


@app.route("/informal_complaints")
def informal_complaints():
    data = fetch_section("Inform Complaint")
    return render_template("informal_complaints.html", data=data)


# ---------------- SETTINGS ----------------
@app.route("/settings")
def settings():

    structure = {

        "Customer Score card": [
            "RENAULT", "NISSAN", "PSA",
            "PSA AVTECH", "DAIMLER",
            "ALF", "GESTAMP"
        ],

        "No of Customer Complaints": [
            "No of Complaints", "Target"
        ],

        "Customer PPM": [
            "Rej Qty", "Supplied Qty",
            "PPM", "Target"
        ],

        "No of Warranty Complaints": [
            "No of Complaints", "Target"
        ],

        "Warranty Charge back": [
            "WCB Cost", "Target"
        ],

        "Sales Return": [
            "Sales Rtn Qty", "Cost", "Target"
        ],

        "Inform Complaint": [
            "No of Complaints", "Target"
        ]
    }

    return render_template("settings.html",
                           structure=structure)


# ---------------- SAVE DATA ----------------
@app.route("/submit_data", methods=["POST"])
def submit_data():

    try:

        data = request.get_json()

        conn = get_db()
        cursor = conn.cursor()

        month_map = {

            "Jan'26": "jan",
            "Feb'26": "feb",
            "Mar'26": "mar",
            "Apr'26": "apr",
            "May'26": "may",
            "Jun'26": "jun",
            "Jul'26": "jul",
            "Aug'26": "aug",
            "Sep'26": "sep",
            "Oct'26": "oct",
            "Nov'26": "nov",
            "Dec'26": "dec"
        }

        for cell in data:

            section = cell["section"]
            parameter = cell["parameter"]
            month = cell["month"]
            value = int(cell["value"]) if cell["value"] else 0

            column = month_map.get(month)

            if column:

                sql = f"""
                INSERT INTO quality_data
                (section, parameter, `{column}`)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE
                `{column}` = VALUES(`{column}`)
                """

                cursor.execute(sql,
                               (section, parameter, value))

        # FAST YTD UPDATE (NO LOCK)
        cursor.execute("""

            UPDATE quality_data
            SET ytd =
            IFNULL(jan,0)+IFNULL(feb,0)+IFNULL(mar,0)+
            IFNULL(apr,0)+IFNULL(may,0)+IFNULL(jun,0)+
            IFNULL(jul,0)+IFNULL(aug,0)+IFNULL(sep,0)+
            IFNULL(oct,0)+IFNULL(nov,0)+IFNULL(`dec`,0)

        """)

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": "Saved successfully"
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# ---------------- LOAD DATA ----------------
@app.route("/get_data")
def get_data():

    try:

        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM quality_data")

        rows = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify(rows)

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# ---------------- RUN ----------------
if __name__ == "__main__":


port = int(os.environ.get("PORT", 5005))


app.run(host="0.0.0.0", port=port)

