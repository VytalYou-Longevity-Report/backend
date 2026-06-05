"""
VYTALYOU™ Anthropic Claude A4 HTML Generator
Renders the premium 11-page A4 longevity report from Claude's structured JSON output.
Matches the design system of Vytalyou_Vivek_Kishore_A4_Final_2.html exactly.
"""
from __future__ import annotations
import json
import html as html_module
from datetime import datetime
from typing import Any


def _e(text: Any) -> str:
    """HTML-escape a value safely."""
    return html_module.escape(str(text or ""))


def _status_color_class(status: str) -> str:
    """Map status string to CSS class suffix (r=red, a=amber, g=green, n=navy)."""
    s = (status or "").lower()
    if s in ("critical", "high", "low"):
        return "r"
    if s in ("borderline", "moderate", "elevated"):
        return "a"
    if s in ("normal", "optimal", "good"):
        return "g"
    return "n"


def _flag_class(flag_type: str) -> str:
    mapping = {"C": "C", "H": "H", "L": "L", "G": "G", "W": "W"}
    return mapping.get(str(flag_type).upper(), "H")


def _severity_to_label_class(sev: str) -> str:
    s = (sev or "").lower()
    if s == "critical":
        return "cr"
    if s in ("moderate", "borderline"):
        return "wt"
    return "cr"


def _impact_bg(sev: str) -> str:
    s = (sev or "").lower()
    if s == "critical":
        return "background:var(--red-bg);border:1px solid rgba(176,48,48,0.2);color:var(--red);"
    if s == "positive":
        return "background:var(--green-bg);border:1px solid rgba(38,122,80,0.2);color:var(--green);"
    return "background:var(--amber-bg);border:1px solid rgba(200,125,30,0.22);color:var(--amber);"


def _traj_icon(ttype: str) -> str:
    if ttype == "improving":
        return "↑"
    if ttype == "danger":
        return "↓"
    return "→"


def _proj_bar_style(item: dict) -> str:
    color_map = {
        "red": "var(--red)", "green": "var(--green)",
        "navy": "var(--navy)", "amber": "var(--amber)",
    }
    color = color_map.get(item.get("color", "navy"), "var(--navy)")
    opacity = ";opacity:0.7" if item.get("color") == "red" else ""
    return f"width:{item.get('pct', 100)}%;background:{color}{opacity};"


COMMON_CSS = """:root{
  --cream:#F5F1EA;--cream-mid:#EDE8DF;--cream-deep:#E0D9CE;
  --white:#FFFFFF;--navy:#0C1D43;--navy-mid:#1A3262;
  --gold:#B8851E;--gold-light:#E8BE6A;
  --amber:#C87D1E;--amber-bg:rgba(200,125,30,0.07);
  --red:#B03030;--red-bg:rgba(176,48,48,0.06);
  --green:#267A50;--green-bg:rgba(38,122,80,0.07);
  --teal:#187068;--teal-bg:rgba(24,112,104,0.07);
  --text:#0C1D43;--text-mid:#38506A;--text-muted:#6A7F96;
  --border:rgba(12,29,67,0.09);
  --shadow:0 1px 3px rgba(12,29,67,0.07),0 2px 8px rgba(12,29,67,0.04);
}
*{margin:0;padding:0;box-sizing:border-box;}
html{font-size:11.5px;}
body{background:#C8C2B8;font-family:'DM Sans',sans-serif;color:var(--text);
     line-height:1.58;-webkit-print-color-adjust:exact;print-color-adjust:exact;}
.pg{width:210mm;min-height:297mm;background:var(--cream);
    margin:8px auto;padding:10mm 13mm 0 13mm;
    box-shadow:0 2px 16px rgba(0,0,0,0.2);
    display:flex;flex-direction:column;position:relative;overflow:visible;}
.pg-body{flex:1;}
.pf{margin-top:6px;padding-top:5px;border-top:1px solid var(--cream-deep);
    display:grid;grid-template-columns:1fr auto 1fr;
    gap:4px;font-size:7px;color:var(--text-muted);padding-bottom:8mm;flex-shrink:0;}
.pf-l{text-align:left;line-height:1.35;}
.pf-c{text-align:center;letter-spacing:0.07em;font-size:6.5px;text-transform:uppercase;white-space:nowrap;}
.pf-r{text-align:right;line-height:1.35;}
.ph{display:flex;justify-content:space-between;align-items:center;
    padding-bottom:7px;border-bottom:1px solid var(--border);margin-bottom:11px;}
.phi{font-size:8.5px;color:var(--text-mid);line-height:1.35;}
.phi strong{color:var(--navy);}
.phr{font-size:7.5px;color:var(--text-muted);}
.logo{font-family:'DM Sans',sans-serif;font-size:19px;font-weight:700;
      letter-spacing:-0.02em;color:var(--navy);line-height:1;}
.logo span{color:var(--gold);}
.logo-sub{font-size:6.5px;letter-spacing:0.26em;text-transform:uppercase;color:var(--text-muted);}
.sh{display:flex;align-items:flex-start;gap:8px;margin-bottom:10px;}
.sn{width:23px;height:23px;background:var(--navy);color:var(--gold-light);
    font-size:9px;font-weight:600;display:flex;align-items:center;justify-content:center;
    border-radius:2px;flex-shrink:0;font-family:'DM Mono',monospace;margin-top:2px;}
.st{font-family:'Playfair Display',serif;font-size:20px;font-weight:400;color:var(--navy);line-height:1.08;}
.stg{display:flex;gap:4px;flex-wrap:wrap;margin-top:2px;}
.stag{font-size:6.5px;letter-spacing:0.15em;text-transform:uppercase;padding:1.5px 6px;
      border-radius:1px;color:var(--text-muted);border:1px solid var(--border);background:var(--white);}
.co{padding:8px 12px;border-left:3px solid var(--gold);background:rgba(184,133,30,0.05);
    font-size:9.5px;color:var(--text-mid);line-height:1.6;border-radius:0 2px 2px 0;margin-bottom:10px;}
.co strong{color:var(--navy);}
.co.red{border-left-color:var(--red);background:var(--red-bg);}
.co.red strong{color:var(--red);}
.co.navy{border-left-color:var(--navy);background:rgba(12,29,67,0.04);}
.co.navy strong{color:var(--navy);}
.card{background:var(--white);border:1px solid var(--border);border-radius:3px;
      box-shadow:var(--shadow);padding:10px 12px;}
.ct{font-family:'Playfair Display',serif;font-size:13px;color:var(--navy);font-weight:500;
    margin-bottom:7px;padding-bottom:6px;border-bottom:1px solid var(--cream-mid);}
.g2{display:grid;grid-template-columns:1fr 1fr;gap:9px;}
.g3{display:grid;grid-template-columns:repeat(3,1fr);gap:9px;}
.g4{display:grid;grid-template-columns:repeat(4,1fr);gap:7px;}
.flag{display:inline-block;padding:1px 6px;border-radius:2px;
      font-size:8px;font-family:'DM Mono',monospace;font-weight:600;letter-spacing:0.04em;}
.flag.H{background:var(--red-bg);color:var(--red);border:1px solid rgba(176,48,48,0.18);}
.flag.L{background:var(--teal-bg);color:var(--teal);border:1px solid rgba(24,112,104,0.18);}
.flag.C{background:rgba(176,48,48,0.12);color:var(--red);border:1px solid rgba(176,48,48,0.28);}
.flag.G{background:var(--green-bg);color:var(--green);border:1px solid rgba(38,122,80,0.2);}
.flag.W{background:var(--amber-bg);color:var(--amber);border:1px solid rgba(200,125,30,0.22);}
.sb{font-size:7.5px;letter-spacing:0.12em;text-transform:uppercase;padding:2px 7px;border-radius:2px;font-weight:500;}
.sb.cr{background:var(--red-bg);color:var(--red);border:1px solid rgba(176,48,48,0.2);}
.sb.wt{background:var(--amber-bg);color:var(--amber);border:1px solid rgba(200,125,30,0.22);}
.dt{width:100%;border-collapse:collapse;font-size:9.5px;}
.dt thead tr{background:var(--navy);}
.dt th{padding:6px 9px;text-align:left;font-size:7px;letter-spacing:0.18em;
       text-transform:uppercase;color:rgba(255,255,255,0.72);font-weight:400;}
.dt td{padding:7px 9px;border-bottom:1px solid var(--cream-mid);vertical-align:top;
       color:var(--text-mid);line-height:1.45;}
.dt tr:last-child td{border-bottom:none;}
.dt td strong{color:var(--navy);font-weight:600;}
.vr{color:var(--red);font-weight:700;}.va{color:var(--amber);font-weight:700;}
.vg{color:var(--green);font-weight:700;}.vt{color:var(--teal);font-weight:700;}
.vn{color:var(--text-muted);font-size:9px;}
.ib{background:var(--white);border:1px solid var(--border);border-radius:2px;
    padding:8px 10px;box-shadow:var(--shadow);}
.ibl{font-size:7px;letter-spacing:0.18em;text-transform:uppercase;
     color:var(--text-muted);line-height:1.3;margin-bottom:3px;}
.ibv{font-family:'Playfair Display',serif;font-size:23px;font-weight:400;line-height:1;}
.ibv.r{color:var(--red);}.ibv.a{color:var(--amber);}
.ibv.g{color:var(--green);}.ibv.n{color:var(--navy);}
.ibn{font-size:8.5px;color:var(--text-muted);line-height:1.35;margin-top:2px;}
.ibn .bad{color:var(--red);font-weight:600;}.ibn .warn{color:var(--amber);font-weight:600;}.ibn .ok{color:var(--green);font-weight:600;}
.sbt{width:100%;height:4px;background:var(--cream-mid);border-radius:2px;overflow:hidden;}
.sbf{height:100%;border-radius:2px;}
.iv{background:var(--white);border:1px solid var(--border);border-top:3px solid var(--teal);
    border-radius:3px;padding:10px 12px;box-shadow:var(--shadow);}
.ivn{font-family:'Playfair Display',serif;font-size:13px;color:var(--navy);font-weight:500;margin-bottom:4px;}
.ivd{font-family:'DM Mono',monospace;font-size:8.5px;color:var(--teal);
     background:var(--teal-bg);padding:2px 7px;border-radius:2px;margin-bottom:3px;}
.ivf{font-size:8px;letter-spacing:0.09em;text-transform:uppercase;color:var(--gold);font-weight:500;margin-bottom:4px;}
.ivb{font-size:9px;color:var(--text-mid);line-height:1.5;}
.ivt{display:flex;flex-wrap:wrap;gap:3px;margin-top:5px;}
.ivtg{font-size:7.5px;padding:2px 5px;background:var(--teal-bg);
      border:1px solid rgba(24,112,104,0.18);color:var(--teal);border-radius:2px;}
.lss{font-family:'Playfair Display',serif;font-size:23px;font-weight:400;line-height:1;}
.lss.bad{color:var(--red);}.lss.warn{color:var(--amber);}.lss.ok{color:var(--green);}
.lss .den{font-size:12px;color:var(--text-muted);}
.tj{font-size:7.5px;padding:2px 6px;border-radius:2px;font-weight:500;letter-spacing:0.04em;}
.tj.bad{background:var(--red-bg);color:var(--red);border:1px solid rgba(176,48,48,0.2);}
.tj.warn{background:var(--amber-bg);color:var(--amber);border:1px solid rgba(200,125,30,0.22);}
.tj.ok{background:var(--green-bg);color:var(--green);border:1px solid rgba(38,122,80,0.2);}
.tr-tot{background:var(--navy)!important;}
.tr-tot td{color:rgba(255,255,255,0.85)!important;border-bottom:none!important;}
.hsc{background:var(--white);border:1px solid var(--border);padding:10px 12px;border-radius:3px;box-shadow:var(--shadow);}
.hsl{font-size:7px;letter-spacing:0.18em;text-transform:uppercase;color:var(--text-muted);margin-bottom:3px;}
.hsv{font-family:'Playfair Display',serif;font-size:34px;font-weight:400;line-height:1;}
.hsv.n{color:var(--navy);}.hsv.a{color:var(--amber);}
.hsv.r{color:var(--red);}.hsv.g{color:var(--green);}
.hsn{font-size:8.5px;color:var(--text-muted);line-height:1.35;margin-top:2px;}
.pr{display:grid;grid-template-columns:180px 1fr 50px;gap:7px;align-items:center;margin-bottom:5px;font-size:9.5px;}
.prl{color:var(--text-mid);}
.prt{height:6px;background:var(--cream-mid);border-radius:3px;overflow:hidden;}
.prf{height:100%;border-radius:3px;}
.prn{text-align:right;font-weight:600;color:var(--navy);font-size:9.5px;}
.rc{background:var(--white);border:1px solid var(--border);border-radius:3px;padding:9px 11px;box-shadow:var(--shadow);}
.rct{font-family:'Playfair Display',serif;font-size:12px;color:var(--navy);font-weight:500;margin:5px 0 7px;}
.ri{display:flex;gap:5px;font-size:9px;color:var(--text-mid);line-height:1.45;margin-bottom:4px;}
.ri::before{content:'→';color:var(--gold);flex-shrink:0;font-weight:600;}
.sr{background:var(--white);border:1px solid var(--border);border-radius:2px;
    padding:7px 10px;display:grid;grid-template-columns:1fr auto;gap:3px;align-items:start;box-shadow:var(--shadow);}
.srn{font-size:10px;font-weight:600;color:var(--navy);}
.srd{font-family:'DM Mono',monospace;font-size:8px;color:var(--gold);text-align:right;white-space:nowrap;}
.srw{font-size:8.5px;color:var(--text-muted);grid-column:1/-1;line-height:1.45;margin-top:1px;}
.ec-row{display:flex;flex-wrap:wrap;gap:5px;margin-top:5px;}
.ec{font-size:9px;padding:2px 8px;border-radius:2px;border:1px solid var(--border);background:var(--cream);}
.ec.g{border-color:rgba(38,122,80,0.2);background:var(--green-bg);color:var(--green);font-weight:600;}
.ec.w{border-color:rgba(200,125,30,0.2);background:var(--amber-bg);color:var(--amber);font-weight:600;}
.ec.r{border-color:rgba(176,48,48,0.2);background:var(--red-bg);color:var(--red);font-weight:600;}
.nb{background:var(--navy);border-radius:3px;padding:11px 15px;
    color:rgba(255,255,255,0.82);font-size:9.5px;line-height:1.6;margin-bottom:8px;}
.nb strong{color:var(--gold-light);}
.nb .hl{color:#FFCC55;font-weight:600;}
.ss{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;
    background:var(--cream-deep);border:1px solid var(--cream-deep);
    overflow:hidden;border-radius:2px;margin-bottom:7px;}
.sc{background:var(--white);padding:10px 12px;display:flex;flex-direction:column;gap:3px;}
.scl{font-size:6.5px;letter-spacing:0.2em;text-transform:uppercase;color:var(--text-muted);line-height:1.3;}
.scv{font-family:'Playfair Display',serif;font-size:28px;font-weight:400;line-height:1;}
.scv.a{color:var(--amber);}.scv.r{color:var(--red);}.scv.n{color:var(--navy);}
.scn{font-size:8.5px;color:var(--text-muted);line-height:1.35;}
.pts{display:grid;grid-template-columns:repeat(6,1fr);gap:1px;background:var(--navy);overflow:hidden;border-radius:2px;}
.ptc{background:var(--navy-mid);padding:7px 10px;}
.ptl{font-size:6.5px;letter-spacing:0.2em;text-transform:uppercase;color:rgba(255,255,255,0.42);}
.ptv{font-size:10px;color:#fff;font-weight:500;margin-top:1px;}
.rw{display:grid;grid-template-columns:175px 1fr;gap:14px;align-items:center;}
.gn{font-family:'Playfair Display',serif;font-size:38px;font-weight:400;color:var(--red);line-height:1;}
.gp{font-size:16px;color:var(--text-muted);vertical-align:super;font-family:'DM Sans',sans-serif;}
.gc{font-size:7.5px;letter-spacing:0.16em;text-transform:uppercase;color:var(--text-muted);text-align:center;}
.fr{display:flex;gap:6px;font-size:9.5px;color:var(--text-mid);line-height:1.5;margin-bottom:4px;}
.fr .ar{color:var(--gold);flex-shrink:0;}
.fr .g{color:var(--green);font-weight:500;}
.fr .a{color:var(--amber);font-weight:500;}
.fr .r{color:var(--red);font-weight:500;}
.sig{background:var(--white);border:1px solid var(--border);border-radius:3px;
     padding:16px 18px;display:flex;flex-direction:column;align-items:center;gap:6px;box-shadow:var(--shadow);}
.siga{width:44px;height:44px;border-radius:50%;background:var(--navy);
      display:flex;align-items:center;justify-content:center;
      font-family:'Playfair Display',serif;font-size:16px;color:var(--gold-light);}
.sign{font-family:'Playfair Display',serif;font-size:15px;color:var(--navy);text-align:center;}
.sigq{font-size:9.5px;color:var(--text-muted);text-align:center;line-height:1.45;}
.sigr{font-size:8px;letter-spacing:0.1em;text-transform:uppercase;color:var(--gold);font-weight:600;text-align:center;}
.sigs{font-style:italic;font-size:16px;font-family:'Playfair Display',serif;color:var(--navy-mid);}
.sigd{font-size:8.5px;color:var(--text-muted);letter-spacing:0.07em;}
.disc{background:var(--white);border:1px solid var(--border);border-radius:3px;padding:13px 16px;box-shadow:var(--shadow);}
.dist{font-family:'Playfair Display',serif;font-size:14px;color:var(--navy);
      margin-bottom:9px;padding-bottom:7px;border-bottom:1px solid var(--cream-mid);}
.disc p{font-size:9px;color:var(--text-muted);line-height:1.7;margin-bottom:6px;}
.disc p strong{color:var(--text-mid);font-weight:600;}
.disc p:last-child{margin-bottom:0;}
.excl{background:rgba(176,48,48,0.04);border:1px solid rgba(176,48,48,0.18);border-radius:3px;
      padding:7px 11px;font-size:9.5px;color:var(--red);line-height:1.55;margin-bottom:9px;}
.rl{font-size:7.5px;letter-spacing:0.18em;text-transform:uppercase;color:var(--text-muted);font-weight:500;margin-bottom:5px;}
.div{height:1px;background:var(--cream-deep);margin:9px 0;}
.mt8{margin-top:8px;}.mt9{margin-top:9px;}.mt10{margin-top:10px;}
.mb8{margin-bottom:8px;}.mb9{margin-bottom:9px;}.mb10{margin-bottom:10px;}
.no-print{display:none;}
@media print{
  @page{size:A4 portrait;margin:0;}
  *{-webkit-print-color-adjust:exact!important;print-color-adjust:exact!important;}
  html,body{background:#fff!important;margin:0;padding:0;}
  .pg{width:210mm;height:297mm;min-height:unset;
      margin:0!important;box-shadow:none!important;
      page-break-after:always;overflow:hidden;padding:10mm 13mm 0 13mm;}
  .pg:last-child{page-break-after:auto;}
  .pf{padding-bottom:8mm;}
  .no-print{display:none!important;}
}
"""


def _footer(name: str) -> str:
    return f"""<div class="pf">
 <div class="pf-l">602, 6th Floor, El Tara Building, Hiranandani Garden, Powai, Mumbai 400 076 · customersupport@vytalyou.com</div>
 <div class="pf-c">Pathology · Radiology · IV Therapy · 2D Echo · ECG</div>
 <div class="pf-r">Page __PAGE_NUM__ of __TOTAL_PAGES__ · {_e(name)} · Confidential</div>
</div>"""


def _page_header(patient: dict) -> str:
    name = _e(patient.get("name", "Patient"))
    age = _e(patient.get("age", ""))
    gender = _e(patient.get("gender", ""))
    lab_id = _e(patient.get("lab_id", ""))
    return f"""<div class="ph"><div style="display:flex;align-items:center;gap:8px;">
 <div class="logo" style="font-size:15px;">vytal<span>you</span></div>
 <div style="width:1px;height:20px;background:var(--border);"></div>
 <div class="phi"><strong>{name}</strong> · {gender} · {age} Years · Lab ID: {lab_id}</div>
</div><div class="phr">Confidential Medical Report</div></div>"""


def _logo_block() -> str:
    return '<div><div class="logo">vytal<span>you</span></div><div class="logo-sub">Your Longevity Hub</div></div>'


def _print_btn() -> str:
    return """<div class="no-print" style="width:210mm;margin:0 auto 8px auto;text-align:right;">
 <button onclick="window.print()" style="background:var(--navy);color:var(--gold-light);border:none;
  padding:8px 20px;border-radius:2px;font-size:10px;cursor:pointer;letter-spacing:0.15em;text-transform:uppercase;">
  ⬇ Download / Print PDF
 </button>
</div>"""


# ──────────────────────────────────────────────────────────────────────────────
# PAGE BUILDERS
# ──────────────────────────────────────────────────────────────────────────────

def _page_cover(d: dict) -> list[str]:
    p = d.get("patient", {})
    c = d.get("cover", {})
    name = _e(p.get("name", ""))
    age = _e(p.get("age", ""))
    gender = _e(p.get("gender", ""))
    assessment_date = _e(p.get("assessment_date", ""))
    lab_id = _e(p.get("lab_id", ""))
    clinical_context = _e(p.get("clinical_context", ""))
    doctor_1 = _e(p.get("doctor_1", ""))
    doctor_2 = _e(p.get("doctor_2", ""))
    report_month = _e(p.get("report_month", datetime.now().strftime("%B %Y")))
    generated_date = _e(p.get("generated_date", datetime.now().strftime("%d %B %Y")))

    ls = c.get("longevity_score", 50)
    ls_label = _e(c.get("longevity_score_label", ""))
    bio_age = _e(c.get("biological_age", ""))
    bio_drift = _e(c.get("biological_age_drift", ""))
    bio_drivers = _e(c.get("biological_age_drivers", ""))
    lpa_val = _e(c.get("lpa_value", ""))
    lpa_label = _e(c.get("lpa_label", "Lp(a) · Critical"))
    lpa_note = _e(c.get("lpa_note", ""))
    hs_gain = _e(c.get("healthspan_gain", ""))
    hs_note = _e(c.get("healthspan_note", ""))
    flags = c.get("key_flags", [])

    flags_html = "".join(
        f'<span style="font-size:8px;letter-spacing:0.1em;text-transform:uppercase;padding:3px 9px;border-radius:2px;border:1px solid rgba(184,133,30,0.22);color:var(--gold);background:rgba(184,133,30,0.05);">{_e(f)}</span>'
        for f in flags
    )

    return [f"""<div class="pg">
 <div class="pg-body">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:20px;">
   {_logo_block()}
   <div style="text-align:right;">
    <div style="background:var(--navy);color:var(--gold-light);font-size:7.5px;letter-spacing:0.22em;text-transform:uppercase;padding:4px 11px;border-radius:2px;margin-bottom:3px;">Ultra Precision Longevity Report &nbsp;·&nbsp; {report_month}</div>
    <div style="font-size:8.5px;color:var(--text-muted);">Lab ID: {lab_id} &nbsp;|&nbsp; Generated: {generated_date}</div>
   </div>
  </div>
  <div style="margin-bottom:18px;">
   <div style="font-size:7.5px;letter-spacing:0.3em;text-transform:uppercase;color:var(--amber);font-weight:500;margin-bottom:11px;">Body Composition · Laboratory · Imaging · Cardiac · Echocardiography · AHA 2026</div>
   <div style="font-family:'Playfair Display',serif;font-size:50px;font-weight:400;color:var(--navy);line-height:1.04;letter-spacing:-0.01em;margin-bottom:5px;">Predictive<br><em style="color:var(--gold);">Longevity</em><br>Report</div>
   <div style="font-size:8.5px;letter-spacing:0.2em;text-transform:uppercase;color:var(--text-muted);margin-bottom:14px;">Comprehensive Biomarker, Imaging &amp; Body Composition Intelligence</div>
   <div style="width:46px;height:2px;background:var(--gold);margin-bottom:14px;"></div>
   <div style="display:flex;gap:5px;flex-wrap:wrap;margin-bottom:16px;">{flags_html}</div>
  </div>
  <div class="ss">
   <div class="sc"><div class="scl">Overall Longevity Score</div><div class="scv a">{ls}<span style="font-size:14px;color:var(--text-muted);">/100</span></div><div class="scn">{ls_label}</div></div>
   <div class="sc"><div class="scl">Biological Age (Estimated)</div><div class="scv r">{bio_age} <span style="font-size:12px;color:var(--text-muted);">yrs ({bio_drift})</span></div><div class="scn">{bio_drivers}</div></div>
   <div class="sc"><div class="scl">{lpa_label}</div><div class="scv r">{lpa_val}</div><div class="scn">{lpa_note}</div></div>
   <div class="sc"><div class="scl">Potential Healthspan Gain</div><div class="scv n">{hs_gain}</div><div class="scn">{hs_note}</div></div>
  </div>
  <div class="pts">
   <div class="ptc"><div class="ptl">Patient Name</div><div class="ptv">{name}</div></div>
   <div class="ptc"><div class="ptl">Age / Gender</div><div class="ptv">{age} Years · {gender}</div></div>
   <div class="ptc"><div class="ptl">Assessment Date</div><div class="ptv">{assessment_date}</div></div>
   <div class="ptc"><div class="ptl">Lab ID</div><div class="ptv">{lab_id}</div></div>
   <div class="ptc"><div class="ptl">Clinical Context</div><div class="ptv">{clinical_context}</div></div>
   <div class="ptc"><div class="ptl">Medical Directors</div><div class="ptv" style="font-size:9px;">{doctor_1} &amp; {doctor_2}</div></div>
  </div>
 </div>
 {_footer(name)}
</div>"""]

def _page_executive_summary(d: dict) -> list[str]:
    p = d.get("patient", {})
    es = d.get("executive_summary", {})
    name = _e(p.get("name", ""))

    crit = es.get("critical_findings", [])
    prot = es.get("protective_findings", [])

    sev_icon = {"critical": "✦", "high": "✦", "moderate": "✦", "low": "✦"}
    sev_color = {"critical": "var(--red)", "high": "var(--red)", "moderate": "var(--amber)", "low": "var(--gold)"}

    crit_html = ""
    for f in crit:
        ic = sev_icon.get(f.get("severity", "moderate"), "✦")
        col = sev_color.get(f.get("severity", "moderate"), "var(--amber)")
        crit_html += f'<div style="display:flex;gap:5px;"><span style="color:{col};font-weight:700;flex-shrink:0;">{ic}</span><div><strong style="color:{col};">{_e(f.get("title",""))}</strong> — {_e(f.get("detail",""))}</div></div><br>'

    prot_html = ""
    for f in prot:
        prot_html += f'<div style="display:flex;gap:5px;"><span style="color:var(--green);font-weight:700;flex-shrink:0;">✓</span><div><strong style="color:var(--green);">{_e(f.get("title",""))}</strong> — {_e(f.get("detail",""))}</div></div><br>'

    cascade = _e(es.get("cascade_text", ""))
    key_flags = _e(es.get("key_flags_text", ""))

    section_tag = _e(es.get("section_tag", "AHA 2026 · Integrated Analysis"))

    return [f"""<div class="pg">
 <div class="pg-body">
  {_page_header(p)}
  <div class="sh"><div class="sn">01</div><div><div class="st">Executive Summary</div><div class="stg"><span class="stag">{section_tag}</span></div></div></div>
  <div class="co red" style="font-size:9px;"><strong>KEY FLAGS:</strong> {key_flags}</div>
  <div class="g2 mb9">
   <div>
    <div class="rl" style="color:var(--red);">Critical &amp; Abnormal Findings</div>
    <div style="display:flex;flex-direction:column;gap:5px;font-size:9.5px;color:var(--text-mid);">{crit_html}</div>
   </div>
   <div>
    <div class="rl" style="color:var(--green);">Excellent Protective Results</div>
    <div style="display:flex;flex-direction:column;gap:5px;font-size:9.5px;color:var(--text-mid);">{prot_html}</div>
   </div>
  </div>
  <div class="nb" style="font-size:9px;">{cascade}</div>
 </div>
 {_footer(name)}
</div>"""]

def _page_risk_radar_inbody(d: dict) -> list[str]:
    p = d.get("patient", {})
    rr = d.get("risk_radar", [])
    ib = d.get("inbody", {})
    name = _e(p.get("name", ""))

    sev_bg = {"critical": "var(--red-bg)", "moderate": "var(--amber-bg)", "high": "var(--red-bg)"}
    sev_border = {"critical": "rgba(176,48,48,0.2)", "moderate": "rgba(200,125,30,0.22)", "high": "rgba(176,48,48,0.2)"}
    sev_text = {"critical": "var(--red)", "moderate": "var(--amber)", "high": "var(--red)"}

    rr_html = ""
    for card in rr[:3]:
        sev = card.get("status_severity", "moderate")
        bg = sev_bg.get(sev, "var(--amber-bg)")
        brd = sev_border.get(sev, "rgba(200,125,30,0.22)")
        col = sev_text.get(sev, "var(--amber)")
        rr_html += f"""<div class="card">
     <div style="font-size:7px;letter-spacing:0.16em;text-transform:uppercase;color:var(--text-muted);margin-bottom:3px;">{_e(card.get("domain",""))}</div>
     <div style="font-family:'Playfair Display',serif;font-size:12px;color:var(--navy);margin-bottom:5px;line-height:1.28;">{_e(card.get("headline",""))}</div>
     <div style="background:{bg};border:1px solid {brd};padding:2px 7px;border-radius:2px;font-size:7.5px;letter-spacing:0.08em;text-transform:uppercase;color:{col};font-weight:600;margin-bottom:6px;display:inline-block;">{_e(card.get("status_label",""))}</div>
     <div style="font-size:9px;color:var(--text-mid);line-height:1.5;">{_e(card.get("detail",""))}</div>
    </div>"""

    # InBody metrics grid
    metrics = ib.get("metrics", [])
    status_class = {"normal": "g", "low": "r", "high": "r", "borderline": "a", "optimal": "g"}
    ib_cells = ""
    for m in metrics:
        sc = status_class.get(m.get("status", "n"), "n")
        note_cls = "ok" if sc == "g" else ("bad" if sc == "r" else "warn")
        val_parts = str(m.get("value", "")).split(".", 1)
        val_int = val_parts[0]
        val_dec = "." + val_parts[1] if len(val_parts) > 1 else ""
        ib_cells += f"""<div class="ib"><div class="ibl">{_e(m.get("label",""))}</div>
  <div class="ibv {sc}">{_e(val_int)}<span style="font-size:11px;color:var(--text-muted);">{_e(val_dec)} {_e(m.get("unit",""))}</span></div>
  <div class="ibn"><span class="{note_cls}">{_e(m.get("note",""))}</span><br>{_e(m.get("ref",""))}</div></div>"""

    # Segmental bars
    seg_html = ""
    for seg in ib.get("segmental", []):
        pct = seg.get("percent", 0)
        bar_col = "var(--amber)" if pct < 100 else "var(--green)"
        seg_html += f"""<tr><td style="color:var(--text-muted);padding:3px 0;width:130px;">{_e(seg.get("segment",""))} ({_e(seg.get("value",""))})</td>
   <td><div class="sbt"><div class="sbf" style="width:{pct}%;background:{bar_col};"></div></div></td>
   <td style="text-align:right;color:var(--amber);font-weight:600;padding-left:7px;">{pct}% ⚠</td></tr>"""

    # Key params
    kp_html = ""
    kp_col = {"critical": "var(--red)", "low": "var(--red)", "high": "var(--red)", "borderline": "var(--amber)", "normal": "var(--green)"}
    for kp in ib.get("key_params", []):
        col = kp_col.get(kp.get("status", "normal"), "var(--text-mid)")
        kp_html += f"""<tr style="border-bottom:1px solid var(--cream-mid);">
   <td style="padding:3px 0;color:var(--text-muted);">{_e(kp.get("label",""))}</td>
   <td style="text-align:right;color:{col};font-weight:600;">{_e(kp.get("value",""))}</td></tr>"""

    ib_date = _e(ib.get("date", ""))
    ib_score = _e(ib.get("score", ""))
    ib_score_label = _e(ib.get("score_label", ""))
    presc = _e(ib.get("prescription_text", ""))
    fat_ctrl = _e(ib.get("fat_control", ""))
    muscle_ctrl = _e(ib.get("muscle_control", ""))
    tgt_wt = _e(ib.get("target_weight", ""))

    rr_tag = _e(ib.get("risk_radar_tag", d.get("risk_radar_tag", "AHA 2026 · Multi-Domain Risk Assessment")))
    ib_tag = _e(ib.get("inbody_tag", "InBody 970S · Sarcopenic Obesity · Body Composition"))

    return [f"""<div class="pg">
 <div class="pg-body">
  {_page_header(p)}
  <div class="sh"><div class="sn">02</div><div><div class="st">Longevity Risk Radar</div><div class="stg"><span class="stag">{rr_tag}</span></div></div></div>
  <div class="g3 mb9">{rr_html}</div>
  <div class="div"></div>
  <div class="sh" style="margin-bottom:8px;"><div class="sn">03</div><div><div class="st">Body Composition Analysis</div><div class="stg"><span class="stag">InBody 970S · {ib_date} · {ib_tag}</span></div></div></div>
  <div class="g4 mb9">{ib_cells}</div>
  <div class="g2">
   <div class="card">
    <div style="font-weight:600;font-size:10.5px;color:var(--navy);margin-bottom:7px;">Segmental Lean Mass — All Segments Below 100%</div>
    <table style="width:100%;font-size:9.5px;">{seg_html}</table>
    <div style="font-size:8.5px;color:var(--amber);margin-top:5px;">All segments below 100% — confirmed sarcopenic obesity. Both fat loss AND muscle gain required.</div>
   </div>
   <div class="card">
    <div style="font-weight:600;font-size:10.5px;color:var(--navy);margin-bottom:7px;">Key Research Parameters · InBody Score: {ib_score} · {ib_score_label}</div>
    <table style="width:100%;font-size:9.5px;">{kp_html}</table>
   </div>
  </div>
  <div class="nb mt9" style="font-size:9px;"><strong>InBody Prescription — Dual Target (Unique in This Series):</strong> Target weight {tgt_wt}. Fat Control: <span class="hl">{fat_ctrl}</span>. Muscle Control: <span class="hl">{muscle_ctrl}</span>. {presc}</div>
 </div>
 {_footer(name)}
</div>"""]

def _page_lab_results(d: dict) -> list[str]:
    p = d.get("patient", {})
    lr = d.get("lab_results", {})
    name = _e(p.get("name", ""))

    abnormal = lr.get("abnormal", [])
    protective = lr.get("protective", [])

    pages = []
    
    # Combine all lab results into a single list of HTML row blocks
    html_rows = []
    
    if abnormal:
        html_rows.append(f'<div style="display:flex;align-items:center;gap:6px;margin-bottom:7px;margin-top:10px;"><div style="width:6px;height:6px;border-radius:50%;background:var(--red);"></div><span style="font-size:8px;letter-spacing:0.12em;text-transform:uppercase;color:var(--red);font-weight:600;">Abnormal / Critical Results</span></div>')
        html_rows.append('<div style="overflow:hidden;border-radius:3px;border:1px solid var(--border);box-shadow:var(--shadow);margin-bottom:10px;"><table class="dt"><thead><tr><th style="width:130px;">Test</th><th style="width:110px;">Result</th><th style="width:100px;">Reference</th><th style="width:80px;">Flag</th><th>Clinical Significance</th></tr></thead><tbody>')
        for r in abnormal:
            res_col_map = {"critical": "vr", "high": "vr", "low": "vt", "normal": "vg", "borderline": "va", "optimal": "vg"}
            rc = res_col_map.get(r.get("result_status", ""), "va")
            html_rows.append(f"""<tr>
  <td><strong>{_e(r.get("test",""))}</strong></td>
  <td><span class="{rc}">{_e(r.get("result",""))}</span></td>
  <td class="vn">{_e(r.get("reference",""))}</td>
  <td><span class="flag {_flag_class(r.get('flag_type','H'))}">{_e(r.get("flag",""))}</span></td>
  <td>{_e(r.get("clinical_significance",""))}</td></tr>""")
        html_rows.append('</tbody></table></div>')

    if protective:
        html_rows.append(f'<div style="display:flex;align-items:center;gap:6px;margin-bottom:7px;margin-top:10px;"><div style="width:6px;height:6px;border-radius:50%;background:var(--green);"></div><span style="font-size:8px;letter-spacing:0.12em;text-transform:uppercase;color:var(--green);font-weight:600;">Excellent Protective Results</span></div>')
        html_rows.append('<div style="overflow:hidden;border-radius:3px;border:1px solid var(--border);box-shadow:var(--shadow);"><table class="dt"><thead><tr><th style="width:130px;">Test</th><th style="width:130px;">Result</th><th style="width:80px;">Status</th><th>Why This Matters</th></tr></thead><tbody>')
        for r in protective:
            html_rows.append(f"""<tr>
  <td><strong>{_e(r.get("test",""))}</strong></td>
  <td><span class="vg">{_e(r.get("result",""))}</span></td>
  <td><span class="flag G">{_e(r.get("status_label","Excellent"))}</span></td>
  <td>{_e(r.get("why_matters",""))}</td></tr>""")
        html_rows.append('</tbody></table></div>')

    # Split rows into chunks to avoid long pages overflowing
    MAX_ROWS_PER_PAGE = 22
    for i in range(0, len(html_rows), MAX_ROWS_PER_PAGE):
        chunk = html_rows[i:i + MAX_ROWS_PER_PAGE]
        content = "".join(chunk)
        pages.append(f"""<div class="pg">
 <div class="pg-body">
  {_page_header(p)}
  <div class="sh"><div class="sn">04</div><div><div class="st">Laboratory Results</div><div class="stg"><span class="stag">Flagged · AHA 2026 · Male Reference Ranges</span></div></div></div>
  {content}
 </div>
 {_footer(name)}
</div>""")
        
    return pages if pages else [f"""<div class="pg">
 <div class="pg-body">
  {_page_header(p)}
  <div class="sh"><div class="sn">04</div><div><div class="st">Laboratory Results</div><div class="stg"><span class="stag">Flagged · AHA 2026 · Male Reference Ranges</span></div></div></div>
  <div style="font-size:9px;color:var(--text-mid);margin-top:20px;">No specific lab results reported in this section.</div>
 </div>
 {_footer(name)}
</div>"""]

def _page_imaging(d: dict) -> list[str]:
    p = d.get("patient", {})
    img = d.get("imaging", {})
    name = _e(p.get("name", ""))

    usg = img.get("usg", {})
    cxr = img.get("cxr_ecg", {})
    echo = img.get("echo", {})

    usg_findings = usg.get("findings", [])
    usg_rows = "".join(f'<div class="fr"><span class="ar">→</span><div>{_e(f)}</div></div>' for f in usg_findings)
    usg_imp = _e(usg.get("impression", ""))

    cxr_find = _e(cxr.get("cxr_findings", ""))
    cxr_imp = _e(cxr.get("cxr_impression", ""))
    ecg_find = _e(cxr.get("ecg_findings", ""))

    # Echo chips
    chip_class = {"green": "g", "red": "r", "amber": "w"}
    chips_html = '<div class="ec-row">' + "".join(
        f'<span class="ec {chip_class.get(c.get("status",""), "")}">{_e(c.get("label",""))}</span>'
        for c in echo.get("chips", [])
    ) + "</div>"

    echo_params = echo.get("params", [])
    param_rows = "".join(
        f'<tr style="border-bottom:1px solid var(--cream-mid);"><td style="padding:3px 0;color:var(--text-muted);">{_e(ep.get("label",""))}</td><td style="text-align:right;font-weight:600;color:var(--navy);">{_e(ep.get("value",""))}</td></tr>'
        for ep in echo_params
    )
    echo_imp = _e(echo.get("impression", ""))
    aortic_box = _e(echo.get("aortic_sclerosis_box", ""))

    return [f"""<div class="pg">
 <div class="pg-body">
  {_page_header(p)}
  <div class="sh"><div class="sn">05</div><div><div class="st">Imaging &amp; Cardiac</div><div class="stg"><span class="stag">Ultrasound · CXR · ECG · 2D Echo</span></div></div></div>
  <div class="g2 mb9">
   <div class="card">
    <div class="ct">Abdominal Ultrasound</div>
    <div style="font-size:9px;color:var(--text-mid);line-height:1.5;">{usg_rows}</div>
    <div style="font-size:9px;color:var(--navy);font-weight:600;margin-top:5px;">Impression: {usg_imp}</div>
   </div>
   <div>
    <div class="card mb9">
     <div class="ct">Chest X-Ray</div>
     <div style="font-size:9px;color:var(--text-mid);line-height:1.5;">{cxr_find}</div>
     <div style="font-size:9px;color:var(--navy);font-weight:600;margin-top:5px;">Impression: {cxr_imp}</div>
    </div>
    <div class="card">
     <div class="ct">ECG</div>
     <div style="font-size:9px;color:var(--text-mid);line-height:1.5;">{ecg_find}</div>
    </div>
   </div>
  </div>
  <div class="sh"><div class="sn">06</div><div><div class="st">2D Echocardiography</div><div class="stg"><span class="stag">LVEF · Wall Thickness · Aortic Sclerosis · AHA 2026</span></div></div></div>
  <div class="g2">
   <div class="card">
    <div class="ct">Echo Parameters</div>
    {chips_html}
    <table style="width:100%;font-size:9.5px;margin-top:8px;">{param_rows}</table>
   </div>
   <div>
    <div class="card mb9">
     <div class="ct">Echo Impression</div>
     <div style="font-size:9px;color:var(--text-mid);line-height:1.5;">{echo_imp}</div>
    </div>
    <div class="co red" style="font-size:9px;"><strong>Aortic Sclerosis — Progression Risk:</strong> {aortic_box}</div>
   </div>
  </div>
 </div>
 {_footer(name)}
</div>"""]

def _page_aha_risk(d: dict) -> list[str]:
    p = d.get("patient", {})
    aha = d.get("aha_risk", {})
    name = _e(p.get("name", ""))

    risk_lo = aha.get("risk_percent_low", 15)
    risk_hi = aha.get("risk_percent_high", 20)
    gauge_pct = aha.get("gauge_pct", 75)
    risk_label = _e(aha.get("risk_label", ""))
    pce_text = _e(aha.get("pce_base_text", ""))
    enhancers = aha.get("enhancers", [])
    pcsk9 = _e(aha.get("pcsk9_text", ""))
    statin = _e(aha.get("statin_text", ""))
    strategy = _e(aha.get("strategy_text", ""))

    enh_html = "".join(f'<div class="fr"><span class="ar">→</span><div>{_e(e)}</div></div>' for e in enhancers)

    return [f"""<div class="pg">
 <div class="pg-body">
  {_page_header(p)}
  <div class="sh"><div class="sn">07</div><div><div class="st">AHA 2026 Cardiovascular Risk</div><div class="stg"><span class="stag">Lp(a) Critical · LVH · Aortic Sclerosis · PCSK9 Strategy</span></div></div></div>
  <div style="display:flex; flex-direction:column; gap:9px; margin-bottom:9px;">
   <div class="card">
    <div class="ct">10-Year CV Risk Assessment</div>
    <div class="rw">
     <div style="text-align:center;">
      <div class="gn">{risk_lo}–{risk_hi}<span class="gp">%</span></div>
      <div class="gc">10-Year ASCVD Risk</div>
      <div style="margin-top:5px;background:var(--red-bg);border:1px solid rgba(176,48,48,0.2);border-radius:2px;padding:4px 8px;font-size:7.5px;color:var(--red);font-weight:600;text-align:center;">{risk_label[:50]}</div>
     </div>
     <div>
      <div style="font-size:8.5px;color:var(--text-mid);line-height:1.5;margin-bottom:6px;">{pce_text}</div>
      <div class="rl">AHA 2026 Enhancers Present</div>
      {enh_html}
     </div>
    </div>
   </div>
   <div class="card">
    <div class="ct">PCSK9 Inhibitor Strategy</div>
    <div style="font-size:9px;color:var(--text-mid);line-height:1.5;">{pcsk9}</div>
   </div>
   <div class="card">
    <div class="ct">Statin + CoQ10 Mandate</div>
    <div style="font-size:9px;color:var(--text-mid);line-height:1.5;">{statin}</div>
   </div>
  </div>
  <div class="nb" style="font-size:9px;"><strong>AHA 2026 CV Risk Reduction Strategy:</strong> {strategy}</div>
 </div>
 {_footer(name)}
</div>"""]

def _render_roadmap_section(s: dict) -> str:
    """Render a single roadmap section card."""
    priority = _e(s.get("priority", ""))
    title = _e(s.get("title", ""))
    items = s.get("items", [])
    items_html = "".join(f'<div class="ri">{_e(item)}</div>' for item in items)
    # Determine priority color
    p_lower = priority.lower()
    if "week" in p_lower or "immediate" in p_lower or "urgent" in p_lower:
        badge_style = "background:var(--red-bg);color:var(--red);border:1px solid rgba(176,48,48,0.2);"
    elif "month" in p_lower or "30" in p_lower:
        badge_style = "background:var(--amber-bg);color:var(--amber);border:1px solid rgba(200,125,30,0.22);"
    else:
        badge_style = "background:var(--teal-bg);color:var(--teal);border:1px solid rgba(24,112,104,0.18);"
    return f"""<div class="rc">
  <div style="font-size:7.5px;letter-spacing:0.12em;text-transform:uppercase;padding:2px 7px;border-radius:2px;font-weight:600;display:inline-block;{badge_style}">{priority}</div>
  <div class="rct">{title}</div>
  {items_html}
 </div>"""


def _page_roadmap(d: dict) -> list[str]:
    p = d.get("patient", {})
    rm = d.get("roadmap", {})
    name = _e(p.get("name", ""))

    sections = rm.get("sections", [])
    pages = []
    MAX_SECTIONS_PER_PAGE = 4
    
    for i in range(0, len(sections), MAX_SECTIONS_PER_PAGE):
        chunk = sections[i:i + MAX_SECTIONS_PER_PAGE]
        
        # Split chunk into two columns
        half = (len(chunk) + 1) // 2
        col1 = chunk[:half]
        col2 = chunk[half:]
        
        col1_html = "".join(_render_roadmap_section(s) for s in col1)
        col2_html = "".join(_render_roadmap_section(s) for s in col2)

        pages.append(f"""<div class="pg">
 <div class="pg-body">
  {_page_header(p)}
  <div class="sh"><div class="sn">08</div><div><div class="st">Precision Longevity Roadmap</div><div class="stg"><span class="stag">Priority-Sequenced · Evidence-Based · AHA 2026</span></div></div></div>
  <div class="g2">
   <div>{col1_html}</div>
   <div>{col2_html}</div>
  </div>
 </div>
 {_footer(name)}
</div>""")

    if not pages:
        pages.append(f"""<div class="pg">
 <div class="pg-body">
  {_page_header(p)}
  <div class="sh"><div class="sn">08</div><div><div class="st">Precision Longevity Roadmap</div><div class="stg"><span class="stag">Priority-Sequenced · Evidence-Based · AHA 2026</span></div></div></div>
  <div style="font-size:9px;color:var(--text-mid);">No roadmap sections generated.</div>
 </div>
 {_footer(name)}
</div>""")

    return pages

def _page_iv_protocol(d: dict) -> list[str]:
    p = d.get("patient", {})
    iv = d.get("iv_protocol", {})
    name = _e(p.get("name", ""))

    sessions = iv.get("sessions", [])
    orals = iv.get("oral_supplements", [])
    rationale = _e(iv.get("rationale", ""))
    exclusions = _e(iv.get("exclusions", ""))

    pages = []
    
    MAX_SESSIONS_PER_PAGE = 6
    MAX_ORALS_PER_PAGE = 6

    # Convert sessions to HTML
    session_divs = []
    for s in sessions:
        tags_html = "".join(f'<span class="ivtg">{_e(t)}</span>' for t in s.get("tags", []))
        session_divs.append(f"""<div class="iv">
  <div class="ivn">{_e(s.get("name",""))}</div>
  <div class="ivd">{_e(s.get("dose",""))}</div>
  <div class="ivf">{_e(s.get("frequency",""))}</div>
  <div class="ivb">{_e(s.get("rationale",""))}</div>
  <div class="ivt">{tags_html}</div>
 </div>""")

    # Convert orals to HTML
    oral_divs = []
    for o in orals:
        oral_divs.append(f"""<div class="sr">
  <div class="srn">{_e(o.get("name",""))}</div>
  <div class="srd">{_e(o.get("dose",""))}</div>
  <div class="srw">{_e(o.get("rationale",""))}</div>
 </div>""")

    # Create first page with rationale, exclusions, and first chunk of sessions/orals
    sessions_chunk = session_divs[:MAX_SESSIONS_PER_PAGE]
    orals_chunk = oral_divs[:MAX_ORALS_PER_PAGE]
    
    session_html = f'<div class="g2 mb9" style="grid-template-columns:repeat(3,1fr);gap:7px;">{"".join(sessions_chunk)}</div>' if sessions_chunk else ""
    oral_html = f'<div class="rl">Oral Supplement Programme</div><div style="display:flex;flex-direction:column;gap:5px;">{"".join(orals_chunk)}</div>' if orals_chunk else ""
    
    pages.append(f"""<div class="pg">
 <div class="pg-body">
  {_page_header(p)}
  <div class="sh"><div class="sn">09</div><div><div class="st">Vytalyou IV Therapy Protocol</div><div class="stg"><span class="stag">Lp(a) · Sarcopenia · Anaemia · Cardiac · Micronutrients</span></div></div></div>
  <div class="co" style="font-size:9px;">{rationale}</div>
  <div class="excl">{exclusions}</div>
  {session_html}
  {oral_html}
 </div>
 {_footer(name)}
</div>""")

    # Process remaining chunks if any
    session_idx = MAX_SESSIONS_PER_PAGE
    oral_idx = MAX_ORALS_PER_PAGE
    
    while session_idx < len(session_divs) or oral_idx < len(oral_divs):
        sessions_chunk = session_divs[session_idx:session_idx + MAX_SESSIONS_PER_PAGE]
        orals_chunk = oral_divs[oral_idx:oral_idx + MAX_ORALS_PER_PAGE]
        
        session_html = f'<div class="g2 mb9" style="grid-template-columns:repeat(3,1fr);gap:7px;">{"".join(sessions_chunk)}</div>' if sessions_chunk else ""
        oral_html = f'<div class="rl">Oral Supplement Programme (Continued)</div><div style="display:flex;flex-direction:column;gap:5px;">{"".join(orals_chunk)}</div>' if orals_chunk else ""
        
        pages.append(f"""<div class="pg">
 <div class="pg-body">
  {_page_header(p)}
  <div class="sh"><div class="sn">09</div><div><div class="st">Vytalyou IV Therapy Protocol (Continued)</div><div class="stg"><span class="stag">Lp(a) · Sarcopenia · Anaemia · Cardiac · Micronutrients</span></div></div></div>
  {session_html}
  {oral_html}
 </div>
 {_footer(name)}
</div>""")
        
        session_idx += MAX_SESSIONS_PER_PAGE
        oral_idx += MAX_ORALS_PER_PAGE

    return pages

def _page_longevity_scores(d: dict) -> list[str]:
    p = d.get("patient", {})
    ls = d.get("longevity_scores", {})
    name = _e(p.get("name", ""))

    domains = ls.get("domains", [])
    overall = ls.get("overall_score", 50)
    overall_max = ls.get("overall_score_max", 100)
    overall_summary = _e(ls.get("overall_summary", ""))
    overall_traj = _e(ls.get("overall_trajectory", ""))

    def score_class(score, max_score):
        pct = (score / max_score) * 100 if max_score else 0
        if pct >= 75:
            return "lss ok", "tj ok"
        if pct >= 40:
            return "lss warn", "tj warn"
        return "lss bad", "tj bad"

    def traj_class(ttype):
        if ttype == "improving":
            return "tj ok"
        if ttype == "danger":
            return "tj bad"
        return "tj warn"

    rows = ""
    for dom in domains:
        sc = dom.get("score", 0)
        mx = dom.get("max", 20)
        lss_c, tj_c = score_class(sc, mx)
        tj_c = traj_class(dom.get("trajectory_type", "stable"))
        rows += f"""<tr>
  <td style="padding:8px 10px;vertical-align:top;"><div style="font-weight:600;font-size:10.5px;color:var(--navy);">{_e(dom.get("domain",""))}</div></td>
  <td style="padding:8px 10px;vertical-align:top;"><div class="{lss_c}">{sc}<span class="den">/{mx}</span></div></td>
  <td style="padding:8px 10px;vertical-align:top;font-size:9px;color:var(--text-mid);">{_e(dom.get("findings",""))}</td>
  <td style="padding:8px 10px;vertical-align:top;"><div class="{tj_c}">{_traj_icon(dom.get("trajectory_type","stable"))} {_e(dom.get("trajectory",""))}</div></td>
  <td style="padding:8px 10px;vertical-align:top;font-size:9px;color:var(--text-mid);">{_e(dom.get("priority_action",""))}</td>
 </tr>"""

    ov_lss, _ = score_class(overall, overall_max)

    return [f"""<div class="pg">
 <div class="pg-body">
  {_page_header(p)}
  <div class="sh"><div class="sn">10</div><div><div class="st">Longevity Score System</div><div class="stg"><span class="stag">Domain Scoring · Trajectory · Priority Actions</span></div></div></div>
  <div style="overflow:hidden;border-radius:3px;border:1px solid var(--border);box-shadow:var(--shadow);">
  <table style="width:100%;border-collapse:collapse;">
   <thead><tr style="background:var(--navy);">
    <th style="padding:8px 10px;text-align:left;font-size:7px;letter-spacing:0.18em;text-transform:uppercase;color:rgba(255,255,255,0.72);font-weight:400;width:140px;">Domain</th>
    <th style="padding:8px 10px;text-align:left;font-size:7px;letter-spacing:0.18em;text-transform:uppercase;color:rgba(255,255,255,0.72);font-weight:400;width:70px;">Score</th>
    <th style="padding:8px 10px;text-align:left;font-size:7px;letter-spacing:0.18em;text-transform:uppercase;color:rgba(255,255,255,0.72);font-weight:400;">Key Findings</th>
    <th style="padding:8px 10px;text-align:left;font-size:7px;letter-spacing:0.18em;text-transform:uppercase;color:rgba(255,255,255,0.72);font-weight:400;width:120px;">Trajectory</th>
    <th style="padding:8px 10px;text-align:left;font-size:7px;letter-spacing:0.18em;text-transform:uppercase;color:rgba(255,255,255,0.72);font-weight:400;">Priority Action</th>
   </tr></thead>
   <tbody style="font-size:9.5px;">{rows}
   <tr class="tr-tot">
    <td style="padding:10px;"><div style="font-weight:700;font-size:13px;color:#FFF;">Overall Longevity Score</div></td>
    <td style="padding:10px;"><div style="font-family:'Playfair Display',serif;font-size:32px;font-weight:400;color:var(--gold-light);line-height:1;">{overall}<span style="font-size:14px;color:rgba(255,255,255,0.4);">/{overall_max}</span></div></td>
    <td colspan="2" style="padding:10px;font-size:9.5px;">{overall_summary}</td>
    <td style="padding:10px;font-size:9.5px;">{overall_traj}</td>
   </tr>
   </tbody>
  </table>
  </div>
 </div>
 {_footer(name)}
</div>"""]

def _page_healthspan(d: dict) -> list[str]:
    p = d.get("patient", {})
    hs = d.get("healthspan", {})
    name = _e(p.get("name", ""))

    chron = _e(hs.get("chronological_age", ""))
    chron_note = _e(hs.get("chronological_age_note", ""))
    bio = _e(hs.get("biological_age", ""))
    bio_note = _e(hs.get("biological_age_note", ""))
    cur = _e(hs.get("current_healthspan", ""))
    cur_note = _e(hs.get("current_healthspan_note", ""))
    pot = _e(hs.get("potential_healthspan", ""))
    pot_note = _e(hs.get("potential_healthspan_note", ""))
    opp = _e(hs.get("opportunity_text", ""))

    projs = hs.get("projections", [])
    proj_html = ""
    for pr in projs:
        col_map = {"red": "var(--red)", "green": "var(--green)", "navy": "var(--navy)"}
        label_col_map = {"danger": "var(--red)", "success": "var(--green)"}
        lbl_col = label_col_map.get(pr.get("style", ""), "var(--text-mid)")
        bar_style = _proj_bar_style(pr)
        proj_html += f"""<div class="pr">
  <div class="prl" style="color:{lbl_col};">{_e(pr.get("label",""))}</div>
  <div class="prt"><div class="prf" style="{bar_style}"></div></div>
  <div class="prn" style="color:{lbl_col};">{_e(pr.get("value",""))}</div>
 </div>"""

    cards = hs.get("intervention_cards", [])
    cards_html = ""
    for c in cards:
        impact_style = _impact_bg(c.get("impact_severity", "positive"))
        cards_html += f"""<div class="card">
  <div style="font-family:'Playfair Display',serif;font-size:12px;color:var(--navy);margin-bottom:5px;">{_e(c.get("title",""))}</div>
  <div style="font-size:9px;color:var(--text-mid);line-height:1.5;">{_e(c.get("detail",""))}</div>
  <div style="margin-top:6px;{impact_style}border-radius:2px;padding:4px 8px;font-size:8px;font-weight:600;">{_e(c.get("impact_label",""))}</div>
 </div>"""

    hs_tag = _e(hs.get("section_tag", "Healthspan Analysis · Intervention Impact · Projection"))

    return [f"""<div class="pg">
 <div class="pg-body">
  {_page_header(p)}
  <div class="sh"><div class="sn">11</div><div><div class="st">Healthspan Analysis &amp; Projection</div><div class="stg"><span class="stag">{hs_tag}</span></div></div></div>
  <div class="g4 mb9">
   <div class="hsc"><div class="hsl">Chronological Age</div><div class="hsv n">{chron}</div><div class="hsn">{chron_note}</div></div>
   <div class="hsc"><div class="hsl">Estimated Biological Age</div><div class="hsv r">{bio}</div><div class="hsn" style="color:var(--red);">{bio_note}</div></div>
   <div class="hsc"><div class="hsl">Current Healthspan Remaining</div><div class="hsv r">{cur}</div><div class="hsn">{cur_note}</div></div>
   <div class="hsc"><div class="hsl">Potential Healthspan with Intervention</div><div class="hsv g">{pot}</div><div class="hsn" style="color:var(--green);">{pot_note}</div></div>
  </div>
  <div class="card mb9">
   <div style="font-weight:600;font-size:11px;color:var(--navy);margin-bottom:9px;">Healthspan Projection</div>
   {proj_html}
  </div>
  <div class="g3 mb9">{cards_html}</div>
  <div class="nb" style="font-size:9px;"><strong>The Vytalyou Opportunity:</strong> {opp}</div>
 </div>
 {_footer(name)}
</div>"""]

def _page_authorization(d: dict) -> list[str]:
    p = d.get("patient", {})
    auth = d.get("authorization", {})
    name = _e(p.get("name", ""))
    gen_date = _e(p.get("generated_date", datetime.now().strftime("%d %B %Y")))

    auth_text = _e(auth.get("auth_text", ""))
    d1_ini = _e(auth.get("doctor_1_initials", "CB"))
    d1_name = _e(auth.get("doctor_1_name", "Dr. Chirantan Bose"))
    d1_quals = _e(auth.get("doctor_1_quals", "MBBS, MD, MBA"))
    d1_role = _e(auth.get("doctor_1_role", "Medical Director, Vytalyou"))
    d1_sig = _e(auth.get("doctor_1_sig", "Chirantan Bose"))
    d2_ini = _e(auth.get("doctor_2_initials", "PB"))
    d2_name = _e(auth.get("doctor_2_name", "Dr. Preetesh Bhandari"))
    d2_quals = _e(auth.get("doctor_2_quals", "MBBS, MD DNB EDiR DICR"))
    d2_role = _e(auth.get("doctor_2_role", "Medical Director, Vytalyou"))
    d2_sig = _e(auth.get("doctor_2_sig", "Preetesh Bhandari"))

    disc_points = auth.get("disclaimer_points", [])
    disc_html = "".join(
        f'<p><strong>{_e(dp.get("num",""))}. {_e(dp.get("title",""))}:</strong> {_e(dp.get("text",""))}</p>'
        for dp in disc_points
    )

    return [f"""<div class="pg">
 <div class="pg-body">
  {_page_header(p)}
  <div class="sh"><div class="sn">12</div><div><div class="st">Digital Authorization</div><div class="stg"><span class="stag">Vytalyou Medical Team &middot; {gen_date}</span></div></div></div>
  <div class="co navy" style="font-size:9px;margin-bottom:12px;"><strong>Digitally Authorized — Vytalyou Ultra Precision Longevity Report:</strong> {auth_text}</div>
  <div class="g2" style="margin-bottom:12px;">
   <div class="sig">
    <div class="siga">{d1_ini}</div>
    <div class="sign">{d1_name}</div>
    <div class="sigq">{d1_quals}</div>
    <div class="sigr">{d1_role}</div>
    <div style="width:100%;height:1px;background:var(--cream-mid);margin:4px 0;"></div>
    <div class="sigs">{d1_sig}</div>
    <div class="sigd">Digital Signature · {gen_date}</div>
   </div>
   <div class="sig">
    <div class="siga">{d2_ini}</div>
    <div class="sign">{d2_name}</div>
    <div class="sigq">{d2_quals}</div>
    <div class="sigr">{d2_role}</div>
    <div style="width:100%;height:1px;background:var(--cream-mid);margin:4px 0;"></div>
    <div class="sigs">{d2_sig}</div>
    <div class="sigd">Digital Signature · {gen_date}</div>
   </div>
  </div>
  <div class="disc">
   <div class="dist">Medical Disclaimer &amp; Important Notice</div>
   {disc_html}
  </div>
 </div>
 <div class="pf">
  <div class="pf-l"><div class="logo" style="font-size:13px;display:inline;">vytal<span>you</span></div> &nbsp;|&nbsp; 602, 6th Floor, El Tara Building, Hiranandani Garden, Powai, Mumbai 400 076</div>
  <div class="pf-c">Pathology · Radiology · IV Therapy · 2D Echo · ECG &nbsp;|&nbsp; Page __PAGE_NUM__ of __TOTAL_PAGES__</div>
  <div class="pf-r">{_e(p.get("name",""))} · {_e(p.get("gender",""))} · {_e(p.get("age",""))} Years · Confidential · {gen_date}</div>
 </div>
</div>"""]


# ──────────────────────────────────────────────────────────────────────────────
# PUBLIC API
# ──────────────────────────────────────────────────────────────────────────────

class AnthropicPDFGenerator:
    """Renders the premium A4 HTML report from Claude's structured JSON."""

    TOTAL_PAGES = 11

    def generate_report_html(self, json_data: dict, session_id: str) -> str:
        """
        Build the full multi-page A4 HTML from the Claude JSON output.
        json_data: parsed dict from Claude's structured JSON response.
        """
        pages = []
        pages.extend(_page_cover(json_data))
        pages.extend(_page_executive_summary(json_data))
        pages.extend(_page_risk_radar_inbody(json_data))
        pages.extend(_page_lab_results(json_data))
        pages.extend(_page_imaging(json_data))
        pages.extend(_page_aha_risk(json_data))
        pages.extend(_page_roadmap(json_data))
        pages.extend(_page_iv_protocol(json_data))
        pages.extend(_page_longevity_scores(json_data))
        pages.extend(_page_healthspan(json_data))
        pages.extend(_page_authorization(json_data))

        total_pages = len(pages)
        final_pages = []
        for i, p in enumerate(pages, 1):
            p = p.replace("__PAGE_NUM__", str(i))
            p = p.replace("__TOTAL_PAGES__", str(total_pages))
            final_pages.append(p)

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Vytalyou Ultra Precision Longevity Report</title>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,500;0,600;1,400;1,500&family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
{COMMON_CSS}
</style>
</head>
<body>
{_print_btn()}
{"".join(final_pages)}
</body>
</html>"""


anthropic_pdf_generator = AnthropicPDFGenerator()
