from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from database import init_db, get_connection
from scraper import scrape_nagpur_tenders
import json
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

print("Using database at:", os.path.abspath("tender.db"))

init_db()


# ---------------- HOME ----------------

@app.route("/")
def home():

    conn = get_connection()
    cursor = conn.cursor()

    # check if tenders exist
    cursor.execute("SELECT COUNT(*) FROM tenders")
    count = cursor.fetchone()[0]

    # if empty → scrape automatically
    if count == 0:
        print("No tenders found. Scraping...")
        scrape_nagpur_tenders()

    cursor.execute("""
        SELECT id, title, department, location, deadline, emd,
               relevance_score, risk_score, difficulty_score, fit_score
        FROM tenders
        ORDER BY id DESC
        LIMIT 6
    """)

    tenders = cursor.fetchall()
    conn.close()

    return render_template("index.html", tenders=tenders)


# ---------------- ADD TENDER ----------------

@app.route("/add", methods=["POST"])
def add_tender():

    data = request.form

    description = data["description"].lower()
    emd = int(data["emd"])
    tender_category = data["category"].lower()

    # ---------- RELEVANCE SCORE ----------

    keywords = ["construction", "road", "bridge", "ai", "software", "it"]
    relevance_score = sum(10 for word in keywords if word in description)

    # ---------- RISK SCORE ----------

    risk_score = 0

    if emd >= 500000:
        risk_score += 30
    elif emd >= 200000:
        risk_score += 15

    risky_words = ["penalty", "strict", "litigation", "blacklist"]
    risk_score += sum(20 for word in risky_words if word in description)

    # ---------- DIFFICULTY SCORE ----------

    difficulty_score = 0

    if emd >= 300000:
        difficulty_score += 20

    if len(description) > 150:
        difficulty_score += 20

    complex_words = ["technical", "compliance", "eligibility", "certification"]
    difficulty_score += sum(15 for word in complex_words if word in description)

    # ---------- FIT SCORE ----------

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT turnover, experience, category
        FROM company_profile
        ORDER BY id DESC
        LIMIT 1
    """)

    company = cursor.fetchone()

    fit_score = 0

    if company:

        company_turnover = float(company[0])
        company_experience = int(company[1])
        company_category = company[2].lower()

        if company_turnover >= emd:
            fit_score += 30

        if company_experience >= 3:
            fit_score += 30

        if company_category == tender_category:
            fit_score += 40

    # ---------- INSERT TENDER ----------

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
        fit_score
    ))

    conn.commit()
    conn.close()

    return redirect("/dashboard")


# ---------------- COMPANY PROFILE ----------------

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
            return "Email already registered."


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
            session["username"] = user[1]

            return redirect("/dashboard")

        else:
            return "Invalid credentials"


    return render_template("login.html")


# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():

    session.clear()
    return redirect(url_for("home"))


# ---------------- DASHBOARD ----------------

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM tenders")
    count = cursor.fetchone()[0]

    if count == 0:
        scrape_nagpur_tenders()

    cursor.execute("""
        SELECT id, title, department, location, deadline, emd,
               relevance_score, risk_score, difficulty_score, fit_score
        FROM tenders
        ORDER BY fit_score DESC
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


# ---------------- EXPLORE ----------------

@app.route("/explore")
def explore():

    search = request.args.get("search", "")
    category = request.args.getlist("category")
    location = request.args.get("location", "")
    sort = request.args.get("sort", "fit")

    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT id, title, department, location, deadline, emd,
               relevance_score, risk_score, difficulty_score, fit_score, category
        FROM tenders
        WHERE 1=1
    """

    params = []

    if search:
        query += " AND title LIKE ?"
        params.append(f"%{search}%")

    if category:
        placeholders = ",".join(["?"] * len(category))
        query += f" AND category IN ({placeholders})"
        params.extend(category)

    if location:
        query += " AND location = ?"
        params.append(location)

    if sort == "fit":
        query += " ORDER BY fit_score DESC"
    elif sort == "latest":
        query += " ORDER BY id DESC"
    elif sort == "deadline":
        query += " ORDER BY deadline ASC"

    cursor.execute(query, params)

    tenders = cursor.fetchall()
    conn.close()

    return render_template("explore.html", tenders=tenders)


# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run(debug=True)