import streamlit as st
import datetime
import pandas as pd

class SimulatedDatabase:
    def __init__(self):
        # Initialize session state for data persistence if not already present
        if 'db_employees' not in st.session_state:
            st.session_state.db_employees = [
                {
                    "emp_id": "EMP001", "name": "Alice Johnson", "role": "HR", "email": "alice@company.com", 
                    "password": "hr", "ctc": 1200000, "basic": 600000, "hra": 240000, "special": 360000,
                    "joining_date": "2023-01-01", "department": "Human Resources", "designation": "Sr. Manager",
                    "leave_balance": 18
                },
                {
                    "emp_id": "EMP002", "name": "Bob Smith", "role": "Employee", "email": "bob@company.com", 
                    "password": "emp", "ctc": 800000, "basic": 400000, "hra": 160000, "special": 240000,
                    "joining_date": "2023-03-15", "department": "Engineering", "designation": "Backend Developer",
                    "leave_balance": 12
                },
                {
                    "emp_id": "EMP003", "name": "Charlie Brown", "role": "Employee", "email": "charlie@company.com", 
                    "password": "emp", "ctc": 500000, "basic": 250000, "hra": 100000, "special": 150000,
                    "joining_date": "2023-06-10", "department": "Operations", "designation": "Ops Associate",
                    "leave_balance": 10
                },
                {
                    "emp_id": "EMP004", "name": "Diana Prince", "role": "Employee", "email": "diana@company.com", 
                    "password": "emp", "ctc": 1500000, "basic": 750000, "hra": 300000, "special": 450000,
                    "joining_date": "2022-11-20", "department": "Engineering", "designation": "Tech Lead",
                    "leave_balance": 22
                }
            ]
        
        if 'db_attendance' not in st.session_state:
            st.session_state.db_attendance = {}
            # Seed some data for charts
            self._seed_attendance()
        
        if 'db_payroll_history' not in st.session_state:
            st.session_state.db_payroll_history = []

        if 'db_requests' not in st.session_state:
            # Leave, OT, Early Exit requests
            st.session_state.db_requests = []

        if 'db_cases' not in st.session_state:
            # Support cases
            st.session_state.db_cases = []
            
        if 'db_announcements' not in st.session_state:
            st.session_state.db_announcements = [
                {"date": "2023-10-01", "title": "Diwali Bonus", "message": "All employees will receive their Diwali bonus in the Oct payroll."},
                {"date": "2023-09-15", "title": "New IT Policy", "message": "Please review the updated IT usage policy on the intranet."}
            ]

    def _seed_attendance(self):
        # Helper to pre-fill some simple attendance for visual charts
        # 1 = Present, 0 = Absent for simplicity in seeding
        import random
        today = datetime.date.today()
        # Seed last 7 days
        for emp in st.session_state.db_employees:
            eid = emp['emp_id']
            if eid not in st.session_state.db_attendance:
                st.session_state.db_attendance[eid] = {}
            
            for i in range(7):
                d = today - datetime.timedelta(days=i)
                d_str = d.strftime("%Y-%m-%d")
                status = "Present" if d.weekday() < 5 else "Week Off" # Mon-Fri
                # Randomly absent
                if status == "Present" and random.random() < 0.1:
                    status = "Absent"
                
                st.session_state.db_attendance[eid][d_str] = {
                    "status": status,
                    "check_in": "09:00" if status == "Present" else "",
                    "check_out": "18:00" if status == "Present" else "",
                    "ot_hours": 0
                }

    def get_all_employees(self):
        return st.session_state.db_employees

    def get_employee(self, emp_id):
        for emp in st.session_state.db_employees:
            if emp['emp_id'] == emp_id:
                return emp
        return None

    def authenticate(self, username, password, role):
        for emp in st.session_state.db_employees:
            if emp['email'] == username and emp['password'] == password and emp['role'] == role:
                return emp
        return None

    def update_ctc(self, emp_id, ctc):
        emp = self.get_employee(emp_id)
        if emp:
            basic = ctc * 0.50
            hra = basic * 0.20
            special = ctc - basic - hra
            
            emp['ctc'] = ctc
            emp['basic'] = basic
            emp['hra'] = hra
            emp['special'] = special
            return True
        return False

    def add_attendance_log(self, emp_id, date, status="Present", check_in="09:00", check_out="18:00", ot_hours=0):
        if emp_id not in st.session_state.db_attendance:
            st.session_state.db_attendance[emp_id] = {}
        
        st.session_state.db_attendance[emp_id][date] = {
            "status": status,
            "check_in": check_in,
            "check_out": check_out,
            "ot_hours": ot_hours
        }

    def get_attendance(self, emp_id, date_obj):
        date_str = date_obj.strftime("%Y-%m-%d") if hasattr(date_obj, 'strftime') else str(date_obj)
        if emp_id in st.session_state.db_attendance:
            return st.session_state.db_attendance[emp_id].get(date_str, None)
        return None
    
    def get_employee_attendance(self, emp_id):
        return st.session_state.db_attendance.get(emp_id, {})

    def submit_request(self, emp_id, req_type, details):
        req_id = f"REQ-{len(st.session_state.db_requests) + 1000}"
        st.session_state.db_requests.append({
            "req_id": req_id,
            "emp_id": emp_id,
            "type": req_type,
            "details": details,
            "status": "Pending",
            "date": datetime.date.today().strftime("%Y-%m-%d")
        })
        return req_id

    def get_employee_requests(self, emp_id):
        return [r for r in st.session_state.db_requests if r['emp_id'] == emp_id]

    def get_all_requests(self):
        return st.session_state.db_requests

    def update_request_status(self, req_id, status):
        for req in st.session_state.db_requests:
            if req['req_id'] == req_id:
                req['status'] = status
                # Decrease leave balance if approved
                if status == "Approved":
                    # Find emp and type
                    # For demo purposes we just assume leave subtracts
                    # We'd need to lookup request type and emp_id
                    pass 
                return True
        return False

    def submit_case(self, emp_id, category, priority, description):
        case_id = f"CASE-{len(st.session_state.db_cases) + 1000}"
        st.session_state.db_cases.append({
            "case_id": case_id,
            "emp_id": emp_id,
            "category": category,
            "priority": priority,
            "description": description,
            "status": "Open",
            "hr_comments": "",
            "date": datetime.date.today().strftime("%Y-%m-%d")
        })
        return case_id

    def get_all_cases(self):
        return st.session_state.db_cases

    def update_case(self, case_id, status, comments):
        for case in st.session_state.db_cases:
            if case['case_id'] == case_id:
                case['status'] = status
                case['hr_comments'] = comments
                return True
        return False
    
    def save_payroll_record(self, record):
        st.session_state.db_payroll_history.append(record)

    def get_announcements(self):
        return st.session_state.db_announcements
    
    def add_announcement(self, title, message):
        st.session_state.db_announcements.insert(0, {
            "date": datetime.date.today().strftime("%Y-%m-%d"),
            "title": title,
            "message": message
        })
