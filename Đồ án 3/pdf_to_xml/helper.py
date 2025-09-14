import re
from lxml import etree


def clean_page_text(text: str, book_info: dict[str, str]) -> str:
    """Làm sạch text từ PDF, loại bỏ header/footer và text không cần thiết"""
    lines = text.splitlines()
    cleaned = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Bỏ số trang
        if re.match(r"^\d+/\d+$", line):
            continue
        # Bỏ title lặp lại
        if book_info["title"] in line or book_info["author"] in line:
            continue
        # Bỏ footer
        line = re.sub(r"https://thuviensach.vn", "", line, flags=re.IGNORECASE)
        line = re.sub(r"Trang\s+\d+/\d+\s+http://\S+", "", line, flags=re.IGNORECASE)
        # Bỏ các ký tự đặc biệt không cần thiết
        line = re.sub(
            r"[^\w\s\.,!?;:()\-\"\'àáảãạầấẩẫậằắẳẵặèéẻẽẹềếểễệìíỉĩịòóỏõọồốổỗộờớởỡợùúủũụừứửữựỳýỷỹỵđĐ]",
            "",
            line,
        )
        if line.strip():
            cleaned.append(line)

    # Gộp lại và làm sạch khoảng trắng
    return re.sub(r"\s+", " ", " ".join(cleaned)).strip()


def split_into_paragraphs_optimized(text, sentences_per_paragraph=4):
    """Chia text thành các đoạn văn với 3-4 câu mỗi paragraph (optimized for memory)"""
    if not text.strip():
        return []

    # Chia thành câu (sử dụng regex đơn giản hơn)
    sentences = re.split(r"(?<=[.!?])\s+", text)

    paragraphs = []
    current_paragraph = []

    for sentence in sentences:
        if not sentence.strip():
            continue

        current_paragraph.append(sentence.strip())

        # Khi đủ 3-4 câu, tạo paragraph mới
        if len(current_paragraph) >= sentences_per_paragraph:
            paragraph_text = " ".join(current_paragraph)
            if paragraph_text.strip():
                paragraphs.append(paragraph_text)
            current_paragraph = []

    # Thêm paragraph cuối cùng nếu còn
    if current_paragraph:
        paragraph_text = " ".join(current_paragraph)
        if paragraph_text.strip():
            paragraphs.append(paragraph_text)

    # Nếu không chia được theo câu, chia theo từ (fallback)
    if not paragraphs:
        words = text.split()
        if words:
            # Chia thành chunks ~150-200 từ
            chunk_size = 150
            for i in range(0, len(words), chunk_size):
                chunk = " ".join(words[i : i + chunk_size])
                if chunk.strip():
                    paragraphs.append(chunk)

    return paragraphs


def create_dtbook_structure(book_info: dict[str, str]):
    """Tạo cấu trúc DTBook chuẩn cho DAISY 3.0"""
    NS = {"dtb": "http://www.daisy.org/z3986/2005/dtbook/"}
    dtbook = etree.Element(
        "dtbook",
        nsmap={None: NS["dtb"]},
        version="2005-3",
        **{"{http://www.w3.org/XML/1998/namespace}lang": book_info["language"]},
    )

    head = etree.SubElement(dtbook, "head")

    meta_items = [
        ("dc:Title", book_info["title"]),
        ("dc:Creator", book_info["author"]),
        ("dc:Subject", book_info["subject"]),
        ("dc:Description", book_info["description"]),
        ("dc:Publisher", book_info["publisher"]),
        ("dc:Date", book_info["date"]),
        ("dc:Format", "DAISY 3.0"),
        ("dc:Identifier", book_info["identifier"]),
        ("dc:Language", book_info["language"]),
        # ("dtb:multimediaType", "textOnly"),
        # ("dtb:multimediaContent", "text"),
        # ("dtb:totalPageCount", book_info["total_page_count"]),
    ]

    for name, content in meta_items:
        etree.SubElement(head, "meta", name=name, content=content)

    return dtbook, head


def validate_dtbook(xml_path):
    """Kiểm tra DTBook file"""
    try:
        tree = etree.parse(xml_path)
        root = tree.getroot()

        print("\n🔍 KIỂM TRA FILE DTBOOK:")
        print(f"✅ File XML hợp lệ")

        ns = {"dtb": "http://www.daisy.org/z3986/2005/dtbook/"}

        # Đếm elements quan trọng
        counts = {
            "level1": len(root.xpath(".//dtb:level1", namespaces=ns)),
            "p": len(root.xpath(".//dtb:p", namespaces=ns)),
            "pagenum": len(root.xpath(".//dtb:pagenum", namespaces=ns)),
        }

        print(f"📊 Thống kê:")
        for elem, count in counts.items():
            print(f"   {elem}: {count}")

        # Liệt kê sections
        h1_elements = root.xpath(".//dtb:h1", namespaces=ns)
        print(f"\n📖 CÁC SECTIONS ĐƯỢC TẠO:")
        for i, h1 in enumerate(h1_elements, 1):
            text = h1.text or "Không có text"
            print(f"   {i}. {text}")

        return True

    except Exception as e:
        print(f"❌ Lỗi khi kiểm tra file: {e}")
        return False
