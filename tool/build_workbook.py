"""
Build the NIST CSF 2.0 maturity-assessment workbook.

Sheets:
  1. README        - how to use the workbook
  2. Assessment    - all 106 subcategories, Current/Target scoring, auto Gap + Priority
  3. Dashboard     - per-function current vs target (formulas) + maturity chart
  4. Roadmap       - the highest-gap items, auto-ranked, with effort/owner columns

Run:  python build_workbook.py
Output: ../assessment/CSF2.0_Maturity_Assessment.xlsx
"""
import os
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side, NamedStyle
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import ColorScaleRule, CellIsRule
from openpyxl.chart import BarChart, RadarChart, Reference
from openpyxl.utils import get_column_letter

from csf_data import (FUNCTIONS, CATEGORIES, SUBCATEGORIES, TIER_LABELS, ORG)

# ---- palette ----
NAVY   = "1F2A44"
BLUE   = "2E5A88"
LIGHT  = "DCE6F1"
INPUT  = "FFF2CC"   # yellow = cells the user fills in
GREY   = "F2F2F2"
WHITE  = "FFFFFF"
GREEN  = "548235"
AMBER  = "BF8F00"
RED    = "C00000"

FONT = "Arial"
thin = Side(style="thin", color="BFBFBF")
border = Border(left=thin, right=thin, top=thin, bottom=thin)

def hfont(sz=11, color=WHITE, bold=True):
    return Font(name=FONT, size=sz, color=color, bold=bold)
def bfont(sz=10, color="000000", bold=False, italic=False):
    return Font(name=FONT, size=sz, color=color, bold=bold, italic=italic)

wb = Workbook()

# ======================================================================
# Sheet 1: README
# ======================================================================
ws = wb.active
ws.title = "README"
ws.sheet_view.showGridLines = False
ws.column_dimensions["A"].width = 3
ws.column_dimensions["B"].width = 105

def readme_line(row, text, size=10, bold=False, color="000000", fill=None, top=4, italic=False):
    c = ws.cell(row=row, column=2, value=text)
    c.font = bfont(size, color, bold, italic)
    c.alignment = Alignment(wrap_text=True, vertical="top")
    if fill:
        c.fill = PatternFill("solid", fgColor=fill)
    ws.row_dimensions[row].height = top

r = 2
ws.cell(row=r, column=2, value="NIST CSF 2.0 - Cybersecurity Maturity Assessment").font = hfont(16, NAVY)
ws.row_dimensions[r].height = 26
r += 2
readme_line(r, "A guided, framework-anchored maturity assessment. You score where the organisation is today "
               "(Current) against where it should be (Target) across all 106 CSF 2.0 outcomes, and the workbook "
               "turns that into a gap analysis, a function-level dashboard, and a prioritised roadmap.", top=48); r += 2

readme_line(r, "HOW TO USE", 12, True, BLUE); r += 1
steps = [
    "1.  Fill in the scope on the Assessment sheet header (org name, assessor, date).",
    "2.  For each subcategory, set the CURRENT score (0-4) for how the org operates today.",
    "3.  Set the TARGET score (0-4) - the realistic maturity this org should reach given its size and risk.",
    "4.  GAP and PRIORITY are calculated automatically. Add evidence/notes in the last column.",
    "5.  The Dashboard updates automatically. The Roadmap auto-ranks the biggest gaps to work on first.",
    "6.  Only edit the shaded (yellow) cells. Everything else is a formula - leave it alone.",
]
for s in steps:
    readme_line(r, s, top=16); r += 1
r += 1

readme_line(r, "MATURITY SCALE (0-4)", 12, True, BLUE); r += 1
for k in sorted(TIER_LABELS):
    desc = {
        0: "Not implemented, or not known to exist.",
        1: "Partial - ad hoc and reactive; little or nothing written down.",
        2: "Risk Informed - aware of the risk; some practices, applied inconsistently.",
        3: "Repeatable - documented, consistent, backed by policy.",
        4: "Adaptive - measured with metrics and continuously improved.",
    }[k]
    readme_line(r, f"{TIER_LABELS[k]}   -   {desc}", top=15); r += 1
r += 1

readme_line(r, "PRIORITY LOGIC", 12, True, BLUE); r += 1
readme_line(r, "Priority = size of the gap, weighted so gaps at a low current score matter more. "
               "High (red) = fix first; Medium (amber) = plan next; Low (green) = fine-tune.", top=30); r += 2

readme_line(r, "The yellow cells are the ones you edit:", 10, True);
ws.cell(row=r, column=2).fill = PatternFill("solid", fgColor=INPUT); r += 2

readme_line(r, "Functions: GV Govern | ID Identify | PR Protect | DE Detect | RS Respond | RC Recover   "
               "(6 functions, 22 categories, 106 subcategories).", 9, False, "595959", italic=True); r += 1
readme_line(r, "Subcategory IDs follow the official NIST CSF 2.0 Core. Outcome descriptions are plain-language "
               "summaries written for this project, not NIST's official text.", 9, False, "595959", italic=True)

# ======================================================================
# Sheet 2: Assessment
# ======================================================================
aw = wb.create_sheet("Assessment")
aw.sheet_view.showGridLines = False
cols = {"A":5,"B":12,"C":30,"D":52,"E":11,"F":11,"G":9,"H":13,"I":44}
for col,w in cols.items():
    aw.column_dimensions[col].width = w

# Header block
aw.merge_cells("B2:I2")
t = aw.cell(row=2, column=2, value="NIST CSF 2.0 Maturity Assessment")
t.font = hfont(15, NAVY); aw.row_dimensions[2].height = 24

meta = [
    ("Organisation:", ORG["name"]),
    ("Sector / scope:", f'{ORG["sector"]}  -  {ORG["location"]}'),
    ("Assessor:", "<< your name >>"),
    ("Date:", ORG["date"]),
]
mr = 3
for label, val in meta:
    aw.cell(row=mr, column=2, value=label).font = bfont(10, "595959", True)
    vc = aw.cell(row=mr, column=3, value=val); vc.font = bfont(10)
    if label in ("Assessor:",):
        vc.fill = PatternFill("solid", fgColor=INPUT); vc.border = border
    mr += 1
aw.row_dimensions[6].height = 6

# Column headers
HROW = 8
headers = ["", "ID", "Category", "Outcome (plain-language)", "Current (0-4)",
           "Target (0-4)", "Gap", "Priority", "Evidence / notes"]
for i, h in enumerate(headers, start=1):
    c = aw.cell(row=HROW, column=i, value=h)
    c.font = hfont(10); c.fill = PatternFill("solid", fgColor=BLUE)
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    c.border = border
aw.row_dimensions[HROW].height = 30
aw.freeze_panes = "B9"

# Data validation 0-4 for current/target
dv = DataValidation(type="whole", operator="between", formula1="0", formula2="4", allow_blank=True)
dv.error = "Enter a whole number 0-4."; dv.errorTitle = "Invalid score"
aw.add_data_validation(dv)

start = HROW + 1
row = start
for sid, outcome, cur, tgt, note in SUBCATEGORIES:
    func = sid.split(".")[0]
    cat = CATEGORIES[sid.rsplit("-", 1)[0]]
    # alternating function band colour (very light)
    band = {"GV":"EAF1F8","ID":"EFF6EC","PR":"FBF4E6","DE":"F3EEF7","RS":"FDEEEE","RC":"EAF5F6"}[func]
    aw.cell(row=row, column=1, value=func).font = bfont(9, "808080", True)
    aw.cell(row=row, column=1).alignment = Alignment(horizontal="center")
    aw.cell(row=row, column=2, value=sid).font = bfont(10, NAVY, True)
    aw.cell(row=row, column=3, value=cat).font = bfont(9, "404040")
    oc = aw.cell(row=row, column=4, value=outcome); oc.font = bfont(10)
    oc.alignment = Alignment(wrap_text=True, vertical="top")
    # Current + Target = editable yellow cells (pre-filled with example scores)
    cc = aw.cell(row=row, column=5, value=cur)
    tc = aw.cell(row=row, column=6, value=tgt)
    for x in (cc, tc):
        x.fill = PatternFill("solid", fgColor=INPUT)
        x.alignment = Alignment(horizontal="center"); x.font = bfont(10, bold=True)
        dv.add(x)
    # Gap formula
    gc = aw.cell(row=row, column=7, value=f"=MAX(0,F{row}-E{row})")
    gc.alignment = Alignment(horizontal="center"); gc.font = bfont(10, bold=True)
    # Priority formula: weight gap by how low the current score is
    pc = aw.cell(row=row, column=8,
        value=(f'=IF(G{row}=0,"-",IF((G{row}+(4-E{row})/2)>=3.5,"High",'
               f'IF((G{row}+(4-E{row})/2)>=2,"Medium","Low")))'))
    pc.alignment = Alignment(horizontal="center"); pc.font = bfont(10, bold=True)
    nc = aw.cell(row=row, column=9, value=note); nc.font = bfont(9, "595959")
    nc.alignment = Alignment(wrap_text=True, vertical="top")
    # borders + band fill on descriptive cols
    for col in range(1, 10):
        cell = aw.cell(row=row, column=col)
        cell.border = border
        if col in (1,2,3,4,9):
            cell.fill = PatternFill("solid", fgColor=band)
    aw.row_dimensions[row].height = 30
    row += 1
last = row - 1

# Conditional formatting: Current column heatmap (red low -> green high)
aw.conditional_formatting.add(f"E{start}:E{last}",
    ColorScaleRule(start_type="num", start_value=0, start_color="F8696B",
                   mid_type="num", mid_value=2, mid_color="FFEB84",
                   end_type="num", end_value=4, end_color="63BE7B"))
# Priority colouring
aw.conditional_formatting.add(f"H{start}:H{last}",
    CellIsRule(operator="equal", formula=['"High"'],
               fill=PatternFill("solid", fgColor="F4CCCC"), font=Font(name=FONT, color="990000", bold=True)))
aw.conditional_formatting.add(f"H{start}:H{last}",
    CellIsRule(operator="equal", formula=['"Medium"'],
               fill=PatternFill("solid", fgColor="FCE5CD"), font=Font(name=FONT, color="996600", bold=True)))
aw.conditional_formatting.add(f"H{start}:H{last}",
    CellIsRule(operator="equal", formula=['"Low"'],
               fill=PatternFill("solid", fgColor="D9EAD3"), font=Font(name=FONT, color="38761D", bold=True)))

# ======================================================================
# Sheet 3: Dashboard
# ======================================================================
dw = wb.create_sheet("Dashboard")
dw.sheet_view.showGridLines = False
for col,w in {"A":3,"B":12,"C":26,"D":14,"E":14,"F":12,"G":10,"H":3}.items():
    dw.column_dimensions[col].width = w

dw.merge_cells("B2:G2")
dt = dw.cell(row=2, column=2, value="Dashboard - Maturity by Function")
dt.font = hfont(15, NAVY); dw.row_dimensions[2].height = 24
dw.cell(row=3, column=2, value=f'{ORG["name"]}').font = bfont(10, "595959", italic=True)

dh = 5
for i,h in enumerate(["", "Func", "Function", "Avg Current", "Avg Target", "Avg Gap", "% to Target"], start=1):
    c = dw.cell(row=dh, column=i, value=h)
    c.font = hfont(10); c.fill = PatternFill("solid", fgColor=BLUE)
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    c.border = border
dw.row_dimensions[dh].height = 24

# For each function compute AVERAGEIF across the Assessment sheet, using the function tag in col A
func_order = ["GV","ID","PR","DE","RS","RC"]
dr = dh + 1
rng_f = f"Assessment!$A${start}:$A${last}"
rng_cur = f"Assessment!$E${start}:$E${last}"
rng_tgt = f"Assessment!$F${start}:$F${last}"
rng_gap = f"Assessment!$G${start}:$G${last}"
for f in func_order:
    dw.cell(row=dr, column=2, value=f).font = bfont(10, NAVY, True)
    dw.cell(row=dr, column=2).alignment = Alignment(horizontal="center")
    dw.cell(row=dr, column=3, value=FUNCTIONS[f]).font = bfont(10)
    dw.cell(row=dr, column=4, value=f'=ROUND(AVERAGEIF({rng_f},B{dr},{rng_cur}),2)')
    dw.cell(row=dr, column=5, value=f'=ROUND(AVERAGEIF({rng_f},B{dr},{rng_tgt}),2)')
    dw.cell(row=dr, column=6, value=f'=ROUND(AVERAGEIF({rng_f},B{dr},{rng_gap}),2)')
    dw.cell(row=dr, column=7, value=f'=IF(E{dr}=0,1,D{dr}/E{dr})')
    for col in range(4,8):
        cc = dw.cell(row=dr, column=col)
        cc.alignment = Alignment(horizontal="center"); cc.font = bfont(10)
    dw.cell(row=dr, column=7).number_format = "0%"
    for col in range(2,8):
        dw.cell(row=dr, column=col).border = border
    dr += 1
# Overall row
dw.cell(row=dr, column=3, value="OVERALL").font = bfont(10, NAVY, True)
dw.cell(row=dr, column=4, value=f'=ROUND(AVERAGE({rng_cur}),2)')
dw.cell(row=dr, column=5, value=f'=ROUND(AVERAGE({rng_tgt}),2)')
dw.cell(row=dr, column=6, value=f'=ROUND(AVERAGE({rng_gap}),2)')
dw.cell(row=dr, column=7, value=f'=IF(E{dr}=0,1,D{dr}/E{dr})')
for col in range(2,8):
    cell = dw.cell(row=dr, column=col)
    cell.fill = PatternFill("solid", fgColor=LIGHT); cell.font = bfont(10, NAVY, True)
    cell.alignment = Alignment(horizontal="center"); cell.border = border
dw.cell(row=dr, column=7).number_format = "0%"
overall_row = dr

# heatmap on avg current
dw.conditional_formatting.add(f"D{dh+1}:D{dh+6}",
    ColorScaleRule(start_type="num", start_value=0, start_color="F8696B",
                   mid_type="num", mid_value=2, mid_color="FFEB84",
                   end_type="num", end_value=4, end_color="63BE7B"))

# Bar chart: current vs target by function
chart = BarChart(); chart.type = "col"; chart.style = 10
chart.title = "Current vs Target Maturity by Function"
chart.y_axis.title = "Maturity (0-4)"; chart.x_axis.title = "Function"
chart.y_axis.scaling.min = 0; chart.y_axis.scaling.max = 4
data = Reference(dw, min_col=4, max_col=5, min_row=dh, max_row=dh+6)
cats = Reference(dw, min_col=3, max_col=3, min_row=dh+1, max_row=dh+6)
chart.add_data(data, titles_from_data=True)
chart.set_categories(cats)
chart.height = 8.5; chart.width = 17
chart.series[0].graphicalProperties.solidFill = "C0392B"   # current = red-ish
chart.series[1].graphicalProperties.solidFill = "2E5A88"   # target  = blue
dw.add_chart(chart, "B15")

# Radar chart for profile shape
radar = RadarChart(); radar.type = "marker"; radar.style = 11
radar.title = "Maturity Profile (Current vs Target)"
rdata = Reference(dw, min_col=4, max_col=5, min_row=dh, max_row=dh+6)
rcats = Reference(dw, min_col=2, max_col=2, min_row=dh+1, max_row=dh+6)
radar.add_data(rdata, titles_from_data=True); radar.set_categories(rcats)
radar.height = 8.5; radar.width = 11
dw.add_chart(radar, "B33")

# ======================================================================
# Sheet 4: Roadmap  (auto-ranked biggest gaps)
# ======================================================================
rw = wb.create_sheet("Roadmap")
rw.sheet_view.showGridLines = False
for col,w in {"A":3,"B":6,"C":11,"D":46,"E":9,"F":10,"G":16,"H":16,"I":20}.items():
    rw.column_dimensions[col].width = w
rw.merge_cells("B2:I2")
rt = rw.cell(row=2, column=2, value="Prioritised Remediation Roadmap")
rt.font = hfont(15, NAVY); rw.row_dimensions[2].height = 24
rw.cell(row=3, column=2, value="The highest-gap, highest-priority subcategories, worst first. "
        "Fill in Owner / Effort / Target date.").font = bfont(10, "595959", italic=True)

rh = 5
rheaders = ["", "Rank", "ID", "Outcome", "Gap", "Priority", "Owner", "Effort (S/M/L)", "Target date"]
for i,h in enumerate(rheaders, start=1):
    c = rw.cell(row=rh, column=i, value=h)
    c.font = hfont(10); c.fill = PatternFill("solid", fgColor=BLUE)
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True); c.border = border
rw.row_dimensions[rh].height = 22

# Build the ranked list in Python (by priority weight then gap) so it's stable,
# but keep the Gap/Priority as live links back to the Assessment sheet.
def weight(item):
    _,_,cur,tgt,_ = item
    gap = max(0, tgt-cur)
    return gap + (4-cur)/2
ranked = sorted(
    [(idx, s) for idx, s in enumerate(SUBCATEGORIES)],
    key=lambda t: weight(t[1]), reverse=True)
top = [t for t in ranked if max(0, t[1][3]-t[1][2]) > 0][:25]

rr = rh + 1
for rank, (idx, (sid, outcome, cur, tgt, note)) in enumerate(top, start=1):
    arow = start + idx  # matching row on Assessment sheet
    rw.cell(row=rr, column=2, value=rank).font = bfont(10, bold=True)
    rw.cell(row=rr, column=2).alignment = Alignment(horizontal="center")
    rw.cell(row=rr, column=3, value=sid).font = bfont(10, NAVY, True)
    oc = rw.cell(row=rr, column=4, value=outcome); oc.font = bfont(9)
    oc.alignment = Alignment(wrap_text=True, vertical="top")
    rw.cell(row=rr, column=5, value=f"=Assessment!G{arow}").alignment = Alignment(horizontal="center")
    rw.cell(row=rr, column=6, value=f"=Assessment!H{arow}").alignment = Alignment(horizontal="center")
    for col in (7,8,9):
        ic = rw.cell(row=rr, column=col); ic.fill = PatternFill("solid", fgColor=INPUT)
        ic.border = border
    for col in range(2,10):
        rw.cell(row=rr, column=col).border = border
    rw.row_dimensions[rr].height = 28
    rr += 1

rw.conditional_formatting.add(f"F{rh+1}:F{rr-1}",
    CellIsRule(operator="equal", formula=['"High"'],
               fill=PatternFill("solid", fgColor="F4CCCC"), font=Font(name=FONT, color="990000", bold=True)))
rw.conditional_formatting.add(f"F{rh+1}:F{rr-1}",
    CellIsRule(operator="equal", formula=['"Medium"'],
               fill=PatternFill("solid", fgColor="FCE5CD"), font=Font(name=FONT, color="996600", bold=True)))

# ----
outpath = os.path.join(os.path.dirname(__file__), "..", "assessment", "CSF2.0_Maturity_Assessment.xlsx")
outpath = os.path.abspath(outpath)
wb.save(outpath)
print("Saved:", outpath)
print(f"Assessment rows: {start}..{last}  ({last-start+1} subcategories)")
print(f"Roadmap items: {len(top)}")
