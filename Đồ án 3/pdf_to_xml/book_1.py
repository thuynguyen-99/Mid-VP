from pypdf import PdfReader
from lxml import etree
import re
import sys
import os
from helper import clean_page_text, split_into_paragraphs_optimized, create_dtbook_structure, validate_dtbook

pdf_path = "/Users/thuynguyen/Documents/Mid-VP/Đồ án 3/Hồ_quý_ly/ho_quy_ly.pdf"
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
    "total_page_count": "547"
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
                title = getattr(item, 'title', None) or item.get('/Title')
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

def pdf_to_dtbook_optimized(pdf_path: str, out_path: str) -> str:
    """Chuyển đổi PDF sang DTBook với sections cố định và paragraphs optimized"""
    reader = PdfReader(pdf_path)

    dtbook, head = create_dtbook_structure(book_info)
    book = etree.SubElement(dtbook, "book")

    # Tạo containers
    bodymatter = etree.SubElement(book, "bodymatter", id="bodymatter")

    # Tạo trước tất cả sections
    section_elements = {}
    for i, section_title in enumerate(expected_sections):
        container = bodymatter
        # Tạo level1 cho section
        level1 = etree.SubElement(container, "level1", id=f"sec_{i+1}")
        h1 = etree.SubElement(level1, "h1", id=f"h1_{i+1}")
        h1.text = section_title
        section_elements[i] = level1

    # Biến theo dõi
    current_section_idx = 0
    current_level = section_elements[0]
    print("📖 Đang xử lý từng trang...")

    # Xử lý từng trang
    for i, page in enumerate(reader.pages, start=1):
        if i <= 4:
            continue  # Bỏ qua 4 trang đầu
        if i % 50 == 0:
            print(f"   📄 Đã xử lý {i} trang...")

        raw_text = page.extract_text() or ""
        text = clean_page_text(raw_text, book_info)
        if not text.strip():
            continue

        # Kiểm tra section mới
        detected_section = detect_section(text)
        if detected_section:
            # Luôn gán vào section theo thứ tự xuất hiện
            for idx, section in enumerate(expected_sections):
                if detected_section == section and idx >= current_section_idx:
                    current_section_idx = idx
                    current_level = section_elements[idx]
                    print(f"   ✅ Tìm thấy: {section} (index {idx})")
                    break

        # Thêm pagenum
        pagenum = etree.SubElement(current_level, "pagenum", id=f"page_{i}")
        pagenum.text = str(i)

        # Chia thành paragraphs 3-4 câu
        paragraphs = split_into_paragraphs_optimized(text.replace(f"{detected_section} ", "").strip() if detected_section else text, 4)

        for para_text in paragraphs:
            if para_text.strip():
                p = etree.SubElement(current_level, "p")
                p.text = para_text

    # Ghi file
    tree = etree.ElementTree(dtbook)
    tree.write(out_path, encoding="utf-8", xml_declaration=True, pretty_print=True)

    print(f"\n✅ Đã chuyển đổi thành công!")
    print(f"📁 File output: {out_path}")
    print(f"📄 Tổng số trang: {len(reader.pages)}")
    print(f"📚 Số sections: {len(expected_sections)}")

    return out_path



if __name__ == "__main__":
    try:
        output_file = pdf_to_dtbook_optimized(pdf_path, xml_path)
        validate_dtbook(output_file)

    except Exception as e:
        print(f"Error: {e}")
