from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from database import init_db, get_connection
from scraper import scrape_nagpur_tenders
import sqlite3
import json
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

print("Using database at:", os.path.abspath("tender.db"))

# ---------------- INIT DATABASE ----------------

init_db()


# ---------------- AUTO SCRAPE ON START ----------------

def auto_scrape():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM tenders")
    count = cursor.fetchone()[0]

    conn.close()

    if count == 0:
        print("Scraping tenders automatically...")
        scrape_nagpur_tenders()
    else:
        print("Tenders already exist. Skipping scraping.")


auto_scrape()


# ---------------- HOME PAGE ----------------

@app.route("/")
def home():

    conn = get_connection()
    cursor = conn.cursor()

    # Check if tenders exist
    cursor.execute("SELECT COUNT(*) FROM tenders")
    count = cursor.fetchone()[0]

    # If database empty → run scraper automatically
    if count == 0:
        print("No tenders found. Scraping automatically...")
        scrape_nagpur_tenders()

    # Fetch latest tenders
    cursor.execute("""
        SELECT title, department, location, deadline,
               risk_score, difficulty_score, relevance_score, fit_score
        FROM tenders
        ORDER BY id DESC
        LIMIT 6
    """)

    rows = cursor.fetchall()

    tenders = []

    for r in rows:
        tenders.append({
            "title": r[0],
            "department": r[1],
            "location": r[2],
            "deadline": r[3],
            "risk_score": r[4],
            "difficulty_score": r[5],
            "relevance_score": r[6],
            "fit_score": r[7]
        })

    conn.close()

    return render_template("index.html", tenders=tenders)


# ---------------- EXPLORE PAGE ----------------

@app.route("/explore")
def explore():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, title, department, location, deadline, emd,
               relevance_score, risk_score, difficulty_score, fit_score
        FROM tenders
        ORDER BY id DESC
    """)

    tenders = cursor.fetchall()

    conn.close()

    return render_template("explore.html", tenders=tenders)


# ---------------- REGISTER ----------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        category = request.form["category"]
        location = request.form["location"]
        budget = request.form["budget"]

        hashed_password = generate_password_hash(password)

        conn = get_connection()
        cursor = conn.cursor()

        try:

            cursor.execute("""
                INSERT INTO users
                (username, email, password, category, location, budget)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (username, email, hashed_password, category, location, budget))

            conn.commit()
            conn.close()

            return redirect("/login")

        except sqlite3.IntegrityError:

            conn.close()
            return "Email already registered"

    return render_template("register.html")


# ---------------- LOGIN ----------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE email=?", (email,))
        user = cursor.fetchone()

        conn.close()

        if user and check_password_hash(user[3], password):

            session["user_id"] = user[0]
            session["email"] = user[2]

            return redirect("/dashboard")

        else:
            return "Invalid Credentials"

    return render_template("login.html")


# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():

    session.clear()
    return redirect("/")


# ---------------- DASHBOARD ----------------

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, title, department, location, deadline, emd,
               relevance_score, risk_score, difficulty_score, fit_score
        FROM tenders
        ORDER BY fit_score DESC
        LIMIT 12
    """)

    tenders = cursor.fetchall()

    conn.close()

    labels = [t[1] for t in tenders]
    fit_scores = [t[9] for t in tenders]

    return render_template(
        "dashboard.html",
        tenders=tenders,
        labels_json=json.dumps(labels),
        fit_scores_json=json.dumps(fit_scores)
    )


# ---------------- ADD COMPANY PROFILE ----------------

@app.route("/company", methods=["POST"])
def add_company():

    data = request.form

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO company_profile(turnover, experience, category)
        VALUES (?, ?, ?)
    """, (
        data["turnover"],
        data["experience"],
        data["category"]
    ))

    conn.commit()
    conn.close()

    return redirect("/dashboard")


# ---------------- ADD TENDER ----------------

@app.route("/add", methods=["POST"])
def add_tender():

    data = request.form

    description = data["description"].lower()
    emd = int(data["emd"])
    category = data["category"].lower()

    # -------- RELEVANCE --------

    keywords = ["construction", "road", "bridge", "ai", "software", "it"]
    relevance_score = sum(10 for word in keywords if word in description)

    # -------- RISK --------

    risk_score = 0

    if emd >= 500000:
        risk_score += 30
    elif emd >= 200000:
        risk_score += 15

    risky_words = ["penalty", "litigation", "blacklist"]
    risk_score += sum(20 for word in risky_words if word in description)

    # -------- DIFFICULTY --------

    difficulty_score = 0

    if emd >= 300000:
        difficulty_score += 20

    if len(description) > 150:
        difficulty_score += 20

    complex_words = ["technical", "compliance", "eligibility"]
    difficulty_score += sum(15 for word in complex_words if word in description)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO tenders(
            title, department, location, deadline, emd, category, description,
            relevance_score, risk_score, difficulty_score, fit_score
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["title"],
        data["department"],
        data["location"],
        data["deadline"],
        emd,
        data["category"],
        data["description"],
        relevance_score,
        risk_score,
        difficulty_score,
        0
    ))

    conn.commit()
    conn.close()

    return redirect("/dashboard")


# ---------------- RUN SERVER ----------------

if __name__ == "__main__":
    app.run(debug=True)