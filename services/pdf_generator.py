import os
from datetime import datetime
from jinja2 import Template

import json

LOGO_B64 = "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"

class PDFGenerator:
    """
    Generates the final multi-page VYTALYOU Longevity Report in HTML format.
    Uses marked.js to dynamically parse the LLM's raw markdown output, styled
    extremely precisely to look like a high-end Med-Tech PDF report.
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

        template_str = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>VYTALYOU™ Longevity Intelligence Report</title>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400&display=swap" rel="stylesheet">
            <!-- Include marked.js for Markdown parsing -->
            <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
            <style>
                :root {
                    --bg: #ffffff;
                    --text: #111827;
                    --grey: #4b5563;
                    --accent: #B8905B; /* Gold */
                    --accent-light: #d4b87a;
                    --border: #d1d5db;
                    --red: #b91c1c;
                    --green: #047857;
                    --orange: #d97706;
                }

                @media print {
                    .no-print { display: none !important; }
                    body { font-size: 10pt; background: white; margin: 0; padding: 0; }
                    .document { 
                        box-shadow: none !important; 
                        margin: 0 !important; 
                        padding: 0 !important; /* Managed by @page margins */
                        max-width: 100% !important; 
                        border: none !important;
                    }
                    h1, h2, h3 { page-break-after: avoid; }
                    table { page-break-inside: avoid; border-collapse: collapse; }
                    p { page-break-inside: avoid; }
                    
                    /* Repeating page header bar */
                    .page-header-bar { 
                        position: fixed;
                        top: 0;
                        left: 0;
                        right: 0;
                        background: white;
                        margin-bottom: 0;
                        padding-top: 15mm; /* Extra space from top of physical page */
                        z-index: 1000;
                    }
                    
                    #markdown-content {
                        margin-top: 45mm; /* Space to clear the fixed header on NEW pages */
                    }

                    .signature-container { page-break-inside: avoid; }
                    .disclaimer { page-break-inside: avoid; }
                    
                    /* Force A4 Size with 4-side margins */
                    @page {
                        size: A4;
                        margin: 20mm;
                    }
                }

                * { 
                    box-sizing: border-box; 
                    -webkit-print-color-adjust: exact !important;
                    print-color-adjust: exact !important;
                }

                body {
                    font-family: 'Inter', sans-serif;
                    background: #f3f4f6;
                    color: var(--text);
                    margin: 0;
                    padding: 2rem;
                    line-height: 1.7;
                }
                
                .action-bar {
                    max-width: 21cm;
                    margin: 0 auto 3rem auto; /* Increased margin from button */
                    display: flex;
                    justify-content: flex-end;
                }
                
                .btn-download {
                    background: #111827;
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    font-family: 'Inter', sans-serif;
                    font-size: 14px;
                    font-weight: 500;
                    border-radius: 8px;
                    cursor: pointer;
                    display: inline-flex;
                    align-items: center;
                    gap: 8px;
                    transition: background 0.2s;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                }
                .btn-download:hover { background: var(--accent); }

                /* PDF Document Wrapper representing an A4 page */
                .document {
                    background: var(--bg);
                    width: 21cm; /* Exact A4 Width */
                    min-height: 29.7cm; /* Exact A4 Height */
                    margin: 0 auto;
                    padding: 3rem 4rem;
                    box-shadow: 0 20px 40px rgba(0,0,0,0.08);
                    border-radius: 4px;
                    border: 1px solid #e5e7eb;
                    position: relative;
                }

                /* Repeating page header bar */
                .page-header-bar {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    border-bottom: 2px solid var(--accent);
                    padding-bottom: 1rem;
                    margin-bottom: 2rem;
                    gap: 1.5rem;
                }

                .page-header-logo {
                    height: 45px;
                    width: auto;
                    object-fit: contain;
                }

                .page-header-text {
                    text-align: right;
                }

                .page-header-bar .title {
                    font-family: 'Playfair Display', serif;
                    font-size: 0.8rem;
                    font-weight: 700;
                    letter-spacing: 2px;
                    color: var(--text);
                    margin-bottom: 0.2rem;
                    text-transform: uppercase;
                }

                .page-header-bar .subtitle {
                    font-size: 0.65rem;
                    color: var(--grey);
                    letter-spacing: 1px;
                    text-transform: uppercase;
                }

                .header {
                    border-bottom: 3px solid var(--accent);
                    padding-bottom: 1.5rem;
                    margin-bottom: 2.5rem;
                }

                .header-title {
                    font-family: 'Playfair Display', serif;
                    font-size: 2.2rem;
                    color: #111827;
                    letter-spacing: -0.5px;
                    margin-bottom: 0.3rem;
                }

                .header-subtitle {
                    font-family: 'Inter', sans-serif;
                    font-size: 0.9rem;
                    color: var(--grey);
                    font-weight: 400;
                    letter-spacing: 0.5px;
                    font-style: italic;
                }

                .patient-meta {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 1rem;
                    color: var(--text);
                    font-size: 1rem;
                    margin-top: 1rem;
                    background: #f9fafb;
                    padding: 1.5rem;
                    border-radius: 8px;
                    border: 1px solid var(--border);
                }

                .data-sources {
                    font-size: 0.85rem;
                    color: var(--grey);
                    font-style: italic;
                    margin-top: 1rem;
                    padding: 0.75rem 1rem;
                    background: #fefce8;
                    border-radius: 6px;
                    border: 1px solid #fde68a;
                }

                /* Markdown Content Overrides */
                #markdown-content h1 {
                    font-family: 'Playfair Display', serif;
                    font-size: 1.6rem;
                    color: var(--accent);
                    margin-top: 3rem;
                    margin-bottom: 1.2rem;
                    border-bottom: 2.5px solid var(--accent);
                    padding-bottom: 0.5rem;
                }

                #markdown-content h2 {
                    font-family: 'Inter', sans-serif;
                    font-size: 1.2rem;
                    color: var(--text);
                    margin-top: 1.8rem;
                    margin-bottom: 1rem;
                    font-weight: 700;
                    border-bottom: 1.5px solid var(--border);
                    padding-bottom: 0.4rem;
                }

                #markdown-content h3 {
                    font-family: 'Inter', sans-serif;
                    font-size: 1rem;
                    color: var(--text);
                    margin-top: 1.8rem;
                    margin-bottom: 0.8rem;
                    font-weight: 600;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                }

                #markdown-content p {
                    font-size: 0.95rem;
                    color: var(--text);
                    margin-bottom: 1rem;
                    line-height: 1.7;
                }

                /* Specific Request: bullets with small black texts */
                #markdown-content ul, #markdown-content ol {
                    color: var(--text);
                    padding-left: 1.2rem;
                    margin-bottom: 1.5rem;
                    font-size: 0.9rem; /* Small black text */
                }

                #markdown-content li {
                    margin-bottom: 0.45rem;
                    line-height: 1.6;
                    color: #000000 !important; /* Force Black */
                }

                #markdown-content li strong {
                    color: #000000 !important;
                    font-weight: 600;
                }

                #markdown-content strong {
                    color: var(--accent);
                    font-weight: 700;
                }

                #markdown-content table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 1rem;
                    margin-bottom: 2rem;
                    font-size: 0.9rem;
                    background: #ffffff;
                }

                #markdown-content th {
                    background-color: #111827;
                    color: #ffffff;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                    font-size: 0.75rem;
                    padding: 10px 12px;
                    text-align: left;
                    font-weight: 600;
                    border: 1px solid #111827;
                }

                #markdown-content td {
                    padding: 9px 12px;
                    text-align: left;
                    border: 1px solid var(--border);
                    color: var(--text);
                    vertical-align: top;
                }

                #markdown-content tr:nth-child(even) td {
                    background-color: #f9fafb;
                }

                #markdown-content blockquote {
                    border-left: 4px solid var(--accent);
                    background: #fefce8;
                    margin: 1.5rem 0;
                    padding: 1rem 1.5rem;
                    color: #064e3b;
                    font-weight: 500;
                    border-radius: 0 8px 8px 0;
                }

                /* Signatures */
                .signature-container {
                    margin-top: 4rem;
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 2rem;
                    text-align: center;
                    border-top: 2px solid var(--border);
                    padding-top: 3rem;
                }

                .sig-box {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                }

                .sig-line {
                    width: 70%;
                    border-bottom: 1px solid var(--text);
                    margin-bottom: 1rem;
                }

                .sig-label {
                    font-size: 0.8rem;
                    color: var(--grey);
                    font-style: italic;
                    margin-bottom: 0.5rem;
                }

                .sig-name {
                    font-weight: 700;
                    font-size: 1.05rem;
                    color: var(--text);
                }

                .sig-title {
                    color: var(--grey);
                    font-size: 0.85rem;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }

                .watermark {
                    text-align: center;
                    color: #9ca3af;
                    font-size: 0.8rem;
                    margin-top: 3rem;
                }

                .disclaimer {
                    margin-top: 3.5rem;
                    padding: 2rem;
                    background: #f9fafb;
                    border: 1px solid var(--border);
                    border-radius: 8px;
                    font-size: 0.75rem;
                    color: var(--grey);
                    line-height: 1.7;
                    page-break-inside: avoid;
                }

                .disclaimer h4 {
                    font-family: 'Inter', sans-serif;
                    font-size: 0.8rem;
                    color: var(--text);
                    text-transform: uppercase;
                    letter-spacing: 1px;
                    margin-bottom: 1rem;
                    font-weight: 700;
                }
            </style>
        </head>
        <body>
            <div class="action-bar no-print">
                <button class="btn-download" onclick="exportToPDF()">
                    <svg width="18" height="18" fill="currentColor" viewBox="0 0 16 16">
                      <path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"/>
                      <path d="M7.646 11.854a.5.5 0 0 0 .708 0l3-3a.5.5 0 0 0-.708-.708L8.5 10.293V1.5a.5.5 0 0 0-1 0v8.793L5.354 8.146a.5.5 0 1 0-.708.708l3 3z"/>
                    </svg>
                    Export High-Res PDF
                </button>
            </div>

            <div class="document">
                <!-- Page Header Bar with Logo -->
                <div class="page-header-bar">
                    <img class="page-header-logo" src="data:image/png;base64,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" alt="VytalYou Logo">
                    <div class="page-header-text">
                        <div class="title">ULTRA PRECISION LONGEVITY REPORT™</div>
                        <div class="subtitle">Pathology &nbsp;/&nbsp; Radiology &nbsp;/&nbsp; Cardiac Evaluation &nbsp;/&nbsp; Body Composition &nbsp;/&nbsp; Genomics</div>
                    </div>
                </div>
                
                <div class="patient-info-summary">
                    <div class="patient-meta">
                        <div>
                            <strong>Name:</strong> {{ p_name }} <br><br>
                            <strong>Age/Sex:</strong> {{ p_age }} Years / {{ p_gender }}
                        </div>
                        <div>
                            <strong>Assessment Date:</strong> {{ date }} <br><br>
                            &nbsp;
                        </div>
                    </div>
                    <div class="data-sources">
                        [Data Sources: Deep integrated analysis of pathology + InBody + radiology + cardiac data]
                    </div>
                </div>

                <!-- Where markdown is injected -->
                <div id="markdown-content"></div>

                <!-- Signatures -->
                <div class="signature-container">
                    <div class="sig-box">
                        <div class="sig-label">Digitally Signed by</div>
                        <div class="sig-line"></div>
                        <div class="sig-name">Dr. Chirantan Bose MD</div>
                        <div class="sig-title">Longevity Expert / Director</div>
                    </div>
                    <div class="sig-box">
                        <div class="sig-label">&nbsp;</div>
                        <div class="sig-line"></div>
                        <div class="sig-name">Dr. Preetesh Bhandari MD</div>
                        <div class="sig-title">Longevity Expert / Director</div>
                    </div>
                </div>

                <div class="watermark">
                    &copy; VYTALYOU™ Longevity Intelligence Platform
                </div>

                <!-- Medical Disclaimer -->
                <div class="disclaimer">
                    <h4>Medical & Clinical Disclaimer</h4>
                    <p>This VYTALYOU™ Longevity Intelligence Report is a comprehensive, integrative health assessment based on available laboratory data, imaging findings, body composition analysis, and proprietary longevity algorithms. The report is intended solely for informational, educational, and preventive health guidance purposes. It is designed to support clinical decision-making and enhance patient awareness regarding metabolic health, aging biology, and potential risk factors.</p>
                    <p>This report does not constitute a medical diagnosis, treatment plan, or prescription. Any medical decisions, including initiation, modification, or discontinuation of medications, therapies, or lifestyle interventions, must be made only after consultation with a qualified registered medical practitioner.</p>
                    <p>While every effort has been made to ensure accuracy, VYTALYOU™ does not guarantee completeness or absolute precision, as interpretations are dependent on available data, evolving scientific evidence, and individual variability.</p>
                    <p>Advanced therapies mentioned in this report (including but not limited to IV nutrient therapy, NAD+ therapy, hyperbaric oxygen therapy, photobiomodulation, and cryotherapy) should be undertaken only under appropriate medical supervision and after thorough clinical evaluation.</p>
                    <p>This report should be interpreted in conjunction with:</p>
                    <ul>
                        <li>Detailed clinical history</li>
                        <li>Physical examination</li>
                        <li>Additional diagnostic investigations (if required)</li>
                    </ul>
                    <p>VYTALYOU™ shall not be held liable for any direct or indirect consequences arising from the use, interpretation, or application of this report without appropriate medical consultation.</p>
                    <p>By using this report, the recipient acknowledges and agrees to the above terms.</p>
                    <p style="text-align: center; margin-top: 1.5rem; font-weight: 700; color: #111827;">VYTALYOU™ — Precision Longevity Medicine</p>
                </div>
            </div>

            <!-- Hidden JSON container for safe cross-language data transfer -->
            <script type="application/json" id="markdown-data">
{{ markdown_payload }}
            </script>

            <!-- Include html2pdf.js for perfect layout-to-PDF generation -->
            <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>

            <script>
                // Securely extract the JSON string and parse it to prevent any Javascript Syntax Errors!
                const rawMarkdown = JSON.parse(document.getElementById('markdown-data').textContent);

                // Pre-process the numbered sections (e.g. "1. Executive Longevity Summary") 
                // into H1 Markdown headers. Only numbered items 1 through 12.
                let preProcessed = rawMarkdown.replace(/^(?!#)(\d{1,2}\.\s+[A-Za-z].*)$/gm, '# $1');
                
                // Convernon-numbered significant headers into H1/H2
                preProcessed = preProcessed.replace(/^(?!#)(Overall Longevity Status.*)$/gm, '## $1');
                preProcessed = preProcessed.replace(/^(?!#)(Final Longevity (?:Diagnosis|Statement).*)$/gm, '# $1');
                preProcessed = preProcessed.replace(/^(?!#)(Physician Interpretation Sheet.*)$/gm, '# $1');

                // Filter out duplicated titles if the LLM adds one at the very top
                // e.g. "# VYTALYOU ULTRA PRECISION LONGEVITY REPORT"
                preProcessed = preProcessed.replace(/^\s*#\s*VYTALYOU.*REPORT\s*$/gmi, '');

                try {
                    document.getElementById('markdown-content').innerHTML = marked.parse(preProcessed);
                } catch (e) {
                    document.getElementById('markdown-content').innerHTML = "<p style='color:red'>Markdown Parsing Error: " + e.message + "</p>";
                }

                async function exportToPDF() {
                    const element = document.querySelector('.document');
                    const worker = html2pdf().from(element).set({
                        margin: 0,
                        filename: 'VYTALYOU_Longevity_Report.pdf',
                        html2canvas: { scale: 2, useCORS: true, logging: false },
                        jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
                    }).save();
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
                p_name=p_name,
                p_gender=p_gender,
                p_age=p_age,
                date=datetime.now().strftime("%d %B %Y")
            )
            return html
        except Exception as e:
            return f"<h3>Markdown Rendering Error</h3><p>{str(e)}</p>"

# Create singleton instance
pdf_generator = PDFGenerator()
