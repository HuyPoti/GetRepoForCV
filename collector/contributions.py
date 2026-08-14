"""
Module chứa các hàm kiểm tra và đếm số lượng đóng góp của người dùng 
vào các repository (bao gồm: commit, pull request, issue).
"""
import time

SEARCH_THROTTLE_SECONDS = 2.2  # keep under ~30 req/min secondary rate limit


def get_commit_count(client, owner, name, username):
    """
    Đếm số lượng commit của người dùng trong một repository 
    (giới hạn số trang tối đa để tránh vượt quá rate limit của API).
    """
    count, capped = client.count_via_last_page(
        f"/repos/{owner}/{name}/commits",
        params={"author": username},
        cap_pages=300,
    )
    return {"count": count, "capped": capped}


def get_pr_authored_count(client, owner, name, username):
    """
    Đếm số lượng pull request do người dùng tạo trong một repository.
    """
    query = f"repo:{owner}/{name} type:pr author:{username}"
    count = client.search_count(query)
    # time.sleep: Dừng luồng hiện tại một khoảng thời gian (Input: số giây, Output: None)
    time.sleep(SEARCH_THROTTLE_SECONDS)
    return count


def get_pr_reviewed_count(client, owner, name, username):
    """
    Đếm số lượng pull request do người dùng review trong một repository.
    """
    query = f"repo:{owner}/{name} type:pr reviewed-by:{username}"
    count = client.search_count(query)
    # time.sleep: Dừng luồng hiện tại một khoảng thời gian (Input: số giây, Output: None)
    time.sleep(SEARCH_THROTTLE_SECONDS)
    return count


def get_issues_authored_count(client, owner, name, username):
    """
    Đếm số lượng issue do người dùng tạo trong một repository.
    """
    query = f"repo:{owner}/{name} type:issue author:{username}"
    count = client.search_count(query)
    # time.sleep: Dừng luồng hiện tại một khoảng thời gian (Input: số giây, Output: None)
    time.sleep(SEARCH_THROTTLE_SECONDS)
    return count
