#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app.py — Rankfully PDF API (Railway Cloud Deployment)
Replaces local rankfully-pdf-api.py for 24/7 cloud operation.

POST /generate-pdf  → returns PDF as base64
GET  /health        → health check
"""

import os
import sys
import json
import base64
import traceback
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)

# Use /tmp for PDF storage on Railway (ephemeral is fine — we return base64)
REPORTS_DIR = "/tmp/rankfully-reports"
os.makedirs(REPORTS_DIR, exist_ok=True)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "rankfully-pdf-api",
        "environment": "railway",
        "time": datetime.now().isoformat()
    })


@app.route("/generate-pdf", methods=["POST"])
def generate_pdf():
    """
    POST body: JSON with all audit report fields
    Returns: { "success": true, "pdf_base64": "...", "filename": "..." }
    """
    try:
        data = request.get_json(force=True)

        # n8n sometimes sends JSON.stringify output — a string instead of a dict.
        # Unwrap it until we have a dict.
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except Exception:
                pass

        if not data or not isinstance(data, dict):
            return jsonify({"success": False, "error": "Empty or invalid request body"}), 400

        report_id  = data.get("report_id", f"RF-{int(datetime.now().timestamp())}")
        output_path = os.path.join(REPORTS_DIR, f"{report_id}.pdf")

        from rankfully_report_generator import generate_report
        generate_report(data, output_path)

        with open(output_path, "rb") as f:
            pdf_bytes = f.read()
        pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")

        # Clean up temp file
        try:
            os.remove(output_path)
        except Exception:
            pass

        return jsonify({
            "success":    True,
            "pdf_base64": pdf_base64,
            "filename":   f"{report_id}.pdf",
            "size_bytes": len(pdf_bytes)
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
