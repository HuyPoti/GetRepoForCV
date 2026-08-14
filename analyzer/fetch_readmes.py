"""Fetches README content for repos that show real contribution activity.

Script này có nhiệm vụ thu thập nội dung README của các repository mà người dùng
có đóng góp thực sự (commit, PR, issue). Đây là bước thu thập dữ liệu thô, 
việc phân tích dữ liệu sẽ được thực hiện ở một bước khác.
"""
import json
import sys
from pathlib import Path

from collector.github_client import GitHubClient

OUTPUT_DIR = Path(__file__).parent.parent / "output"


def find_latest(pattern):
    """
    Tìm file mới nhất khớp với pattern truyền vào trong thư mục OUTPUT_DIR.
    """
    # sorted: Sắp xếp danh sách (Input: iterable, Output: list đã sắp xếp)
    # glob: Tìm các file khớp với pattern (Input: chuỗi pattern, Output: generator các Path)
    matches = sorted(OUTPUT_DIR.glob(pattern))
    if not matches:
        raise FileNotFoundError(f"No file matching {pattern} in {OUTPUT_DIR}")
    return matches[-1]


def has_contribution(repo):
    """
    Kiểm tra xem người dùng có bất kỳ đóng góp nào (commit, PR, issue) 
    trong repository này hay không.
    """
    c = repo["your_contributions"]
    return (
        c["commits"]["count"] > 0
        or c["pull_requests_authored"] > 0
        or c["pull_requests_reviewed"] > 0
        or c["issues_authored"] > 0
    )


def main():
    """
    Hàm chính của script:
    1. Đọc danh sách repo từ file JSON mới nhất.
    2. Lọc ra các repo có đóng góp.
    3. Tải nội dung README của các repo đó thông qua GitHub API.
    4. Lưu kết quả ra file repo_readmes.json.
    """
    repos_path = find_latest("github_repos_*.json")
    # open: Mở file (Input: đường dẫn file, chế độ mở, encoding, Output: file object)
    with open(repos_path, encoding="utf-8") as f:
        # json.load: Đọc dữ liệu JSON từ file (Input: file object, Output: dict/list)
        data = json.load(f)

    client = GitHubClient()
    readmes = {}
    contributed = [r for r in data["repositories"] if has_contribution(r)]
    # len: Lấy số lượng phần tử (Input: danh sách, Output: số nguyên)
    # print: In dữ liệu ra màn hình (Input: chuỗi/biến, Output: None)
    print(f"Fetching READMEs for {len(contributed)} repos with real contribution "
          f"(out of {len(data['repositories'])} total)")

    # enumerate: Tạo iterator kèm chỉ số (Input: iterable, start index, Output: tuple (index, item))
    for i, repo in enumerate(contributed, 1):
        full_name = repo["repo"]
        # split: Cắt chuỗi thành danh sách (Input: ký tự phân cách, Output: list các chuỗi)
        owner, name = full_name.split("/")
        # print: In dữ liệu ra màn hình (Input: chuỗi/biến, Output: None)
        print(f"[{i}/{len(contributed)}] {full_name}")
        try:
            text = client.get_readme_text(owner, name)
        except Exception as exc:
            # print: In dữ liệu ra màn hình (Input: chuỗi/biến, Output: None)
            print(f"  ! README fetch failed: {exc}")
            text = None
        readmes[full_name] = text

    out_path = OUTPUT_DIR / "repo_readmes.json"
    # open: Mở file để ghi (Input: đường dẫn, chế độ "w", encoding, Output: file object)
    with open(out_path, "w", encoding="utf-8") as f:
        # json.dump: Ghi object Python ra file dưới dạng JSON (Input: object, file object, indent, ensure_ascii)
        json.dump(readmes, f, indent=2, ensure_ascii=False)

    # print: In dữ liệu ra màn hình (Input: chuỗi/biến, Output: None)
    print(f"\nSaved {len(readmes)} README entries to {out_path}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        # print: In dữ liệu ra luồng được chỉ định (Input: chuỗi/biến, file/stream, Output: None)
        print(f"Fatal error: {exc}", file=sys.stderr)
        # sys.exit: Thoát chương trình (Input: mã lỗi (1 là lỗi, 0 là thành công), Output: None)
        sys.exit(1)
