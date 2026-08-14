"""
Module cung cấp lớp GitHubClient để tương tác với GitHub API, bao gồm việc 
xử lý xác thực, tự động phân trang, và tự động chờ khi vượt quá rate limit.
"""
import base64
import os
import re
import time

import requests
from dotenv import load_dotenv

load_dotenv()

API_ROOT = "https://api.github.com"


class GitHubClient:
    """
    Lớp client đóng gói các thao tác gọi API tới GitHub.
    """
    def __init__(self, token=None):
        """
        Khởi tạo GitHubClient với token xác thực. 
        Nếu không truyền token, sẽ tự động lấy từ biến môi trường GITHUB_TOKEN.
        """
        # os.getenv: Lấy giá trị biến môi trường (Input: tên biến, Output: giá trị chuỗi hoặc None)
        self.token = token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            # RuntimeError: Báo lỗi khi thiếu token (Input: thông báo lỗi, Output: Exception)
            raise RuntimeError("GITHUB_TOKEN not set (check .env)")
        # requests.Session: Tạo phiên kết nối HTTP (Output: Session object)
        self.session = requests.Session()
        # dict.update: Cập nhật dictionary với các cặp key-value mới (Input: dictionary/mapping, Output: None)
        self.session.headers.update({
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        })

    def _request(self, method, path, **kwargs):
        """
        Thực hiện một HTTP request tới GitHub API, có xử lý tự động chờ (retry) 
        khi gặp lỗi rate limit (mã lỗi 403).
        """
        # startswith: Kiểm tra chuỗi bắt đầu (Input: chuỗi tiền tố, Output: bool)
        url = path if path.startswith("http") else f"{API_ROOT}{path}"
        while True:
            # session.request: Gửi HTTP request (Input: phương thức HTTP, URL, kwargs, Output: Response object)
            resp = self.session.request(method, url, **kwargs)
            # str.lower: Chuyển chuỗi thành chữ thường (Input: không, Output: chuỗi chữ thường)
            if resp.status_code == 403 and "rate limit" in resp.text.lower():
                # int: Ép kiểu sang số nguyên (Input: số/chuỗi, Output: int)
                # dict.get: Lấy giá trị header theo tên, nếu không có thì trả về default (Input: tên header, default, Output: string/float)
                # time.time: Lấy thời gian hiện tại (Output: số float giây từ epoch)
                reset = int(resp.headers.get("X-RateLimit-Reset", time.time() + 30))
                # max: Lấy giá trị lớn nhất (Input: các số, Output: số lớn nhất)
                wait = max(reset - time.time(), 1)
                # min: Lấy giá trị nhỏ nhất (Input: các số, Output: số nhỏ nhất)
                # time.sleep: Dừng luồng hiện tại một khoảng thời gian (Input: số giây, Output: None)
                time.sleep(min(wait, 60))
                continue
            if resp.status_code == 403 and resp.headers.get("Retry-After"):
                time.sleep(int(resp.headers["Retry-After"]))
                continue
            return resp

    def get(self, path, params=None):
        """
        Gửi request GET tới GitHub API và trả về object response của thư viện requests.
        """
        return self._request("GET", path, params=params)

    def get_json(self, path, params=None):
        """
        Gửi request GET tới GitHub API và trả về dữ liệu dưới dạng JSON.
        """
    def get_json(self, path, params=None):
        """
        Gửi request GET tới GitHub API và trả về dữ liệu dưới dạng JSON.
        """
        resp = self.get(path, params=params)
        # raise_for_status: Phát sinh exception nếu HTTP status code là lỗi (4xx, 5xx) (Output: None hoặc Exception)
        resp.raise_for_status()
        # json: Chuyển đổi payload từ JSON sang object Python (Output: dict/list)
        return resp.json()

    def paginate(self, path, params=None, per_page=100):
        """
        Tự động phân trang (paginate) các kết quả trả về từ GitHub API. 
        Trả về một generator yield từng item một.
        """
        params = dict(params or {})
        params["per_page"] = per_page
        page = 1
        while True:
            params["page"] = page
            resp = self.get(path, params=params)
            resp.raise_for_status()
            items = resp.json()
            if not items:
                break
            yield from items
            if len(items) < per_page:
                break
            page += 1

    def count_via_last_page(self, path, params=None, cap_pages=5):
        """
        Đếm số lượng item một cách nhanh chóng bằng cách kiểm tra số trang cuối cùng 
        trong header Link (với per_page=1).
        Giới hạn số trang tối đa (cap_pages) để tránh sử dụng quá nhiều rate limit 
        cho các lịch sử quá lớn. Trả về tuple: (số lượng, có bị giới hạn hay không).
        """
        # dict: Tạo dictionary (Input: iterable/mapping, Output: dict)
        params = dict(params or {})
        params["per_page"] = 1
        params["page"] = 1
        resp = self.get(path, params=params)
        # raise_for_status: Kiểm tra trạng thái HTTP (Output: None/Exception)
        resp.raise_for_status()
        # dict.get: Lấy giá trị header "Link" (Input: key, default, Output: string)
        link = resp.headers.get("Link", "")
        # re.search: Tìm kiếm chuỗi theo Regex (Input: regex pattern, chuỗi, Output: match object)
        match = re.search(r'page=(\d+)>; rel="last"', link)
        if match:
            # match.group: Lấy chuỗi khớp với pattern theo nhóm (Input: index nhóm, Output: chuỗi)
            total = int(match.group(1))
            if total > cap_pages * 1:
                return cap_pages * 1, True
            return total, False
        # json: Chuyển payload của response sang object Python
        data = resp.json()
        return (1 if data else 0), False

    def get_readme_text(self, owner, name, max_chars=6000):
        """
        Lấy nội dung file README của một repository, giải mã base64 và trả về chuỗi text.
        Trả về tối đa `max_chars` ký tự đầu tiên.
        """
        resp = self.get(f"/repos/{owner}/{name}/readme")
        if resp.status_code == 404:
            return None
        # raise_for_status: Kiểm tra HTTP errors
        resp.raise_for_status()
        # json: Phân tích JSON body
        data = resp.json()
        # base64.b64decode: Giải mã chuỗi base64 (Input: chuỗi/byte base64, Output: bytes)
        # decode: Chuyển bytes thành chuỗi (Input: encoding, errors, Output: chuỗi)
        content = base64.b64decode(data["content"]).decode("utf-8", errors="replace")
        return content[:max_chars]

    def search_count(self, query):
        """
        Sử dụng Search API của GitHub để lấy tổng số lượng kết quả (total_count).
        Vì Search API có rate limit khắt khe (~30 request/phút), 
        các hàm gọi tới cần tự throttle (chờ) giữa các lần gọi.
        """
        data = self.get_json("/search/issues", params={"q": query, "per_page": 1})
        return data.get("total_count", 0)
