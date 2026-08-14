"""
Script chính của chương trình.
Thực hiện việc xác thực GitHub, lấy danh sách các repository có quyền truy cập,
thu thập dữ liệu về ngôn ngữ và các đóng góp (commits, PRs, issues) của người dùng,
và lưu toàn bộ dữ liệu vào một file JSON trong thư mục output.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from collector.github_client import GitHubClient
from collector.repositories import get_authenticated_user, get_languages, list_accessible_repos
from collector.contributions import (
    get_commit_count,
    get_issues_authored_count,
    get_pr_authored_count,
    get_pr_reviewed_count,
)

OUTPUT_DIR = Path(__file__).parent / "output"


def build_repo_record(client, repo, username):
    """
    Xây dựng một bản ghi (dictionary) chứa đầy đủ thông tin chi tiết về một repository, 
    bao gồm thống kê các đóng góp của người dùng (commits, PRs, issues) và ngôn ngữ sử dụng.
    """
    owner = repo["owner"]["login"]
    name = repo["name"]
    full_name = repo["full_name"]

    try:
        languages = get_languages(client, owner, name)
    except Exception as exc:
        # print: In dữ liệu ra màn hình (Input: chuỗi/biến, Output: None)
        print(f"  ! languages failed for {full_name}: {exc}")
        languages = {}

    try:
        commits = get_commit_count(client, owner, name, username)
    except Exception as exc:
        print(f"  ! commit count failed for {full_name}: {exc}")
        commits = {"count": 0, "capped": False}

    try:
        prs_authored = get_pr_authored_count(client, owner, name, username)
    except Exception as exc:
        print(f"  ! PR authored count failed for {full_name}: {exc}")
        prs_authored = 0

    try:
        prs_reviewed = get_pr_reviewed_count(client, owner, name, username)
    except Exception as exc:
        print(f"  ! PR reviewed count failed for {full_name}: {exc}")
        prs_reviewed = 0

    try:
        issues_authored = get_issues_authored_count(client, owner, name, username)
    except Exception as exc:
        print(f"  ! issues count failed for {full_name}: {exc}")
        issues_authored = 0

    # dict.get: Lấy giá trị từ dictionary theo key, trả về default nếu không có (Input: key, giá trị mặc định, Output: giá trị)
    permissions = repo.get("permissions", {})

    return {
        "repo": full_name,
        "url": repo["html_url"],
        "description": repo.get("description"),
        "private": repo["private"],
        "fork": repo["fork"],
        "archived": repo["archived"],
        "owner_type": repo["owner"]["type"],
        "created_at": repo["created_at"],
        "updated_at": repo["updated_at"],
        "pushed_at": repo["pushed_at"],
        "stars": repo["stargazers_count"],
        "primary_language": repo.get("language"),
        "languages": languages,
        "topics": repo.get("topics", []),
        "permission": {
            "admin": permissions.get("admin", False),
            "maintain": permissions.get("maintain", False),
            "push": permissions.get("push", False),
            "pull": permissions.get("pull", False),
        },
        "your_contributions": {
            "commits": commits,
            "pull_requests_authored": prs_authored,
            "pull_requests_reviewed": prs_reviewed,
            "issues_authored": issues_authored,
        },
    }


def main():
    """
    Hàm chính của chương trình:
    1. Xác thực người dùng qua GitHubClient.
    2. Lấy danh sách các repository có thể truy cập.
    3. Thu thập thông tin chi tiết và thống kê đóng góp cho từng repository.
    4. Lưu kết quả ra file JSON có kèm timestamp.
    5. In ra màn hình số lượng repo có hoạt động đóng góp thực sự.
    """
    client = GitHubClient()

    user = get_authenticated_user(client)
    username = user["login"]
    # print: In dữ liệu ra màn hình (Input: chuỗi/biến, Output: None)
    print(f"Authenticated as: {username}")

    repos = list_accessible_repos(client)
    # len: Lấy số lượng phần tử của list/collection (Input: collection, Output: integer)
    print(f"Found {len(repos)} accessible repositories\n")

    records = []
    # enumerate: Tạo iterator gồm cặp (index, giá trị) (Input: iterable, start, Output: iterator)
    for i, repo in enumerate(repos, 1):
        # print: In dữ liệu ra màn hình (Input: chuỗi/biến, Output: None)
        print(f"[{i}/{len(repos)}] {repo['full_name']}")
        record = build_repo_record(client, repo, username)
        # append: Thêm phần tử vào cuối danh sách (Input: object, Output: None)
        records.append(record)

    OUTPUT_DIR.mkdir(exist_ok=True)
    # datetime.now: Lấy thời gian hiện tại (Input: timezone, Output: datetime object)
    # strftime: Định dạng chuỗi thời gian (Input: format string, Output: chuỗi thời gian)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = OUTPUT_DIR / f"github_repos_{timestamp}.json"
    # open: Mở file (Input: file path, mode, encoding, Output: file object)
    with open(out_path, "w", encoding="utf-8") as f:
        # json.dump: Lưu object dưới dạng JSON vào file (Input: object, file object, indent, ensure_ascii, Output: None)
        json.dump({"username": username, "collected_at": timestamp, "repositories": records}, f, indent=2, ensure_ascii=False)

    # print: In dữ liệu ra màn hình (Input: chuỗi/biến, Output: None)
    print(f"\nSaved {len(records)} repo records to {out_path}")

    with_contribution = [r for r in records if r["your_contributions"]["commits"]["count"] > 0
                          or r["your_contributions"]["pull_requests_authored"] > 0]
    print(f"Repos with actual contribution activity: {len(with_contribution)}/{len(records)}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        # print: In dữ liệu ra luồng được chỉ định (Input: chuỗi/biến, file/stream, Output: None)
        print(f"Fatal error: {exc}", file=sys.stderr)
        # sys.exit: Thoát chương trình (Input: mã lỗi, Output: None)
        sys.exit(1)
