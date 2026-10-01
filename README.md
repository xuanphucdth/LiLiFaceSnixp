# LiLiFaceSnixp

Phiên bản 1.1 bổ sung **Camera Box Snip** ngay trong ứng dụng hiện tại. Các cài đặt và chế độ Face/Head/Portrait của bạn được giữ lại.

Ứng dụng Windows tự tìm khuôn mặt trên màn hình, cắt ảnh và đưa vào clipboard. Chạy hoàn toàn trên máy, không nhận dạng danh tính và không gửi ảnh lên mạng.

## Cách mở

Mở thư mục **dist → LiLiFaceSnixp**, nhấp đúp **LiLiFaceSnixp.exe**. Không cần cài Python, không cần quyền Administrator.

Giữ nguyên cả thư mục LiLiFaceSnixp, gồm EXE và thư mục `_internal`. Nếu chuyển sang chỗ khác, hãy chuyển cả thư mục.

Lần đầu, cửa sổ Settings mở sẵn. Đóng cửa sổ này vẫn để ứng dụng chạy nền. Tìm biểu tượng khuôn mặt màu xanh trong khay hệ thống cạnh đồng hồ, có thể nằm trong nút **^**.

## Cách bật và dùng

Nhấp phải biểu tượng → **Auto Face Snip**. Có dấu chọn là ON; không có dấu chọn là OFF.

- **PrtSc**: khi ON, tự tìm và cắt mặt; khi OFF, mở Windows Snipping Tool.
- **Shift + PrtSc**: luôn mở Windows Snipping Tool để chọn vùng bằng tay.
- **Ctrl + PrtSc**: sao chép nguyên màn hình theo mục Capture, bỏ qua nhận diện.
- **Ctrl + V**: dán ảnh vào ứng dụng hỗ trợ dán hình ảnh.

Máy có phím PrtSc dùng chung có thể cần giữ **Fn**. Alt+PrtSc và Win+PrtSc vẫn do Windows xử lý.

Một mặt được chọn tự động. Không thấy mặt hoặc gặp lỗi thì ứng dụng chuyển sang Snipping Tool. Khi một lần chụp đang xử lý, lần bấm chụp tự động tiếp theo được bỏ qua; Shift+PrtSc vẫn mở chế độ thủ công.

## Chọn kiểu cắt

Nhấp phải biểu tượng → Settings. Cài đặt được lưu tự động.

- **Face**: sát mặt. **Head**: thêm tóc, tai và cổ. **Portrait**: thêm vai, thân trên theo ước lượng.
- **Padding**: lề bổ sung trên mỗi cạnh, từ 10% đến 50%. Mặc định Head + 25%.
- **Ask me**: nhiều mặt sẽ hiện khung đánh số. Nhấp bên trong khung hoặc bấm 1–9. Những mặt sau số 9 chọn bằng chuột. Esc/Cancel hủy, không đổi clipboard. Overlay tự đóng sau 60 giây.
- **Largest face**: chọn mặt lớn nhất.
- **Face nearest cursor**: chọn mặt gần vị trí chuột lúc bấm PrtSc nhất.
- **Crop all faces together**: tạo **một ảnh** chứa tất cả mặt, sau đó thêm lề.
- **Capture**: màn hình dưới chuột, màn hình chính hoặc tất cả màn hình.
- **Confidence**: mặc định 0.60. Giảm nếu bỏ sót mặt; tăng nếu nhận nhầm. Áp dụng cho lần chụp tiếp theo, không cần khởi động lại.
- **Test Detection**: ẩn Settings, chụp thử và hiện khung mặt; không cắt, không chép clipboard. Esc/Close để trở lại.

Overlay hiển thị khung hình đã chụp với nền chỉ tối nhẹ; ảnh để cắt đã được chụp trước đó. Nếu đang xem video, kết quả là khung hình tại thời điểm chụp.

## Camera Box — cắt cả khung camera

Trong **Settings → Snip Target**, chọn **Camera Box**, sau đó đưa cửa sổ cuộc gọi lên trước và nhấn **PrtSc**. Ứng dụng tìm khuôn mặt làm điểm neo, rồi tìm biên khung video bao quanh mặt. Khi thấy nhiều tile, lựa chọn Ask me vẽ khung quanh **cả tile**, chọn bằng chuột/phím 1–9; Esc hủy.

- **Camera Box Padding:** mặc định 0 px; có thể chọn 2, 4, 8, 12, 16 px. Lề 25% của Head không áp dụng cho camera.
- **Largest camera box:** chọn tile lớn nhất.
- **Camera box nearest cursor:** ưu tiên tile chứa chuột; nếu không có thì chọn tâm tile gần nhất. Có thể chọn self-view nhỏ.
- **Crop all camera boxes together:** trả về một ảnh bao tất cả các tile đã xác định.
- **Camera Box Confidence:** mặc định 0.55; tăng để thận trọng hơn, giảm để chấp nhận thêm ứng viên. Đây là điểm đánh giá hình học/biên ảnh, không phải xác suất được AI đảm bảo.
- **Camera Box Search Area:** mặc định Foreground window, chỉ xét phần cửa sổ đang hoạt động trong ảnh chụp. Current monitor xét màn hình dưới chuột. Mục Capture vẫn quyết định ảnh chụp nguồn; với cửa sổ trải trên nhiều màn hình, có thể dùng All monitors cùng Foreground window. Khi không lấy được biên cửa sổ, ứng dụng xét màn hình hiện tại trong ảnh đã chụp.
- **Camera Box Fallback:** mặc định Crop Head nếu có mặt nhưng thiếu biên đáng tin. Có thể chọn Ask me with candidates để xác nhận thủ công ứng viên; nếu không có ứng viên thì mở Snipping Tool. Open Snipping Tool luôn chuyển sang chọn vùng thủ công khi không chắc chắn.

Nếu chỉ xác định được một phần các tile có mặt, ứng dụng dùng fallback cho tập mặt trong vùng tìm kiếm, tránh âm thầm bỏ người. Không có mặt thì mở Snipping Tool. Test Detection trong Camera Box hiện các tile/ứng viên, không thay clipboard.

Tính năng dùng OpenCV có sẵn, chạy local, không tải model mới và không dùng OCR. Camera tắt/avatar không có mặt không được bảo đảm. Khuôn mặt quá nhỏ so với khung sẽ kích hoạt fallback để tránh chọn nhầm cả cửa sổ. Biên hòa với nền, nhiều cửa sổ chồng lấp, cảnh trong video có đồ vật hình chữ nhật hoặc toolbar có màu giống video vẫn có thể gây nhầm. Khi đó dùng Shift+PrtSc hoặc đổi fallback sang Ask me/Open Snipping Tool. Chuyển Snip Target về Head để dùng hành vi cũ.

Chế độ production không lưu ảnh debug, kể cả khi bật cờ debug trong config. Công cụ phát triển riêng `tools/test_camera_images.py --debug` chỉ xử lý ảnh tĩnh được cung cấp và lưu minh họa vào `debug/camera_detection/`; cờ `debug_camera_detection` cũng chỉ được công cụ này đọc.

## Lưu ảnh và khởi động cùng Windows

**Save a copy** mặc định OFF: ứng dụng không lưu ảnh chụp thành tệp. Bật để lưu ảnh kết quả vào **Pictures/LiLiFaceSnixp**. Clipboard do Windows quản lý; thiết lập lịch sử/đồng bộ clipboard của bạn vẫn có hiệu lực. Snipping Tool có thiết lập tự lưu riêng của Windows.

**Start with Windows** mặc định OFF. Bật nếu muốn chạy nền mỗi khi đăng nhập. Nếu di chuyển thư mục ứng dụng, tắt rồi bật lại mục này để cập nhật đường dẫn. Chỉ dùng thiết lập của tài khoản hiện tại.

## Cách thoát

Nhấp phải biểu tượng trong khay hệ thống → **Exit**. Phím PrtSc sau đó do Windows xử lý theo thiết lập hiện có.

## Nếu không chạy

1. Kiểm tra biểu tượng trong nút **^** cạnh đồng hồ; ứng dụng có thể đã chạy.
2. Đảm bảo EXE vẫn nằm cùng thư mục `_internal`.
3. Nếu phím tắt bị ứng dụng khác chiếm, thoát phần mềm chụp màn hình đó rồi mở lại LiLiFaceSnixp.
4. Nếu bỏ sót khuôn mặt, thử Test Detection, giảm Confidence hoặc chọn một màn hình thay vì All monitors.
5. Trong Settings, bấm **Open logs**. Log cũng nằm ở `%LOCALAPPDATA%\LiLiFaceSnixp\logs\LiLiFaceSnixp.log`.

Cài đặt nằm ở `%LOCALAPPDATA%\LiLiFaceSnixp\config\settings.json`. JSON hỏng sẽ được thay bằng mặc định. Log tự xoay vòng, tối đa khoảng 8 MB, không chứa pixel hay nội dung ảnh.

Ứng dụng không tự thay đổi thiết lập Print Screen, không tắt Snipping Tool và không yêu cầu tắt bảo mật Windows. Bản EXE cá nhân chưa có chữ ký số.

## Giới hạn thực tế

Đây là phát hiện khuôn mặt, không phải công cụ cắt tóc chính xác. Mặt rất nhỏ, nghiêng, bị che, tranh cách điệu hoặc hình ảnh được bảo vệ có thể không nhận được. Desktop rất lớn được thu nhỏ về cạnh dài 1920 pixel khi nhận diện để giảm thời gian CPU; ảnh kết quả vẫn ở độ phân giải gốc. Portrait là ước lượng; không phân tích dáng người. Không chụp được màn hình khóa/UAC secure desktop.

Để gỡ: tắt Start with Windows, chọn Exit, rồi xóa thư mục ứng dụng. Có thể xóa thêm thư mục `%LOCALAPPDATA%\LiLiFaceSnixp` nếu muốn bỏ cài đặt và log.

## Đã kiểm tra trên máy này

**Cập nhật Camera Box 1.1 — 01/10/2026:** 54 kiểm thử logic/tích hợp đã đạt. Các tình huống Camera A–F (tile đơn, nhiều tile/Ask me, nearest cursor, PiP, Head fallback, chuyển về Head) đạt trên ảnh tĩnh và cửa sổ cuộc gọi mô phỏng. Bản EXE riêng đã xác nhận PrtSc, phím số thật trên overlay, ảnh clipboard khớp từng pixel, tile đơn, self-view, All boxes và chạy lại chế độ Portrait. Có 9 kiểm tra thành phần trong EXE đạt.

**Chưa thử cuộc gọi thật trong Discord, Meet, Teams, Zoom, Messenger hay Telegram.** Không tự tạo/gọi người khác để kiểm tra. Các mẫu hiện tại dùng bố cục tổng hợp và ảnh NASA có sẵn; kết quả không bảo đảm mọi giao diện cuộc gọi đều tìm đúng biên. Khung có biên yếu/đối tượng chữ nhật trong feed vẫn có thể nhận nhầm; hãy dùng fallback khi cần.

Bản cũ được giữ trong `backups/LiLiFaceSnixp-before-camera-20261001`. Mã nguồn trước khi sửa được lưu trong `backups/before-camera-box-source.zip`. Những cài đặt riêng trước đó của bạn vẫn được giữ; để dùng tính năng mới, bật **Auto Face Snip** và chọn **Snip Target → Camera Box**.

Ngày 30/09/2026, Windows 11 64-bit, màn hình 1920×1080:

- A: OFF mở Snipping Tool; H: Shift+PrtSc mở Snipping Tool.
- B: một mặt được cắt Head +25%, dữ liệu clipboard khớp từng pixel.
- C: ba mặt hiện overlay; chọn phím 2, nhấp chuột và Esc đều hoạt động.
- D/E/F: Largest, Nearest cursor, All faces chọn đúng; ảnh crop khớp từng pixel.
- G: không có mặt mở Snipping Tool; I: Ctrl+PrtSc sao chép toàn màn hình.
- J: hai lần chạy EXE riêng biệt dùng lại đúng cài đặt đã lưu.
- K: EXE chạy với PATH không có Python; nhận diện, phím tắt, clipboard và thoát đều hoạt động.
- Dán Ctrl+V vào Chrome đã xác nhận nhận được ảnh PNG đúng kích thước.
- 18 kiểm thử logic/xử lý lỗi và 8 kiểm tra thành phần trong EXE đã đạt.

Chưa xác nhận trực tiếp việc dán trong Photoshop, Discord, Telegram và Paint. Photoshop trên máy này không cung cấp COM scripting để kiểm tra tự động. Ứng dụng cung cấp dữ liệu ảnh CF_DIB và PNG tiêu chuẩn, không phải đường dẫn tệp. Nhiều màn hình/toạ độ âm đã qua kiểm thử toán học; chưa có kiểm tra trên phần cứng nhiều màn hình/DPI khác nhau. Không cần đổi setting Print Screen của Windows trên máy đã kiểm tra.
