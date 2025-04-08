import streamlit as st
import cx_Oracle
import pandas as pd
import re

# Oracle DB connection
def get_db_connection():
    dsn = cx_Oracle.makedsn("localhost", 1521, service_name="XE")
    conn = cx_Oracle.connect(user="SYSTEM", password="manager", dsn=dsn)
    return conn

# Fetch data
def fetch_data(query, params=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params or [])
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data

# Execute insert/update/delete
def execute_query(query, params=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params or [])
    conn.commit()
    cursor.close()
    conn.close()

# Streamlit UI
st.title("🏥 Hospital Management System")

menu = st.sidebar.selectbox("Menu", [
    "Home", "Add Patient", "Update/Delete Patient", "Medical History",
    "Treatment Plans", "Billing", "View All Patients", "Full Patient Record"
])

# Home
if menu == "Home":
    st.subheader("Welcome to the Hospital Management System!")
    st.write("""
        This application allows you to manage patients, view their medical history, 
        treatment plans, and billing records efficiently. 
        Navigate using the sidebar to explore different features.
    """)

# Add Patient
elif menu == "Add Patient":
    st.header("➕ Add New Patient")
    with st.form("add_patient_form"):
        name = st.text_input("Name")
        age = st.number_input("Age", min_value=0)
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        contact = st.text_input("Contact (10 digits)")
        address = st.text_area("Address")
        submit = st.form_submit_button("Add Patient")

        if submit:
            if not re.fullmatch(r"\d{10}", contact):
                st.error("❌ Invalid contact number. Please enter exactly 10 digits.")
            elif name.strip() == "":
                st.error("❌ Name cannot be empty.")
            else:
                try:
                    query = """
                        INSERT INTO MINE.Patients (Name, Age, Gender, Contact, Address) 
                        VALUES (:1, :2, :3, :4, :5)
                    """
                    execute_query(query, (name, age, gender, contact, address))
                    st.success("✅ Patient added successfully!")
                except cx_Oracle.IntegrityError as e:
                    st.error(f"❌ Error: {e}")

# Update/Delete Patient
elif menu == "Update/Delete Patient":
    st.header("✏️ Update or Delete Patient")
    data = fetch_data("SELECT * FROM MINE.Patients")
    df = pd.DataFrame(data, columns=["Patient ID", "Name", "Age", "Gender", "Contact", "Address"])
    st.dataframe(df)

    if not df.empty:
        selected = st.selectbox("Select Patient ID", df["Patient ID"])
        row = df[df["Patient ID"] == selected].iloc[0]
        with st.form("update_patient"):
            name = st.text_input("Name", row["Name"])
            age = st.number_input("Age", value=row["Age"])
            gender = st.selectbox("Gender", ["Male", "Female", "Other"], index=["Male", "Female", "Other"].index(row["Gender"]))
            contact = st.text_input("Contact", row["Contact"])
            address = st.text_area("Address", row["Address"])
            update = st.form_submit_button("Update")
            delete = st.form_submit_button("Delete")

            if update:
                if not re.fullmatch(r"\d{10}", contact):
                    st.error("❌ Contact must be exactly 10 digits.")
                elif name.strip() == "":
                    st.error("❌ Name cannot be empty.")
                else:
                    try:
                        execute_query("""
                            UPDATE MINE.Patients 
                            SET Name=:1, Age=:2, Gender=:3, Contact=:4, Address=:5 
                            WHERE PatientID=:6
                        """, (name, age, gender, contact, address, selected))
                        st.success("✅ Patient updated!")
                    except cx_Oracle.IntegrityError as e:
                        st.error(f"❌ Error: {e}")

            if delete:
                execute_query("DELETE FROM MINE.Patients WHERE PatientID=:1", (selected,))
                st.success("🗑️ Patient deleted!")

# Medical History
elif menu == "Medical History":
    st.header("🩺 Medical History")
    patient_ids = [r[0] for r in fetch_data("SELECT PatientID FROM MINE.Patients")]
    if patient_ids:
        patient_id = st.selectbox("Select Patient ID", patient_ids)
        with st.form("add_history"):
            diagnosis = st.text_input("Diagnosis")
            meds = st.text_input("Medications")
            allergy = st.text_input("Allergies")
            submit = st.form_submit_button("Add")

            if submit:
                query = """
                    INSERT INTO MINE.MedicalHistory (PatientID, Diagnosis, Medications, Allergies) 
                    VALUES (:1, :2, :3, :4)
                """
                execute_query(query, (patient_id, diagnosis, meds, allergy))
                st.success("✅ History added!")

        if st.button("View History"):
            data = fetch_data("SELECT * FROM MINE.MedicalHistory WHERE PatientID = :1", (patient_id,))
            df = pd.DataFrame(data, columns=["History ID", "Patient ID", "Diagnosis", "Medications", "Allergies"])
            st.dataframe(df)

# Treatment Plans
elif menu == "Treatment Plans":
    st.header("🧪 Treatment Plans")
    patient_ids = [r[0] for r in fetch_data("SELECT PatientID FROM MINE.Patients")]
    if patient_ids:
        patient_id = st.selectbox("Select Patient ID", patient_ids)
        with st.form("add_treatment"):
            desc = st.text_input("Treatment Description")
            start = st.date_input("Start Date")
            end = st.date_input("End Date")
            submit = st.form_submit_button("Add")

            if submit:
                query = """
                    INSERT INTO MINE.TreatmentPlans (PatientID, TreatmentDescription, StartDate, EndDate) 
                    VALUES (:1, :2, :3, :4)
                """
                execute_query(query, (patient_id, desc, start, end))
                st.success("✅ Treatment plan added!")

        if st.button("View Plans"):
            data = fetch_data("SELECT * FROM MINE.TreatmentPlans WHERE PatientID = :1", (patient_id,))
            df = pd.DataFrame(data, columns=["Plan ID", "Patient ID", "Description", "Start Date", "End Date"])
            st.dataframe(df)

# Billing
elif menu == "Billing":
    st.header("💵 Billing")
    patient_ids = [r[0] for r in fetch_data("SELECT PatientID FROM MINE.Patients")]
    if patient_ids:
        patient_id = st.selectbox("Select Patient ID", patient_ids)
        with st.form("add_bill"):
            amt = st.number_input("Amount", min_value=0.0, format="%.2f")
            status = st.selectbox("Status", ["Pending", "Paid"])
            submit = st.form_submit_button("Add")

            if submit:
                query = "INSERT INTO MINE.Billing (PatientID, Amount, Status) VALUES (:1, :2, :3)"
                execute_query(query, (patient_id, amt, status))
                st.success("✅ Bill added!")

        if st.button("View Bills"):
            data = fetch_data("SELECT * FROM MINE.Billing WHERE PatientID = :1", (patient_id,))
            df = pd.DataFrame(data, columns=["Bill ID", "Patient ID", "Amount", "Status"])
            st.dataframe(df)

# View All Patients
elif menu == "View All Patients":
    st.header("📋 All Patients")
    data = fetch_data("SELECT * FROM MINE.Patients")
    df = pd.DataFrame(data, columns=["Patient ID", "Name", "Age", "Gender", "Contact", "Address"])
    st.dataframe(df)

# Full Patient Record
elif menu == "Full Patient Record":
    st.header("📚 Complete Patient Records")
    patient_ids = [r[0] for r in fetch_data("SELECT PatientID FROM MINE.Patients")]
    if patient_ids:
        patient_id = st.selectbox("Select Patient ID", patient_ids)

        # Data fetching
        patient = fetch_data("SELECT * FROM MINE.Patients WHERE PatientID = :1", (patient_id,))
        hist = fetch_data("SELECT Diagnosis, Medications, Allergies FROM MINE.MedicalHistory WHERE PatientID = :1", (patient_id,))
        treat = fetch_data("SELECT TreatmentDescription, StartDate, EndDate FROM MINE.TreatmentPlans WHERE PatientID = :1", (patient_id,))
        bill = fetch_data("SELECT Amount, Status FROM MINE.Billing WHERE PatientID = :1", (patient_id,))

        st.subheader("Basic Info")
        st.dataframe(pd.DataFrame(patient, columns=["Patient ID", "Name", "Age", "Gender", "Contact", "Address"]))

        st.subheader("Medical History")
        st.dataframe(pd.DataFrame(hist, columns=["Diagnosis", "Medications", "Allergies"]))

        st.subheader("Treatment Plans")
        st.dataframe(pd.DataFrame(treat, columns=["Description", "Start Date", "End Date"]))

        st.subheader("Billing Info")
        st.dataframe(pd.DataFrame(bill, columns=["Amount", "Status"]))
