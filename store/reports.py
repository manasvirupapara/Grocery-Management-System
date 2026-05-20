from io import BytesIO
from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from django.db.models import Sum, F, Count
from datetime import datetime
from typing import Optional, List, Tuple
from .models import Order, OrderItem, Category, Product, Invoice
from customers.models import Customer


def _format_money(value):
    try:
        return f"₹{float(value):,.2f}"
    except Exception:
        return f"₹{value}"


def generate_table_report_pdf(
    *,
    company_name: str,
    report_title: str,
    date_range_text: str,
    columns: list,
    rows: list,
    totals: Optional[List[Tuple[str, str]]] = None,
):
    """Generic table PDF generator for admin reports."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=48, leftMargin=48, topMargin=48, bottomMargin=36)

    styles = getSampleStyleSheet()
    elements = []

    title_style = ParagraphStyle(
        'ReportTitle',
        parent=styles['Heading1'],
        fontSize=22,
        textColor=colors.HexColor('#1b5e20'),
        spaceAfter=10,
        alignment=TA_CENTER,
    )
    subtitle_style = ParagraphStyle(
        'ReportSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#374151'),
        spaceAfter=6,
        alignment=TA_CENTER,
    )

    elements.append(Paragraph(company_name, ParagraphStyle(
        'Company',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#2e7d32'),
        alignment=TA_CENTER,
        spaceAfter=6,
    )))
    elements.append(Paragraph(report_title, title_style))
    elements.append(Paragraph(date_range_text, subtitle_style))
    elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", subtitle_style))
    elements.append(Spacer(1, 12))

    table_data = [columns] + rows
    table = Table(table_data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8f5e9')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1b5e20')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(table)

    if totals:
        elements.append(Spacer(1, 12))
        totals_data = [['Total', 'Value']] + [[k, v] for k, v in totals]
        totals_table = Table(totals_data, colWidths=[3.5*inch, 2.0*inch])
        totals_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2e7d32')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#e8f5e9')),
        ]))
        elements.append(totals_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_sales_report_pdf(orders, period, start_date=None, end_date=None):
    """Generate PDF report for sales data"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    elements.append(Paragraph("Sales Report", title_style))
    
    # Period info
    period_text = f"Period: {period}"
    if start_date and end_date:
        period_text += f" ({start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')})"
    elements.append(Paragraph(period_text, styles['Normal']))
    elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Summary statistics
    total_orders = orders.count()
    total_revenue = OrderItem.objects.filter(order__in=orders).aggregate(
        total=Sum(F('quantity') * F('price'))
    )['total'] or 0
    
    success_orders = orders.filter(payment_status='Success').count()
    pending_orders = orders.filter(payment_status='Pending').count()
    cancelled_orders = orders.filter(payment_status='Cancelled').count()
    
    summary_data = [
        ['Metric', 'Value'],
        ['Total Orders', str(total_orders)],
        ['Total Revenue', f'₹{total_revenue:,.2f}'],
        ['Successful Orders', str(success_orders)],
        ['Pending Orders', str(pending_orders)],
        ['Cancelled Orders', str(cancelled_orders)],
    ]
    
    summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(summary_table)
    elements.append(Spacer(1, 30))
    
    # Orders detail table
    elements.append(Paragraph("Order Details", styles['Heading2']))
    elements.append(Spacer(1, 12))
    
    order_data = [['Order ID', 'Customer', 'Date', 'Items', 'Amount', 'Status']]
    
    for order in orders[:50]:  # Limit to 50 orders for PDF
        order_total = order.items.aggregate(total=Sum(F('quantity') * F('price')))['total'] or 0
        order_data.append([
            order.order_id,
            order.customer.name[:20],
            order.order_date.strftime('%Y-%m-%d'),
            str(order.total_items),
            f'₹{order_total:,.2f}',
            order.payment_status
        ])
    
    order_table = Table(order_data, colWidths=[1.2*inch, 1.5*inch, 1*inch, 0.7*inch, 1*inch, 1*inch])
    order_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2ecc71')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    
    elements.append(order_table)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_customer_report_pdf(customers, orders_data):
    """Generate PDF report for customer data"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    elements.append(Paragraph("Customer Report", title_style))
    elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Summary
    total_customers = customers.count()
    male_count = customers.filter(gender='Male').count()
    female_count = customers.filter(gender='Female').count()
    
    summary_data = [
        ['Metric', 'Value'],
        ['Total Customers', str(total_customers)],
        ['Male Customers', str(male_count)],
        ['Female Customers', str(female_count)],
    ]
    
    summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9b59b6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(summary_table)
    elements.append(Spacer(1, 30))
    
    # Customer details
    elements.append(Paragraph("Customer Details", styles['Heading2']))
    elements.append(Spacer(1, 12))
    
    customer_data = [['Name', 'Email', 'Phone', 'Location', 'Orders', 'Total Spent']]
    
    for customer in customers[:40]:
        customer_orders = orders_data.get(customer.id, {'count': 0, 'total': 0})
        customer_data.append([
            customer.name[:20],
            customer.email[:25],
            customer.phone,
            customer.location[:15],
            str(customer_orders['count']),
            f"₹{customer_orders['total']:,.2f}"
        ])
    
    customer_table = Table(customer_data, colWidths=[1.3*inch, 1.5*inch, 1*inch, 1*inch, 0.7*inch, 1*inch])
    customer_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    
    elements.append(customer_table)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_inventory_report_pdf(categories):
    """Generate PDF report for inventory/categories"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    elements.append(Paragraph("Inventory Report", title_style))
    elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Summary
    total_categories = categories.count()
    active_categories = categories.filter(is_active=True).count()
    inactive_categories = categories.filter(is_active=False).count()
    
    summary_data = [
        ['Metric', 'Value'],
        ['Total Categories', str(total_categories)],
        ['Active Categories', str(active_categories)],
        ['Inactive Categories', str(inactive_categories)],
    ]
    
    summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f39c12')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(summary_table)
    elements.append(Spacer(1, 30))
    
    # Category details
    elements.append(Paragraph("Category Details", styles['Heading2']))
    elements.append(Spacer(1, 12))
    
    category_data = [['Category Name', 'Status', 'Has Image']]
    
    for category in categories:
        category_data.append([
            category.name,
            'Active' if category.is_active else 'Inactive',
            'Yes' if category.image else 'No'
        ])
    
    category_table = Table(category_data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
    category_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#16a085')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    elements.append(category_table)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_daily_sales_report_pdf(*, company_name, rows, from_date, to_date, totals):
    return generate_table_report_pdf(
        company_name=company_name,
        report_title="Daily Sales Report",
        date_range_text=f"Date range: {from_date} to {to_date}",
        columns=["Date", "Orders", "Items Sold", "Revenue"],
        rows=rows,
        totals=totals,
    )


def generate_monthly_sales_report_pdf(*, company_name, rows, from_date, to_date, totals):
    return generate_table_report_pdf(
        company_name=company_name,
        report_title="Monthly Sales Report",
        date_range_text=f"Date range: {from_date} to {to_date}",
        columns=["Month", "Orders", "Items Sold", "Revenue"],
        rows=rows,
        totals=totals,
    )


def generate_product_wise_sales_report_pdf(*, company_name, rows, from_date, to_date, totals):
    return generate_table_report_pdf(
        company_name=company_name,
        report_title="Product Wise Sales Report",
        date_range_text=f"Date range: {from_date} to {to_date}",
        columns=["Product", "Qty Sold", "Revenue", "COGS", "Profit"],
        rows=rows,
        totals=totals,
    )


def generate_low_stock_report_pdf(*, company_name, rows, from_date, to_date, totals):
    return generate_table_report_pdf(
        company_name=company_name,
        report_title="Low Stock Report",
        date_range_text=f"Date range: {from_date} to {to_date}",
        columns=["Product", "SKU", "Category", "Stock", "Threshold", "Status"],
        rows=rows,
        totals=totals,
    )


def generate_customer_purchase_report_pdf(*, company_name, rows, from_date, to_date, totals):
    return generate_table_report_pdf(
        company_name=company_name,
        report_title="Customer Purchase Report",
        date_range_text=f"Date range: {from_date} to {to_date}",
        columns=["Customer", "Email", "Orders", "Items", "Total Spent", "Last Purchase"],
        rows=rows,
        totals=totals,
    )


def generate_profit_loss_report_pdf(*, company_name, rows, from_date, to_date, totals):
    return generate_table_report_pdf(
        company_name=company_name,
        report_title="Profit & Loss Report",
        date_range_text=f"Date range: {from_date} to {to_date}",
        columns=["Date", "Revenue", "COGS", "Gross Profit"],
        rows=rows,
        totals=totals,
    )


def generate_invoice_pdf(*, company_name: str, invoice: Invoice):
    """Generate a professional Invoice PDF (A4)."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=48, leftMargin=48, topMargin=40, bottomMargin=36)
    styles = getSampleStyleSheet()
    elements = []

    title_style = ParagraphStyle(
        'InvTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1b5e20'),
        alignment=TA_LEFT,
        spaceAfter=8,
    )
    muted = ParagraphStyle('Muted', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#475569'))

    elements.append(Paragraph(company_name, ParagraphStyle(
        'Company', parent=styles['Heading2'], fontSize=14, textColor=colors.HexColor('#2e7d32'), spaceAfter=4
    )))
    elements.append(Paragraph("INVOICE", title_style))
    elements.append(Paragraph(f"Invoice No: <b>{invoice.invoice_number}</b>", muted))
    elements.append(Paragraph(f"Order ID: <b>{invoice.order.order_id}</b>", muted))
    elements.append(Paragraph(f"Date: <b>{invoice.issue_date.strftime('%Y-%m-%d %H:%M')}</b>", muted))
    elements.append(Spacer(1, 10))

    # Customer block
    elements.append(Paragraph("<b>Bill To</b>", styles['Heading3']))
    elements.append(Paragraph(f"{invoice.customer.name}", styles['Normal']))
    if invoice.customer.email:
        elements.append(Paragraph(f"Email: {invoice.customer.email}", muted))
    if invoice.customer.phone:
        elements.append(Paragraph(f"Phone: {invoice.customer.phone}", muted))
    if invoice.customer.location:
        elements.append(Paragraph(f"Location: {invoice.customer.location}", muted))
    elements.append(Spacer(1, 12))

    # Items table
    data = [["#", "Product", "Qty", "Unit Price", "Total"]]
    for idx, it in enumerate(invoice.items.all(), start=1):
        data.append([
            str(idx),
            it.product_name,
            str(it.quantity),
            f"₹{it.unit_price:,.2f}",
            f"₹{(it.quantity * it.unit_price):,.2f}",
        ])
    t = Table(data, colWidths=[0.4*inch, 3.1*inch, 0.7*inch, 1.2*inch, 1.2*inch], repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8f5e9')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1b5e20')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
        ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 12))

    # Totals table
    totals = [
        ("Subtotal", f"₹{invoice.subtotal:,.2f}"),
        ("Discount", f"- ₹{invoice.discount:,.2f}"),
        (f"{invoice.tax_name or 'GST'} ({invoice.tax_percentage}%)", f"₹{invoice.tax_amount:,.2f}"),
        ("Total", f"₹{invoice.total_amount:,.2f}"),
        ("Payment Status", invoice.payment_status),
        ("Transaction ID", invoice.transaction_id or "-"),
    ]
    tt = Table([["", ""]] + totals, colWidths=[3.5*inch, 2.0*inch])
    tt.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
        ('GRID', (0, 1), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
        ('FONTNAME', (0, 4), (-1, 4), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 4), (-1, 4), colors.HexColor('#e8f5e9')),
        ('TEXTCOLOR', (0, 4), (-1, 4), colors.HexColor('#1b5e20')),
    ]))
    elements.append(tt)

    elements.append(Spacer(1, 14))
    elements.append(Paragraph("Thank you for your purchase.", muted))

    doc.build(elements)
    buffer.seek(0)
    return buffer
