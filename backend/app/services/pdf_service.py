from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)
from reportlab.lib.enums import TA_JUSTIFY, TA_RIGHT
from datetime import datetime
import io
from html import escape


def generate_incident_report_pdf(report_data: dict) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        title="Vorfallsbericht",
    )
    story = []
    styles = getSampleStyleSheet()

    style_body = ParagraphStyle(
        "BodyTextCustom",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=11,
        leading=15,
        alignment=TA_JUSTIFY,
        spaceAfter=10,
    )
    style_meta_right = ParagraphStyle(
        "MetaRight",
        parent=styles["Normal"],
        alignment=TA_RIGHT,
        fontSize=9,
        textColor=colors.gray,
    )

    annotations = report_data.get("annotations", {})
    incidents = annotations.get("incidents", [])

    def get_val(key):
        val = annotations.get(key, "-")
        if val in [None, "N/A", "", "Unknown"]:
            return "-"
        return str(val)

    case_id = f"Case-No: {datetime.now().strftime('%Y%m%d')}-AUTO"
    report_date = annotations.get("report_date", datetime.now().strftime("%d.%m.%Y"))

    # --- Header ---
    header_table_data = [
        [
            Paragraph("<b>VORFALLSBERICHT</b>", styles["Heading1"]),
            Paragraph(f"{case_id}<br/>Datum: {report_date}", style_meta_right),
        ]
    ]
    header_table = Table(header_table_data, colWidths=[100 * mm, 70 * mm])
    header_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    story.append(header_table)
    story.append(
        HRFlowable(width="100%", thickness=1, color=colors.black, spaceAfter=5 * mm)
    )
    story.append(Spacer(1, 5 * mm))

    # --- Metadata Table ---
    p_date = Paragraph(get_val("date"), styles["Normal"])
    p_time = Paragraph(get_val("time"), styles["Normal"])
    p_place = Paragraph(get_val("place"), styles["Normal"])
    
    accused_list = annotations.get("accused", [])
    accused_str = (
        ", ".join(accused_list)
        if isinstance(accused_list, list) and accused_list
        else str(accused_list) if accused_list else "-"
    )
    p_accused = Paragraph(accused_str, styles["Normal"])

    t = Table(
        [
            ["Vorfallsdatum:", p_date],
            ["Tatzeit:", p_time],
            ["Tatort:", p_place],
            ["Beschuldigte:", p_accused],
        ],
        colWidths=[50 * mm, 120 * mm],
    )
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                ("padding", (0, 0), (-1, -1), 6),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]
        )
    )
    story.append(t)
    story.append(Spacer(1, 10 * mm))

    # --- Report Body ---
    story.append(Paragraph("Sachverhalt / Amtliche Feststellung", styles["Heading3"]))

    text_found = False
    for inc in incidents:
        text_content = inc.get("text", "")
        if not text_content or text_content.strip() == "":
            continue
        text_found = True

        # Text cleaning & rendering
        text_content = text_content.replace("**", "")
        formatted_text = escape(text_content).replace("\n", "<br/>")
        story.append(Paragraph(formatted_text, style_body))
        story.append(Spacer(1, 2 * mm))

    if not text_found:
        story.append(Paragraph("<i>Kein Berichtstext generiert.</i>", style_body))

    # --- Fertigungsvermerk ---
    story.append(Spacer(1, 8 * mm))
    closing_sentence = "Der Sachverhalt wird hiermit gefertigt und zur weiteren Veranlassung vorgelegt."
    story.append(Paragraph(closing_sentence, style_body))

    # --- Signature Section ---
    story.append(Spacer(1, 15 * mm)) 
    
    reporter = annotations.get("reporter", "Beamter")
    
    # table for signatures
    sig_table = Table(
        [
            ["_" * 35, "_" * 35], 
            [f"Meldungsleger: {reporter}", "Dienstführender / Kommandant"],
        ],
        colWidths=[85 * mm, 85 * mm],
    )
    sig_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.black), 
                ("TOPPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(sig_table)

    try:
        doc.build(story)
    except Exception as e:
        print(f"PDF ERROR: {e}")
        return b"PDF Error"
    return buffer.getvalue()