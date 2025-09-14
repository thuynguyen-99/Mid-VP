
# Đồ án 2: Thống kê & Phân tích Âm Tiết Tiếng Việt

## Dữ liệu

Phân tích và thống kê âm tiết tiếng Việt dựa trên dữ liệu từ điển (`VDic_uni.txt`) với `37464` dòng.

## Chức năng chính

- **Thống kê số lượng âm tiết thực tế** từ từ điển.
- **Tính số lượng âm tiết khả dĩ** dựa trên tổ hợp các thành phần: Phụ âm đầu, Âm đệm, Âm chính, Âm cuối, Thanh điệu.
- **So sánh và khám quá các quy luật** được trình bày chi tiết trong báo cáo.

## Hướng dẫn sử dụng

1. Thay đổi đường dẫn tới file dữ liệu `VDic_uni.txt` thông qua biến `DICT_PATH` trong `source.ipynb`
2. Chạy `source.ipynb`
3. Dữ liệu đầu ra:
   - `unique_syllables.csv`: Danh sách âm tiết duy nhất được trích xuất.
   - Thống kê số lượng từng loại được in ra trực tiếp trên màn hình.

