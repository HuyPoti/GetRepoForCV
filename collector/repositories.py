"""
Module cung cấp các hàm để lấy thông tin repository và người dùng từ GitHub API.
"""
def get_authenticated_user(client):
    """
    Lấy thông tin của người dùng đang được xác thực (dựa vào token).
    """
    return client.get_json("/user")


def list_accessible_repos(client):
    """
    Lấy danh sách các repository mà người dùng có quyền truy cập 
    (bao gồm: sở hữu, cộng tác viên, hoặc thành viên tổ chức).
    """
    repos = client.paginate(
        "/user/repos",
        params={"affiliation": "owner,collaborator,organization_member"},
    )
    # list: Chuyển đổi một iterable thành danh sách (Input: iterable, Output: list)
    return list(repos)


def get_languages(client, owner, name):
    """
    Lấy danh sách các ngôn ngữ lập trình được sử dụng trong một repository cụ thể.
    """
    return client.get_json(f"/repos/{owner}/{name}/languages")
