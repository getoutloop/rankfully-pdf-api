#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rankfully_report_generator.py  —  V3 Competitor Intelligence PDF
Rankfully.io — GEO + SEO + Competitor Teardown Report

Prepared by Ronnel Besagre | SEO/GEO Strategist

POST /generate-pdf → returns PDF as base64 via app.py
"""

import os
import sys
import json
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, NextPageTemplate
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas as pdfcanvas

# ── Color Palette ─────────────────────────────────────────────
NAVY       = HexColor("#0A1628")
DEEP_BLUE  = HexColor("#0F3460")
STEEL_BLUE = HexColor("#1A5276")
GOLD       = HexColor("#D4AC0D")
GREEN      = HexColor("#1E8449")
RED        = HexColor("#C0392B")
ORANGE     = HexColor("#D35400")
LIGHT_GRAY = HexColor("#F2F3F4")
MID_GRAY   = HexColor("#7F8C8D")
WHITE      = white
TABLE_BLUE = HexColor("#D6EAF8")
LIGHT_PINK = HexColor("#FDEDEC")
LIGHT_GRN  = HexColor("#EAFAF1")
LIGHT_ORG  = HexColor("#FEF9E7")
INDIGO     = HexColor("#6366F1")  # Rankfully brand primary
THREAT_RED = HexColor("#7B241C")

W, H = letter


# ── Score Helpers ─────────────────────────────────────────────
def score_color(score):
    if score >= 75: return GREEN
    if score >= 60: return GOLD
    if score >= 40: return STEEL_BLUE
    return RED

def score_label(score):
    if score >= 75: return "Good"
    if score >= 60: return "Fair"
    if score >= 40: return "Poor"
    return "Critical"

def threat_color(level):
    level = (level or "").upper()
    if level == "HIGH":   return RED
    if level == "MEDIUM": return ORANGE
    return GREEN


# ── Styles ────────────────────────────────────────────────────
def build_styles():
    return {
        "body": ParagraphStyle(
            "body", fontSize=9.5, fontName="Helvetica",
            leading=14, alignment=TA_JUSTIFY, textColor=HexColor("#1A1A2E")
        ),
        "section_note": ParagraphStyle(
            "section_note", fontSize=8.5, fontName="Helvetica",
            leading=12, textColor=MID_GRAY, alignment=TA_LEFT
        ),
        "table_header": ParagraphStyle(
            "table_header", fontSize=9, fontName="Helvetica-Bold",
            textColor=WHITE, alignment=TA_LEFT
        ),
        "table_cell": ParagraphStyle(
            "table_cell", fontSize=8.5, fontName="Helvetica",
            leading=12, textColor=HexColor("#1A1A2E")
        ),
        "impact_title": ParagraphStyle(
            "impact_title", fontSize=9.5, fontName="Helvetica-Bold",
            textColor=NAVY, leading=13
        ),
        "impact_body": ParagraphStyle(
            "impact_body", fontSize=9, fontName="Helvetica",
            leading=13, textColor=HexColor("#2C3E50")
        ),
        "action_item": ParagraphStyle(
            "action_item", fontSize=8.5, fontName="Helvetica",
            leading=12, textColor=HexColor("#1A1A2E"),
            leftIndent=8
        ),
        "bottom_line": ParagraphStyle(
            "bottom_line", fontSize=10.5, fontName="Helvetica-Bold",
            leading=16, textColor=WHITE, alignment=TA_CENTER
        ),
        "bottom_sub": ParagraphStyle(
            "bottom_sub", fontSize=9, fontName="Helvetica",
            leading=13, textColor=HexColor("#BDC3C7"), alignment=TA_CENTER
        ),
        "week_label": ParagraphStyle(
            "week_label", fontSize=9, fontName="Helvetica-Bold",
            textColor=WHITE, alignment=TA_CENTER
        ),
        "week_action": ParagraphStyle(
            "week_action", fontSize=8.5, fontName="Helvetica-Bold",
            textColor=NAVY, leading=12
        ),
        "week_outcome": ParagraphStyle(
            "week_outcome", fontSize=8, fontName="Helvetica",
            leading=12, textColor=HexColor("#2C3E50")
        ),
    }


# ── Section Header ────────────────────────────────────────────
def section_header(title, color=NAVY):
    style = ParagraphStyle("sh", fontSize=11, fontName="Helvetica-Bold", textColor=WHITE)
    data = [[Paragraph(f"<font color='white'><b>{title}</b></font>", style)]]
    t = Table(data, colWidths=[7.5 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), color),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
    ]))
    return t


# ── Score Bar Cell ────────────────────────────────────────────
def score_bar_cell(score):
    bar_color = score_color(score)
    MAX_W = 2.2 * inch
    fill_w  = max(MAX_W * score / 100, 0.05 * inch)
    empty_w = MAX_W - fill_w
    inner = Table([[" ", " "]], colWidths=[fill_w, empty_w])
    inner.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (0, -1), bar_color),
        ("BACKGROUND",    (1, 0), (1, -1), HexColor("#D5D8DC")),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("GRID",          (0, 0), (-1, -1), 0, WHITE),
    ]))
    return inner


def rating_para(score):
    label = score_label(score)
    col = {
        "Good": "#1E8449", "Fair": "#D35400",
        "Poor": "#1A5276", "Critical": "#922B21"
    }.get(label, "#1A5276")
    return Paragraph(
        f'<font color="{col}"><b>{label}</b></font>',
        ParagraphStyle("rat", fontSize=8.5, fontName="Helvetica-Bold",
                       alignment=TA_CENTER, leading=11)
    )


# ── Status Badge ──────────────────────────────────────────────
def status_badge(status_text):
    s = (status_text or "WARNING").upper()
    if s in ("MISSING", "FAIL", "ERROR", "CRITICAL"):
        return Paragraph(
            f'<font color="#C0392B"><b>{s}</b></font>',
            ParagraphStyle("badge", fontSize=8.5, fontName="Helvetica-Bold",
                           backColor=LIGHT_PINK, alignment=TA_CENTER, borderPad=2)
        )
    elif s in ("PASS", "OK", "GOOD"):
        return Paragraph(
            f'<font color="#1E8449"><b>{s}</b></font>',
            ParagraphStyle("badge", fontSize=8.5, fontName="Helvetica-Bold",
                           backColor=LIGHT_GRN, alignment=TA_CENTER, borderPad=2)
        )
    else:
        return Paragraph(
            f'<font color="#D35400"><b>{s}</b></font>',
            ParagraphStyle("badge", fontSize=8.5, fontName="Helvetica-Bold",
                           backColor=LIGHT_ORG, alignment=TA_CENTER, borderPad=2)
        )


# ── Impact Box ────────────────────────────────────────────────
def impact_box(title, body_text, S):
    data = [
        [Paragraph(f"<b>{title}</b>", S["impact_title"])],
        [Paragraph(body_text, S["impact_body"])],
    ]
    t = Table(data, colWidths=[7.0 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), HexColor("#EBF5FB")),
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
        ("TOPPADDING",    (0, 0), (0, 0),   10),
        ("BOTTOMPADDING", (0, 0), (0, 0),   3),
        ("TOPPADDING",    (0, 1), (0, 1),   3),
        ("BOTTOMPADDING", (0, 1), (0, 1),   10),
        ("BOX",           (0, 0), (-1, -1), 0.5, STEEL_BLUE),
        ("LINEBEFORE",    (0, 0), (0, -1),  3, NAVY),
    ]))
    return t


# ── Threat Banner ─────────────────────────────────────────────
def threat_banner(level, lead_loss_pct, competitor_domain, S):
    """Red/orange/green banner showing competitive threat level."""
    tc = threat_color(level)
    level_str = (level or "Unknown").upper()
    loss_str  = f" · ~{lead_loss_pct}% of AI leads going to {competitor_domain}" if lead_loss_pct else ""
    data = [[
        Paragraph(
            f'<font color="white"><b>COMPETITIVE THREAT: {level_str}{loss_str}</b></font>',
            ParagraphStyle("threat", fontSize=10, fontName="Helvetica-Bold",
                           textColor=WHITE, alignment=TA_CENTER)
        )
    ]]
    t = Table(data, colWidths=[7.5 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), tc),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
    ]))
    return t


# ── Page Decorations (Header + Footer on every body page) ─────
def make_page_decorations(report_data):
    domain = report_data.get("domain", report_data.get("url", "rankfully.io"))
    audit_date = report_data.get("audit_date", datetime.now().strftime("%B %Y"))

    def add_page_decorations(canvas_obj, doc):
        canvas_obj.saveState()

        # ── Top header bar ──────────────────────────────────
        canvas_obj.setFillColor(NAVY)
        canvas_obj.rect(0, H - 0.55 * inch, W, 0.55 * inch, fill=1, stroke=0)

        canvas_obj.setFillColor(WHITE)
        canvas_obj.setFont("Helvetica-Bold", 9)
        canvas_obj.drawString(0.5 * inch, H - 0.35 * inch, "COMPETITOR INTELLIGENCE REPORT")
        canvas_obj.setFont("Helvetica", 8)
        canvas_obj.drawRightString(W - 0.5 * inch, H - 0.35 * inch,
                                   f"{domain}  |  {audit_date}")

        # ── Gold accent line ─────────────────────────────────
        canvas_obj.setStrokeColor(GOLD)
        canvas_obj.setLineWidth(2)
        canvas_obj.line(0, H - 0.57 * inch, W, H - 0.57 * inch)

        # ── Bottom footer bar ────────────────────────────────
        canvas_obj.setFillColor(NAVY)
        canvas_obj.rect(0, 0, W, 0.45 * inch, fill=1, stroke=0)

        canvas_obj.setFillColor(WHITE)
        canvas_obj.setFont("Helvetica", 7)
        canvas_obj.drawString(0.5 * inch, 0.16 * inch,
                              "Rankfully.io  |  Competitor Intelligence Report")
        canvas_obj.drawCentredString(W / 2, 0.16 * inch, f"Page {doc.page}")
        canvas_obj.drawRightString(W - 0.5 * inch, 0.16 * inch,
                                   "Prepared by Ronnel Besagre | SEO/GEO Strategist")

        canvas_obj.restoreState()

    return add_page_decorations


# ── Cover Page ────────────────────────────────────────────────
def draw_cover_page(canvas_obj, doc, data):
    geo          = data.get("geo_score", 0)
    seo          = data.get("seo_score", 0)
    comp_geo     = data.get("competitor_geo_score", 0)
    comp_domain  = data.get("competitor_domain", "competitor.com")
    threat_level = data.get("competitive_threat_level", "Unknown")
    lead_loss    = data.get("estimated_ai_lead_loss_pct", 0)
    url          = data.get("url", "your-website.com")
    name         = data.get("name", "")
    audit_date   = data.get("audit_date", datetime.now().strftime("%B %d, %Y"))

    canvas_obj.saveState()

    # Full navy background
    canvas_obj.setFillColor(NAVY)
    canvas_obj.rect(0, 0, W, H, fill=1, stroke=0)

    # Deep-blue diagonal triangle at bottom
    canvas_obj.setFillColor(DEEP_BLUE)
    p = canvas_obj.beginPath()
    p.moveTo(0, 0)
    p.lineTo(W, 0)
    p.lineTo(W, H * 0.28)
    p.lineTo(0, H * 0.38)
    p.close()
    canvas_obj.drawPath(p, fill=1, stroke=0)

    # Rankfully logo text (top-left small)
    canvas_obj.setFillColor(GOLD)
    canvas_obj.setFont("Helvetica-Bold", 10)
    canvas_obj.drawString(0.6 * inch, H - 0.55 * inch, "RANKFULLY.IO")

    # Report Title
    canvas_obj.setFillColor(WHITE)
    canvas_obj.setFont("Helvetica-Bold", 26)
    canvas_obj.drawCentredString(W / 2, H * 0.72, "COMPETITOR INTELLIGENCE REPORT")

    # Subtitle (gold) — the audited URL
    canvas_obj.setFillColor(GOLD)
    canvas_obj.setFont("Helvetica-Bold", 14)
    canvas_obj.drawCentredString(W / 2, H * 0.665, url)

    # Meta line — competitor name
    canvas_obj.setFillColor(MID_GRAY)
    canvas_obj.setFont("Helvetica", 9)
    canvas_obj.drawCentredString(W / 2, H * 0.623,
                                 f"vs. {comp_domain}  |  GEO Score  |  SEO Score  |  Competitor GEO")

    # Gold divider line
    canvas_obj.setStrokeColor(GOLD)
    canvas_obj.setLineWidth(1.5)
    canvas_obj.line(0.75 * inch, H * 0.598, W - 0.75 * inch, H * 0.598)

    # Meta info
    canvas_obj.setFillColor(WHITE)
    canvas_obj.setFont("Helvetica", 8.5)
    canvas_obj.drawCentredString(W / 2, H * 0.565, f"Audit Date: {audit_date}")
    if name:
        canvas_obj.drawCentredString(W / 2, H * 0.543, f"Prepared for: {name}")

    # Score boxes — 3 cards
    scores = [
        ("YOUR GEO SCORE",     geo,      score_label(geo)),
        ("YOUR SEO SCORE",     seo,      score_label(seo)),
        ("COMPETITOR GEO",     comp_geo, score_label(comp_geo)),
    ]

    def box_color(sc):
        if sc >= 75: return HexColor("#1E8449")
        if sc >= 60: return HexColor("#D4AC0D")
        if sc >= 40: return HexColor("#1A5276")
        return HexColor("#922B21")

    box_w   = 1.65 * inch
    box_h   = 0.95 * inch
    box_gap = 0.25 * inch
    total_w = 3 * box_w + 2 * box_gap
    box_x0  = (W - total_w) / 2
    box_y   = H * 0.375

    for i, (label, sc, rating) in enumerate(scores):
        x = box_x0 + i * (box_w + box_gap)
        canvas_obj.setFillColor(box_color(sc))
        canvas_obj.roundRect(x, box_y, box_w, box_h, 6, fill=1, stroke=0)
        canvas_obj.setFillColor(WHITE)
        canvas_obj.setFont("Helvetica", 7)
        canvas_obj.drawCentredString(x + box_w / 2, box_y + box_h - 0.18 * inch, label)
        canvas_obj.setFont("Helvetica-Bold", 22)
        canvas_obj.drawCentredString(x + box_w / 2, box_y + 0.38 * inch, f"{sc}/100")
        canvas_obj.setFont("Helvetica", 8)
        canvas_obj.drawCentredString(x + box_w / 2, box_y + 0.14 * inch, rating)

    # Competitor GEO sub-label
    canvas_obj.setFillColor(MID_GRAY)
    canvas_obj.setFont("Helvetica", 7)
    canvas_obj.drawCentredString(
        box_x0 + 2 * (box_w + box_gap) + box_w / 2,
        box_y - 0.14 * inch,
        comp_domain
    )

    # Threat Level badge
    tc_map = {"HIGH": HexColor("#922B21"), "MEDIUM": HexColor("#D35400"),
               "LOW": HexColor("#1E8449"), "UNKNOWN": HexColor("#1A5276")}
    tc = tc_map.get((threat_level or "").upper(), HexColor("#1A5276"))
    badge_w = 2.5 * inch
    badge_h = 0.3 * inch
    badge_x = (W - badge_w) / 2
    badge_y = box_y - 0.55 * inch
    canvas_obj.setFillColor(tc)
    canvas_obj.roundRect(badge_x, badge_y, badge_w, badge_h, 4, fill=1, stroke=0)
    canvas_obj.setFillColor(WHITE)
    canvas_obj.setFont("Helvetica-Bold", 8)
    loss_str = f"  ·  ~{lead_loss}% leads lost" if lead_loss else ""
    canvas_obj.drawCentredString(W / 2, badge_y + 0.09 * inch,
                                  f"THREAT: {(threat_level or 'Unknown').upper()}{loss_str}")

    # Classification label
    canvas_obj.setFillColor(GOLD)
    canvas_obj.setFont("Helvetica-Bold", 10)
    canvas_obj.drawCentredString(W / 2, H * 0.138, "RANKFULLY COMPETITOR INTELLIGENCE REPORT")

    # Bottom branding
    canvas_obj.setFillColor(MID_GRAY)
    canvas_obj.setFont("Helvetica", 7.5)
    canvas_obj.drawCentredString(W / 2, H * 0.065,
        "Be Found. Be Trusted. Beat Your Competition.  |  rankfully.io")

    # Prepared by
    canvas_obj.setFillColor(MID_GRAY)
    canvas_obj.setFont("Helvetica", 7)
    canvas_obj.drawCentredString(W / 2, H * 0.040,
        "Prepared by Ronnel Besagre | SEO/GEO Strategist")

    canvas_obj.restoreState()


# ── Score Dashboard Table ─────────────────────────────────────
def build_score_dashboard(data, S):
    geo      = data.get("geo_score", 0)
    seo      = data.get("seo_score", 0)
    comp_geo = data.get("competitor_geo_score", 0)
    overall  = round((geo + seo) / 2)

    rows_data = [
        ("Your GEO Score — AI Search Visibility",          geo),
        ("Your SEO Score — Traditional Search",            seo),
        (f"Competitor GEO — {data.get('competitor_domain','competitor.com')}", comp_geo),
        ("OVERALL VISIBILITY SCORE",                       overall),
    ]
    bold_rows = {3}

    header = [
        Paragraph("<b>Category</b>",  S["table_header"]),
        Paragraph("<b>Score</b>",     S["table_header"]),
        Paragraph("<b>Visual</b>",    S["table_header"]),
        Paragraph("<b>Rating</b>",    S["table_header"]),
    ]
    table_data = [header]
    for i, (label, sc) in enumerate(rows_data):
        fn = "Helvetica-Bold" if i in bold_rows else "Helvetica"
        table_data.append([
            Paragraph(f"<b>{label}</b>" if i in bold_rows else label,
                      ParagraphStyle("lbl", fontSize=8.5, fontName=fn, leading=12)),
            Paragraph(f"<b>{sc}/100</b>",
                      ParagraphStyle("sc", fontSize=8.5, fontName="Helvetica-Bold",
                                     alignment=TA_CENTER, leading=12)),
            score_bar_cell(sc),
            rating_para(sc),
        ])

    t = Table(table_data, colWidths=[3.1*inch, 0.75*inch, 2.2*inch, 1.15*inch], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",     (0, 0), (-1, 0),  NAVY),
        ("TEXTCOLOR",      (0, 0), (-1, 0),  WHITE),
        ("FONTNAME",       (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",       (0, 0), (-1, 0),  9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
        # Highlight competitor row
        ("BACKGROUND",     (0, 3), (-1, 3),  LIGHT_PINK),
        ("BACKGROUND",     (0, 4), (-1, 4),  HexColor("#D6EAF8")),
        ("GRID",           (0, 0), (-1, -1), 0.4, HexColor("#D5D8DC")),
        ("TOPPADDING",     (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 6),
        ("LEFTPADDING",    (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",   (0, 0), (-1, -1), 8),
        ("VALIGN",         (0, 0), (-1, -1), "MIDDLE"),
        ("FONTSIZE",       (0, 1), (-1, -1), 8.5),
    ]))
    return t


# ── Competitor Findings Table (Side-by-Side) ──────────────────
def build_competitor_findings_table(findings, S):
    """
    findings: list of {check, your_status, competitor_status, your_finding, competitor_finding}
    Renders a side-by-side comparison table.
    """
    if not findings:
        return Paragraph("No competitor findings available.", S["section_note"])

    header = [
        Paragraph("<b>GEO Check</b>",       S["table_header"]),
        Paragraph("<b>Your Site</b>",        S["table_header"]),
        Paragraph("<b>Competitor</b>",       S["table_header"]),
        Paragraph("<b>Gap &amp; Opportunity</b>", S["table_header"]),
    ]
    rows = [header]
    for f in findings:
        rows.append([
            Paragraph(f.get("check", ""),               S["table_cell"]),
            status_badge(f.get("your_status", "WARNING")),
            status_badge(f.get("competitor_status", "WARNING")),
            Paragraph(f.get("gap", f.get("finding", "")), S["table_cell"]),
        ])
    t = Table(rows, colWidths=[1.6*inch, 1.0*inch, 1.0*inch, 3.9*inch], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",     (0, 0), (-1, 0),  NAVY),
        ("TEXTCOLOR",      (0, 0), (-1, 0),  WHITE),
        ("FONTNAME",       (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",       (0, 0), (-1, 0),  9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
        ("GRID",           (0, 0), (-1, -1), 0.4, HexColor("#D5D8DC")),
        ("TOPPADDING",     (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 5),
        ("LEFTPADDING",    (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",   (0, 0), (-1, -1), 6),
        ("VALIGN",         (0, 0), (-1, -1), "MIDDLE"),
        ("FONTSIZE",       (0, 1), (-1, -1), 8.5),
    ]))
    return t


# ── Competitor Weaknesses List ────────────────────────────────
def build_weaknesses_section(weaknesses, comp_domain, S):
    """3 exploitable gaps as styled bullet boxes."""
    elements = []
    for i, w in enumerate(weaknesses[:3], 1):
        title = w.get("weakness", w.get("title", f"Gap #{i}"))
        exploit = w.get("how_to_exploit", w.get("action", ""))
        data = [
            [Paragraph(f"<b>Gap #{i}: {title}</b>",
                       ParagraphStyle("wt", fontSize=9.5, fontName="Helvetica-Bold", textColor=NAVY))],
            [Paragraph(f"<b>How to exploit it:</b> {exploit}", S["impact_body"])],
        ]
        t = Table(data, colWidths=[7.0 * inch])
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (0, 0),   HexColor("#FDEDEC")),
            ("BACKGROUND",    (0, 1), (0, 1),   HexColor("#FEF9E7")),
            ("LEFTPADDING",   (0, 0), (-1, -1), 12),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
            ("TOPPADDING",    (0, 0), (0, 0),   9),
            ("BOTTOMPADDING", (0, 0), (0, 0),   4),
            ("TOPPADDING",    (0, 1), (0, 1),   4),
            ("BOTTOMPADDING", (0, 1), (0, 1),   9),
            ("BOX",           (0, 0), (-1, -1), 0.5, RED),
            ("LINEBEFORE",    (0, 0), (0, -1),  4, RED),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 6))
    return elements


# ── 3-Week Recovery Plan ──────────────────────────────────────
def build_recovery_plan(recovery_plan, S):
    """
    recovery_plan: {week1: {action, outcome}, week2: {...}, week3: {...}}
    """
    if not recovery_plan:
        return []

    week_colors = [
        ("WEEK 1",  HexColor("#154360")),  # dark navy
        ("WEEK 2",  HexColor("#1A5276")),  # steel blue
        ("WEEK 3",  HexColor("#1E8449")),  # green — final win
    ]
    week_keys = ["week1", "week2", "week3"]

    cells = []
    for (label, color), key in zip(week_colors, week_keys):
        week = recovery_plan.get(key, {})
        action  = week.get("action", "")
        outcome = week.get("outcome", "")
        cell_data = [
            [Paragraph(label, S["week_label"])],
            [Paragraph(f"<b>{action}</b>", S["week_action"])],
            [Paragraph(outcome, S["week_outcome"])],
        ]
        ct = Table(cell_data, colWidths=[2.35 * inch])
        ct.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (0, 0),   color),
            ("BACKGROUND",    (0, 1), (0, 1),   HexColor("#EBF5FB")),
            ("BACKGROUND",    (0, 2), (0, 2),   WHITE),
            ("LEFTPADDING",   (0, 0), (-1, -1), 10),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
            ("TOPPADDING",    (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("BOX",           (0, 0), (-1, -1), 0.5, HexColor("#D5D8DC")),
        ]))
        cells.append(ct)

    row_t = Table([cells], colWidths=[2.35 * inch] * 3,
                  spaceAfter=0, hAlign="LEFT")
    row_t.setStyle(TableStyle([
        ("ALIGN",        (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    return [row_t]


# ── Action Plan Table ─────────────────────────────────────────
def build_action_table(actions, S):
    header = [
        Paragraph("<b>#</b>",          S["table_header"]),
        Paragraph("<b>Priority</b>",   S["table_header"]),
        Paragraph("<b>Action</b>",     S["table_header"]),
        Paragraph("<b>Category</b>",   S["table_header"]),
        Paragraph("<b>Impact</b>",     S["table_header"]),
    ]
    rows = [header]
    for i, a in enumerate(actions[:15], 1):
        priority_text = a.get("priority", "Medium")
        priority_col = {"High": "#C0392B", "Medium": "#D35400", "Low": "#1A5276"}.get(priority_text, "#1A5276")
        rows.append([
            Paragraph(str(i),
                      ParagraphStyle("num", fontSize=8.5, fontName="Helvetica-Bold",
                                     alignment=TA_CENTER, leading=12)),
            Paragraph(f'<font color="{priority_col}"><b>{priority_text}</b></font>',
                      ParagraphStyle("pri", fontSize=8.5, fontName="Helvetica-Bold",
                                     alignment=TA_CENTER, leading=12)),
            Paragraph(a.get("action", ""), S["table_cell"]),
            Paragraph(a.get("category", ""), S["table_cell"]),
            Paragraph(a.get("impact", ""), S["table_cell"]),
        ])
    t = Table(rows, colWidths=[0.3*inch, 0.65*inch, 3.2*inch, 0.9*inch, 2.15*inch], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",     (0, 0), (-1, 0),  NAVY),
        ("TEXTCOLOR",      (0, 0), (-1, 0),  WHITE),
        ("FONTNAME",       (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",       (0, 0), (-1, 0),  9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
        ("GRID",           (0, 0), (-1, -1), 0.4, HexColor("#D5D8DC")),
        ("TOPPADDING",     (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 5),
        ("LEFTPADDING",    (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",   (0, 0), (-1, -1), 6),
        ("VALIGN",         (0, 0), (-1, -1), "TOP"),
        ("FONTSIZE",       (0, 1), (-1, -1), 8.5),
    ]))
    return t


# ── Main Generator ────────────────────────────────────────────
def generate_report(data, output_path):
    S = build_styles()

    geo          = data.get("geo_score", 0)
    seo          = data.get("seo_score", 0)
    comp_geo     = data.get("competitor_geo_score", 0)
    comp_domain  = data.get("competitor_domain", "your-competitor.com")
    threat_level = data.get("competitive_threat_level", "Unknown")
    lead_loss    = data.get("estimated_ai_lead_loss_pct", 0)
    overall      = round((geo + seo) / 2)

    url        = data.get("url", "your-website.com")
    name       = data.get("name", "")
    email      = data.get("email", "")
    report_id  = data.get("report_id", "RF-000")
    audit_date = data.get("audit_date", datetime.now().strftime("%B %d, %Y"))

    geo_findings        = data.get("geo_findings", [])
    seo_findings        = data.get("seo_findings", [])
    competitor_findings = data.get("competitor_findings", [])
    competitor_weaknesses = data.get("competitor_weaknesses", [])
    recovery_plan       = data.get("recovery_plan", {})
    all_findings        = geo_findings + seo_findings

    actions = data.get("action_plan", [])
    exec_summary = data.get("executive_summary", (
        f"This Rankfully Competitor Intelligence Report analysed {url} and its primary AI search "
        f"competitor, {comp_domain}. Your GEO score is {geo}/100 vs your competitor's {comp_geo}/100. "
        f"Your SEO score is {seo}/100. Overall visibility: {overall}/100. "
        f"Competitive threat level: {threat_level}. "
        f"The 3-week recovery plan and competitor blind spots are detailed below."
    ))

    impacts = data.get("impacts", [
        {
            "title": f"GEO Score: {geo}/100 — AI Search Visibility",
            "body": (
                f"Your business scores {geo}/100 for AI search visibility vs {comp_domain}'s {comp_geo}/100. "
                "When potential customers ask ChatGPT, Perplexity, or Google AI Overviews "
                "about services in your category, your competitor currently has the advantage. "
                "The fixes in this report will close that gap within 3 weeks."
            )
        },
        {
            "title": f"SEO Score: {seo}/100 — Traditional Search",
            "body": (
                f"Your business scores {seo}/100 for traditional SEO. "
                "This reflects keyword targeting, meta data, technical health, and content quality "
                "across Google and Bing — where your competitor is also fighting for the same customers."
            )
        },
        {
            "title": f"Competitive Threat: {threat_level} — {lead_loss}% of AI Leads at Risk",
            "body": (
                f"{comp_domain} is currently winning in AI search for your target category. "
                f"An estimated {lead_loss}% of leads that should come to you are going to them instead. "
                "The 3 competitor blind spots in this report are your fastest path to closing that gap."
            )
        },
    ])

    # ── Build the PDF ────────────────────────────────────────
    page_decorations = make_page_decorations(data)

    story = []

    # Section 01: Executive Summary + Threat Banner
    story.append(KeepTogether([
        section_header("01  |  EXECUTIVE SUMMARY"),
        Spacer(1, 8),
        threat_banner(threat_level, lead_loss, comp_domain, S),
        Spacer(1, 10),
        Paragraph(exec_summary, S["body"]),
    ]))
    story.append(Spacer(1, 16))

    # Score callout row
    geo_idx  = min(geo  // 25, 3)
    seo_idx  = min(seo  // 25, 3)
    comp_idx = min(comp_geo // 25, 3)
    score_colors = ["#922B21", "#1A5276", "#D4AC0D", "#1E8449"]

    score_callout_data = [[
        Paragraph(f'<font color="{score_colors[geo_idx]}"><b>GEO: {geo}/100</b></font>',
                  ParagraphStyle("sc2", fontSize=13, fontName="Helvetica-Bold", alignment=TA_CENTER)),
        Paragraph(f'<font color="{score_colors[seo_idx]}"><b>SEO: {seo}/100</b></font>',
                  ParagraphStyle("sc2", fontSize=13, fontName="Helvetica-Bold", alignment=TA_CENTER)),
        Paragraph(f'<font color="{score_colors[comp_idx]}"><b>vs {comp_domain}: {comp_geo}/100</b></font>',
                  ParagraphStyle("sc2", fontSize=11, fontName="Helvetica-Bold", alignment=TA_CENTER)),
    ]]
    score_row_t = Table(score_callout_data, colWidths=[2.5*inch]*3)
    score_row_t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), LIGHT_GRAY),
        ("TOPPADDING",    (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("BOX",           (0, 0), (-1, -1), 0.5, HexColor("#D5D8DC")),
        ("GRID",          (0, 0), (-1, -1), 0.5, HexColor("#D5D8DC")),
    ]))
    story.append(score_row_t)
    story.append(Spacer(1, 20))

    # Section 02: Score Dashboard
    story.append(KeepTogether([
        section_header("02  |  SCORE DASHBOARD"),
        Spacer(1, 8),
        Paragraph(
            f"Your AI visibility vs {comp_domain} across all dimensions. "
            "75+ = Good  |  60-74 = Fair  |  40-59 = Poor  |  0-39 = Critical",
            S["section_note"]
        ),
        Spacer(1, 6),
        build_score_dashboard(data, S),
    ]))
    story.append(Spacer(1, 20))

    # Section 03: Side-by-Side Competitor GEO Comparison
    if competitor_findings:
        story.append(KeepTogether([
            section_header("03  |  COMPETITOR GEO COMPARISON", color=STEEL_BLUE),
            Spacer(1, 8),
            Paragraph(
                f"Side-by-side GEO health check: your site vs {comp_domain}. "
                "Green = advantage. Red = gap to close.",
                S["section_note"]
            ),
            Spacer(1, 6),
            build_competitor_findings_table(competitor_findings, S),
        ]))
        story.append(Spacer(1, 20))

    # Section 04: What We Found (your GEO + SEO findings)
    if all_findings:
        first_rows = all_findings[:5]
        rest_rows  = all_findings[5:]
        hdr_row = [
            Paragraph("<b>Category</b>",  S["table_header"]),
            Paragraph("<b>Check</b>",     S["table_header"]),
            Paragraph("<b>Status</b>",    S["table_header"]),
            Paragraph("<b>Finding</b>",   S["table_header"]),
        ]

        def make_finding_row(f):
            return [
                Paragraph(f.get("category", ""), S["table_cell"]),
                Paragraph(f.get("check", ""),    S["table_cell"]),
                status_badge(f.get("status", "WARNING")),
                Paragraph(f.get("finding", ""),  S["table_cell"]),
            ]

        first_data = [hdr_row] + [make_finding_row(f) for f in first_rows]
        first_t = Table(first_data, colWidths=[1.1*inch,1.4*inch,0.8*inch,4.2*inch], repeatRows=1)
        first_t.setStyle(TableStyle([
            ("BACKGROUND",     (0, 0), (-1, 0),  NAVY),
            ("TEXTCOLOR",      (0, 0), (-1, 0),  WHITE),
            ("FONTNAME",       (0, 0), (-1, 0),  "Helvetica-Bold"),
            ("FONTSIZE",       (0, 0), (-1, 0),  9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
            ("GRID",           (0, 0), (-1, -1), 0.4, HexColor("#D5D8DC")),
            ("TOPPADDING",     (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING",  (0, 0), (-1, -1), 5),
            ("LEFTPADDING",    (0, 0), (-1, -1), 6),
            ("RIGHTPADDING",   (0, 0), (-1, -1), 6),
            ("VALIGN",         (0, 0), (-1, -1), "TOP"),
            ("FONTSIZE",       (0, 1), (-1, -1), 8.5),
        ]))
        story.append(KeepTogether([
            section_header("04  |  YOUR SITE AUDIT FINDINGS"),
            Spacer(1, 8),
            first_t,
        ]))
        if rest_rows:
            rest_data = [hdr_row] + [make_finding_row(f) for f in rest_rows]
            rest_t = Table(rest_data, colWidths=[1.1*inch,1.4*inch,0.8*inch,4.2*inch], repeatRows=1)
            rest_t.setStyle(TableStyle([
                ("BACKGROUND",     (0, 0), (-1, 0),  NAVY),
                ("TEXTCOLOR",      (0, 0), (-1, 0),  WHITE),
                ("FONTNAME",       (0, 0), (-1, 0),  "Helvetica-Bold"),
                ("FONTSIZE",       (0, 0), (-1, 0),  9),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
                ("GRID",           (0, 0), (-1, -1), 0.4, HexColor("#D5D8DC")),
                ("TOPPADDING",     (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING",  (0, 0), (-1, -1), 5),
                ("LEFTPADDING",    (0, 0), (-1, -1), 6),
                ("RIGHTPADDING",   (0, 0), (-1, -1), 6),
                ("VALIGN",         (0, 0), (-1, -1), "TOP"),
                ("FONTSIZE",       (0, 1), (-1, -1), 8.5),
            ]))
            story.append(rest_t)
        story.append(Spacer(1, 20))

    # Section 05: Competitor Blind Spots (3 exploitable weaknesses)
    if competitor_weaknesses:
        weakness_elements = build_weaknesses_section(competitor_weaknesses, comp_domain, S)
        story.append(KeepTogether([
            section_header("05  |  3 COMPETITOR BLIND SPOTS TO EXPLOIT", color=RED),
            Spacer(1, 10),
            Paragraph(
                f"These are confirmed weaknesses in {comp_domain}'s AI search presence. "
                "Act on these before they do.",
                S["section_note"]
            ),
            Spacer(1, 8),
        ]))
        for el in weakness_elements:
            story.append(el)
        story.append(Spacer(1, 20))

    # Section 06: What This Means For You
    if impacts:
        story.append(KeepTogether([
            section_header("06  |  WHAT THIS MEANS FOR YOUR REVENUE"),
            Spacer(1, 10),
            impact_box(impacts[0]["title"], impacts[0]["body"], S),
        ]))
        story.append(Spacer(1, 8))
        for imp in impacts[1:]:
            story.append(KeepTogether([impact_box(imp["title"], imp["body"], S)]))
            story.append(Spacer(1, 8))
        story.append(Spacer(1, 12))

    # Section 07: 3-Week Recovery Plan
    if recovery_plan:
        plan_elements = build_recovery_plan(recovery_plan, S)
        story.append(KeepTogether([
            section_header("07  |  YOUR 3-WEEK RECOVERY BATTLE PLAN", color=GREEN),
            Spacer(1, 8),
            Paragraph(
                "Three focused weeks to close the AI search gap and take leads back from your competitor.",
                S["section_note"]
            ),
            Spacer(1, 8),
        ]))
        for el in plan_elements:
            story.append(el)
        story.append(Spacer(1, 20))

    # Section 08: Priority Action Plan
    if actions:
        story.append(KeepTogether([
            section_header("08  |  30-DAY PRIORITY ACTION PLAN"),
            Spacer(1, 8),
            Paragraph(
                "Prioritised fixes — start with HIGH priority items for fastest competitive gain.",
                S["section_note"]
            ),
            Spacer(1, 6),
            build_action_table(actions[:6], S),
        ]))
        if len(actions) > 6:
            rest_actions = actions[6:]
            story.append(build_action_table(
                [{"priority": "", "action": "", "category": "", "impact": ""}] + rest_actions,
                S
            ))
        story.append(Spacer(1, 20))

    # Section 09: Bottom Line
    bottom_text = data.get("bottom_line", (
        f"Your overall visibility score is {overall}/100 vs {comp_domain}'s GEO score of {comp_geo}/100. "
        f"Every week you wait is another week your competitor captures the AI search leads that should be yours. "
        f"Start Week 1 today."
    ))
    cta_data = [
        [Paragraph(
            f"<b>Your Score: {overall}/100  |  {comp_domain}: {comp_geo}/100 GEO</b>",
            ParagraphStyle("bl_title", fontSize=13, fontName="Helvetica-Bold",
                           textColor=WHITE, alignment=TA_CENTER, leading=18)
        )],
        [Spacer(1, 4)],
        [Paragraph(bottom_text, S["bottom_line"])],
        [Spacer(1, 8)],
        [Paragraph(
            f"Re-audit next month to track your gains.  |  hello@rankfully.io  |  rankfully.io",
            S["bottom_sub"]
        )],
        [Paragraph(
            "Prepared by Ronnel Besagre | SEO/GEO Strategist",
            ParagraphStyle("prep", fontSize=7.5, fontName="Helvetica",
                           textColor=HexColor("#7F8C8D"), alignment=TA_CENTER, leading=11)
        )],
    ]
    cta_t = Table(cta_data, colWidths=[7.5 * inch])
    cta_t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), NAVY),
        ("TOPPADDING",    (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING",   (0, 0), (-1, -1), 20),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 20),
    ]))
    story.append(KeepTogether([
        section_header("09  |  BOTTOM LINE"),
        Spacer(1, 8),
        cta_t,
    ]))

    # ── Build with page templates ────────────────────────────
    from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate

    def on_page(canvas_obj, doc):
        if doc.page == 1:
            draw_cover_page(canvas_obj, doc, data)
        else:
            page_decorations(canvas_obj, doc)

    frame_body = Frame(
        0.65 * inch, 0.70 * inch,
        W - 1.3 * inch, H - 1.55 * inch,
        id="body_frame"
    )

    doc = BaseDocTemplate(
        output_path,
        pagesize=letter,
        pageTemplates=[PageTemplate(id="main", frames=[frame_body], onPage=on_page)],
        title=f"Rankfully Competitor Intelligence — {url}",
        author="Rankfully.io | Prepared by Ronnel Besagre | SEO/GEO Strategist",
    )

    # PageBreak() keeps page 1 empty so cover draws cleanly; story starts on page 2.
    doc.build([PageBreak()] + story)
    return output_path


# ── Entry Point ───────────────────────────────────────────────
if __name__ == "__main__":
    """
    Usage: python rankfully_report_generator.py "path/to/report-data.json"
    """

    data = None

    if len(sys.argv) > 1:
        json_path = sys.argv[1]
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            print(f"ERROR: JSON data file not found: {json_path}", file=sys.stderr)
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"ERROR: Failed to parse JSON file {json_path}: {e}", file=sys.stderr)
            sys.exit(1)

    if data is None:
        raw = os.environ.get("REPORT_DATA", "")
        if not raw:
            print("ERROR: No JSON file path provided and REPORT_DATA env var is empty.", file=sys.stderr)
            sys.exit(1)
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            print(f"ERROR: Failed to parse REPORT_DATA: {e}", file=sys.stderr)
            sys.exit(1)

    report_id  = data.get("report_id", f"RF-{int(datetime.now().timestamp())}")
    output_dir = os.environ.get("REPORT_OUTPUT_DIR",
                                 r"D:\Claude_Code\RonnelBesagre\Project SaaS\reports")
    if len(sys.argv) > 1:
        output_dir = os.path.dirname(sys.argv[1])
    output_path = os.path.join(output_dir, f"{report_id}.pdf")

    os.makedirs(output_dir, exist_ok=True)

    try:
        result = generate_report(data, output_path)
        print(f"SUCCESS:{result}")
    except Exception as e:
        print(f"ERROR: PDF generation failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
