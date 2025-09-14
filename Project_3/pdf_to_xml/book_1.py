from pypdf import PdfReader
from lxml import etree
import re
from math import ceil
from copy import deepcopy
import os
from helper import (
    clean_page_text,
    split_into_paragraphs_optimized,
    create_dtbook_structure,
    validate_dtbook,
)
from pathlib import Path


pdf_path = Path(__file__).parent.parent / "data" / "ho_quy_ly.pdf"
xml_path = "HoQuyLy.xml"
book_info = {
    "title": "Hồ Quý Ly",
    "author": "Nguyễn Xuân Khánh",
    "publisher": "Nhà Xuất Bản Phụ Nữ Việt Nam",
    "date": "2025",
    "description": "Hồ Quý Ly của Nguyễn Xuân Khánh là một tiểu thuyết lịch sử nổi bật, tái hiện bối cảnh đầy biến động của xã hội Việt Nam cuối thế kỷ XIV – đầu thế kỷ XV. Tác phẩm khắc họa những nhân vật, sự kiện và tư tưởng xoay quanh triều đại nhà Trần cùng quá trình chuyển giao quyền lực sang nhà Hồ.",
    "subject": "Tiểu thuyết",
    "language": "vi-VN",
    "identifier": "urn:isbn:9786044727998",
    "total_page_count": "547",
}


def get_expected_sections_from_pdf(pdf_path):
    """Get list of sections from PDF outline"""
    reader = PdfReader(pdf_path)
    if not hasattr(reader, "outline") or not reader.outline:
        print("No outline found.")
        return []
    outlines = reader.outline
    sections = []

    def walk(items):
        for item in items:
            if isinstance(item, list):
                walk(item)
            else:
                title = getattr(item, "title", None) or item.get("/Title")
                if title:
                    sections.append(title.strip())

    walk(outlines)
    return sections


expected_sections = get_expected_sections_from_pdf(pdf_path)


def detect_section(text):
    text = text.strip()
    for section in expected_sections:
        pattern = r"^" + re.escape(section.strip())
        if re.search(pattern, text, re.IGNORECASE):
            return section
    return None


def pdf_to_dtbook_optimized(
    pdf_path: str, out_path: str, sections_per_file: int = None
) -> str | list[str]:
    """Chuyển đổi PDF sang DTBook, có thể tách ra nhiều file theo N chương"""

    reader = PdfReader(pdf_path)

    total_sections = len(expected_sections)
    num_parts = ceil(total_sections / sections_per_file)
    os.makedirs("dtbook_parts", exist_ok=True)

    parts = []
    for part_idx in range(num_parts):
        start_idx = part_idx * sections_per_file
        end_idx = min(total_sections, (part_idx + 1) * sections_per_file)
        part_sections = expected_sections[start_idx:end_idx]

        bi = deepcopy(book_info)
        bi["identifier"] = f"{book_info['identifier']}-p{part_idx + 1:02d}"

        dtbook, head = create_dtbook_structure(bi)
        book = etree.SubElement(dtbook, "book")
        bodymatter = etree.SubElement(
            book, "bodymatter", id=f"bodymatter_p{part_idx + 1:02d}"
        )

        section_elements = {}
        for i, section_title in enumerate(part_sections, start=start_idx):
            level1 = etree.SubElement(bodymatter, "level1", id=f"sec_{i + 1}")
            h1 = etree.SubElement(level1, "h1", id=f"h1_{i + 1}")
            h1.text = section_title
            section_elements[i] = level1

        outfile = os.path.join("dtbook_parts", f"part_{part_idx + 1:02d}.xml")
        parts.append(
            {"dtbook": dtbook, "section_elements": section_elements, "outfile": outfile}
        )

    current_section_idx = 0
    current_file_idx = 0
    current_level = parts[current_file_idx]["section_elements"][current_section_idx]

    for i, page in enumerate(reader.pages, start=1):
        if i <= 4:
            continue
        if i % 50 == 0:
            print(f"   📄 Đã xử lý {i} trang...")

        raw_text = page.extract_text() or ""
        text = clean_page_text(raw_text, book_info)
        if not text.strip():
            continue

        detected = detect_section(text)
        if detected:
            for idx, sec in enumerate(expected_sections):
                if detected == sec and idx >= current_section_idx:
                    current_section_idx = idx
                    current_file_idx = current_section_idx // sections_per_file
                    current_level = parts[current_file_idx]["section_elements"][
                        current_section_idx
                    ]
                    break

        pagenum = etree.SubElement(current_level, "pagenum", id=f"page_{i}")
        pagenum.text = str(i)

        content_text = text.replace(f"{detected} ", "").strip() if detected else text
        paragraphs = split_into_paragraphs_optimized(content_text, 10)

        for para_text in paragraphs:
            if para_text.strip():
                p = etree.SubElement(current_level, "p")
                p.text = para_text

    outputs = []
    for part in parts:
        tree = etree.ElementTree(part["dtbook"])
        tree.write(
            part["outfile"], encoding="utf-8", xml_declaration=True, pretty_print=True
        )
        outputs.append(part["outfile"])
        print(f"📁 Đã xuất: {part['outfile']}")
        try:
            validate_dtbook(part["outfile"])
        except Exception as ve:
            print(f"Validate lỗi cho {part['outfile']}: {ve}")

    print(f"📄 Tổng số trang PDF: {len(reader.pages)}")

    return outputs


if __name__ == "__main__":
    try:
        output_file = pdf_to_dtbook_optimized(pdf_path, xml_path, 10)

    except Exception as e:
        print(f"Error: {e}")
