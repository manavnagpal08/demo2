import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
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
        
        present_days = 0
        ot_hours = 0
        
        # If demo mode (no records), assume full attendance
        if not attendance_records:
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
            
        pt_deduction = self.PT_DEFAULT if gross_salary > 15000 else 0 
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
            "designation": employee.get('designation', 'Employee'),
            "department": employee.get('department', 'General'),
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

def generate_payslip_html(data):
    """Generates a HTML representation of the payslip for UI preview."""
    
    # Helper to format currency
    fmt = lambda x: f"₹{x:,.2f}"
    
    return f"""
    <div style="font-family: 'Helvetica', sans-serif; max-width: 800px; margin: auto; padding: 20px; border: 1px solid #ddd; background: #fff; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #2c3e50; padding-bottom: 15px; margin-bottom: 20px;">
            <div>
                <h1 style="margin: 0; color: #2c3e50; font-size: 24px;">Helix Corp.</h1>
                <p style="margin: 5px 0 0; color: #7f8c8d; font-size: 14px;">123 Innovation Drive, Tech City</p>
            </div>
            <div style="text-align: right;">
                <h2 style="margin: 0; color: #2980b9;">PAYSLIP</h2>
                <p style="margin: 5px 0 0; color: #7f8c8d;">{data['month']}</p>
            </div>
        </div>

        <div style="display: flex; gap: 40px; margin-bottom: 30px;">
            <div style="flex: 1;">
                <p style="margin: 5px 0;"><strong>Employee ID:</strong> {data['emp_id']}</p>
                <p style="margin: 5px 0;"><strong>Name:</strong> {data['name']}</p>
                <p style="margin: 5px 0;"><strong>Department:</strong> {data.get('department', '')}</p>
            </div>
            <div style="flex: 1;">
                <p style="margin: 5px 0;"><strong>Designation:</strong> {data.get('designation', '')}</p>
                <p style="margin: 5px 0;"><strong>Paid Days:</strong> {data['paid_days']}</p>
                <p style="margin: 5px 0;"><strong>Working Days:</strong> {data['working_days']}</p>
            </div>
        </div>

        <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
            <thead style="background-color: #f2f2f2;">
                <tr>
                    <th style="padding: 12px; text-align: left; border: 1px solid #ddd;">Earnings</th>
                    <th style="padding: 12px; text-align: right; border: 1px solid #ddd;">Amount</th>
                    <th style="padding: 12px; text-align: left; border: 1px solid #ddd;">Deductions</th>
                    <th style="padding: 12px; text-align: right; border: 1px solid #ddd;">Amount</th>
                </tr>
            </thead>
            <tbody>
                {''.join([f"<tr><td style='padding: 8px; border: 1px solid #ddd;'>{k}</td><td style='padding: 8px; text-align: right; border: 1px solid #ddd; color: #27ae60;'>{fmt(v)}</td><td style='padding: 8px; border: 1px solid #ddd;'>{k2 if i < len(data['deductions']) else ''}</td><td style='padding: 8px; text-align: right; border: 1px solid #ddd; color: #c0392b;'>{fmt(v2) if i < len(data['deductions']) else ''}</td></tr>" 
                          for i, ((k, v), (k2, v2)) in enumerate(zip(list(data['earnings'].items()) + [('',0)]*10, list(data['deductions'].items()) + [('',0)]*10)) if k or k2])}
            </tbody>
            <tfoot style="background-color: #ecf0f1; font-weight: bold;">
                <tr>
                    <td style="padding: 12px; border: 1px solid #ddd;">Total Earnings</td>
                    <td style="padding: 12px; text-align: right; border: 1px solid #ddd;">{fmt(data['gross_salary'])}</td>
                    <td style="padding: 12px; border: 1px solid #ddd;">Total Deductions</td>
                    <td style="padding: 12px; text-align: right; border: 1px solid #ddd;">{fmt(data['total_deductions'])}</td>
                </tr>
            </tfoot>
        </table>

        <div style="background-color: #e8f6f3; padding: 20px; text-align: center; border-radius: 8px; border: 1px solid #1abc9c;">
            <h3 style="margin: 0; color: #16a085;">Net Payable: {fmt(data['net_salary'])}</h3>
            <p style="margin: 5px 0 0; font-size: 12px; color: #7f8c8d;">(This is a system generated slip)</p>
        </div>
    </div>
    """

def generate_payslip_pdf(salary_data):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = ParagraphStyle('Header', parent=styles['Heading1'], alignment=TA_CENTER, textColor=colors.HexColor('#2c3e50'))
    sub_style = ParagraphStyle('Sub', parent=styles['Normal'], alignment=TA_CENTER, textColor=colors.grey)
    
    # Header
    elements.append(Paragraph("HELIX CORP", title_style))
    elements.append(Paragraph(f"Payslip for the period of {salary_data['month']}", sub_style))
    elements.append(Spacer(1, 20))
    
    # Employee Details Box
    emp_data = [
        ["Employee ID:", salary_data['emp_id'], "Designation:", salary_data.get('designation', 'N/A')],
        ["Name:", salary_data['name'], "Department:", salary_data.get('department', 'N/A')],
        ["Paid Days:", str(salary_data['paid_days']), "Working Days:", str(salary_data['working_days'])]
    ]
    
    t_emp = Table(emp_data, colWidths=[100, 150, 100, 150])
    t_emp.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('TEXTCOLOR', (0,0), (0,-1), colors.grey), # Labels
        ('TEXTCOLOR', (2,0), (2,-1), colors.grey), # Labels
        ('TEXTCOLOR', (1,0), (1,-1), colors.black), # Values
        ('TEXTCOLOR', (3,0), (3,-1), colors.black), # Values
        ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(t_emp)
    elements.append(Spacer(1, 20))
    
    # Earnings & Deductions Table
    data = [["EARNINGS", "AMOUNT (INR)", "DEDUCTIONS", "AMOUNT (INR)"]]
    
    earnings = salary_data['earnings']
    deductions = salary_data['deductions']
    
    earning_keys = list(earnings.keys())
    deduction_keys = list(deductions.keys())
    max_rows = max(len(earning_keys), len(deduction_keys))
    
    for i in range(max_rows):
        e_key = earning_keys[i] if i < len(earning_keys) else ""
        e_val = f"{earnings[e_key]:,.2f}" if i < len(earning_keys) else ""
        
        d_key = deduction_keys[i] if i < len(deduction_keys) else ""
        d_val = f"{deductions[d_key]:,.2f}" if i < len(deduction_keys) else ""
        
        data.append([e_key, e_val, d_key, d_val])
        
    data.append(["Total Earnings", f"{salary_data['gross_salary']:,.2f}", "Total Deductions", f"{salary_data['total_deductions']:,.2f}"])
    
    t = Table(data, colWidths=[160, 90, 160, 90])
    
    # Styling
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('ALIGN', (1,0), (1,-1), 'RIGHT'), # Amount cols
        ('ALIGN', (3,0), (3,-1), 'RIGHT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 10),
        ('TOPPADDING', (0,0), (-1,0), 10),
        
        ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'), # Totals row
        ('LINEABOVE', (0,-1), (-1,-1), 1, colors.black),
        
        # Grid
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 30))
    
    # Net Pay Box
    net_text = f"Net Salary Payable: INR {salary_data['net_salary']:,.2f}"
    p_net = Paragraph(net_text, ParagraphStyle('NetPay', parent=styles['Heading3'], alignment=TA_CENTER, textColor=colors.HexColor('#27ae60'), fontSize=14))
    elements.append(p_net)
    
    elements.append(Spacer(1, 40))
    elements.append(Paragraph("Authorized Signatory", ParagraphStyle('Sign', parent=styles['Normal'], alignment=TA_RIGHT)))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer
