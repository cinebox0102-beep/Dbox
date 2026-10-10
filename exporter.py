import csv
from pathlib import Path
from datetime import datetime

def export_csv(products, folder="."):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"beep_estoque_{datetime.now():%Y%m%d_%H%M%S}.csv"
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["ID","Produto","Código de barras","Descrição","Quantidade","Estoque mínimo","Validade"])
        for p in products:
            writer.writerow([p["id"],p["name"],p.get("barcode") or "",p.get("description") or "",
                             p["quantity"],p["min_stock"],p.get("expiry") or ""])
    return str(path.resolve())

def export_pdf(products, folder="."):
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
    except ImportError:
        raise RuntimeError("Para exportar PDF, instale reportlab: pip install reportlab")
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"beep_estoque_{datetime.now():%Y%m%d_%H%M%S}.pdf"
    doc = SimpleDocTemplate(str(path), pagesize=landscape(A4))
    styles = getSampleStyleSheet()
    data = [["Produto","Código","Qtd.","Mínimo","Validade"]]
    for p in products:
        data.append([p["name"], p.get("barcode") or "-", str(p["quantity"]), str(p["min_stock"]), p.get("expiry") or "-"])
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#17365D")),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("GRID",(0,0),(-1,-1),0.4,colors.grey),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#EFF5FB")]),
        ("PADDING",(0,0),(-1,-1),7),
    ]))
    doc.build([Paragraph("Beep Estoque Pro 2.0 — Relatório de estoque", styles["Title"]), Spacer(1,12), table])
    return str(path.resolve())
