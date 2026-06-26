from __future__ import annotations

from datetime import datetime
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet


def create_pdf_report(title: str, content: str, output_dir: str = "reports") -> str:
    Path(output_dir).mkdir(exist_ok=True)
    filename = f"documind_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    path = str(Path(output_dir) / filename)

    doc = SimpleDocTemplate(path, pagesize=A4)
    styles = getSampleStyleSheet()
    story = [Paragraph(title, styles["Title"]), Spacer(1, 12)]
    for line in content.split("\n"):
        safe_line = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        story.append(Paragraph(safe_line if safe_line.strip() else " ", styles["BodyText"]))
        story.append(Spacer(1, 6))
    doc.build(story)
    return path
