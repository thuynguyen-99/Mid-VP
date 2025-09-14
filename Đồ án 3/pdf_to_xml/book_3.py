from pypdf import PdfReader
from lxml import etree
import re
from helper import (
    clean_page_text,
    split_into_paragraphs_optimized,
    create_dtbook_structure,
    validate_dtbook,
)

pdf_path = "thanhcattuhan.pdf"
xml_path = "thanhcattuhan.xml"
book_info = {
    "title": "Thành Cát Tư Hãn và Sự hình thành thế giới hiện đại",
    "author": "Jack Weatherford",
    "publisher": "Nhà Xuất BảnKhoa học Xã hội",
    "date": "14/07/2018",
    "description": "Thành Cát Tư Hãn và Sự hình thành thế giới hiện đại của Jack Weatherford là cuốn sách lịch sử hấp dẫn, nhìn lại cuộc đời và di sản của vị đại hãn Mông Cổ. Không chỉ khắc họa một nhân vật lẫy lừng trong chiến trận, tác phẩm còn cho thấy ảnh hưởng sâu rộng của đế chế Mông Cổ trong việc định hình thương mại, văn hóa và trật tự thế giới hiện đại.",
    "subject": "Lịch sử",
    "language": "vi-VN",
    "identifier": "urn:isbn:8935270703943",
    "total_page_count": "469",
}


def get_expected_sections_from_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    if not hasattr(reader, "outline") or not reader.outline:
        print("No outline found.")
        return []

    hierarchical_sections = [
        {
            "title": "LỜI TỰA CỦA TÁC GIẢ (cho ấn bản tại Việt Nam)",
            "level": 1,
            "id": "loi_tua",
        },
        {"title": "MỞ ĐẦU: Nhà chinh phục mất tích", "level": 1, "id": "mo_dau"},
        {
            "title": "PHẦN I NỖI KINH HOÀNG NGỰ TRỊ THẢO NGUYÊN: 1162-1206",
            "level": 1,
            "id": "phan_1",
        },
        {"title": "1 CỤC MÁU ĐÔNG", "level": 2, "id": "chuong_1", "parent": "phan_1"},
        {
            "title": "2 CÂU CHUYỆN BA CON SÔNG",
            "level": 2,
            "id": "chuong_2",
            "parent": "phan_1",
        },
        {
            "title": "3 CHIẾN TRANH GIỮA CÁC HÃN",
            "level": 2,
            "id": "chuong_3",
            "parent": "phan_1",
        },
        {"title": "PHẦN II THẾ CHIẾN MÔNG CỔ: 1211-1261", "level": 1, "id": "phan_2"},
        {
            "title": "4 SỈ NHỤC VỊ HOÀNG HÃN",
            "level": 2,
            "id": "chuong_4",
            "parent": "phan_2",
        },
        {
            "title": "5 SULTAN ĐỐI ĐẦU VỚI KHẮC HÃN",
            "level": 2,
            "id": "chuong_5",
            "parent": "phan_2",
        },
        {
            "title": "6 KHÁM PHÁ VÀ CHINH PHỤC CHÂU ÂU",
            "level": 2,
            "id": "chuong_6",
            "parent": "phan_2",
        },
        {
            "title": "7 CHIẾN TRANH GIỮA CÁC HOÀNG HẬU",
            "level": 2,
            "id": "chuong_7",
            "parent": "phan_2",
        },
        {
            "title": "PHẦN III Thế giới Thức tỉnh: 1262 – 1962",
            "level": 1,
            "id": "phan_3",
        },
        {
            "title": "8 HÃN HỐT TẤT LIỆT VÀ ĐẾ CHẾ MÔNG CỔ MỚI",
            "level": 2,
            "id": "chuong_8",
            "parent": "phan_3",
        },
        {
            "title": "9 ÁNH DƯƠNG HOÀNG KIM CỦA HỌ",
            "level": 2,
            "id": "chuong_9",
            "parent": "phan_3",
        },
        {
            "title": "10 ĐẾ CHẾ ẢO ẢNH",
            "level": 2,
            "id": "chuong_10",
            "parent": "phan_3",
        },
        {
            "title": "LỜI BẠT: Tinh thần bất diệt của Thành Cát Tư Hãn",
            "level": 1,
            "id": "loi_bat",
        },
    ]

    return hierarchical_sections


expected_sections = get_expected_sections_from_pdf(pdf_path)


def detect_section(text):
    text = text.strip().upper()

    for section in expected_sections:
        title = section["title"].strip()

        if title.upper() in text:
            return section

        if "PHẦN" in title:
            if "PHẦN I" in title and ("PHẦN I" in text or "PHẦN 1" in text):
                return section
            elif "PHẦN II" in title and ("PHẦN II" in text or "PHẦN 2" in text):
                return section
            elif "PHẦN III" in title and ("PHẦN III" in text or "PHẦN 3" in text):
                return section

        elif "MỞ ĐẦU" in title and "MỞ ĐẦU" in text:
            return section
        elif "LỜI TỰA" in title and "LỜI TỰA" in text:
            return section
        elif "LỜI BẠT" in title and "LỜI BẠT" in text:
            return section

        elif title[0].isdigit():
            chapter_num = title.split()[0]
            if re.search(rf"^{re.escape(chapter_num)}\s+", text):
                title_words = title.split()[1:3]
                if any(word.upper() in text for word in title_words if len(word) > 2):
                    return section

    return None


def pdf_to_dtbook_optimized(pdf_path: str, out_path: str) -> str:
    reader = PdfReader(pdf_path)

    dtbook, head = create_dtbook_structure(book_info)
    book = etree.SubElement(dtbook, "book")

    bodymatter = etree.SubElement(book, "bodymatter", id="bodymatter")

    current_section_idx = -1
    current_level = bodymatter
    level_stack = []  # Stack để theo dõi các level đang mở
    section_elements = {}

    level1_elements = {}
    for section in expected_sections:
        if section["level"] == 1:
            level1 = etree.SubElement(bodymatter, "level1", id=section["id"])
            h1 = etree.SubElement(level1, "h1", id=f"h1_{section['id']}")
            h1.text = section["title"]
            level1_elements[section["id"]] = level1

    print("📖 Đang xử lý từng trang...")

    for i, page in enumerate(reader.pages, start=1):
        if i <= 2:
            continue  # Bỏ qua 2 trang đầu
        if i > 469:
            break  # Dừng ở trang 469
        if i % 50 == 0:
            print(f"   📄 Đã xử lý {i} trang...")

        raw_text = page.extract_text() or ""
        text = clean_page_text(raw_text, book_info)
        if not text.strip():
            continue

        detected_section = detect_section(text)
        if detected_section:
            for idx, section in enumerate(expected_sections):
                if (
                    detected_section["title"] == section["title"]
                    and idx > current_section_idx
                ):
                    current_section_idx = idx
                    section_level = section["level"]
                    section_id = section["id"]

                    if section_level == 1:
                        current_level = level1_elements[section_id]
                        level_stack = [{"level": 1, "element": current_level}]
                    elif section_level == 2:
                        parent_id = section.get("parent")
                        if parent_id and parent_id in level1_elements:
                            parent_level = level1_elements[parent_id]
                            level2 = etree.SubElement(
                                parent_level, "level2", id=section_id
                            )
                            h2 = etree.SubElement(level2, "h2", id=f"h2_{section_id}")
                            h2.text = section["title"]
                            current_level = level2
                            level_stack = [
                                {"level": 1, "element": parent_level},
                                {"level": 2, "element": level2},
                            ]

                    section_elements[idx] = current_level
                    print(
                        f"   ✅ Tìm thấy: {section['title']} (level {section['level']}, index {idx})"
                    )
                    break

        pagenum = etree.SubElement(current_level, "pagenum", id=f"page_{i}")
        pagenum.text = str(i)

        content_text = (
            text.replace(f"{detected_section['title']} ", "").strip()
            if detected_section
            else text
        )
        paragraphs = split_into_paragraphs_optimized(content_text, 10)

        for para_text in paragraphs:
            if para_text.strip():
                p = etree.SubElement(current_level, "p")
                p.text = para_text

    tree = etree.ElementTree(dtbook)
    tree.write(out_path, encoding="utf-8", xml_declaration=True, pretty_print=True)

    print("\n✅ Đã chuyển đổi thành công!")
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
