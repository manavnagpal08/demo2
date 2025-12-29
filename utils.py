import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
import datetime

class PayrollCalculator:
    def __init__(self):
        self.PF_RATE = 0.12
        self.ESI_RATE = 0.0075
        self.ESI_LIMIT = 21000
        self.PT_DEFAULT = 200
        self.LWF_DEFAULT = 25

    def calculate_salary(self, employee, attendance_records, month, year, working_days=30):
        # attendance_records: list of dicts for this month
        
        # Calculate Paid Days
        # For simulation, we'll assume 'Present' = 1, 'Half Day' = 0.5, 'Absent' = 0
        present_days = 0
        ot_hours = 0
        
        # Default to full presence if no records (for demo smoothness if data missing)
        # But if records exist, use them.
        if not attendance_records:
            # If no data, assume full presence for demo purposes unless specifically 0
            paid_days = working_days 
        else:
            for day_log in attendance_records:
                status = day_log.get('status', 'Absent')
                if status == 'Present':
                    present_days += 1
                elif status == 'Half Day':
                    present_days += 0.5
                
                ot_hours += float(day_log.get('ot_hours', 0))
            paid_days = present_days

        # Prorate factors
        prorate_factor = paid_days / working_days if working_days > 0 else 0
        
        # Earnings
        basic_earned = employee['basic'] / 12 * prorate_factor
        hra_earned = employee['hra'] / 12 * prorate_factor
        special_earned = employee['special'] / 12 * prorate_factor
        
        # OT Calculation (Assume flat rate 500/hr for demo)
        ot_amount = ot_hours * 500 
        
        gross_salary = basic_earned + hra_earned + special_earned + ot_amount
        
        # Deductions
        pf_deduction = basic_earned * self.PF_RATE
        
        esi_deduction = 0
        if gross_salary < self.ESI_LIMIT:
            esi_deduction = gross_salary * self.ESI_RATE
            
        pt_deduction = self.PT_DEFAULT if gross_salary > 15000 else 0 # Simplified PT
        lwf_deduction = self.LWF_DEFAULT
        
        # Mock TDS (10% if gross > 50000)
        tds_deduction = 0
        if gross_salary > 50000:
            tds_deduction = (gross_salary - 50000) * 0.10
            
        total_deductions = pf_deduction + esi_deduction + pt_deduction + lwf_deduction + tds_deduction
        
        net_salary = gross_salary - total_deductions
        
        return {
            "emp_id": employee['emp_id'],
            "name": employee['name'],
            "month": f"{month}-{year}",
            "paid_days": paid_days,
            "working_days": working_days,
            "earnings": {
                "Basic Salary": round(basic_earned, 2),
                "HRA": round(hra_earned, 2),
                "Special Allowance": round(special_earned, 2),
                "Overtime Pay": round(ot_amount, 2)
            },
            "deductions": {
                "PF": round(pf_deduction, 2),
                "ESI": round(esi_deduction, 2),
                "Professional Tax": round(pt_deduction, 2),
                "LWF": round(lwf_deduction, 2),
                "TDS": round(tds_deduction, 2)
            },
            "gross_salary": round(gross_salary, 2),
            "total_deductions": round(total_deductions, 2),
            "net_salary": round(net_salary, 2)
        }

def generate_payslip_pdf(salary_data):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Header
    elements.append(Paragraph(f"<b>Payslip for {salary_data['month']}</b>", styles['Title']))
    elements.append(Spacer(1, 12))
    
    # Employee Details
    emp_data = [
        ["Employee ID:", salary_data['emp_id'], "Name:", salary_data['name']],
        ["Designation:", "N/A", "Department:", "N/A"], # Could pass these in if needed
        ["Paid Days:", str(salary_data['paid_days']), "Working Days:", str(salary_data['working_days'])]
    ]
    t_emp = Table(emp_data, colWidths=[100, 150, 100, 150])
    t_emp.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(t_emp)
    elements.append(Spacer(1, 20))
    
    # Earnings & Deductions Table
    data = [["Earnings", "Amount (INR)", "Deductions", "Amount (INR)"]]
    
    earnings = salary_data['earnings']
    deductions = salary_data['deductions']
    
    # Pad lists to be same length
    earning_keys = list(earnings.keys())
    deduction_keys = list(deductions.keys())
    max_rows = max(len(earning_keys), len(deduction_keys))
    
    for i in range(max_rows):
        e_key = earning_keys[i] if i < len(earning_keys) else ""
        e_val = f"{earnings[e_key]:,.2f}" if i < len(earning_keys) else ""
        
        d_key = deduction_keys[i] if i < len(deduction_keys) else ""
        d_val = f"{deductions[d_key]:,.2f}" if i < len(deduction_keys) else ""
        
        data.append([e_key, e_val, d_key, d_val])
        
    data.append(["", "", "", ""])
    data.append(["Total Earnings", f"{salary_data['gross_salary']:,.2f}", "Total Deductions", f"{salary_data['total_deductions']:,.2f}"])
    
    t = Table(data, colWidths=[150, 100, 150, 100])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND', (0,-1), (-1,-1), colors.lightgrey),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 20))
    
    # Net Pay
    elements.append(Paragraph(f"<b>Net Salary Payable: INR {salary_data['net_salary']:,.2f}</b>", styles['Heading2']))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer

