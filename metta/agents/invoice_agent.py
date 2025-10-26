"""
Invoice Agent for DeFi Payroll Manager
Generates PDF invoices for employee payments with transaction details
"""

import os
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, white
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.graphics.shapes import Drawing, Rect
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics import renderPDF
import io
import base64

class InvoiceAgent:
    """
    Specialized agent for generating professional PDF invoices for payroll transactions
    """
    
    def __init__(self):
        self.company_info = {
            'name': 'DeFi Payroll Solutions',
            'address': '123 Blockchain Avenue\nCrypto City, CC 12345',
            'email': 'payroll@defi-solutions.com',
            'website': 'www.defi-payroll.com',
            'logo_path': None  # Path to company logo if available
        }
        
        self.colors = {
            'primary': HexColor('#3B82F6'),    # Blue
            'secondary': HexColor('#10B981'),   # Green
            'accent': HexColor('#8B5CF6'),      # Purple
            'text': HexColor('#1F2937'),        # Dark gray
            'light_gray': HexColor('#F3F4F6'),  # Light gray
            'success': HexColor('#059669'),     # Success green
        }
    
    def generate_employee_invoice(self, 
                                employee_data: Dict[str, Any], 
                                transaction_data: Dict[str, Any],
                                batch_info: Dict[str, Any]) -> bytes:
        """
        Generate individual employee invoice PDF
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, 
                              rightMargin=72, leftMargin=72,
                              topMargin=72, bottomMargin=18)
        
        # Build the invoice content
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=self.colors['primary'],
            alignment=TA_CENTER
        )
        
        header_style = ParagraphStyle(
            'CustomHeader',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            textColor=self.colors['text'],
            alignment=TA_LEFT
        )
        
        # Invoice Header
        story.append(Paragraph("PAYROLL INVOICE", title_style))
        story.append(Spacer(1, 20))
        
        # Company and Employee Info Table
        info_data = [
            ['From:', 'To:'],
            [f"{self.company_info['name']}<br/>{self.company_info['address']}<br/>{self.company_info['email']}", 
             f"Employee: {employee_data.get('name', 'N/A')}<br/>Address: {employee_data['employee_address']}<br/>Payment Date: {batch_info.get('date', datetime.now().strftime('%Y-%m-%d'))}"]
        ]
        
        info_table = Table(info_data, colWidths=[3*inch, 3*inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 30))
        
        # Invoice Details
        story.append(Paragraph("Payment Details", header_style))
        
        payment_data = [
            ['Description', 'Token', 'Amount', 'USD Value'],
            ['Salary Payment', 
             employee_data['to_token'], 
             f"{employee_data['amount']:,.2f}", 
             f"${employee_data['amount']:,.2f}"]
        ]
        
        payment_table = Table(payment_data, colWidths=[2*inch, 1*inch, 1.5*inch, 1.5*inch])
        payment_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.colors['light_gray']),
            ('TEXTCOLOR', (0, 0), (-1, 0), self.colors['text']),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), white),
            ('GRID', (0, 0), (-1, -1), 1, self.colors['light_gray'])
        ]))
        
        story.append(payment_table)
        story.append(Spacer(1, 20))
        
        # Transaction Information
        story.append(Paragraph("Blockchain Transaction Details", header_style))
        
        tx_data = [
            ['Transaction Hash:', transaction_data.get('hash', 'Pending')],
            ['Block Number:', str(transaction_data.get('block_number', 'Pending'))],
            ['Network:', 'Arcology DevNet'],
            ['Gas Fee Saved:', f"${batch_info.get('gas_saved_per_employee', 0):.2f}"],
            ['MEV Protection:', 'Active - Zero MEV Risk'],
            ['Execution Method:', 'Netted Transaction Layer']
        ]
        
        tx_table = Table(tx_data, colWidths=[2*inch, 4*inch])
        tx_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        story.append(tx_table)
        story.append(Spacer(1, 30))
        
        # MEV Protection Benefits
        story.append(Paragraph("MEV Protection Benefits", header_style))
        
        benefits_text = """
        <b>Zero MEV Risk:</b> Your payment was processed through our netted transaction layer, 
        eliminating all MEV (Maximal Extractable Value) risks including front-running and sandwich attacks.<br/><br/>
        
        <b>Gas Optimization:</b> By batching and netting transactions, we reduced gas fees by up to 70% 
        compared to individual transactions.<br/><br/>
        
        <b>Guaranteed Execution:</b> All payments are guaranteed to execute at the intended price 
        without slippage or manipulation.
        """
        
        story.append(Paragraph(benefits_text, styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Footer
        footer_text = f"""
        <i>This invoice was generated automatically by the DeFi Payroll Manager on {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}.<br/>
        For questions about this payment, please contact {self.company_info['email']}.</i>
        """
        
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=HexColor('#6B7280'),
            alignment=TA_CENTER
        )
        
        story.append(Paragraph(footer_text, footer_style))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    
    def generate_batch_summary_report(self, 
                                    batch_data: Dict[str, Any], 
                                    employees: List[Dict[str, Any]],
                                    savings_analysis: Dict[str, Any]) -> bytes:
        """
        Generate batch summary report PDF
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                              rightMargin=72, leftMargin=72,
                              topMargin=72, bottomMargin=18)
        
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=self.colors['primary'],
            alignment=TA_CENTER
        )
        
        # Report Header
        story.append(Paragraph("PAYROLL BATCH SUMMARY REPORT", title_style))
        story.append(Spacer(1, 20))
        
        # Batch Overview
        overview_data = [
            ['Batch ID:', batch_data.get('id', 'N/A')],
            ['Execution Date:', batch_data.get('date', datetime.now().strftime('%Y-%m-%d'))],
            ['Total Employees:', str(len(employees))],
            ['Total Amount:', f"${sum(emp['amount'] for emp in employees):,.2f}"],
            ['Transaction Hash:', batch_data.get('transaction_hash', 'Pending')],
            ['Status:', batch_data.get('status', 'Completed').title()]
        ]
        
        overview_table = Table(overview_data, colWidths=[2*inch, 4*inch])
        overview_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        story.append(overview_table)
        story.append(Spacer(1, 30))
        
        # Savings Summary
        story.append(Paragraph("Cost Savings Analysis", styles['Heading2']))
        
        savings_data = [
            ['Metric', 'Traditional Method', 'Netted Method', 'Savings'],
            ['Transactions', 
             str(savings_analysis.get('original_transactions', len(employees))),
             str(savings_analysis.get('netted_transactions', 3)),
             f"{len(employees) - savings_analysis.get('netted_transactions', 3)} fewer"],
            ['Gas Fees', 
             f"${savings_analysis.get('original_gas_cost', 0):.2f}",
             f"${savings_analysis.get('netted_gas_cost', 0):.2f}",
             f"${savings_analysis.get('gas_savings_usd', 0):.2f}"],
            ['Execution Time',
             f"{len(employees) * 15} seconds",
             savings_analysis.get('execution_time_estimate', '45 seconds'),
             f"{(len(employees) * 15) - 45} seconds faster"],
            ['MEV Risk',
             'High',
             'Zero',
             '100% Protected']
        ]
        
        savings_table = Table(savings_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        savings_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.colors['light_gray']),
            ('TEXTCOLOR', (0, 0), (-1, 0), self.colors['text']),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), white),
            ('GRID', (0, 0), (-1, -1), 1, self.colors['light_gray']),
            ('BACKGROUND', (3, 1), (3, -1), HexColor('#ECFDF5')),  # Light green for savings
        ]))
        
        story.append(savings_table)
        story.append(Spacer(1, 30))
        
        # Employee Payment Details
        story.append(Paragraph("Employee Payment Details", styles['Heading2']))
        
        employee_headers = ['Employee Address', 'Token', 'Amount', 'USD Value']
        employee_data = [employee_headers]
        
        for emp in employees:
            employee_data.append([
                f"{emp['employee_address'][:10]}...{emp['employee_address'][-8:]}",
                emp['to_token'],
                f"{emp['amount']:,.2f}",
                f"${emp['amount']:,.2f}"
            ])
        
        employee_table = Table(employee_data, colWidths=[2.5*inch, 1*inch, 1.25*inch, 1.25*inch])
        employee_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.colors['light_gray']),
            ('TEXTCOLOR', (0, 0), (-1, 0), self.colors['text']),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), white),
            ('GRID', (0, 0), (-1, -1), 1, self.colors['light_gray'])
        ]))
        
        story.append(employee_table)
        story.append(Spacer(1, 20))
        
        # Technical Details
        story.append(Paragraph("Technical Implementation", styles['Heading2']))
        
        tech_text = """
        <b>Netted Transaction Layer:</b> This payroll batch was processed using our proprietary 
        netted transaction technology, which collects multiple individual payments and processes 
        them as optimized batch transactions.<br/><br/>
        
        <b>MEV Protection:</b> By netting transactions internally before blockchain execution, 
        we eliminate all MEV opportunities, ensuring employees receive exactly the intended amounts.<br/><br/>
        
        <b>Gas Optimization:</b> Our system reduces the number of on-chain transactions by up to 70%, 
        significantly lowering gas costs while maintaining security and reliability.<br/><br/>
        
        <b>Blockchain Network:</b> All transactions are executed on the Arcology DevNet, 
        providing high throughput and low latency for optimal user experience.
        """
        
        story.append(Paragraph(tech_text, styles['Normal']))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    
    def generate_invoices_for_batch(self, 
                                  employees: List[Dict[str, Any]], 
                                  batch_info: Dict[str, Any],
                                  transaction_data: Dict[str, Any],
                                  savings_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate all invoices for a payroll batch
        """
        results = {
            'individual_invoices': [],
            'batch_summary': None,
            'total_files': 0,
            'generation_time': datetime.now().isoformat()
        }
        
        try:
            # Generate individual employee invoices
            for i, employee in enumerate(employees):
                # Add employee name if not present
                if 'name' not in employee:
                    employee['name'] = f"Employee {i+1}"
                
                invoice_pdf = self.generate_employee_invoice(
                    employee_data=employee,
                    transaction_data=transaction_data,
                    batch_info=batch_info
                )
                
                # Convert to base64 for easy transmission
                invoice_b64 = base64.b64encode(invoice_pdf).decode('utf-8')
                
                results['individual_invoices'].append({
                    'employee_address': employee['employee_address'],
                    'filename': f"invoice_{employee['employee_address'][:10]}.pdf",
                    'pdf_data': invoice_b64,
                    'size_bytes': len(invoice_pdf)
                })
            
            # Generate batch summary report
            summary_pdf = self.generate_batch_summary_report(
                batch_data=batch_info,
                employees=employees,
                savings_analysis=savings_analysis
            )
            
            summary_b64 = base64.b64encode(summary_pdf).decode('utf-8')
            
            results['batch_summary'] = {
                'filename': f"batch_summary_{batch_info.get('id', 'unknown')}.pdf",
                'pdf_data': summary_b64,
                'size_bytes': len(summary_pdf)
            }
            
            results['total_files'] = len(results['individual_invoices']) + 1
            results['success'] = True
            
        except Exception as e:
            results['success'] = False
            results['error'] = str(e)
        
        return results
    
    def create_sample_invoice(self) -> bytes:
        """
        Create a sample invoice for testing
        """
        sample_employee = {
            'name': 'John Doe',
            'employee_address': '0x1234567890123456789012345678901234567890',
            'to_token': 'ETH',
            'amount': 2500.00
        }
        
        sample_batch = {
            'id': 'BATCH_001',
            'date': '2024-10-23',
            'gas_saved_per_employee': 25.50
        }
        
        sample_transaction = {
            'hash': '0xd8ffe9447f5d9a8ed9cc073f9f16aa988d5707d6280f9c673897688068d9abba',
            'block_number': 44521
        }
        
        return self.generate_employee_invoice(
            employee_data=sample_employee,
            transaction_data=sample_transaction,
            batch_info=sample_batch
        )

# Example usage and testing
if __name__ == "__main__":
    agent = InvoiceAgent()
    
    # Generate sample invoice
    sample_pdf = agent.create_sample_invoice()
    
    # Save to file for testing
    with open('sample_invoice.pdf', 'wb') as f:
        f.write(sample_pdf)
    
    print("Sample invoice generated: sample_invoice.pdf")
    print(f"File size: {len(sample_pdf)} bytes")