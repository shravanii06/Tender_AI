import os
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from webdriver_manager.chrome import ChromeDriverManager

from database import get_connection

from ai_engine import (
    calculate_relevance,
    calculate_risk,
    calculate_difficulty,
    calculate_fit
)


# ---------------- URGENCY CALCULATOR ----------------

def get_urgency(deadline):

    try:

        deadline_date = datetime.strptime(deadline, "%d-%m-%Y")

        days_left = (deadline_date - datetime.now()).days

        if days_left <= 3:
            return "High"

        elif days_left <= 10:
            return "Medium"

        else:
            return "Low"

    except:

        return "Low"



# ---------------- MAIN SCRAPER ----------------

def scrape_nagpur_tenders():

    url = "https://nagpur.gov.in/past-notices/tenders/"

    options = Options()

    # Uncomment this later for server deployment
    # options.add_argument("--headless")

    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--start-maximized")

    service = Service(ChromeDriverManager().install())

    driver = webdriver.Chrome(service=service, options=options)

    conn = get_connection()
    cursor = conn.cursor()

    try:

        driver.get(url)

        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "table"))
        )

        rows = driver.find_elements(By.TAG_NAME, "tr")

        added_count = 0

        for row in rows[1:]:

            cols = row.find_elements(By.TAG_NAME, "td")

            if len(cols) >= 5:

                title = cols[1].text.strip()
                deadline = cols[3].text.strip()

                if not title:
                    continue

                if "meeting" in title.lower():
                    continue


                # Avoid duplicates
                cursor.execute(
                    "SELECT id FROM tenders WHERE title=?",
                    (title,)
                )

                if cursor.fetchone():
                    continue


                department = "Nagpur Municipal Corporation"
                location = "Nagpur"
                category = "General"
                description = "Scraped from Nagpur municipal portal"
                emd = 0


                # ---------------- AI SCORING ----------------

                relevance = calculate_relevance(title, description)

                risk = calculate_risk(deadline, emd)

                difficulty = calculate_difficulty(title, category)

                fit = calculate_fit(relevance, risk, difficulty)


                # ---------------- INSERT ----------------

                cursor.execute("""

                INSERT INTO tenders(
                    title,
                    department,
                    location,
                    deadline,
                    emd,
                    category,
                    description,
                    relevance_score,
                    risk_score,
                    difficulty_score,
                    fit_score
                )

                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

                """, (

                    title,
                    department,
                    location,
                    deadline,
                    emd,
                    category,
                    description,
                    relevance,
                    risk,
                    difficulty,
                    fit

                ))


                conn.commit()

                added_count += 1


        print(f"{added_count} tenders scraped successfully")

        return added_count


    except Exception as e:

        print("Scraper Error:", e)

        return 0


    finally:

        conn.close()

        driver.quit()



# ---------------- RUN SCRAPER ----------------

if __name__ == "__main__":

    print("Starting Nagpur Tender Scraper...")

    scrape_nagpur_tenders()