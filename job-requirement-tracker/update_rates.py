import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'recruitment_tracker.db')
conn = sqlite3.connect(db_path)
c = conn.cursor()

# Update pay rates for any final selected candidates where pay rate is null or empty
c.execute("UPDATE candidates SET consultant_pay_rate = '$65/hr' WHERE candidate_name LIKE '%Alex%'")
c.execute("UPDATE candidates SET consultant_pay_rate = '$80/hr' WHERE candidate_name LIKE '%Frank%'")
c.execute("UPDATE candidates SET consultant_pay_rate = '$70/hr' WHERE candidate_name LIKE '%Samantha%'")
c.execute("UPDATE candidates SET consultant_pay_rate = '$65/hr' WHERE current_stage = 'Final Selected' AND consultant_pay_rate = '/hr'")

conn.commit()
rows = c.execute("SELECT candidate_name, final_billing_rate, consultant_pay_rate FROM candidates WHERE current_stage = 'Final Selected'").fetchall()
print("Updated Final Selected candidates:")
for r in rows:
    print(r)

conn.close()
