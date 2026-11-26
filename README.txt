PT Agency V2.0 — bản thử nghiệm máy chủ
Windows: cài Python 3.11+, mở CMD trong thư mục này.
python -m pip install -r requirements.txt
set ADMIN_EMAIL=admin@ptagency.local
set ADMIN_PASSWORD=MatKhauRiengCuaBan123!
python app.py
Mở http://127.0.0.1:8000/login. Dùng email và mật khẩu đã đặt.
Không dùng mật khẩu ví dụ khi triển khai thật.
Linux hosting: cấu hình ADMIN_EMAIL, ADMIN_PASSWORD (>=12 ký tự), SECRET_KEY (ngẫu nhiên dài, cố định), HTTPS=1, DB_PATH (đường dẫn ổ đĩa persistent). Khởi chạy gunicorn app:app. Cần HTTPS, sao lưu, giới hạn đăng nhập, kiểm thử bảo mật trước khi dùng khách thật. Không upload lên static hosting dưới dạng HTML. Chưa có tích hợp ngân hàng, CTV, nhân viên, hoàn tiền hay hệ thống bảo hành ticket. Mô hình hiện tại có Admin và Customer, phân quyền phía server. Admin chỉ được tạo khi email chưa tồn tại; đổi biến môi trường không đổi mật khẩu đã lưu. Không để khách đăng ký trước lúc khởi tạo Admin. Không dùng dữ liệu thật trong bản thử nghiệm.
