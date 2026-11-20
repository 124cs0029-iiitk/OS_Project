"""Build an illustrated copy of the report from its text draft and generated figures."""
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt
from docx.text.paragraph import Paragraph
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


ROOT = Path(__file__).resolve().parents[2]
FIGURES = ROOT / "results" / "images"
SOURCE = ROOT / "reports" / "DBDAA_Enhancement_Study_Revised.docx"
OUTPUT = ROOT / "reports" / "DBDAA_Enhancement_Study_Illustrated_Revised.docx"


def set_columns(section, count):
    columns = section._sectPr.xpath("./w:cols")
    spec = columns[0] if columns else OxmlElement("w:cols")
    if not columns:
        section._sectPr.append(spec)
    spec.set(qn("w:num"), str(count))
    spec.set(qn("w:space"), "360")


def add_after(element, doc, text=None, style=None, image=None, width=None):
    paragraph_element = OxmlElement("w:p")
    element.addnext(paragraph_element)
    paragraph = Paragraph(paragraph_element, doc._body)
    if style:
        paragraph.style = style
    if image:
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragraph.add_run().add_picture(str(image), width=width)
    if text:
        paragraph.add_run(text)
    return paragraph


def add_caption(doc, text):
    paragraph = doc.add_paragraph(style="figure caption")
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.add_run(text)
    return paragraph


def add_picture(doc, filename, caption, width=3.12):
    doc.add_picture(str(FIGURES / filename), width=Inches(width))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_caption(doc, caption)


def add_full_width_picture(doc, filename, caption, width=5.95):
    doc.add_picture(str(FIGURES / filename), width=Inches(width))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_caption(doc, caption)


def insert_body_text_after(element, doc, text):
    paragraph = add_after(element, doc, text=text, style="Body Text")
    paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    return paragraph


def insert_picture_after(element, doc, filename, caption):
    picture = add_after(
        element, doc, image=FIGURES / filename, width=Inches(3.12)
    )
    picture.alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption_paragraph = add_after(picture._p, doc, text=caption, style="figure caption")
    caption_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    return caption_paragraph


def main():
    if not SOURCE.exists():
        raise FileNotFoundError("Create the text report first: %s" % SOURCE)
    required = [
        "paper_dataset_checks.png",
        "scaling_checks.png",
        "workload_total_work.png",
        "workload_safety_checks.png",
        "starvation_wait.png",
        "runtime_small_workloads.png",
        "high_dimension_runtime.png",
        "adaptive_sensitivity.png",
        "aging_sensitivity.png",
        "dbdaa_baseline_flowchart.png",
        "enhanced_final_flowchart.png",
    ]
    missing = [name for name in required if not (FIGURES / name).exists()]
    if missing:
        raise FileNotFoundError("Generate evidence figures first: %s" % ", ".join(missing))

    doc = Document(str(SOURCE))
    # Keep the source report untouched and produce a separate illustrated deliverable.
    for paragraph in list(doc.paragraphs):
        if paragraph.text.strip().upper() == "REFERENCES":
            paragraph._p.getparent().remove(paragraph._p)
        elif paragraph.text.startswith("[1] M. F. Zohora"):
            paragraph._p.getparent().remove(paragraph._p)

    result_tables = [
        table for table in doc.tables
        if table.rows and table.rows[0].cells[0].text in ("Dataset", "Workload", "Scenario", "Processes")
    ]
    if len(result_tables) != 5:
        raise ValueError("Expected five result tables in the source report")

    # Add the main evidence plots beside the corresponding discussion tables.
    caption = insert_picture_after(
        result_tables[0]._tbl, doc, "paper_dataset_checks.png",
        "Fig. 1. Safety-check comparisons on the paper datasets."
    )
    text = insert_body_text_after(
        caption._p, doc,
        "Fig. 2 shows generated systems with low resource headroom (slack = 3) and high "
        "resource headroom (slack = 12). At n = 200, Enhanced uses 5,653 comparisons "
        "versus 8,474 for DBDAA in the low-headroom case, and 3,423 versus 4,434 in the "
        "high-headroom case. Traditional Banker counts remain substantially higher."
    )
    caption = insert_picture_after(
        text._p, doc, "scaling_checks.png",
        "Fig. 2. Safety-check comparisons as process count grows (log scale)."
    )
    caption = insert_picture_after(
        result_tables[1]._tbl, doc, "workload_total_work.png",
        "Fig. 3. Total counted work includes safety checks and queue-order comparisons."
    )
    insert_picture_after(
        caption._p, doc, "workload_safety_checks.png",
        "Fig. 4. Safety-check comparisons alone; ordering work is excluded."
    )
    insert_picture_after(
        result_tables[2]._tbl, doc, "starvation_wait.png",
        "Fig. 5. Heavy-process and maximum waiting under repeated overtaking."
    )
    insert_picture_after(
        result_tables[3]._tbl, doc, "runtime_small_workloads.png",
        "Fig. 6. Mean runtime on seven small-workload families."
    )
    insert_picture_after(
        result_tables[4]._tbl, doc, "high_dimension_runtime.png",
        "Fig. 7. Median runtime for high-dimensional safe systems (log scale)."
    )

    # The source body is two-column. Put full-sized flowcharts and sensitivity figures
    # on their own one-column appendix pages so labels remain readable.
    appendix = doc.add_section(WD_SECTION.NEW_PAGE)
    set_columns(appendix, 1)
    heading = doc.add_paragraph("APPENDIX A. ALGORITHM FLOWCHARTS", style="Heading 1")
    heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_full_width_picture(
        doc, "dbdaa_baseline_flowchart.png",
        "Fig. 8. DBDAA baseline flowchart from the project."
    )
    doc.add_page_break()
    add_full_width_picture(
        doc, "enhanced_final_flowchart.png",
        "Fig. 9. Final Enhanced DBDAA flowchart; idle retry is used for fair comparison."
    )
    doc.add_page_break()
    heading = doc.add_paragraph("APPENDIX B. PARAMETER SENSITIVITY", style="Heading 1")
    heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph = doc.add_paragraph(style="Body Text")
    paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    paragraph.add_run(
        "Negative adaptive-check percentages mean fewer checks than DBDAA. The selected "
        "(2, 4) setting is highlighted. The aging plot compares overtaking thresholds; "
        "the report uses a threshold of five and a probe gap of five."
    )
    add_full_width_picture(
        doc, "adaptive_sensitivity.png",
        "Fig. 10. Adaptive-check sensitivity across the paper and generated scenarios."
    )
    add_full_width_picture(
        doc, "aging_sensitivity.png",
        "Fig. 11. Heavy-process waiting by aging threshold and probe interval."
    )

    references = doc.add_section(WD_SECTION.NEW_PAGE)
    set_columns(references, 2)
    doc.add_paragraph("REFERENCES", style="Heading 1")
    doc.add_paragraph(
        "[1] M. F. Zohora, F. Farhin, and M. S. Kaiser, "
        "\"DBDAA: A real-time approach to Dynamic Banker's Deadlock Avoidance Algorithm "
        "with optimized time complexity,\" PLoS ONE, vol. 19, no. 9, Art. no. e0310807, "
        "Sep. 2024, doi: 10.1371/journal.pone.0310807.",
        style="references",
    )

    if len(doc.sections) != 4:
        raise AssertionError("Expected title, body, appendix, and references sections")
    set_columns(doc.sections[0], 1)
    set_columns(doc.sections[1], 2)
    set_columns(doc.sections[2], 1)
    set_columns(doc.sections[3], 2)
    doc.save(str(OUTPUT))

    check = Document(str(OUTPUT))
    text = "\n".join(paragraph.text for paragraph in check.paragraphs)
    for number in range(1, 12):
        if "Fig. %d." % number not in text:
            raise AssertionError("Missing figure caption %d" % number)
    if len(check.inline_shapes) != 11:
        raise AssertionError("Expected 11 inline figures, found %d" % len(check.inline_shapes))
    print("Created illustrated report:", OUTPUT)
    print("Inline figures:", len(check.inline_shapes), "sections:", len(check.sections))


if __name__ == "__main__":
    main()
