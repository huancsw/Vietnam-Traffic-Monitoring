# Thông báo kẹt xe (Traffic Jam) – ghi chú để phát triển sau

**Trạng thái: tạm gỡ khỏi dự án.** Tính năng này chưa được làm lại cho model `yolo26n`, nên toàn bộ code, ảnh minh họa và phần mô tả của nó đã được loại khỏi app. File này ghi lại tính năng từng làm gì, vì sao thiết kế cũ chưa đủ tốt và hướng phát triển tiếp.

## 1. Tính năng cũ hoạt động như thế nào

Một script chạy riêng (không nằm trong app Streamlit) lặp vô hạn như sau:

1. Duyệt lần lượt từng camera trong [cameras.py](cameras.py), lấy ảnh mới nhất bằng `get_image()`. Giữa hai camera nghỉ `15 / số_camera` giây, vì cổng giao thông chỉ làm mới ảnh khoảng 15 giây một lần.
2. Chạy model phát hiện xe với ngưỡng tin cậy 0,3.
3. Kiểm tra điều kiện kẹt xe bằng hàm sau (chỉ so sánh tổng số xe với lần chụp trước của cùng camera):

   ```python
   def is_congestion(camera, sum_vehicle):
       return (
           camera["previous_sum"] != -1
           and sum_vehicle - camera["previous_sum"] > 2
           and sum_vehicle > 5
       )
   ```

4. Nếu đúng, vẽ khung lên ảnh và gửi ảnh vào một channel Slack, kèm dòng `"<tên camera> traffic jam!"`. Token Slack nằm trong một file Python không đưa vào git.

## 2. Vì sao thiết kế cũ chưa đủ tốt

- **Đo sai thứ cần đo.** "Số xe tăng hơn 2 so với 15 giây trước" chỉ phát hiện lượng xe tăng đột ngột, chứ không phải kẹt xe. Đường đông xe nhưng chạy thông vẫn bị báo, còn đường kẹt cứng từ trước (số xe không đổi) thì không bao giờ được báo.
- **Mọi loại xe tính như nhau.** Một xe buýt hay xe tải chiếm chỗ nhiều hơn xe máy rất nhiều.
- **Không có ngưỡng riêng cho từng camera.** Camera nhìn bao quát và camera nhìn cận cảnh có số xe bình thường rất khác nhau, và số xe cũng khác theo giờ trong ngày.
- **Một mẫu là báo.** Dễ báo nhầm do nhiễu của model, và không có cơ chế chống gửi liên tục (cooldown).
- **Gửi ảnh bằng API đã hết hạn.** Script cũ gọi `files.upload`. Theo tài liệu Slack, method này đã bị ngừng hoạt động từ ngày 12/11/2025, nên phải dùng quy trình ở mục 4.

## 3. Hướng thiết kế đề xuất

**Đo mức độ đông đúc** thay vì đếm thô:

- Tải xe quy đổi: `load = Σ (trọng số của loại xe × số xe loại đó)`. Trọng số chỉ là gợi ý ban đầu và cần hiệu chỉnh theo camera thực tế, ví dụ motorbike 0,3, car 1, bus 2,5, truck 2,5.
- Nếu có vùng quan tâm (ROI) trên mặt đường thì chỉ đếm xe nằm trong vùng đó.
- Ảnh từ cổng chỉ làm mới mỗi 15 giây nên **không đo được tốc độ** bằng tracking. Nếu sau này có luồng video thật thì mới nên thêm tốc độ trung bình (ví dụ `model.track` của Ultralytics) để phân biệt "đông nhưng chạy" với "kẹt".

**Quyết định có kẹt hay không:**

- So `load` với mức bình thường của riêng camera đó theo khung giờ, lấy từ dữ liệu thu thập bằng [get_data.py](get_data.py) (ví dụ trung vị theo giờ).
- Chỉ báo khi vượt ngưỡng liên tiếp N lần (ví dụ 3 trong 4 lần chụp gần nhất).
- Có cooldown (ví dụ 10 phút mỗi camera) để không báo lặp, và có thể gửi thêm một tin "đã thông thoáng" khi hết kẹt.

**Gửi thông báo qua Slack (quy trình hiện hành):**

1. Gọi `files.getUploadURLExternal` với `filename` và `length` (số byte) để lấy `upload_url` và `file_id`.
2. `POST` nguyên nội dung file (`Content-Type: application/octet-stream`) tới `upload_url` và kiểm tra mã HTTP.
3. Gọi `files.completeUploadExternal` với `files=[{"id": file_id, "title": ...}]`, `channel_id` và `initial_comment`.

Cần Bot Token có scope `files:write` và bot phải được mời vào channel. Token và channel ID đọc từ biến môi trường (ví dụ `SLACK_BOT_TOKEN`, `SLACK_CHANNEL_ID`), tuyệt đối không ghi vào code hay commit vào git. Có thể làm nơi nhận tin thay thế được (Telegram, email, webhook) bằng cách tách thành một lớp `Notifier` riêng.

## 4. Gợi ý cấu trúc code

```
traffic_jam/
├── rules.py      # CongestionDetector: giữ lịch sử từng camera, tính load, quyết định báo
├── notifier.py   # SlackNotifier (và các notifier khác), đọc cấu hình từ biến môi trường
└── monitor.py    # vòng lặp: get_image -> YoloPredictor.predict -> rules -> notifier
```

Tái sử dụng sẵn có: `YoloPredictor` ([yolo_predictor.py](yolo_predictor.py)), `get_image` và `draw_boxes` ([utils/utils.py](utils/utils.py)), danh sách camera ([cameras.py](cameras.py)). Phần quy tắc nên viết thuần (không gọi mạng, không gọi model) để kiểm thử bằng chuỗi số xe giả lập.

## 5. Việc cần làm

- [ ] Thu thập dữ liệu vài ngày bằng `get_data.py` rồi tính mức đông xe bình thường theo giờ cho từng camera.
- [ ] Viết `CongestionDetector` kèm unit test (chuỗi tăng đột biến, kẹt kéo dài, nhiễu một khung, cooldown).
- [ ] Viết `SlackNotifier` theo quy trình ở mục 3 và thử trên một channel riêng.
- [ ] Viết vòng lặp giám sát và cho chạy thử, ghi log số lần báo và duyệt lại các lần báo nhầm.
- [ ] (Tuỳ chọn) Hiển thị trạng thái kẹt xe và lịch sử trên tab Live Camera của app.
- [ ] Cập nhật README và thêm lại mục này vào danh sách tính năng khi hoàn thành.

## 6. Lưu ý và rủi ro

- **Độ chính xác của model theo loại xe không đều.** Trên tập test, bus và truck còn yếu (recall truck khoảng 0,68), nên trọng số lớn của hai loại này có thể làm `load` dao động mạnh.
- **Camera giao thông chỉ phục vụ tham khảo.** Kiểm tra điều khoản sử dụng của cổng dữ liệu trước khi chạy giám sát liên tục. Ảnh có thể trễ hoặc lỗi theo từng camera.
- **Số liệu đánh giá model có thể lạc quan.** Tập train, val, test được chia ngẫu nhiên theo từng ảnh nên có nhiều khung hình gần giống nhau giữa các tập. Nên đo độ chính xác bằng ảnh từ camera mới trước khi tin vào ngưỡng báo.
