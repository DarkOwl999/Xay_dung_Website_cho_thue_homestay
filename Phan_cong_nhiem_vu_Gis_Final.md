---
title: "PHÂN CÔNG NHIỆM VỤ NHÓM DỰ ÁN GIS_FINAL"
subtitle: "Tài liệu phục vụ đăng GitHub nhóm 3 thành viên cho môn Lập Trình GIS"
author: "Hồ sơ phân công cho nhóm: Giang, Bảo, Hiếu"
date: "17/04/2026"
---

# 1. Mục đích tài liệu

Tài liệu này được lập ra để thống nhất cách phân công nhiệm vụ khi đưa dự án `Gis_Final` lên GitHub cho nhóm 3 người gồm `Giang`, `Bảo`, `Hiếu`.

Yêu cầu đặc biệt của môn **Lập Trình GIS** là:

1. Toàn bộ phần liên quan đến **GIS** phải được chia **thật đều** cho cả 3 thành viên.
2. Các phần không thuần GIS như `HTML`, `CSS`, `auth`, `booking`, `admin` có thể phân bố linh hoạt hơn.
3. Đầu ra cần dễ đối chiếu trên GitHub, vì vậy tài liệu này sẽ chia theo:
   - cụm chức năng GIS,
   - file code,
   - cú pháp branch/commit gợi ý,
   - phần việc chính và phần việc phụ của từng người.

# 2. Nguyên tắc phân công

## 2.1. Nguyên tắc quan trọng nhất

Phần **GIS** của hệ thống được chia thành 3 cụm tương đương về mặt học thuật và khối lượng:

1. **GIS 1 - Bản đồ hiển thị và quản lý dữ liệu bản đồ**
   - hiển thị map,
   - marker,
   - popup,
   - đồng bộ danh sách căn hộ với marker,
   - quản lý dữ liệu hiển thị cho map.
2. **GIS 2 - Tìm kiếm không gian và geocoding**
   - geocoding,
   - reverse geocoding,
   - tìm theo khu vực,
   - tìm căn hộ gần vị trí hiện tại,
   - lọc theo bán kính và theo thời gian di chuyển.
3. **GIS 3 - Chỉ đường và routing**
   - lấy đường đi,
   - đổi phương tiện di chuyển,
   - hiển thị nhiều tuyến đường,
   - vẽ route trên map,
   - tương tác với bảng chỉ đường.

## 2.2. Nguyên tắc khi làm trên GitHub

1. Mỗi thành viên có **một cụm GIS chính** để thể hiện đóng góp chuyên môn đúng với môn học.
2. Không chỉnh sửa tràn lan vào GIS của người khác, nhất là trong `myapp/templates/map.html`, `myapp/views.py`, `myapp/tool.py`.
3. Mỗi người có branch riêng và commit đúng theo module đã được giao.
4. Nếu có trùng file, phải tách theo **cụm hàm** hoặc **cụm giao diện** như tài liệu này quy định.

# 3. Kết luận phân chia GIS

Bảng sau là phần chia **bắt buộc** cho phần GIS:

| Thành viên | Cụm GIS chính | Tỷ trọng GIS |
|---|---|---:|
| Giang | GIS 1 - Bản đồ hiển thị và quản lý dữ liệu bản đồ | 33% |
| Bảo | GIS 2 - Tìm kiếm không gian và geocoding | 33% |
| Hiếu | GIS 3 - Chỉ đường và routing | 33% |

Nhận xét:

- Phần GIS đã được chia đều theo 3 nhóm chức năng lớn.
- Mỗi người đều có cả **frontend GIS** và **backend GIS** để contribution trên GitHub rõ ràng hơn.
- Đây là cách chia phù hợp với yêu cầu "các phần liên quan đến GIS tuyệt đối phải chia đều cho 3 người".

# 4. Bảng phân công tổng hợp

| Thành viên | Nhiệm vụ GIS chính | Nhiệm vụ bổ trợ không GIS | Branch GitHub gợi ý |
|---|---|---|---|
| Giang | Map core, marker, popup, listing panel, dữ liệu hiển thị map, admin map picker | base layout, home, intro, CSS nền | `feature/giang-map-core` |
| Bảo | Geocoding, reverse geocoding, spatial search, nearby search, lọc theo khu vực và bán kính | booking, review, payment, form booking | `feature/bao-spatial-search` |
| Hiếu | Routing, chỉ đường, nhiều tuyến, đổi phương tiện, panel chỉ đường, deep-link route | auth, OTP, admin dashboard, user management | `feature/hieu-routing-auth-admin` |

# 5. Phân công chi tiết theo từng thành viên

## 5.1. Giang

### A. Phần GIS chính của Giang

**Cụm GIS 1 - Bản đồ hiển thị và quản lý dữ liệu bản đồ**

#### File và cụm code Giang phụ trách

1. `myapp/templates/map.html`
   - Khối khởi tạo bản đồ Leaflet `const map = L.map("map").setView(...)` - dòng `267` tới `272`
   - Hàm `toggleSidebar()` - dòng `376` tới `380`
   - Hàm `renderApartments(dataList, geoData)` - dòng `486` tới `581`
   - Hàm `showAllApartments()` - dòng `703` tới `715`
   - Khu vực danh sách kết quả `id="listing-panel"` - dòng `205` tới `205`
   - Trọng tâm Giang chịu trách nhiệm trong file này là cụm:
     - khởi tạo map,
     - layer nền,
     - marker,
     - popup,
     - đồng bộ marker với danh sách căn hộ,
     - zoom/focus kết quả hiển thị.

2. `myapp/views.py`
   - Hàm `_serialize_apartments_for_map(...)` - dòng `308` tới `326`
   - Hàm `_build_geojson_payload(...)` - dòng `329` tới `351`
   - Hàm `map_view(request)` - dòng `354` tới `363`

3. `myapp/templates/apartment_form.html`
   - Khối khởi tạo bản đồ picker `const map = L.map('picker-map').setView(...)` - dòng `218` tới `223`
   - Hàm `placeMarker(lat, lng, label)` - dòng `243` tới `256`
   - Nhiệm vụ: khởi tạo bản đồ trong form quản trị căn hộ, cho phép click lên map để lấy tọa độ và hiển thị marker.

#### Mục tiêu sản phẩm của Giang

1. Hoàn thiện phần **hiển thị map** và dữ liệu căn hộ trên map.
2. Đảm bảo khi hiển thị danh sách căn hộ thì marker và popup đồng bộ chính xác.
3. Hoàn thiện bản đồ chọn vị trí trong trang thêm/sửa căn hộ để admin có thể cập nhật `lat/lng`.

### B. Phần không GIS bổ trợ của Giang

Giang phụ trách giao diện tổng thể và các trang mang tính trình bày:

1. `myapp/templates/base.html` - toàn file, dòng `1` tới `272`
2. `myapp/templates/home.html` - toàn file, dòng `1` tới `213`
3. `myapp/templates/intro_page.html` - toàn file, dòng `1` tới `242`
4. `myapp/static/css/base-layout.css` - toàn file, dòng `1` tới `303`
5. `myapp/static/css/home.css` - toàn file, dòng `1` tới `96`
6. `myapp/static/css/intro-page.css` - toàn file, dòng `1` tới `790`
7. `myapp/static/css/map-page.css` - toàn file, dòng `1` tới `89`

#### Lý do giao bổ trợ

Giang đang giữ **map core**, nên việc phụ trách tiếp giao diện tổng thể và bố cục frontend sẽ giúp:

1. thống nhất giao diện map với trang chủ và trang giới thiệu,
2. tránh việc quá nhiều người cùng sửa CSS nền.

### C. Commit gợi ý cho Giang

1. `feat(map): khởi tạo map, marker và popup căn hộ`
2. `feat(map): đồng bộ listing panel với marker trên leaflet`
3. `feat(admin-map): thêm map picker cho form căn hộ`
4. `style(ui): hoàn thiện base, home và intro`

---

## 5.2. Bảo

### A. Phần GIS chính của Bảo

**Cụm GIS 2 - Tìm kiếm không gian và geocoding**

#### File và cụm code Bảo phụ trách

1. `myapp/tool.py`
   - Hàm `haversine_distance_km(...)` - dòng `26` tới `41`
   - Lớp `GISSearchTool` - dòng `108` tới `331`
   - Phần trọng tâm bên trong `GISSearchTool` gồm:
     - `build_search_aliases(...)` - dòng `140` tới `174`
     - `get_textual_matches(...)` - dòng `176` tới `200`
     - `search_locations(...)` - dòng `206` tới `226`
     - `reverse_geocode(...)` - dòng `228` tới `242`
     - `get_apartments_in_region(...)` - dòng `244` tới `280`
     - `get_apartments_near_location(...)` - dòng `282` tới `331`

2. `myapp/views.py`
   - Hàm `geocode_place_api(request)` - dòng `600` tới `610`
   - Hàm `reverse_geocode_api(request)` - dòng `613` tới `631`
   - Hàm `search_region_api(request)` - dòng `1038` tới `1051`
   - Hàm `search_nearby_api(request)` - dòng `1054` tới `1118`

3. `myapp/templates/map.html`
   - Khối tìm theo khu vực với `regionSearch` - dòng `45` tới `58`
   - Khối tìm quanh vị trí hiện tại và nút `nearbySearchButton` - dòng `61` tới `179`
   - Hàm `setPinnedSearchPoint(...)` - dòng `642` tới `668`
   - Hàm `searchNearbyApartments()` - dòng `717` tới `769`
   - Hàm `filterByRegion()` - dòng `786` tới `818`
   - Toàn bộ cụm giao diện/JS mà Bảo chịu trách nhiệm trong file này gồm:
     - tìm theo khu vực,
     - tìm quanh vị trí hiện tại,
     - lọc theo bán kính,
     - lọc theo thời gian di chuyển,
     - chọn điểm ghim để tìm kiếm.

4. `myapp/templates/apartment_form.html`
   - Khối UI nhập địa điểm `locationSearchInput` - dòng `147` tới `165`
   - Hàm `setSelectedMapAddressMessage(message, tone)` - dòng `258` tới `270`
   - Lệnh gọi API geocode `fetch('/api/geocode-place/...')` - dòng `319` tới `319`
   - Lệnh gọi API reverse geocode `fetch('/api/reverse-geocode/...')` - dòng `339` tới `339`
   - Nhiệm vụ: tìm địa điểm, hiển thị kết quả tìm kiếm, tự động điền địa chỉ khi admin chọn điểm.

#### Mục tiêu sản phẩm của Bảo

1. Hoàn thiện tìm kiếm theo địa danh, quận, phường, tên đường.
2. Hoàn thiện tìm căn hộ gần vị trí hiện tại theo:
   - khoảng cách,
   - thời gian di chuyển.
3. Hoàn thiện geocoding và reverse geocoding cho:
   - map chính,
   - form quản trị căn hộ.

### B. Phần không GIS bổ trợ của Bảo

Bảo phụ trách cụm nghiệp vụ đặt thuê và thanh toán:

1. `myapp/forms.py`
   - Lớp `CustomerBookingForm` - dòng `297` tới `370`
   - Lớp `BookingPaymentMethodForm` - dòng `463` tới `496`

2. `myapp/views.py`
   - Hàm `apartment_detail(...)` - dòng `366` tới `491`
   - Hàm `booking_payment(...)` - dòng `494` tới `541`
   - Hàm `booking_history(...)` - dòng `545` tới `549`
   - Hàm `booking_cancel(...)` - dòng `553` tới `569`

3. `myapp/templates/apartment_detail.html`
   - Toàn file - dòng `1` tới `725`
   - Trọng tâm phần booking/review và modal đặt căn hộ - dòng `264` tới `716`

4. `myapp/templates/booking_payment.html` - toàn file, dòng `1` tới `247`

5. `myapp/templates/booking_history.html` - toàn file, dòng `1` tới `110`

#### Lý do giao bổ trợ

Phần booking liên quan mạnh đến:

1. vị trí căn hộ,
2. lịch thuê,
3. trải nghiệm người dùng khi tìm căn hộ và đặt căn hộ.

Do đó Bảo phụ trách GIS search kèm booking/payment là hợp lý.

### C. Commit gợi ý cho Bảo

1. `feat(search): bổ sung GISSearchTool và tìm theo khu vực`
2. `feat(search): nearby search theo khoảng cách và thời gian`
3. `feat(geocode): kết nối geocode và reverse geocode cho map và admin form`
4. `feat(booking): hoàn thiện form đặt căn hộ và trang thanh toán cọc`

---

## 5.3. Hiếu

### A. Phần GIS chính của Hiếu

**Cụm GIS 3 - Chỉ đường và routing**

#### File và cụm code Hiếu phụ trách

1. `myapp/tool.py`
   - Hàm `get_travel_speed_kmh(...)` - dòng `9` tới `15`
   - Hàm `estimate_duration_minutes(...)` - dòng `18` tới `23`
   - Lớp `RoutingTool` - dòng `44` tới `105`
   - Phương thức `RoutingTool.get_route(...)` - dòng `47` tới `105`

2. `myapp/views.py`
   - Hàm `get_route_api(request)` - dòng `584` tới `597`

3. `myapp/templates/map.html`
   - Khối giao diện `direction-panel` - dòng `207` tới `234`
   - Hàm `prepareRoute(lat, lng, name)` - dòng `888` tới `899`
   - Hàm `callPythonAPI()` - dòng `901` tới `962`
   - Hàm `selectRoute(selectedIndex)` - dòng `987` tới `1009`
   - Hàm `changeMode(mode, button)` - dòng `1011` tới `1016`
   - Hàm `checkUrlForAutoRoute()` - dòng `1039` tới `1057`
   - Các phần giao diện/JS liên quan đến:
     - mở panel chỉ đường,
     - gọi API route,
     - hiển thị nhiều tuyến,
     - đổi chế độ di chuyển,
     - hiển thị khoảng cách và thời gian,
     - chọn tuyến đang active.

4. Tích hợp deep-link route
   - `myapp/templates/home.html` - nút chuyển sang map với `target_id` ở dòng `94` tới `96`
   - `myapp/templates/apartment_detail.html` - liên kết mở đường đi ở dòng `83` tới `85`
   - `myapp/templates/map.html` - cụm xử lý `target_id`, `q` trong `checkUrlForAutoRoute()` ở dòng `1039` tới `1057`

#### Mục tiêu sản phẩm của Hiếu

1. Hoàn thiện chức năng **chỉ đường** từ vị trí người dùng đến căn hộ.
2. Hỗ trợ nhiều phương tiện:
   - ô tô,
   - xe máy,
   - đi bộ.
3. Hiển thị nhiều tuyến đường và cho phép chọn tuyến.
4. Đảm bảo từ trang chủ và trang chi tiết căn hộ có thể bấm để mở map và chỉ đường ngay.

### B. Phần không GIS bổ trợ của Hiếu

Hiếu phụ trách auth, OTP và dashboard quản trị:

1. `myapp/models.py`
   - Lớp `PasswordOTP` - dòng `186` tới `226`

2. `myapp/views.py`
   - Hàm `register(...)` - dòng `634` tới `664`
   - Hàm `register_confirm(...)` - dòng `667` tới `722`
   - Hàm `forgot_password_request(...)` - dòng `725` tới `749`
   - Hàm `forgot_password_confirm(...)` - dòng `752` tới `782`
   - Hàm `password_change_request(...)` - dòng `786` tới `812`
   - Hàm `password_change_confirm(...)` - dòng `816` tới `847`
   - Hàm `custom_admin(...)` - dòng `851` tới `867`
   - Hàm `user_admin(...)` - dòng `1122` tới `1124`
   - Hàm `user_create(...)` - dòng `1128` tới `1137`
   - Hàm `user_update(...)` - dòng `1141` tới `1151`
   - Hàm `user_delete(...)` - dòng `1155` tới `1165`

3. `myapp/forms.py`
   - Lớp `CustomRegisterForm` - dòng `499` tới `533`
   - Lớp `EmailOTPConfirmForm` - dòng `543` tới `563`
   - Lớp `PasswordResetRequestForm` - dòng `566` tới `586`
   - Lớp `OTPPasswordSetForm` - dòng `589` tới `648`
   - Lớp `UserAdminForm` - dòng `651` tới `682`

4. Các template:
   - `myapp/templates/login.html` - toàn file, dòng `1` tới `35`
   - `myapp/templates/register.html` - toàn file, dòng `1` tới `86`
   - `myapp/templates/register_confirm.html` - toàn file, dòng `1` tới `78`
   - `myapp/templates/forgot_password_request.html` - toàn file, dòng `1` tới `42`
   - `myapp/templates/forgot_password_confirm.html` - toàn file, dòng `1` tới `46`
   - `myapp/templates/password_change_request.html` - toàn file, dòng `1` tới `30`
   - `myapp/templates/password_change_confirm.html` - toàn file, dòng `1` tới `46`
   - `myapp/templates/custom_admin.html` - toàn file, dòng `1` tới `165`
   - `myapp/templates/user_admin.html` - toàn file, dòng `1` tới `80`
   - `myapp/templates/user_form.html` - toàn file, dòng `1` tới `56`

#### Lý do giao bổ trợ

Hiếu phụ trách routing, là phần GIS có sự kết hợp giữa:

1. dữ liệu vị trí,
2. session người dùng,
3. luồng thao tác trên hệ thống.

Vì vậy giao thêm auth và admin là hợp lý về mặt vận hành hệ thống.

### C. Commit gợi ý cho Hiếu

1. `feat(route): xây dựng RoutingTool và route API`
2. `feat(route-ui): thêm panel chỉ đường và chọn nhiều tuyến`
3. `feat(route): thêm đổi phương tiện di chuyển`
4. `feat(auth): hoàn thiện đăng ký, OTP và đổi mật khẩu`
5. `feat(admin): hoàn thiện dashboard và quản lý tài khoản`

# 6. Ma trận file code để đối chiếu trên GitHub

| File / Module | Giang | Bảo | Hiếu |
|---|---|---|---|
| `myapp/templates/map.html` | Map core, marker, popup, listing | Region search, nearby search, geocoding UI | Direction panel, route rendering, change mode |
| `myapp/views.py` | `map_view`, serialize data, GeoJSON | `geocode_place_api`, `reverse_geocode_api`, `search_region_api`, `search_nearby_api` | `get_route_api`, auth/admin phần bổ trợ |
| `myapp/tool.py` | Không phụ trách chính | `GISSearchTool`, `haversine_distance_km` | `RoutingTool`, `get_travel_speed_kmh`, `estimate_duration_minutes` |
| `myapp/templates/apartment_form.html` | Map picker, marker đặt tọa độ | geocode/reverse geocode và search địa điểm | Không phụ trách chính |
| `myapp/templates/home.html` | Trang chủ, UI tổng thể | Không phụ trách chính | Nút mở route, deep-link routing |
| `myapp/templates/apartment_detail.html` | Không phụ trách chính | booking/review/payment UI | Nút mở route và liên kết đến map |
| `myapp/templates/booking_payment.html` | Không phụ trách chính | Phụ trách | Không phụ trách chính |
| `myapp/templates/login-register-otp-admin` | Không phụ trách chính | Không phụ trách chính | Phụ trách |
| `myapp/static/css/*` | Phụ trách chính phần UI tổng thể | CSS booking/detail nếu cần | CSS auth/admin nếu cần |

# 7. Cách tổ chức GitHub để contribution rõ ràng

## 7.1. Cấu trúc branch đề xuất

1. `main`
2. `feature/giang-map-core`
3. `feature/bao-spatial-search`
4. `feature/hieu-routing-auth-admin`

## 7.2. Cách commit để dễ đối chiếu

### Giang

1. `feat(map): init leaflet map and apartment markers`
2. `feat(map): sync popup with apartment listing panel`
3. `feat(admin-map): add coordinate picker in apartment form`
4. `style(ui): refine base, home and intro pages`

### Bảo

1. `feat(search): add region search for apartment map`
2. `feat(search): add nearby search by distance/time`
3. `feat(geocode): connect geocode and reverse geocode APIs`
4. `feat(booking): improve booking and deposit payment flow`

### Hiếu

1. `feat(route): add routing service and API endpoint`
2. `feat(route-ui): render multi-route direction panel on map`
3. `feat(route): add travel mode switching`
4. `feat(auth): complete register OTP and password flows`
5. `feat(admin): complete admin dashboard and user management`

## 7.3. Nguyên tắc để tránh xung đột code

1. `map.html` là file dễ xung đột nhất, nên:
   - Giang commit xong cụm map core trước,
   - Bảo commit cụm search sau,
   - Hiếu commit cụm routing cuối,
   - merge theo từng pull request nhỏ.
2. `views.py` và `tool.py` phải commit theo hàm, không chỉnh sửa lấn sang hàm GIS của người khác.
3. Nếu cần sửa chung một file lớn, phải thống nhất trước ở mức hàm được giao trong tài liệu này.

# 8. Mục tiêu nộp môn và cách giải trình với giảng viên

Khi nộp môn, nhóm có thể giải trình theo cách sau:

1. **Giang** phụ trách lớp hiển thị và quản lý dữ liệu map.
2. **Bảo** phụ trách lớp tìm kiếm không gian và geocoding.
3. **Hiếu** phụ trách lớp chỉ đường và routing.
4. Ba phần trên hợp lại thành toàn bộ module GIS của hệ thống, được chia đều 33% - 33% - 33%.
5. Các phần còn lại được chia bổ trợ để đảm bảo mỗi thành viên vẫn có contribution rộng hơn trong dự án.

Đây là cách chia **hợp lý, cân bằng và dễ đối chiếu trên GitHub** cho một đồ án môn **Lập Trình GIS** cấp độ đại học.

# 9. Kết luận chính thức

Nhóm thống nhất phân công như sau:

1. **Giang** giữ **GIS 1 - Bản đồ hiển thị và quản lý dữ liệu map**.
2. **Bảo** giữ **GIS 2 - Tìm kiếm không gian và geocoding**.
3. **Hiếu** giữ **GIS 3 - Chỉ đường và routing**.

Phần GIS đã được chia đều cho 3 người đúng theo yêu cầu đặc biệt của môn học. Các phần không GIS được bố trí bổ trợ để việc lập trình, commit và trình bày trên GitHub rõ ràng hơn.

---

**Tài liệu này có thể dùng trực tiếp để nộp kèm hồ sơ GitHub của nhóm.**
