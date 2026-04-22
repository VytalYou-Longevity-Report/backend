import os
from datetime import datetime
from jinja2 import Template

import json

from services.logo_b64 import LOGO_B64


class PDFGenerator:
    """
    Generates the final multi-page VYTALYOU Longevity Report in HTML format.
    Uses marked.js to dynamically parse the LLM's raw markdown output.
    Content is paginated into discrete A4-sized pages on-screen.
    PDF export uses window.print() for native high-quality output.
    """

    def generate_report_html(
        self,
        report: dict,
        physician_sheet: dict,
        risk_projection: dict,
        patient_data: dict,
        derived_metrics: dict,
        session_id: str,
    ) -> str:
        
        # Handle both dicts and Pydantic models gracefully
        if hasattr(report, "markdown"):
            markdown_text = getattr(report, "markdown", "# Report Failed")
        else:
            markdown_text = report.get("markdown", "# Clinical Report Generation Failed")

        # Strip GPT-4 protective formatting blocks if present
        markdown_text = markdown_text.strip()
        if markdown_text.startswith("```"):
            lines = markdown_text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            markdown_text = "\n".join(lines).strip()

        # Properly serialize as a JSON string to completely prevent Javascript evaluation errors
        markdown_js_safe = json.dumps(markdown_text)

        template_str = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VYTALYOU™ Longevity Intelligence Report</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        :root {
            --bg: #ffffff;
            --text: #111827;
            --grey: #4b5563;
            --accent: #B8905B;
            --accent-light: #d4b87a;
            --border: #d1d5db;
        }

        * {
            box-sizing: border-box;
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
        }

        html { scroll-behavior: smooth; }

        body {
            font-family: 'Inter', sans-serif;
            background: #e5e7eb;
            color: var(--text);
            margin: 0;
            padding: 2rem 1rem;
            line-height: 1.65;
        }

        /* ─── Action Bar ─── */
        .action-bar {
            max-width: 21cm;
            margin: 0 auto 1.5rem auto;
            display: flex;
            justify-content: flex-end;
            position: sticky;
            top: 1rem;
            z-index: 100;
        }

        .btn-download {
            background: #111827;
            color: white;
            border: none;
            padding: 14px 30px;
            font-family: 'Inter', sans-serif;
            font-size: 14px;
            font-weight: 600;
            border-radius: 10px;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 10px;
            transition: all 0.3s;
            box-shadow: 0 4px 14px rgba(0,0,0,0.18);
            letter-spacing: 0.3px;
        }
        .btn-download:hover {
            background: var(--accent);
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(184,144,91,0.35);
        }

        /* ─── Loading Overlay ─── */
        #loading-overlay {
            position: fixed;
            inset: 0;
            background: rgba(229,231,235,0.95);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            z-index: 9999;
            gap: 1.5rem;
        }
        .loader-spinner {
            width: 48px;
            height: 48px;
            border: 4px solid #d1d5db;
            border-top-color: var(--accent);
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        .loader-text {
            font-size: 1rem;
            color: var(--grey);
            font-weight: 500;
            letter-spacing: 0.5px;
        }

        /* ─── A4 Page Container ─── */
        .a4-page {
            width: 21cm;
            height: 29.7cm;
            background: var(--bg);
            margin: 0 auto 2.5rem auto;
            padding: 1.4cm 1.8cm;
            box-shadow:
                0 1px 3px rgba(0,0,0,0.06),
                0 4px 12px rgba(0,0,0,0.04),
                0 12px 40px rgba(0,0,0,0.06);
            border-radius: 2px;
            display: flex;
            flex-direction: column;
            position: relative;
            overflow: hidden;
        }

        /* ─── Page Header ─── */
        .page-header-bar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 2px solid var(--accent);
            padding-bottom: 0.7rem;
            margin-bottom: 0.9rem;
            gap: 1rem;
            flex-shrink: 0;
        }
        .page-header-logo {
            height: 38px;
            width: auto;
            object-fit: contain;
        }
        .page-header-text { text-align: right; }
        .page-header-bar .title {
            font-family: 'Playfair Display', serif;
            font-size: 0.68rem;
            font-weight: 700;
            letter-spacing: 2px;
            color: var(--text);
            margin-bottom: 0.1rem;
            text-transform: uppercase;
        }
        .page-header-bar .subtitle {
            font-size: 0.52rem;
            color: var(--grey);
            letter-spacing: 0.7px;
            text-transform: uppercase;
        }

        /* ─── Page Body (fills remaining vertical space) ─── */
        .page-body {
            flex: 1;
            overflow: hidden;
            min-height: 0;
        }

        /* ─── Page Footer ─── */
        .page-footer {
            flex-shrink: 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-top: 1px solid var(--border);
            padding-top: 0.5rem;
            margin-top: 0.7rem;
            font-size: 0.6rem;
            color: var(--grey);
            letter-spacing: 0.3px;
        }

        /* ─── Patient Info ─── */
        .patient-meta {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0.65rem;
            color: var(--text);
            font-size: 0.88rem;
            background: #f9fafb;
            padding: 1rem 1.2rem;
            border-radius: 8px;
            border: 1px solid var(--border);
            margin-bottom: 0.8rem;
        }
        .data-sources {
            font-size: 0.78rem;
            color: var(--grey);
            font-style: italic;
            padding: 0.5rem 0.8rem;
            background: #fefce8;
            border-radius: 6px;
            border: 1px solid #fde68a;
            margin-bottom: 1.2rem;
        }

        /* ─── Markdown Rendered Content ─── */
        .page-body h1 {
            font-family: 'Playfair Display', serif;
            font-size: 1.35rem;
            color: var(--accent);
            margin-top: 1.8rem;
            margin-bottom: 0.9rem;
            border-bottom: 2.5px solid var(--accent);
            padding-bottom: 0.35rem;
            line-height: 1.3;
        }
        .page-body h1:first-child { margin-top: 0.3rem; }

        .page-body h2 {
            font-family: 'Inter', sans-serif;
            font-size: 1.05rem;
            color: var(--text);
            margin-top: 1.4rem;
            margin-bottom: 0.7rem;
            font-weight: 700;
            border-bottom: 1.5px solid var(--border);
            padding-bottom: 0.25rem;
            line-height: 1.3;
        }

        .page-body h3 {
            font-family: 'Inter', sans-serif;
            font-size: 0.9rem;
            color: var(--text);
            margin-top: 1.3rem;
            margin-bottom: 0.5rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.7px;
            line-height: 1.3;
        }

        .page-body p {
            font-size: 0.85rem;
            color: var(--text);
            margin-bottom: 0.7rem;
            line-height: 1.6;
        }

        .page-body ul, .page-body ol {
            color: var(--text);
            padding-left: 1.1rem;
            margin-bottom: 1rem;
            font-size: 0.82rem;
        }

        .page-body li {
            margin-bottom: 0.3rem;
            line-height: 1.5;
            color: #000000 !important;
        }
        .page-body li strong {
            color: #000000 !important;
            font-weight: 600;
        }
        .page-body strong {
            color: var(--accent);
            font-weight: 700;
        }

        .page-body table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 0.6rem;
            margin-bottom: 1.2rem;
            font-size: 0.78rem;
            background: #ffffff;
        }
        .page-body th {
            background-color: #111827;
            color: #ffffff;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            font-size: 0.68rem;
            padding: 7px 9px;
            text-align: left;
            font-weight: 600;
            border: 1px solid #111827;
        }
        .page-body td {
            padding: 6px 9px;
            text-align: left;
            border: 1px solid var(--border);
            color: var(--text);
            vertical-align: top;
        }
        .page-body tr:nth-child(even) td {
            background-color: #f9fafb;
        }

        .page-body blockquote {
            border-left: 4px solid var(--accent);
            background: #fefce8;
            margin: 0.8rem 0;
            padding: 0.7rem 1rem;
            color: #064e3b;
            font-weight: 500;
            border-radius: 0 8px 8px 0;
            font-size: 0.83rem;
        }

        .page-body hr {
            border: none;
            border-top: 1px solid var(--border);
            margin: 1.2rem 0;
        }

        /* ─── Signatures Block ─── */
        .signature-container {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1.5rem;
            text-align: center;
            border-top: 2px solid var(--border);
            padding-top: 1.8rem;
            margin-top: 1.5rem;
        }
        .sig-box {
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .sig-line {
            width: 70%;
            border-bottom: 1px solid var(--text);
            margin-bottom: 0.7rem;
        }
        .sig-label {
            font-size: 0.72rem;
            color: var(--grey);
            font-style: italic;
            margin-bottom: 0.3rem;
        }
        .sig-name {
            font-weight: 700;
            font-size: 0.92rem;
            color: var(--text);
        }
        .sig-title {
            color: var(--grey);
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        /* ─── Disclaimer ─── */
        .disclaimer {
            margin-top: 1.5rem;
            padding: 1.2rem;
            background: #f9fafb;
            border: 1px solid var(--border);
            border-radius: 8px;
            font-size: 0.65rem;
            color: var(--grey);
            line-height: 1.55;
        }
        .disclaimer h4 {
            font-family: 'Inter', sans-serif;
            font-size: 0.72rem;
            color: var(--text);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 0.6rem;
            font-weight: 700;
        }

        /* ─── Print Styles ─── */
        @media print {
            body {
                background: white;
                padding: 0;
                margin: 0;
            }

            .no-print { display: none !important; }
            #loading-overlay { display: none !important; }

            @page {
                size: A4;
                margin: 0;
            }

            .a4-page {
                box-shadow: none !important;
                margin: 0 !important;
                border-radius: 0 !important;
                page-break-after: always;
                break-after: page;
            }

            .a4-page:last-child {
                page-break-after: auto;
                break-after: auto;
            }
        }
    </style>
</head>
<body>
    <!-- Loading overlay -->
    <div id="loading-overlay">
        <div class="loader-spinner"></div>
        <div class="loader-text">Preparing Report Pages…</div>
    </div>

    <!-- Action bar -->
    <div class="action-bar no-print">
        <button class="btn-download" onclick="window.print()">
            <svg width="18" height="18" fill="currentColor" viewBox="0 0 16 16">
                <path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"/>
                <path d="M7.646 11.854a.5.5 0 0 0 .708 0l3-3a.5.5 0 0 0-.708-.708L8.5 10.293V1.5a.5.5 0 0 0-1 0v8.793L5.354 8.146a.5.5 0 1 0-.708.708l3 3z"/>
            </svg>
            Generate High-Res PDF
        </button>
    </div>

    <!-- Hidden logo for JS access -->
    <img id="hidden-logo" style="display:none" src="data:image/png;base64,{{ logo_b64 }}" alt="">

    <!-- Hidden staging area for markdown parsing (offscreen) -->
    <div id="markdown-staging" style="position:absolute;left:-9999px;top:0;width:17cm;visibility:hidden;font-family:'Inter',sans-serif;font-size:0.85rem;line-height:1.6;"></div>

    <!-- Visible paginated pages -->
    <div id="pages-container"></div>

    <!-- JSON data container -->
    <script type="application/json" id="markdown-data">{{ markdown_payload }}</script>

    <script>
        // ─── Resolve Template Data ───
        const LOGO_SRC = document.getElementById('hidden-logo').src;
        const PATIENT_NAME = {{ p_name_json }};
        const PATIENT_AGE  = {{ p_age_json }};
        const PATIENT_GENDER = {{ p_gender_json }};
        const REPORT_DATE  = {{ date_json }};

        // ─── Parse Markdown ───
        const rawMarkdown = JSON.parse(document.getElementById('markdown-data').textContent);

        let preProcessed = rawMarkdown.replace(/^(?!#)(\d{1,2}\.\s+[A-Za-z].*)$/gm, '# $1');
        preProcessed = preProcessed.replace(/^(?!#)(Overall Longevity Status.*)$/gm, '## $1');
        preProcessed = preProcessed.replace(/^(?!#)(Final Longevity (?:Diagnosis|Statement).*)$/gm, '# $1');
        preProcessed = preProcessed.replace(/^(?!#)(Physician Interpretation Sheet.*)$/gm, '# $1');
        preProcessed = preProcessed.replace(/^\s*#\s*VYTALYOU.*REPORT\s*$/gmi, '');

        const staging = document.getElementById('markdown-staging');
        try {
            staging.innerHTML = marked.parse(preProcessed);
        } catch (e) {
            staging.innerHTML = '<p style="color:red">Markdown Error: ' + e.message + '</p>';
        }

        // ─── Wait for fonts then paginate ───
        document.fonts.ready.then(function() {
            requestAnimationFrame(function() {
                paginateContent();
                document.getElementById('loading-overlay').style.display = 'none';
            });
        });

        // ─── Page Creation Helpers ───
        function makePageHeader() {
            var div = document.createElement('div');
            div.className = 'page-header-bar';
            div.innerHTML =
                '<img class="page-header-logo" src="' + LOGO_SRC + '" alt="VytalYou">' +
                '<div class="page-header-text">' +
                    '<div class="title">ULTRA PRECISION LONGEVITY REPORT\u2122</div>' +
                    '<div class="subtitle">Pathology \u00A0/\u00A0 Radiology \u00A0/\u00A0 Cardiac Evaluation \u00A0/\u00A0 Body Composition \u00A0/\u00A0 Genomics</div>' +
                '</div>';
            return div;
        }

        function makePageFooter() {
            var div = document.createElement('div');
            div.className = 'page-footer';
            div.innerHTML =
                '<span>\u00A9 VYTALYOU\u2122 Longevity Intelligence Platform</span>' +
                '<span class="page-num"></span>';
            return div;
        }

        function makePatientInfo() {
            var div = document.createElement('div');
            div.className = 'patient-info-summary';
            div.innerHTML =
                '<div class="patient-meta">' +
                    '<div><strong>Name:</strong> ' + PATIENT_NAME + '<br><br><strong>Age/Sex:</strong> ' + PATIENT_AGE + ' Years / ' + PATIENT_GENDER + '</div>' +
                    '<div><strong>Assessment Date:</strong> ' + REPORT_DATE + '<br><br>\u00A0</div>' +
                '</div>' +
                '<div class="data-sources">[Data Sources: Deep integrated analysis of pathology + InBody + radiology + cardiac data]</div>';
            return div;
        }

        function makeSignatures() {
            var div = document.createElement('div');
            div.className = 'signature-container';
            div.innerHTML =
                '<div class="sig-box">' +
                    '<div class="sig-label">Digitally Signed by</div>' +
                    '<div class="sig-line"></div>' +
                    '<div class="sig-name">Dr. Chirantan Bose MD</div>' +
                    '<div class="sig-title">Longevity Expert / Director</div>' +
                '</div>' +
                '<div class="sig-box">' +
                    '<div class="sig-label">\u00A0</div>' +
                    '<div class="sig-line"></div>' +
                    '<div class="sig-name">Dr. Preetesh Bhandari MD</div>' +
                    '<div class="sig-title">Longevity Expert / Director</div>' +
                '</div>';
            return div;
        }

        function makeDisclaimer() {
            var div = document.createElement('div');
            div.className = 'disclaimer';
            div.innerHTML =
                '<h4>Medical &amp; Clinical Disclaimer</h4>' +
                '<p>This VYTALYOU\u2122 Longevity Intelligence Report is a comprehensive, integrative health assessment based on available laboratory data, imaging findings, body composition analysis, and proprietary longevity algorithms. The report is intended solely for informational, educational, and preventive health guidance purposes.</p>' +
                '<p>This report does not constitute a medical diagnosis, treatment plan, or prescription. Any medical decisions must be made only after consultation with a qualified registered medical practitioner.</p>' +
                '<p>While every effort has been made to ensure accuracy, VYTALYOU\u2122 does not guarantee completeness or absolute precision, as interpretations depend on available data, evolving scientific evidence, and individual variability.</p>' +
                '<p>Advanced therapies mentioned in this report should be undertaken only under appropriate medical supervision and after thorough clinical evaluation.</p>' +
                '<p>VYTALYOU\u2122 shall not be held liable for any direct or indirect consequences arising from the use, interpretation, or application of this report without appropriate medical consultation.</p>' +
                '<p style="text-align:center;margin-top:1rem;font-weight:700;color:#111827;">VYTALYOU\u2122 \u2014 Precision Longevity Medicine</p>';
            return div;
        }

        function createNewPage(container) {
            var page = document.createElement('div');
            page.className = 'a4-page';

            page.appendChild(makePageHeader());

            var body = document.createElement('div');
            body.className = 'page-body';
            page.appendChild(body);

            page.appendChild(makePageFooter());

            container.appendChild(page);
            return body;
        }

        // ─── Core Pagination Engine ───
        function addElementToPages(el, currentBody, container) {
            currentBody.appendChild(el);

            // Check if the element causes overflow
            if (currentBody.scrollHeight > currentBody.clientHeight + 2) {
                currentBody.removeChild(el);

                // Start a new page
                currentBody = createNewPage(container);
                currentBody.appendChild(el);

                // If a single element is taller than one full page,
                // leave it (it will be clipped on screen but print CSS handles it).
            }
            return currentBody;
        }

        function paginateContent() {
            var staging = document.getElementById('markdown-staging');
            var container = document.getElementById('pages-container');

            // Collect all top-level elements from the parsed markdown
            var elements = [];
            while (staging.firstChild) {
                elements.push(staging.removeChild(staging.firstChild));
            }

            // ── First page includes patient info ──
            var currentBody = createNewPage(container);
            currentBody.appendChild(makePatientInfo());

            // ── Flow all markdown elements into pages ──
            for (var i = 0; i < elements.length; i++) {
                var el = elements[i];

                // Skip empty text nodes
                if (el.nodeType === 3 && el.textContent.trim() === '') continue;

                // For non-element nodes (text), wrap in a span
                if (el.nodeType !== 1) {
                    var wrapper = document.createElement('span');
                    wrapper.appendChild(el);
                    el = wrapper;
                }

                currentBody = addElementToPages(el, currentBody, container);
            }

            // ── Add signatures ──
            currentBody = addElementToPages(makeSignatures(), currentBody, container);

            // ── Add disclaimer ──
            currentBody = addElementToPages(makeDisclaimer(), currentBody, container);

            // ── Number all pages ──
            var pages = container.querySelectorAll('.a4-page');
            var total = pages.length;
            for (var j = 0; j < pages.length; j++) {
                pages[j].querySelector('.page-num').textContent = 'Page ' + (j + 1) + ' of ' + total;
            }

            // Clean up staging area
            staging.remove();
        }
    </script>
</body>
</html>
        """

        try:
            # Handle both dicts and Pydantic models
            if hasattr(patient_data, "patient"):
                p_obj = patient_data.patient
                p_name = getattr(p_obj, "name", "Unknown")
                p_gender = getattr(p_obj, "gender", "N/A")
                p_age = getattr(p_obj, "age", "N/A")
            else:
                p_dict = patient_data.get("patient", {})
                p_name = p_dict.get("name", "Unknown")
                p_gender = p_dict.get("gender", "N/A")
                p_age = p_dict.get("age", "N/A")

            template = Template(template_str)
            html = template.render(
                markdown_payload=markdown_js_safe,
                logo_b64=LOGO_B64,
                p_name_json=json.dumps(str(p_name)),
                p_age_json=json.dumps(str(p_age)),
                p_gender_json=json.dumps(str(p_gender)),
                date_json=json.dumps(datetime.now().strftime("%d %B %Y")),
            )
            return html
        except Exception as e:
            return f"<h3>Rendering Error</h3><p>{str(e)}</p>"

# Create singleton instance
pdf_generator = PDFGenerator()
