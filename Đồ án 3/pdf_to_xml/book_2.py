
from pypdf import PdfReader
from lxml import etree
import re
import math
import uuid
from helper import clean_page_text, split_into_paragraphs_optimized, create_dtbook_structure, validate_dtbook

book_info = {
    "title": "Điệp Viên Hoàn Hảo",
    "author": "Larry Berman",
    "publisher": "Chuyển đổi từ PDF",
    "date": "2025",
    "description": "Sách điện tử định dạng DTBook DAISY 3.0",
    "subject": "Tiểu thuyết",
    "language": "vi-VN",
    "identifier": f"dtb-{uuid.uuid4()}",
    "total_page_count": "657"
}


def detect_section(text):
    """Phát hiện section dựa trên pattern trong text"""
    text = text.strip()

    # Danh sách sections với pattern matching
    section_patterns = [
        (r"^(LỜI TỰA|Lời Tựa)", "Lời Tựa"),
        (r"^(MỞ ĐẦU|Mở Đầu)", "Mở Đầu - Giờ Thì Tôi Có Thể Thanh Thản Ra Đi Được Rồi"),
        (r"^(CHƯƠNG 1|Chương 1)", "Chương 1 - Hoà Bình, Nhà Tình Báo Và Người Bạn"),
        (r"^(CHƯƠNG 2|Chương 2)", "Chương 2 - Thời Gian Học Nghề Của Một Điệp Viên"),
        (r"^(CHƯƠNG 3|Chương 3)", "Chương 3 - California Rộng Mở"),
        (r"^(CHƯƠNG 4|Chương 4)", "Chương 4 - Sự Xuất Hiện Của Một Cuộc Đời Hai Mặt"),
        (r"^(CHƯƠNG 5|Chương 5)", "Chương 5 - Từ Tạp Chí Time Đến Tết Mậu Thân"),
        (r"^(CHƯƠNG 6|Chương 6)", "Chương 6 - Những vai trò mập mờ: tháng 4/1975"),
        (r"^(CHƯƠNG 7|Chương 7)", "Chương 7 - Dưới Bóng Người Cha"),
        (r"^(CHƯƠNG KẾT|Chương kết)", "Chương kết - Một Cuộc Đời Hai Mặt Khác Thường"),
        (r"^(LỜI CẢM ƠN|Lời Cám Ơn)", "Lời Cám Ơn")
    ]

    for pattern, section_name in section_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return section_name

    return None

def pdf_to_dtbook_optimized(pdf_path, out_path):
    """Chuyển đổi PDF sang DTBook với sections cố định và paragraphs optimized"""
    reader = PdfReader(pdf_path)

    dtbook, head = create_dtbook_structure(book_info)
    book = etree.SubElement(dtbook, "book")

    # Danh sách 11 sections đúng thứ tự
    expected_sections = [
        "Lời Tựa",
        "Mở Đầu - Giờ Thì Tôi Có Thể Thanh Thản Ra Đi Được Rồi",
        "Chương 1 - Hoà Bình, Nhà Tình Báo Và Người Bạn",
        "Chương 2 - Thời Gian Học Nghề Của Một Điệp Viên",
        "Chương 3 - California Rộng Mở",
        "Chương 4 - Sự Xuất Hiện Của Một Cuộc Đời Hai Mặt",
        "Chương 5 - Từ Tạp Chí Time Đến Tết Mậu Thân",
        "Chương 6 - Những vai trò mập mờ: tháng 4/1975",
        "Chương 7 - Dưới Bóng Người Cha",
        "Chương kết - Một Cuộc Đời Hai Mặt Khác Thường",
        "Lời Cám Ơn"
    ]

    # Tạo containers
    frontmatter = etree.SubElement(book, "frontmatter", id="frontmatter")
    bodymatter = etree.SubElement(book, "bodymatter", id="bodymatter")
    backmatter = etree.SubElement(book, "backmatter", id="backmatter")

    # Tạo trước tất cả sections
    section_elements = {}
    for i, section_title in enumerate(expected_sections):
        # Xác định container
        if i == 0:  # Lời Tựa
            container = frontmatter
        elif i == 10:  # Lời Cám Ơn
            container = backmatter
        else:  # Các chương
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
        if i % 50 == 0:
            print(f"   📄 Đã xử lý {i}/657 trang...")

        raw_text = page.extract_text() or ""
        text = clean_page_text(raw_text, book_info)
        if not text.strip():
            continue

        # Kiểm tra section mới
        detected_section = detect_section(text)
        if detected_section:
            for idx, section in enumerate(expected_sections):
                if detected_section == section:
                    if idx > current_section_idx:
                        current_section_idx = idx
                        current_level = section_elements[idx]
                        print(f"   ✅ Tìm thấy: {section}")
                    break

        # Thêm pagenum
        pagenum = etree.SubElement(current_level, "pagenum", id=f"page_{i}")
        pagenum.text = str(i)

        # Chia thành paragraphs 3-4 câu
        paragraphs = split_into_paragraphs_optimized(text, 4)

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
    pdf_path = "/Users/thuynguyen/Downloads/c491ie1bb87p-vic3aan-hoc3a0n-he1baa3o-larry-berman.pdf"
    xml_path = "DiepVienHoanHao_Optimized.xml"
    try:
        output_file = pdf_to_dtbook_optimized(pdf_path, xml_path)
        validate_dtbook(output_file)


    except Exception as e:
        print(f"❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()