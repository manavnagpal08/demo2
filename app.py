import streamlit as st
import pandas as pd
import time
from database import SimulatedDatabase
from utils import PayrollCalculator, generate_payslip_pdf
import datetime

# --- Configuration & Styles ---
st.set_page_config(page_title="Helix Payroll Portal", layout="wide", page_icon=None)

# Initialize Database & Logic
if 'db' not in st.session_state:
    st.session_state.db = SimulatedDatabase()
if 'calc' not in st.session_state:
    st.session_state.calc = PayrollCalculator()

db = st.session_state.db
calc = st.session_state.calc

# Custom CSS for SaaS aesthetics
st.markdown("""
<style>
    /* Global Styles */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background-color: #f8f9fa;
    }
    
    /* Login Container */
    .login-container {
        max-width: 400px;
        margin: auto;
        padding: 40px;
        background: white;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.05);
        text-align: center;
    }
    
    /* Metrics */
    div[data-testid="stMetricValue"] {
        font-size: 24px;
        font-weight: 600;
        color: #2c3e50;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e9ecef;
    }
    
    /* Tables */
    div[data-testid="stDataFrame"] {
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid #e0e0e0;
    }
    
    /* Buttons */
    div.stButton > button {
        border-radius: 6px;
        font-weight: 500;
        transition: all 0.2s;
    }
    div.stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Header/Subheader */
    h1, h2, h3 {
        color: #1a1f36;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    
    /* Custom Card */
    .css-card {
        background: white;
        padding: 24px;
        border-radius: 12px;
        border: 1px solid #e9ecef;
        box-shadow: 0 2px 8px rgba(0,0,0,0.02);
        margin-bottom: 24px;
    }
</style>
""", unsafe_allow_html=True)

# --- Authentication Handling ---
def login_page():
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.title("Helix Payroll")
        st.markdown("### Secure Access Portal")
        
        role = st.selectbox("Select Role", ["HR", "Employee"])
        username = st.text_input("Email ID")
        password = st.text_input("Password", type="password")
        
        if st.button("Sign In", use_container_width=True):
            user = db.authenticate(username, password, role)
            if user:
                st.session_state.user = user
                st.success("Authenticated successfully.")
                st.rerun()
            else:
                st.error("Invalid credentials or role.")
        
        st.markdown("</div>", unsafe_allow_html=True)
        # Hint for demo
        st.info("Demo Login: alice@company.com / hr (HR) | bob@company.com / emp (Employee)")

def logout():
    st.session_state.user = None
    st.rerun()

# --- HR Modules ---

def hr_dashboard():
    st.title("HR Dashboard")
    st.markdown("Overview of organization status.")
    
    employees = db.get_all_employees()
    cases = db.get_all_cases()
    pending_cases = [c for c in cases if c['status'] == 'Open']
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Employees", len(employees))
    c2.metric("Pending Cases", len(pending_cases))
    c3.metric("Payroll Period", datetime.date.today().strftime("%B %Y"))
    
    st.markdown("### Recent Activities")
    st.table(pd.DataFrame([
        {"Activity": "System Initialization", "Time": "Today", "Status": "Completed"},
        {"Activity": "Master Data Sync", "Time": "Today", "Status": "Active"}
    ]).set_index("Activity"))

def hr_master_data():
    st.title("Master Data Registry")
    
    tab1, tab2, tab3 = st.tabs(["Employee List", "Update CTC", "Attendance Import"])
    
    with tab1:
        st.subheader("Employee Directory")
        employees = db.get_all_employees()
        df = pd.DataFrame(employees)
        # Hide password
        if 'password' in df.columns:
            df = df.drop(columns=['password'])
        st.dataframe(df, use_container_width=True)
        
    with tab2:
        st.subheader("Automated CTC Update")
        with st.container():
            st.markdown('<div class="css-card">', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                emp_id_input = st.selectbox("Select Employee", [e['emp_id'] for e in db.get_all_employees()])
            with c2:
                new_ctc = st.number_input("New Annual CTC (INR)", min_value=100000, value=500000, step=10000)
                
            if st.button("Update Structure"):
                success = db.update_ctc(emp_id_input, new_ctc)
                if success:
                    st.success(f"CTC updated for {emp_id_input}. Salary structure automatically recalculated.")
                    # Show new breakdown
                    emp = db.get_employee(emp_id_input)
                    st.json({
                        "New CTC": emp['ctc'],
                        "Basic (50%)": emp['basic'],
                        "HRA (20% of Basic)": emp['hra'],
                        "Special Allowance": emp['special']
                    })
                else:
                    st.error("Employee not found.")
            st.markdown('</div>', unsafe_allow_html=True)

    with tab3:
        st.subheader("Attendance Management")
        upload_file = st.file_uploader("Upload Attendance CSV", type=["csv"])
        if upload_file:
            try:
                # Expected: EmpID, Date (YYYY-MM-DD), Status, CheckIn, CheckOut, OTHours
                df_att = pd.read_csv(upload_file)
                st.dataframe(df_att.head())
                if st.button("Process & Import Logs"):
                    count = 0
                    for _, row in df_att.iterrows():
                        db.add_attendance_log(
                            row['EmpID'], row['Date'], row.get('Status', 'Present'), 
                            row.get('CheckIn', ''), row.get('CheckOut', ''), row.get('OTHours', 0)
                        )
                        count += 1
                    st.success(f"Successfully imported {count} records.")
            except Exception as e:
                st.error(f"Error parsing file: {e}")
        
        st.divider()
        st.subheader("Manual Attendance Override")
        c1, c2, c3 = st.columns(3)
        m_emp = c1.selectbox("Employee", [e['emp_id'] for e in db.get_all_employees()], key='att_man_emp')
        m_date = c2.date_input("Date")
        m_status = c3.selectbox("Status", ["Present", "Absent", "Half Day", "Leave"])
        
        c4, c5 = st.columns(2)
        m_ot = c4.number_input("Overtime Hours", min_value=0.0, step=0.5)
        
        if st.button("Update Attendance Record"):
            db.add_attendance_log(m_emp, str(m_date), m_status, ot_hours=m_ot)
            st.success("Record updated.")

def hr_payroll_engine():
    st.title("Payroll Engine")
    
    c1, c2 = st.columns(2)
    with c1:
        pay_month = st.selectbox("Month", ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"])
    with c2:
        pay_year = st.number_input("Year", value=2023)
        
    st.divider()
    
    st.subheader("Payroll Computation")
    
    if st.button("Run Payroll Calculation Batch"):
        results = []
        progress = st.progress(0)
        employees = db.get_all_employees()
        
        for idx, emp in enumerate(employees):
            # Fetch attendance for this month? 
            # For demo, we assume the attendance logs in DB cover the period or we simulate
            # Let's map Month Name to number
            m_num = datetime.datetime.strptime(pay_month, "%B").month
            # We would typically filter attendance logs for this month.
            # Simplified: Just grab what's there or pass empty if naive
            # Ideally: get_attendance_range or something. 
            # I'll rely on the calc logic handling 'None' gracefully or we iterate days
            
            # Use a dummy list of attendance for demo calculation if DB is empty
            # to ensure the USER sees numbers.
            # Or use actual DB data.
            
            # Let's construct a list of logs for this Emp for this month from DB
            att_records = []
            user_att = db.get_employee_attendance(emp['emp_id'])
            for date_str, log in user_att.items():
                d = datetime.datetime.strptime(date_str, "%Y-%m-%d")
                if d.month == m_num and d.year == pay_year:
                    att_records.append(log)
            
            salary = calc.calculate_salary(emp, att_records, pay_month, pay_year)
            results.append(salary)
            progress.progress((idx + 1) / len(employees))
            
        st.session_state.current_payroll_batch = results
        st.success("Batch calculation complete.")
        
    if 'current_payroll_batch' in st.session_state:
        batch = st.session_state.current_payroll_batch
        st.subheader("Batch Review")
        
        # Summary Dataframe
        summary_data = []
        for rec in batch:
            summary_data.append({
                "ID": rec['emp_id'],
                "Name": rec['name'],
                "Gross": rec['gross_salary'],
                "Deductions": rec['total_deductions'],
                "Net Pay": rec['net_salary']
            })
        st.dataframe(pd.DataFrame(summary_data))
        
        # Individual Actions
        st.subheader("Payslip Generation")
        selected_emp = st.selectbox("Select Employee for Payslip", [r['emp_id'] for r in batch])
        
        if st.button("Generate PDF Payslip"):
            record = next(r for r in batch if r['emp_id'] == selected_emp)
            pdf_buffer = generate_payslip_pdf(record)
            st.download_button(
                label="Download PDF",
                data=pdf_buffer,
                file_name=f"Payslip_{selected_emp}_{pay_month}.pdf",
                mime="application/pdf"
            )
            
            # Save to history
            db.save_payroll_record(record)
            
def hr_case_console():
    st.title("Case Management Console")
    
    cases = db.get_all_cases()
    if not cases:
        st.info("No active cases.")
        return
        
    for case in cases:
        with st.container():
            st.markdown(f"**Case ID:** {case['case_id']} | **Priority:** {case['priority']} | **Status:** {case['status']}")
            st.markdown(f"*{case['category']} - Submitted by {case['emp_id']} on {case['date']}*")
            st.text(case['description'])
            
            if case['status'] == 'Open':
                c1, c2 = st.columns([3, 1])
                comments = c1.text_input("HR Comments", key=f"c_{case['case_id']}")
                if c2.button("Resolve Case", key=f"b_{case['case_id']}"):
                    db.update_case(case['case_id'], "Resolved", comments)
                    st.success("Case resolved.")
                    st.rerun()
            else:
                st.markdown(f"**Resolution:** {case['hr_comments']}")
            st.divider()

# --- Employee Modules ---

def ess_dashboard():
    user = st.session_state.user
    st.title(f"Welcome, {user['name']}")
    
    c1, c2 = st.columns(2)
    c1.metric("Designation", user.get('designation', 'N/A'))
    c2.metric("Department", user.get('department', 'N/A'))
    
    st.subheader("Attendance Log")
    att = db.get_employee_attendance(user['emp_id'])
    if att:
        # Convert dict to DF
        data = []
        for d, inf in att.items():
            inf['Date'] = d
            data.append(inf)
        st.dataframe(pd.DataFrame(data).set_index("Date"))
    else:
        st.info("No attendance records found.")

def ess_requests():
    st.title("My Requests")
    user = st.session_state.user
    
    tab1, tab2 = st.tabs(["New Request", "History"])
    
    with tab1:
        req_type = st.selectbox("Request Type", ["Leave", "Early Exit", "Overtime Claim", "Missed Punch"])
        reason = st.text_area("Reason / Details")
        
        if st.button("Submit Request"):
            db.submit_request(user['emp_id'], req_type, reason)
            st.success("Request submitted successfully.")
            
    with tab2:
        reqs = db.get_employee_requests(user['emp_id'])
        if reqs:
            st.dataframe(pd.DataFrame(reqs))
        else:
            st.info("No request history.")

def ess_support():
    st.title("Help Desk & Support")
    user = st.session_state.user
    
    tab1, tab2 = st.tabs(["Raise Ticket", "My Tickets"])
    
    with tab1:
        st.markdown("Submit a query to HR or IT.")
        cat = st.selectbox("Category", ["Payroll", "Attendance", "IT Support", "Policy", "Other"])
        prio = st.select_slider("Priority", ["Low", "Medium", "High"])
        desc = st.text_area("Description of issue")
        
        if st.button("Create Ticket"):
            db.submit_case(user['emp_id'], cat, prio, desc)
            st.success("Ticket # created.")
            
    with tab2:
        # Filter for this user
        all_cases = db.get_all_cases()
        my_cases = [c for c in all_cases if c['emp_id'] == user['emp_id']]
        if my_cases:
            for c in my_cases:
                st.markdown(f"**{c['case_id']}** ({c['status']}): {c['description']}")
                if c['hr_comments']:
                    st.markdown(f"> HR: {c['hr_comments']}")
                st.divider()
        else:
            st.info("No tickets raised.")
            
    st.markdown("---")
    st.markdown("### External Links")
    st.markdown("[Access Corporate Shared Services Portal](#) (Simulated Link)")

# --- Main App Logic ---

if 'user' not in st.session_state or st.session_state.user is None:
    login_page()
else:
    user = st.session_state.user
    role = user['role']
    
    # Sidebar Navigation
    with st.sidebar:
        st.title("Helix Payroll")
        st.markdown(f"Logged in as **{user['name']}** ({role})")
        
        if role == 'HR':
            nav = st.radio("Navigation", ["Dashboard", "Master Data", "Payroll Engine", "Case Console"])
        else:
            nav = st.radio("Navigation", ["My Profile", "Requests", "Support"])
            
        st.markdown("---")
        if st.button("Logout"):
            logout()
            
    # Routing
    if role == 'HR':
        if nav == "Dashboard":
            hr_dashboard()
        elif nav == "Master Data":
            hr_master_data()
        elif nav == "Payroll Engine":
            hr_payroll_engine()
        elif nav == "Case Console":
            hr_case_console()
            
    elif role == 'Employee':
        if nav == "My Profile":
            ess_dashboard()
        elif nav == "Requests":
            ess_requests()
        elif nav == "Support":
            ess_support()
