from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_JUSTIFY, TA_RIGHT
from datetime import datetime
import io
from html import escape

def generate_police_report_pdf(report_data: dict) -> bytes:
    """
    Generates a formatted PDF report. Handles text wrapping and basic sanitation.
    """
    buffer = io.BytesIO()
    
    # Setup document with standard margins
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4,
        rightMargin=20*mm, leftMargin=20*mm, 
        topMargin=20*mm, bottomMargin=20*mm,
        title="PolizeiBericht"
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    # --- Custom Styles ---
    style_body = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=11,
        leading=15, 
        alignment=TA_JUSTIFY,
        spaceAfter=10
    )

    style_meta_right = ParagraphStyle(
        'MetaRight',
        parent=styles['Normal'],
        alignment=TA_RIGHT,
        fontSize=9,
        textColor=colors.gray
    )

    # --- Prepare Data ---
    annotations = report_data.get("annotations", {})
    incidents = annotations.get("incidents", [])
    
    def get_val(key):
        val = annotations.get(key, '-')
        if val in [None, "N/A", "", "Unknown"]: return "-"
        return str(val)

    # Timestamp
    case_id = f"Case-No: {datetime.now().strftime('%Y%m%d')}-AUTO"

    # -----------------------------------------------------------
    # Datum aus den extrahierten Daten holen
    # -----------------------------------------------------------
    # Wir schauen, ob 'report_date' in den Annotations steht
    # Wenn nicht, nehmen wir das heutige Datum

    report_date = annotations.get("report_date", datetime.now().strftime('%d.%m.%Y'))

    # --- Header Section ---
    header_table_data = [
        [
            Paragraph("<b>POLIZEIBERICHT / PROTOKOLL</b>", styles['Heading1']), 
            Paragraph(f"{case_id}<br/>Datum: {report_date}", style_meta_right)
        ]
    ]
    
    header_table = Table(header_table_data, colWidths=[100*mm, 70*mm])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(header_table)
    
    # Horizontal line 
    story.append(HRFlowable(width="100%", thickness=1, color=colors.black, spaceAfter=5*mm))
    story.append(Spacer(1, 5*mm))
    
    # --- Metadata Table ---
    
    # Use Paragraphs inside table cells to enable text wrapping
    p_date = Paragraph(get_val('date'), styles['Normal'])
    p_time = Paragraph(get_val('time'), styles['Normal'])
    p_place = Paragraph(get_val('place'), styles['Normal'])
    
    # Format accused list
    accused_list = annotations.get('accused', [])
    if isinstance(accused_list, list):
        accused_str = ", ".join(accused_list) if accused_list else "-"
    else:
        accused_str = str(accused_list) if accused_list else "-"
    p_accused = Paragraph(accused_str, styles['Normal'])

    table_data = [
        ["Vorfallsdatum:", p_date],
        ["Tatzeit:", p_time],
        ["Tatort:", p_place],
        ["Beschuldigte / Beteiligte:", p_accused]
    ]
    
    # Create Table 
    t = Table(table_data, colWidths=[50*mm, 120*mm])
    
    # Styling
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.whitesmoke),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('padding', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    
    story.append(t)
    story.append(Spacer(1, 10*mm))
    
    # --- Report Body ---
    story.append(Paragraph("Sachverhalt / Amtliche Feststellung", styles['Heading3']))
    
    # Extract text from incidents structure
    body_text = ""
    for inc in incidents:
        if inc.get("structure") == "Incident":
            val = inc.get("text", "")
            if val: 
                body_text = val
            break
            
    if body_text:
        # Sanitize
        body_text = body_text.replace("**", "") 
        
        # HTML Escape and format newlines
        safe_text = escape(body_text)
        formatted_text = safe_text.replace("\n", "<br/>")
        story.append(Paragraph(formatted_text, style_body))
    else:
        story.append(Paragraph("<i>Kein Berichtstext generiert.</i>", style_body))

    story.append(Spacer(1, 20*mm))
    
    # --- Signature Section ---
    signature_table_data = [
        ["_" * 30, "_" * 30],
        ["Unterschrift Beamter", "Unterschrift Dienstgruppenleiter"]
    ]
    
    sig_table = Table(signature_table_data, colWidths=[85*mm, 85*mm])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.gray),
        ('TOPPADDING', (0,0), (-1,-1), 2),
    ]))
    
    story.append(sig_table)
    
    try:
        doc.build(story)
    except Exception as e:
        print(f"PDF BUILD ERROR: {e}")
        return b"PDF Error"

    return buffer.getvalue()