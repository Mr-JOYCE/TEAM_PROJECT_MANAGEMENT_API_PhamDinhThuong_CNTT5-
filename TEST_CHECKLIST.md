# Checklist kiểm thử tích hợp

## 1. Chuẩn bị môi trường

- [ ] Cấu hình `DATABASE_URL` và `SECRET_KEY` trong file `.env`.
- [ ] Cài dependencies: `pip install -r requirements.txt`.
- [ ] Chạy migration: `alembic upgrade head`.
- [ ] Khởi động API: `uvicorn app.main:app --reload`.
- [ ] Kiểm tra API tại `/health`.
- [ ] Mở Swagger tại `/docs`.
- [ ] Nếu dùng Postman, tạo biến `base_url` và `access_token`.
- [ ] Có thể chạy `python seed.py` để tạo dữ liệu mẫu.

## 2. Authentication

| Trường hợp      | Request                                                                               | Kết quả mong đợi                              |
| --------------- | ------------------------------------------------------------------------------------- | --------------------------------------------- |
| Đăng ký đúng    | `POST /auth/register` với email mới, password tối thiểu 8 ký tự và `full_name` hợp lệ | `201`, response khớp `UserResponse`           |
| Email trùng     | Đăng ký lại cùng email                                                                | `400`, `code=BAD_REQUEST`, không phải `500`   |
| Body sai        | Thiếu password, password ngắn, email sai hoặc có field thừa                           | `422`, `code=VALIDATION_ERROR`                |
| Đăng nhập đúng  | `POST /auth/login` với form `email` và `password`                                     | `200`, nhận `access_token` và `refresh_token` |
| Sai password    | Đăng nhập với password sai                                                            | `401`, có `WWW-Authenticate: Bearer`          |
| Vượt rate limit | Sai password quá số lần cho phép                                                      | `429`, có header `Retry-After`                |
| Refresh đúng    | `POST /auth/refresh` với refresh token hợp lệ                                         | `200`, nhận cặp token mới                     |
| Refresh sai     | Gửi access token, token hỏng hoặc token hết hạn                                       | `401`, không phải `500`                       |

## 3. Users và phân quyền

| Trường hợp               | Request                                                 | Kết quả mong đợi                    |
| ------------------------ | ------------------------------------------------------- | ----------------------------------- |
| Xem hồ sơ hiện tại       | `GET /users/me` với Bearer token                        | `200`, response khớp `UserResponse` |
| Không có token           | Gọi endpoint cần đăng nhập                              | `401`                               |
| USER gọi endpoint admin  | `GET /users` hoặc `GET /admin/me` bằng token USER       | `403`                               |
| ADMIN xem danh sách user | `GET /users?search=...&is_active=true` bằng token ADMIN | `200`, danh sách `UserResponse`     |

## 4. Projects và members

| Trường hợp                        | Request                                                  | Kết quả mong đợi                       |
| --------------------------------- | -------------------------------------------------------- | -------------------------------------- |
| Tạo project                       | `POST /projects`                                         | `201`, user hiện tại là OWNER          |
| Liệt kê/tìm kiếm                  | `GET /projects` và `GET /projects?search=...`            | `200`, chỉ thấy project mình là member |
| Xem project                       | `GET /projects/{project_id}` khi là member               | `200`                                  |
| Project không tồn tại hoặc đã xóa | GET/PATCH/DELETE với id không hợp lệ                     | `404`, không phải `500`                |
| Cập nhật rỗng                     | `PATCH /projects/{id}` với `{}`                          | `400`                                  |
| MEMBER cập nhật/xóa project       | MEMBER gọi PATCH hoặc DELETE project                     | `403`                                  |
| Thêm member                       | OWNER gọi `POST /projects/{id}/members` với user tồn tại | `201`                                  |
| Member trùng hoặc không tồn tại   | Gửi lại member hoặc gửi user id sai                      | `400` hoặc `404`, không phải `500`     |
| Xóa OWNER                         | OWNER tự xóa mình khỏi project                           | `400`                                  |
| Xóa project                       | OWNER gọi `DELETE /projects/{id}`                        | `204`, project không còn trong list    |

## 5. Tasks, comments và attachments

| Trường hợp             | Request                                                                          | Kết quả mong đợi                    |
| ---------------------- | -------------------------------------------------------------------------------- | ----------------------------------- |
| Tạo task               | `POST /projects/{id}/tasks` với title, status và priority hợp lệ                 | `201`, response khớp `TaskResponse` |
| Assignee ngoài project | Tạo task với `assignee_id` không phải member                                     | `403`                               |
| Lọc và phân trang      | GET tasks với `status`, `priority`, `search`, `limit`, `offset`, `sort`, `order` | `200`, kết quả đúng bộ lọc          |
| Query sai              | `limit=0`, `offset=-1` hoặc sort/order không hợp lệ                              | `422`                               |
| Xem và sửa task        | GET/PATCH task hợp lệ                                                            | `200`                               |
| Cập nhật rỗng          | PATCH task với `{}`                                                              | `400`                               |
| MEMBER sửa trái quyền  | MEMBER sửa assignee hoặc field không được phép                                   | `403`                               |
| Xóa task               | OWNER xóa task; MEMBER xóa task                                                  | OWNER: `204`; MEMBER: `403`         |
| Task không tồn tại     | GET/PATCH/DELETE/comment/attachment với id sai                                   | `404`, không phải `500`             |
| Thêm và xem bình luận  | POST comment hợp lệ, sau đó GET comments                                         | POST: `201`; GET: `200`             |
| Bình luận sai          | Content rỗng, quá dài hoặc không có quyền                                        | `422` hoặc `403`                    |
| File hợp lệ            | Multipart PDF/PNG/TXT/DOCX không quá 10 MB, sau đó GET attachments               | POST: `201`; GET: `200`             |
| File sai loại          | Upload `.exe` hoặc content type không được phép                                  | `400`                               |
| File quá lớn           | Upload file trên 10 MB                                                           | `400`                               |
| Tên file sai           | Extension không cho phép hoặc tên dài hơn 255 ký tự                              | `400`                               |

## 6. Tiêu chí nghiệm thu

### Lỗi và response

- [ ] Không có case nghiệp vụ thông thường nào trả `500`.
- [ ] Lỗi xác thực trả `401`.
- [ ] Lỗi quyền trả `403`.
- [ ] Không tìm thấy tài nguyên trả `404`.
- [ ] Dữ liệu request sai trả `422`.
- [ ] Xung đột dữ liệu trả `400` hoặc `409` theo contract.
- [ ] Response thành công đúng schema và status code trong Swagger.

### OpenAPI

- [ ] Mỗi operation có `tags`.
- [ ] Mỗi operation có `summary` và `description` dễ hiểu.
- [ ] Khai báo đầy đủ response thành công và response lỗi.
- [ ] Response model trong OpenAPI khớp với dữ liệu thực tế.
- [ ] Kiểm tra thành công endpoint `GET /openapi.json`.

## 7. Chạy test tự động

```powershell
pytest -q
```
