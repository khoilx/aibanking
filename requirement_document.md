# Tài liệu Yêu cầu Sản phẩm (Product Requirement Document - PRD)
**Dự án:** Hệ thống Phân tích Tín dụng phục vụ Kiểm toán (Audit AI System)
**Phiên bản:** 1.0.0
**Ngày lập:** 13/03/2026

---

## 1. Giới thiệu (Introduction)
### 1.1. Mục tiêu (Objective)
Xây dựng một hệ thống phần mềm ứng dụng trí tuệ nhân tạo và phân tích dữ liệu lớn nhằm hỗ trợ Kiểm toán viên Ngân hàng Nhà nước trong việc thanh tra, giám sát chất lượng tín dụng, phát hiện sớm các rủi ro, sai phạm, và các khoản vay sử dụng sai mục đích (Misuse of Loans).

### 1.2. Đối tượng sử dụng (Target Users)
- **Kiểm toán viên (Auditors / KTV):** Người trực tiếp sử dụng hệ thống để phân tích danh mục, điều tra khách hàng, theo dõi cảnh báo (Red flags).
- **Quản lý / Trưởng đoàn kiểm toán (Audit Managers):** Xem báo cáo tổng quan, theo dõi KPI của chi nhánh, theo dõi tiến độ xử lý case.
- **Người quản trị hệ thống (System Administrators):** Quản lý phân quyền, cấu hình rules (quy tắc) rủi ro.

---

## 2. Tổng quan Hệ thống (System Overview)
Hệ thống bao gồm hai giai đoạn (Phases) chính:
- **Phase 1 (Core Module):** Quản lý danh mục, chấm điểm rủi ro khách hàng (Risk Scoring), phát hiện các cờ đỏ (Red Flags) cơ bản trên dữ liệu nội bộ (Khoản vay, Giao dịch, CIC).
- **Phase 2 (Loan Misuse Module):** Tích hợp dữ liệu thay thế (Alternative Data) bao gồm Hóa đơn điện tử quan thuế, Bảo hiểm xã hội, Trạng thái MST và Vận đơn logistics nhằm phát hiện sâu các hành vi gian lận, rút tiền mặt, sử dụng vốn sai mục đích.

---

## 3. Các tính năng chính (Key Features)

### 3.1. Dashboard Tổng quan (Executive Dashboard)
- Hiển thị các chỉ số rủi ro chính (KPIs): Tỷ lệ NPL, Tỷ lệ nợ nhóm 2, Tỷ lệ cơ cấu nợ, Tỷ lệ bao phủ nợ xấu (LLCR).
- Biểu đồ xu hướng chất lượng tín dụng qua các tháng.
- Danh sách khách hàng (Top Red Flags) có rủi ro cao nhất dựa trên điểm số (Risk Score) hiện tại, hiển thị tổng dư nợ và chi tiết cảnh báo.

### 3.2. Quản lý Chi nhánh (Branch Overview)
- Cung cấp góc nhìn 360 độ về một chi nhánh (Ví dụ: CN Sài Gòn, CN Hà Nội).
- Hiển thị thông tin Giám đốc chi nhánh, tổng dư nợ, xếp hạng của hệ thống.
- Chi tiết danh mục tín dụng theo lĩnh vực (Bất động sản, Nông nghiệp, Bán lẻ,...).
- Liệt kê các khoản vay rủi ro cao nhất thuộc chi nhánh và các sự kiện đáng chú ý (Cảnh báo sớm).

### 3.3. Hồ sơ Khách hàng 360 (Customer 360-View)
- Tìm kiếm và tra cứu chi tiết một khách hàng theo CIF.
- **Dư nợ (Exposure):** Liệt kê chi tiết dư nợ nội bảng (Loans) và ngoại bảng (L/C, Guarantee, Credit Commitment).
- **Lịch sử Giao dịch (Timeline):** Các giao dịch giải ngân, trả nợ gần nhất.
- **Phân tích Rủi ro:** Hiển thị điểm số rủi ro, phân loại (Green/Amber/Red) và liệt kê chi tiết các quy tắc rủi ro vi phạm (Rule hits).
- **Dữ liệu Sai mục đích (Misuse Data - Phase 2):** 
  - Khớp nối thông tin tờ khai thuế, hóa đơn mua bán.
  - Phân tích trạng thái Mã số thuế (Đóng/Mở/Bỏ trốn).
  - Đối chiếu số lượng nhân sự qua Bảo hiểm xã hội.
  - Đối chiếu vận đơn giao hàng (Logistics).

### 3.4. Phân tích Sai mục đích (Loan Misuse Analytics)
- Báo cáo tổng quan về rủi ro sai mục đích vốn trên toàn hệ thống (Tổng dư nợ bị cảnh báo, số lượng case).
- Biểu đồ phân bổ các mẫu hình gian lận (Rút tiền mặt, hóa đơn hủy, Vendor Hub, Mismatch BHXH,...).
- Phân tích các Hub nhà cung cấp (Vendor Hubs) có biểu hiện đáng ngờ (Nhiều khách hàng vay cùng chuyển tiền cho 1 Vendor, xuất hóa đơn khống).

### 3.5. Quản lý Case (Case Management)
- Tự động sinh ra các Case điều tra (Nghi vấn) dựa trên tổng điểm rủi ro vượt ngưỡng.
- Bảng Kanban cho phép KTV theo dõi tiến độ xử lý: Kế hoạch (To Do), Đang xử lý (In Progress), Chờ giải trình (Pending Branch), Đóng (Closed).
- Lưu vết toàn bộ lịch sử can thiệp hệ thống, thay đổi trạng thái case (Audit logs).

---

## 4. Yêu cầu Phi chức năng (Non-Functional Requirements)

### 4.1. Công nghệ (Technology Stack)
- **Frontend:** React, TypeScript, Vite, Tailwind CSS (hoặc CSS thuần tối ưu). Giao diện thiết kế theo phong cách hiện đại với Glassmorphism phù hợp cho Dashboard phân tích tài chính.
- **Backend:** Python (FastAPI).
- **Database:** PostgreSQL (Môi trường production), Môi trường phát triển có thể dùng SQLite mô phỏng.

### 4.2. Bảo mật và Tuân thủ (Security & Compliance)
- Toàn bộ dữ liệu khách hàng (CIF, tên, số thẻ, số tài khoản) phải được mã hóa theo tiêu chuẩn ngân hàng.
- Lưu lại log (Audit Trail) của toàn bộ các thao tác (truy vấn, thay đổi báo cáo) của KTV.
- Phân quyền nghiêm ngặt theo mô hình RBAC (Role-Based Access Control).

### 4.3. Hiệu năng (Performance)
- Các truy vấn trên Dashboard đối với khối dữ liệu giao dịch lớn phải phản hồi dưới 2 giây.
- Batch Job tính điểm rủi ro qua đêm (Overnight Batch) phải hoàn thành trước giờ làm việc của ngày tiếp theo.

---

## 5. Dữ liệu Đầu vào (Data Requirements)
Hệ thống yêu cầu tích hợp các nguồn dữ liệu thông qua batch (ETL):
1. Dữ liệu Khách hàng (`dim_customer`).
2. Dữ liệu Hợp đồng vay (`dim_loan_master`).
3. Dữ liệu Giao dịch (`fact_transactions`).
4. Ngoại bảng & Lãi dự thu (`fact_off_balance`, `fact_accrued_interest`).
5. Dữ liệu CIC (`fact_cic_extract`).
6. Dữ liệu Tài sản Đảm bảo (`dim_collateral`).
7. Dữ liệu Thuế, BHXH, Hải quan (Dành cho Misuse Module).

---

*Tài liệu này là phiên bản gốc. Có thể điều chỉnh dựa theo góp ý của nghiệp vụ.*
