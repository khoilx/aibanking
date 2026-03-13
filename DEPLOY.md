# Hướng dẫn Triển khai Hệ thống Audit AI

## Lựa chọn phương án phù hợp

| Phương án | Thời gian cài đặt | Phù hợp với | Chi phí |
|-----------|------------------|-------------|---------|
| **1. LAN** | 2 phút | Demo nội bộ cùng phòng | Miễn phí |
| **2. ngrok** | 5 phút | Demo từ xa qua internet | Miễn phí |
| **3. Docker** | 15 phút | Server nội bộ bền vững | Miễn phí |
| **4. Railway** | 30 phút | Cloud hosting lâu dài | Miễn phí (có giới hạn) |

---

## Phương án 1: Chia sẻ trong mạng LAN (Cùng WiFi/VPN)

Đây là cách **nhanh nhất** nếu mọi người cùng mạng nội bộ.

### Bước 1: Tìm địa chỉ IP của máy
```
ipconfig
```
Tìm dòng `IPv4 Address` (ví dụ: `192.168.1.100`)

### Bước 2: Khởi động Backend với host 0.0.0.0
```
cd backend
venv\Scripts\activate
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Bước 3: Khởi động Frontend với host 0.0.0.0
```
cd frontend
npm run dev -- --host 0.0.0.0
```

### Bước 4: Chia sẻ địa chỉ với đồng nghiệp
- **Frontend:** `http://192.168.1.100:5173`
- **API Docs:** `http://192.168.1.100:8000/docs`

> ⚠️ **Lưu ý:** Cả 2 cửa sổ terminal phải giữ mở. Người dùng khác phải cùng mạng WiFi/VPN với bạn.

---

## Phương án 2: ngrok (Demo qua Internet)

ngrok tạo một URL công khai trỏ về máy tính của bạn.

### Bước 1: Cài đặt ngrok
Tải tại: https://ngrok.com/download
Hoặc: `winget install ngrok`

### Bước 2: Đăng ký tài khoản miễn phí và lấy authtoken
```
ngrok config add-authtoken YOUR_TOKEN_HERE
```

### Bước 3: Khởi động hệ thống bình thường
```
# Terminal 1:
cd backend && venv\Scripts\activate && uvicorn main:app --host 0.0.0.0 --port 8000

# Terminal 2:
cd frontend && npm run dev
```

### Bước 4: Tạo tunnel cho Backend
```
ngrok http 8000
```
Ghi lại URL dạng: `https://xxxx-xxx-xxx.ngrok-free.app`

### Bước 5: Cập nhật Frontend để dùng ngrok URL
Sửa file `frontend/.env.local`:
```
VITE_API_URL=https://xxxx-xxx-xxx.ngrok-free.app
```
Restart frontend: `npm run dev`

### Bước 6: Tạo tunnel cho Frontend
```
ngrok http 5173
```

Chia sẻ URL frontend ngrok cho người dùng.

> ✅ **Ưu điểm:** Không cần server, share được qua internet
> ⚠️ **Hạn chế:** URL thay đổi mỗi lần (free tier), tốc độ phụ thuộc mạng của bạn

---

## Phương án 3: Docker Compose (Server Nội bộ)

Phù hợp khi có một máy chủ Windows/Linux trong mạng nội bộ.

### Yêu cầu
- Docker Desktop: https://www.docker.com/products/docker-desktop/

### Bước 1: Cài Docker Desktop và khởi động

### Bước 2: Build và chạy
```
cd Model_2
docker-compose up --build -d
```

### Bước 3: Kiểm tra
```
docker-compose ps
docker-compose logs -f
```

### Truy cập
- **Frontend:** `http://SERVER_IP:80`
- **Backend API:** `http://SERVER_IP:8000`
- **API Docs:** `http://SERVER_IP:8000/docs`

### Lệnh quản lý
```
# Dừng hệ thống:
docker-compose down

# Xem logs:
docker-compose logs -f backend
docker-compose logs -f frontend

# Restart:
docker-compose restart
```

> ✅ **Ưu điểm:** Tự động khởi động lại khi reboot, dữ liệu được lưu bền vững
> ⚠️ **Yêu cầu:** Cần cài Docker Desktop

---

## Phương án 4: Railway.app (Cloud Hosting Miễn phí)

Railway cho phép deploy cả frontend và backend lên cloud miễn phí.

### Deploy Backend lên Railway

1. Vào https://railway.app → Sign up bằng GitHub
2. New Project → Deploy from GitHub repo
3. Chọn thư mục `backend/`
4. Railway tự detect Python/FastAPI
5. Thêm biến môi trường:
   ```
   DB_PATH=/app/data/audit_system.db
   ```
6. Ghi lại URL: `https://xxx.railway.app`

### Deploy Frontend lên Vercel (miễn phí)

1. Vào https://vercel.com → Sign up bằng GitHub
2. Import project → chọn thư mục `frontend/`
3. Thêm Environment Variable:
   ```
   VITE_API_URL=https://xxx.railway.app
   ```
4. Deploy → Vercel cung cấp URL miễn phí

> ✅ **Ưu điểm:** Có URL cố định, không cần máy tính của bạn luôn bật
> ⚠️ **Lưu ý:** Free tier Railway có giới hạn compute hours/tháng

---

## Tài khoản Demo

```
┌─────────────────────────────────────┐
│  Tài khoản    │  Vai trò            │
├─────────────────────────────────────┤
│  admin        │  Quản trị viên      │
│  ktv_nguyenan │  Kiểm toán viên     │
│  ktv_tranthi  │  Kiểm toán viên     │
│  manager_le   │  Quản lý đoàn KT    │
│  ktv_pham     │  Kiểm toán viên     │
└─────────────────────────────────────┘
Mật khẩu: admin123 (admin), pass123 (các tài khoản còn lại)
```
