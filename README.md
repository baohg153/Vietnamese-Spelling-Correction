# Vietnamese Spelling Correction

## Giới thiệu:
Đây là source code của đồ án cuối kỳ môn Nhập môn xử lí ngôn ngữ tự nhiên. Code này thực hiện việc fine-tune model ViT5 (base) của VietAI, để mô hình có thể phát hiện và sửa lỗi chính tả tiếng Việt trong văn bản (tức mô hình sẽ nhận đầu vào là một văn bản tiếng Việt có thể chứa những lỗi sai chính tả, và cho ra output là văn bản đó đã được sửa lỗi chính tả rồi).

## Cấu trúc source code:
Gồm các file:
- `fine-tuning.ipynb`: File notebook chứa code để fine-tune model.
- `testing.ipynb`: File notebook chứa code để testing model sau khi fine-tune, và vẽ các biểu đồ thể hiện độ lỗi mô hình.
- `train.json`: File json chứa dữ liệu huấn luyện.
- `valid.json`: File json chứa dữ liệu validation.
- `test.json`: File json chứa dữ liệu test.
- `details_1.json`: File json chứa kết quả testing của mô hình sau khi mới được train 1 epoch.
- `details.json`: File json chứa kết quả testing của mô hình sau khi được train nốt 13 epoch còn lại (tuy nhiên cuối cùng file này không được sử dụng vì mô hình đã đạt tốt nhất sau 1 epoch).

## Lưu ý:
Hai file notebook (fine-tuning.ipynb và testing.ipynb) được thiết kế để chạy trên Google Colab.