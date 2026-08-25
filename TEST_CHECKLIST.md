# Checklist integration test

## Chuẩn bị

- [ ] Chạy migration: `alembic upgrade head`.
- [ ] Đặt `DATABASE_URL` và `SECRET_KEY` trong `.env`.
- [ ] Chạy API: `uvicorn app.main:app --reload`.
- [ ] Mở Swagger tại `/docs`; với Postman tạo biến `base_url` và `access_token`.
- [ ] Có thể chạy `python seed.py` để có các tài khoản mẫu.

## Authentication

| Case            | Request                                                                    | Kỳ vọng                                      |
| --------------- | -------------------------------------------------------------------------- | -------------------------------------------- |
| Đăng ký đúng    | `POST /auth/register` với email mới, password >= 8 ký tự, full_name hợp lệ | `201`, body khớp `UserResponse`              |
| Email trùng     | Đăng ký lại cùng email                                                     | `400`, `code=BAD_REQUEST`, không phải `500`  |
| Body sai        | Thiếu password, password ngắn, email sai hoặc field thừa                   | `422`, `code=VALIDATION_ERROR`               |
| Đăng nhập đúng  | `POST /auth/login` form `email` + `password`                               | `200`, lưu `access_token` và `refresh_token` |
| Sai password    | Đăng nhập với password sai                                                 | `401`, có `WWW-Authenticate: Bearer`         |
| Vượt rate limit | Sai password quá số lần cấu hình                                           | `429`, có `Retry-After`                      |
| Refresh đúng    | `POST /auth/refresh` với refresh token                                     | `200`, nhận token mới                        |
| Refresh sai     | Access token, token hỏng hoặc token hết hạn                                | `401`, không phải `500`                      |

## Users và phân quyền

| Case            | Request                                                 | Kỳ vọng                         |
| --------------- | ------------------------------------------------------- | ------------------------------- |
| Hồ sơ hiện tại  | `GET /users/me` với Bearer token                        | `200`, body khớp `UserResponse` |
| Không token     | Gọi endpoint cần đăng nhập                              | `401`                           |
| User gọi admin  | `GET /users` hoặc `GET /admin/me` bằng token USER       | `403`                           |
| Admin list user | `GET /users?search=...&is_active=true` bằng token ADMIN | `200`, danh sách `UserResponse` |

## Projects và members

| Case                         | Request                                              | Kỳ vọng                                |
| ---------------------------- | ---------------------------------------------------- | -------------------------------------- |
| Tạo đúng                     | `POST /projects`                                     | `201`, user hiện tại là OWNER          |
| List/search                  | `GET /projects`, `GET /projects?search=...`          | `200`, chỉ thấy project mình là member |
| Xem đúng                     | `GET /projects/{project_id}` là member               | `200`                                  |
| Project không tồn tại/đã xóa | GET/PATCH/DELETE id không hợp lệ                     | `404`, không phải `500`                |
| Update rỗng                  | `PATCH /projects/{id}` với `{}`                      | `400`                                  |
| Member update/delete         | MEMBER gọi PATCH/DELETE project                      | `403`                                  |
| Thêm member đúng             | OWNER `POST /projects/{id}/members` với user tồn tại | `201`                                  |
| Member trùng/không tồn tại   | Gửi lại hoặc user id sai                             | `400` hoặc `404`, không phải `500`     |
| Xóa OWNER                    | OWNER tự xóa mình khỏi project                       | `400`                                  |
| Xóa project                  | OWNER `DELETE /projects/{id}`                        | `204`, project không còn trong list    |

## Tasks, comments và attachments

| Case                   | Request                                                                          | Kỳ vọng                                 |
| ---------------------- | -------------------------------------------------------------------------------- | --------------------------------------- | ----- |
| Tạo task đúng          | `POST /projects/{id}/tasks` với title, status, priority hợp lệ                   | `201`, body khớp `TaskResponse`         |
| Assignee ngoài project | Tạo task với `assignee_id` không phải member                                     | `403`                                   |
| List/filter            | GET tasks với `status`, `priority`, `search`, `limit`, `offset`, `sort`, `order` | `200`, kết quả đúng filter              |
| Query sai              | `limit=0`, `offset=-1`, sort/order ngoài danh sách                               | `422`                                   |
| Xem/sửa task           | GET/PATCH task hợp lệ                                                            | `200`                                   |
| Update rỗng            | PATCH với `{}`                                                                   | `400`                                   |
| MEMBER sửa trái quyền  | Sửa assignee hoặc field không được phép                                          | `403`                                   |
| Xóa task               | OWNER xóa task                                                                   | `204`; MEMBER xóa task                  | `403` |
| Task không tồn tại     | GET/PATCH/DELETE/comment/attachment với id sai                                   | `404`, không phải `500`                 |
| Bình luận đúng         | POST comment có content hợp lệ, sau đó GET comments                              | `201`, rồi `200`                        |
| Bình luận sai          | Content rỗng/quá dài hoặc không có quyền                                         | `422` hoặc `403`                        |
| File đúng              | Multipart file PDF/PNG/TXT/DOCX <= 10 MB                                         | `201`, sau đó GET attachments trả `200` |
| File sai loại          | Upload `.exe` hoặc content type không cho phép                                   | `400`                                   |
| File quá lớn           | Upload trên 10 MB                                                                | `400`                                   |
| Tên file sai           | Extension không cho phép hoặc tên dài hơn 255 ký tự                              | `400`                                   |

## Tiêu chí nghiệm thu

- [ ] Không có case nghiệp vụ thông thường nào trả `500`.
- [ ] Lỗi xác thực trả `401`, lỗi quyền trả `403`, không tìm thấy trả `404`, dữ liệu sai trả `422`, xung đột dữ liệu trả `400`/`409` theo contract.
- [ ] Response thành công đúng schema và status code trong Swagger.
- [ ] Các endpoint có tag, summary, description và response error dễ đọc.
- [ ] Kiểm tra `GET /openapi.json`: tất cả operation có `tags`, `summary`, `responses`, `response model` phù hợp.
