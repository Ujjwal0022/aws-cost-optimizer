import io, csv, pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from app.models.schemas import ResourceSummaryResponse, CostSummaryResponse

def generate_csv(resource_data: ResourceSummaryResponse) -> bytes:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Resource ID","Type","Region","Issue","Savings/Month (USD)","Severity","Recommendation"])
    for rec in resource_data.recommendations:
        writer.writerow([rec.resource_id,rec.resource_type,rec.region,rec.issue,
                         rec.estimated_monthly_savings,rec.severity,rec.recommendation])
    return output.getvalue().encode("utf-8")

def generate_excel(resource_data: ResourceSummaryResponse, cost_data: CostSummaryResponse) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        pd.DataFrame([{"Metric":"MTD Cost","Value":cost_data.total_cost_mtd},
                      {"Metric":"Last Month","Value":cost_data.total_cost_last_month},
                      {"Metric":"Forecast","Value":cost_data.forecast_end_of_month}]
                    ).to_excel(writer, sheet_name="Cost Summary", index=False)
        pd.DataFrame([{"Service":s.service,"Cost":s.amount} for s in cost_data.top_services]
                    ).to_excel(writer, sheet_name="Top Services", index=False)
        pd.DataFrame([{"Date":d.date,"Cost":d.amount} for d in cost_data.daily_trend]
                    ).to_excel(writer, sheet_name="Daily Trend", index=False)
        pd.DataFrame([{"Resource ID":r.resource_id,"Type":r.resource_type,"Region":r.region,
                        "Issue":r.issue,"Savings/mo":r.estimated_monthly_savings,
                        "Severity":r.severity,"Recommendation":r.recommendation}
                       for r in resource_data.recommendations]
                    ).to_excel(writer, sheet_name="Recommendations", index=False)
    return output.getvalue()

def generate_pdf(resource_data: ResourceSummaryResponse, cost_data: CostSummaryResponse) -> bytes:
    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = [Paragraph("FinOps Cost Optimization Report", styles["Title"]), Spacer(1,12)]
    elements.append(Paragraph("Cost Summary", styles["Heading2"]))
    cost_tbl = Table([["Metric","Value (USD)"],
                       ["MTD Cost", f"${cost_data.total_cost_mtd:,.2f}"],
                       ["Last Month", f"${cost_data.total_cost_last_month:,.2f}"],
                       ["Forecast", f"${cost_data.forecast_end_of_month:,.2f}"],
                       ["Potential Savings", f"${resource_data.total_estimated_savings:,.2f}"]],
                      colWidths=[260,200])
    cost_tbl.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#2B6CB0")),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#EBF8FF")]),
        ("GRID",(0,0),(-1,-1),0.5,colors.grey),("PADDING",(0,0),(-1,-1),8)]))
    elements += [cost_tbl, Spacer(1,18), Paragraph("Recommendations", styles["Heading2"])]
    rows = [["Resource ID","Type","Region","Issue","Savings/mo","Severity"]]
    sev = {"HIGH":colors.HexColor("#FED7D7"),"MEDIUM":colors.HexColor("#FEFCBF"),"LOW":colors.HexColor("#C6F6D5")}
    for rec in resource_data.recommendations[:20]:
        rows.append([rec.resource_id[:20],rec.resource_type,rec.region,rec.issue,
                     f"${rec.estimated_monthly_savings:.2f}",rec.severity])
    rec_tbl = Table(rows, colWidths=[110,55,70,60,65,60])
    style = [("BACKGROUND",(0,0),(-1,0),colors.HexColor("#2B6CB0")),
             ("TEXTCOLOR",(0,0),(-1,0),colors.white),
             ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
             ("FONTSIZE",(0,0),(-1,-1),8),
             ("GRID",(0,0),(-1,-1),0.5,colors.grey),("PADDING",(0,0),(-1,-1),6)]
    for i, rec in enumerate(resource_data.recommendations[:20], start=1):
        style.append(("BACKGROUND",(0,i),(-1,i),sev.get(rec.severity,colors.white)))
    rec_tbl.setStyle(TableStyle(style))
    elements.append(rec_tbl)
    doc.build(elements)
    return output.getvalue()
