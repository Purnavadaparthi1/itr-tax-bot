#rag_engine
import pandas as pd
import json
from datetime import datetime
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
import re

# =====================================================
# Conversation Memory
# =====================================================
last_employee = None

# =====================================================
# Load Data
# =====================================================
employee_df = pd.read_csv("data/employees.csv")

with open("data/holidays.json", "r") as f:
    holiday_data = json.load(f)

# =====================================================
# Load Vector Store (Policies Only)
# =====================================================
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

vectorstore = FAISS.load_local(
    "vector_store",
    embeddings,
    allow_dangerous_deserialization=True
)

# =====================================================
# MAIN ROUTER
# =====================================================
def retrieve_context(question: str):

    global last_employee
    q = question.lower().strip()

    # =====================================================
    # 1️⃣ SALARY FILTER (FIRST – to avoid conflict)
    # =====================================================
    salary_match = re.search(r"(greater than|more than|above|less than|below|>|<)\s*(\d+)", q)

    if "salary" in q and salary_match:
        condition = salary_match.group(1)
        amount = int(salary_match.group(2))

        if condition in ["greater than", "more than", "above", ">"]:
            filtered = employee_df[employee_df["Salary"] > amount]
        else:
            filtered = employee_df[employee_df["Salary"] < amount]

        if "list" in q:
            if filtered.empty:
                return "No employees found."

            names = "\n".join(
                [f"{row.Emp_Name} - {row.Salary}" for _, row in filtered.iterrows()]
            )
            return f"Employees matching salary condition:\n{names}"

        return f"{len(filtered)} employees match the salary condition."

    # =====================================================
    # 2️⃣ COUNT HOLIDAYS
    # =====================================================
    if "holiday" in q and "how many" in q:
        return f"There are {len(holiday_data['holidays'])} holidays in 2026."

    # =====================================================
    # 3️⃣ LIST HOLIDAYS
    # =====================================================
    if "holiday" in q and any(word in q for word in ["list", "show", "what"]):
        holiday_list = "\n".join(
            [
                f"{h['occasion']} - {h['date']} ({h['day']})"
                for h in holiday_data["holidays"]
            ]
        )
        return f"Here are the company holidays:\n{holiday_list}"

    # =====================================================
    # 4️⃣ UPCOMING HOLIDAY
    # =====================================================
    if "upcoming" in q and "holiday" in q:
        today = datetime.today()
        upcoming = None
        upcoming_date = None

        for holiday in holiday_data["holidays"]:
            h_date = datetime.strptime(holiday["date"], "%d-%b-%y")
            if h_date >= today:
                if upcoming_date is None or h_date < upcoming_date:
                    upcoming_date = h_date
                    upcoming = holiday

        if upcoming:
            return f"Upcoming holiday is {upcoming['occasion']} on {upcoming['date']} ({upcoming['day']})."

    # =====================================================
    # 5️⃣ SPECIFIC HOLIDAY MATCH
    # =====================================================
    for holiday in holiday_data["holidays"]:
        pattern = r"\b" + re.escape(holiday["occasion"].lower()) + r"\b"
        if re.search(pattern, q):
            return f"{holiday['occasion']} is on {holiday['date']} ({holiday['day']})."

    # =====================================================
    # 6️⃣ STRICT EMPLOYEE COUNT
    # =====================================================
    if re.fullmatch(r"how many employees\??", q):
        return f"There are {len(employee_df)} employees."

    # =====================================================
    # 7️⃣ EMPLOYEE ID MATCH
    # =====================================================
    for word in q.split():
        if word.isdigit():
            emp = employee_df[employee_df["Emp_ID"] == int(word)]
            if not emp.empty:
                last_employee = emp.iloc[0]
                return employee_field_response(last_employee, q)

    # =====================================================
    # 8️⃣ EMPLOYEE NAME MATCH
    # =====================================================
    for _, row in employee_df.iterrows():
        if row["Emp_Name"].lower() in q:
            last_employee = row
            return employee_field_response(row, q)

    # =====================================================
    # 9️⃣ PRONOUN FOLLOW-UP
    # =====================================================
    if last_employee is not None and any(
        word in q for word in ["his", "her", "him", "he", "she"]
    ):
        return employee_field_response(last_employee, q)

    # =====================================================
    # 🔟 POLICY / HANDBOOK (RAG)
    # =====================================================
    if any(word in q for word in ["policy", "leave", "break", "working hours", "attendance"]):
        docs = vectorstore.similarity_search(question, k=2)
        context = "\n".join([doc.page_content for doc in docs])
        return f"RAG::{context}" if context else None

    return "Information not available."


# =====================================================
# EMPLOYEE FIELD RESPONSE
# =====================================================
def employee_field_response(row, q):

    if "age" in q:
        return f"{row['Emp_Name']} is {row['Age']} years old."

    if "gender" in q:
        return f"{row['Emp_Name']} is {row['Gender']}."

    if "salary" in q:
        return f"{row['Emp_Name']}'s salary is {row['Salary']}."

    if "designation" in q:
        return f"{row['Emp_Name']} works as {row['Designation']}."

    if "email" in q:
        return f"{row['Emp_Name']}'s email is {row['Email']}."

    if "phone" in q:
        return f"{row['Emp_Name']}'s phone number is {row['Phone_Number']}."

    if "experience" in q:
        return f"{row['Emp_Name']} has {row['Experience_Years']} years of experience."

    if "details" in q or "who is" in q:
        return (
            f"{row['Emp_Name']} is a {row['Designation']} with "
            f"{row['Experience_Years']} years of experience. "
            f"Salary: {row['Salary']}."
        )

    return "Information not available."
