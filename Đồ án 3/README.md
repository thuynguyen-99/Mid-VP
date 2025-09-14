
# Đồ án 3: Xây dựng Sách Nói DAISY

## Tiền xử lý dữ liệu trước khi sử dụng ứng dụng `DAISY PIPELINE` để xây dựng sách

### 1. Chuyển đổi PDF sang DTBook(.xml)

- Có 3 file PDF đầu vào, mỗi file tương ứng với một sách:
  - Sách 1: Hồ Quý Ly
  - Sách 2: Điệp Viên Hoàn Hảo
  - Sách 3: Thành Cát Tư Hãn và sự hình thành thế giới hiện đại
- Mỗi sách có một script chuyển đổi riêng trong thư mục `pdf_to_xml` theo thứ tự: `book_1.py`, `book_2.py`, `book_3.py`

#### Đối với sách Hồ Quý Ly (54 chương):
- Do số chương lớn, script sẽ chia thành nhiều file XML, mỗi file chứa 10 chương (tức là 6 file XML cho 54 chương).
- Các file XML sẽ được lưu trong thư mục `dtbook_parts`.

Lệnh chạy:
```bash
python book_1.py  # Chuyển Hồ Quý Ly PDF sang nhiều file XML (10 chương/file)
python book_2.py  # Chuyển sách thứ 2
python book_3.py  # Chuyển sách thứ 3
```

### 2. Dùng `DAISY PIPELINE` để chuyển đổi từ DTBook sang DAISY
- Với sách thứ 2 và sách thứ 3, kết quả của bước này là hoàn thành.
- Với sách thứ 1 (Hồ Quý Ly), lưu tất cả các thư mục DAISY đã được hoàn thành vào 1 thư mục duy nhất, tiến hành bước 3 để hợp nhất thành 1 sách.

### 3. Xử lý đặc biệt với sách Hồ Quý Ly
- Sử dụng script `merge_daisy.py` để hợp nhất.
- Lệnh chạy:
```bash
python merge_daisy.py input output
```