import streamlit as st
import pandas as pd
import datetime
from database import SimulatedDatabase
from utils import PayrollCalculator, generate_payslip_pdf, generate_payslip_html

# --- Configuration & Styles ---
st.set_page_config(page_title="Helix Payroll | Enterprise Portal", layout="wide", page_icon="🏢")

# Initialize Logic
if 'db' not in st.session_state:
    st.session_state.db = SimulatedDatabase()
if 'calc' not in st.session_state:
    st.session_state.calc = PayrollCalculator()

db = st.session_state.db
calc = st.session_state.calc

# --- Custom CSS for Enterprise Aesthetics ---
st.markdown("""
<style>
    /* Import Font */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    /* App Background */
    .stApp {
        background-color: #f0f2f5;
    }
    
    /* Login Box */
    .login-container {
        max-width: 450px;
        margin: 50px auto;
        padding: 50px;
        background: #ffffff;
        border-radius: 16px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.08);
        text-align: center;
        border: 1px solid #e1e4e8;
    }
    
    /* Card Style */
    .css-card {
        background: white;
        padding: 24px;
        border-radius: 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
        border: 1px solid #f0f0f0;
        margin-bottom: 20px;
        transition: transform 0.2s;
    }
    .css-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 16px rgba(0,0,0,0.06);
    }
    
    /* Metrics Override */
    div[data-testid="stMetricValue"] {
        color: #111827;
        font-weight: 700;
        font-size: 28px;
    }
    div[data-testid="stMetricLabel"] {
        color: #6b7280;
        font-weight: 500;
        font-size: 14px;
    }
    
    /* Button Styles */
    div.stButton > button {
        border-radius: 8px;
        height: 42px;
        font-weight: 600;
        border: none;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        transition: all 0.2s;
    }
    div.stButton > button:hover {
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        transform: translateY(-1px);
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e5e7eb;
    }
    
    /* Custom Headers */
    .main-header {
        font-size: 32px;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 8px;
    }
    .sub-header {
        font-size: 16px;
        color: #64748b;
        margin-bottom: 30px;
    }
    
    /* Tables */
    div[data-testid="stDataFrame"] {
        background: white;
        padding: 10px;
        border-radius: 12px;
        border: 1px solid #f1f5f9;
        box-shadow: 0 2px 8px rgba(0,0,0,0.02);
    }
</style>
""", unsafe_allow_html=True)

# --- Helper Components ---
def card(content):
    st.markdown(f'<div class="css-card">{content}</div>', unsafe_allow_html=True)

def header(title, subtitle):
    st.markdown(f'<div class="main-header">{title}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-header">{subtitle}</div>', unsafe_allow_html=True)

# --- Authentication ---
def login_page():
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=60) # Generic Icon
        st.markdown("<h2 style='margin-top:20px; color:#1e293b;'>Helix Secure Portal</h2>", unsafe_allow_html=True)
        st.markdown("<p style='color:#64748b; font-size:14px;'>Enterprise Payroll System</p>", unsafe_allow_html=True)
        
        role = st.selectbox("Select Role", ["HR", "Employee"], label_visibility="collapsed")
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        username = st.text_input("User Email", placeholder="name@company.com")
        password = st.text_input("Password", type="password", placeholder="••••••")
        
        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
        
        if st.button("Sign In →", use_container_width=True, type="primary"):
            user = db.authenticate(username, password, role)
            if user:
                st.session_state.user = user
                st.success("Authenticated successfully.")
                st.rerun()
            else:
                st.error("Invalid credentials.")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Friendly hints
        with st.expander("Demo Credentials"):
            st.markdown("""
            **HR Admin:** `alice@company.com` / `hr`  
            **Employee:** `bob@company.com` / `emp`
            """)

def logout():
    st.session_state.user = None
    st.rerun()

# --- HR Modules ---
def hr_dashboard():
    header("Executive Dashboard", f"Welcome back, {st.session_state.user['name']}")
    
    # Top Metrics
    employees = db.get_all_employees()
    total_ctc = sum(e['ctc'] for e in employees)
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        with st.container(border=True):
            st.metric("Total Headcount", len(employees), delta="Active")
    with c2:
        with st.container(border=True):
            st.metric("Annual CTC Flow", f"₹{total_ctc/1000000:.1f}M")
    with c3:
        cases = db.get_all_cases()
        pending = len([c for c in cases if c['status'] == 'Open'])
        with st.container(border=True):
            st.metric("Pending Action Items", pending, delta=f"{pending} Urgent", delta_color="inverse")
    with c4:
        with st.container(border=True):
            st.metric("Next Payroll", "Oct 30", delta="3 Days")

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Charts Area
    xc1, xc2 = st.columns([2, 1])
    with xc1:
        st.subheader("Department Distribution")
        df_emp = pd.DataFrame(employees)
        dept_counts = df_emp['department'].value_counts()
        st.bar_chart(dept_counts, color="#3b82f6")
        
    with xc2:
        st.subheader("Attendance Heatmap")
        # Simplified mock visualisation
        att_data = {"Present": 85, "Absent": 5, "Leave": 10}
        st.bar_chart(pd.Series(att_data), color="#10b981")

def hr_master_data():
    header("Master Registry", "Manage employee records and attendance.")

    tab1, tab2, tab3 = st.tabs(["👥 Employee Directory", "💰 Compensation Update", "📥 Attendance Import"])

    with tab1:
        employees = db.get_all_employees()
        df = pd.DataFrame(employees)
        if 'password' in df.columns: df = df.drop(columns=['password'])
        
        st.dataframe(
            df.style.background_gradient(subset=['ctc'], cmap="Blues"), 
            use_container_width=True,
            column_config={
                "ctc": st.column_config.NumberColumn("Annual CTC", format="₹%d"),
                "basic": st.column_config.NumberColumn("Basic Pay", format="₹%d"),
                "leave_balance": st.column_config.ProgressColumn("Leave Bal", min_value=0, max_value=30, format="%d days")
            }
        )

    with tab2:
        with st.container(border=True):
            c1, c2 = st.columns(2)
            with c1:
                emp_id_input = st.selectbox("Select Employee", [e['emp_id'] for e in db.get_all_employees()])
                curr_emp = db.get_employee(emp_id_input)
                st.info(f"Current CTC: ₹{curr_emp['ctc']:,}")
            with c2:
                new_ctc = st.number_input("New Annual CTC (INR)", min_value=100000, value=curr_emp['ctc'], step=10000)
            
            if st.button("Apply Structure Update", type="primary"):
                db.update_ctc(emp_id_input, new_ctc)
                st.success("Structure Updated Successfully!")
                
                # Show breakdown
                e = db.get_employee(emp_id_input)
                b1, b2, b3 = st.columns(3)
                b1.metric("Basic", f"₹{e['basic']:,.0f}")
                b2.metric("HRA", f"₹{e['hra']:,.0f}")
                b3.metric("Special", f"₹{e['special']:,.0f}")

    with tab3:
        st.file_uploader("Upload Biometric Log (CSV)", type=["csv"], help="Format: EmpID, Date, Status...")
        st.markdown("### Quick Override")
        with st.form("manual_att"):
            c1, c2, c3 = st.columns(3)
            override_emp = c1.selectbox("Employee", [e['emp_id'] for e in db.get_all_employees()])
            override_status = c2.selectbox("Status", ["Present", "Absent", "Half Day"])
            override_ot = c3.number_input("OT Hours", min_value=0.0)
            if st.form_submit_button("Log Entry"):
                db.add_attendance_log(override_emp, datetime.date.today(), override_status, ot_hours=override_ot)
                st.success("Logged.")

def hr_payroll():
    header("Payroll Engine", "Compute, Review, and Disburse Salaries.")
    
    with st.container(border=True):
        c1, c2, c3 = st.columns([1, 1, 2])
        m = c1.selectbox("Month", ["October", "November", "December"])
        y = c2.number_input("Year", value=2023)
        c3.markdown("##")
        if c3.button("🚀 Run Payroll Batch", type="primary", use_container_width=True):
            # Batch Calc Logic
            results = []
            employees = db.get_all_employees()
            progress = st.progress(0)
            for i, emp in enumerate(employees):
                # Mock attendance fetching
                # In real app, filter for month
                att = db.get_employee_attendance(emp['emp_id'])
                # Flatten the att dict to list
                att_list = []
                for _, log in att.items(): att_list.append(log)
                
                sal = calc.calculate_salary(emp, att_list, m, y)
                results.append(sal)
                progress.progress((i+1)/len(employees))
            
            st.session_state.batch_results = results
            st.success("Batch Completed!")

    if 'batch_results' in st.session_state:
        res = st.session_state.batch_results
        
        # Stats
        total_payout = sum([r['net_salary'] for r in res])
        st.metric("Total Net Payable", f"₹{total_payout:,.2f}")
        
        # Detailed Table
        df_res = pd.DataFrame(res)
        st.dataframe(
            df_res[['emp_id', 'name', 'gross_salary', 'total_deductions', 'net_salary']],
            use_container_width=True,
            column_config={
                "gross_salary": st.column_config.NumberColumn("Gross", format="₹%d"),
                "net_salary": st.column_config.NumberColumn("Net Pay", format="₹%d"), 
            }
        )
        
        st.markdown("### Payslip Preview")
        sel = st.selectbox("Select Employee", [r['emp_id'] for r in res])
        target_rec = next(r for r in res if r['emp_id'] == sel)
        
        # HTML Preview
        html_view = generate_payslip_html(target_rec)
        st.components.v1.html(html_view, height=600, scrolling=True)
        
        # Download
        pdf_data = generate_payslip_pdf(target_rec)
        st.download_button("Download PDF Payslip", pdf_data, file_name=f"Payslip_{sel}.pdf", mime='application/pdf', type="primary")

def hr_cases():
    header("Case Management", "Unified Helpdesk Console")
    
    cases = db.get_all_cases()
    if not cases:
        st.info("No active tickets.")
        return
        
    for case in cases:
        with st.expander(f"{case['priority']} Priority: {case['category']} by {case['emp_id']} ({case['status']})", expanded=(case['status']=='Open')):
            st.markdown(f"**Description:** {case['description']}")
            st.markdown(f"**Date:** {case['date']}")
            
            if case['status'] == 'Open':
                with st.form(f"solve_{case['case_id']}"):
                    ans = st.text_area("Resolution Note")
                    if st.form_submit_button("Mark Resolved"):
                        db.update_case(case['case_id'], "Resolved", ans)
                        st.info("Updating...")
                        st.rerun()
            else:
                st.success(f"Resolved: {case['hr_comments']}")

# --- ESS Modules ---
def ess_home():
    u = st.session_state.user
    header("My Dashboard", f"Hello, {u['name']}")
    
    # Announcements
    anns = db.get_announcements()
    if anns:
        st.info(f"📢 **{anns[0]['title']}**: {anns[0]['message']}")
    
    # Stats
    c1, c2, c3 = st.columns(3)
    with c1:
        with st.container(border=True):
            st.metric("Leave Balance", f"{u.get('leave_balance', 0)} Days")
    with c2:
        with st.container(border=True):
            st.metric("Structure", "Full Time")
    with c3:
        with st.container(border=True):
            st.metric("Next Holiday", "Christmas")
            
    # Attendance History
    st.subheader("My 30-Day Attendance")
    att = db.get_employee_attendance(u['emp_id'])
    if att:
        data = [{"Date": d, **v} for d, v in att.items()]
        st.dataframe(pd.DataFrame(data).set_index("Date"), use_container_width=True)
    else:
        st.info("No logs found.")

def ess_requests():
    header("Services & Requests", "Manage your work life events.")
    
    tab1, tab2 = st.tabs(["New Application", "Track Status"])
    
    with tab1:
        with st.container(border=True):
            req_type = st.selectbox("I want to apply for...", ["Annual Leave", "Sick Leave", "WFH Request", "Missed Punch Correction"])
            dt = st.date_input("For Date")
            reason = st.text_area("Reason")
            
            if st.button("Submit Application", type="primary"):
                db.submit_request(st.session_state.user['emp_id'], req_type, f"{dt}: {reason}")
                st.success("Details forwarded to manager.")
                
    with tab2:
        reqs = db.get_employee_requests(st.session_state.user['emp_id'])
        if reqs:
            st.dataframe(pd.DataFrame(reqs)[['req_id', 'type', 'status', 'date']], use_container_width=True)
        else:
            st.caption("No history.")

def ess_help():
    header("Support Center", "Raise a ticket for HR or IT")
    
    with st.form("ticket"):
        cat = st.selectbox("Category", ["Payroll Issue", "IT Asset", "Policy Query", "Workplace Facility"])
        prio = st.select_slider("Urgency", ["Low", "Medium", "High"])
        desc = st.text_area("Describe the issue")
        if st.form_submit_button("Open Ticket"):
            db.submit_case(st.session_state.user['emp_id'], cat, prio, desc)
            st.success("Ticket Created.")
            
    st.markdown("### My Open Tickets")
    all_c = db.get_all_cases()
    my_c = [c for c in all_c if c['emp_id'] == st.session_state.user['emp_id']]
    for c in my_c:
        st.warning(f"{c['category']}: {c['status']}")

# --- Main Routing ---

if 'user' not in st.session_state or st.session_state.user is None:
    login_page()
else:
    user = st.session_state.user
    
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=40)
        st.markdown(f"**{user['name']}**")
        st.caption(f"{user['role']} | {user['department']}")
        st.markdown("---")
        
        if user['role'] == "HR":
            menu = st.radio("Menu", ["Dashboard", "Master Registry", "Payroll Engine", "Case Console"], label_visibility="collapsed")
        else:
            menu = st.radio("Menu", ["Overview", "My Requests", "Helpdesk"], label_visibility="collapsed")
            
        st.markdown("---")
        if st.button("Logout", use_container_width=True):
            logout()
            
    if user['role'] == "HR":
        if menu == "Dashboard": hr_dashboard()
        elif menu == "Master Registry": hr_master_data()
        elif menu == "Payroll Engine": hr_payroll()
        elif menu == "Case Console": hr_cases()
    else:
        if menu == "Overview": ess_home()
        elif menu == "My Requests": ess_requests()
        elif menu == "Helpdesk": ess_help()
