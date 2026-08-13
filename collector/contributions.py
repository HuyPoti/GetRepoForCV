import time

SEARCH_THROTTLE_SECONDS = 2.2  # keep under ~30 req/min secondary rate limit


def get_commit_count(client, owner, name, username):
    count, capped = client.count_via_last_page(
        f"/repos/{owner}/{name}/commits",
        params={"author": username},
        cap_pages=300,
    )
    return {"count": count, "capped": capped}


def get_pr_authored_count(client, owner, name, username):
    query = f"repo:{owner}/{name} type:pr author:{username}"
    count = client.search_count(query)
    time.sleep(SEARCH_THROTTLE_SECONDS)
    return count


def get_pr_reviewed_count(client, owner, name, username):
    query = f"repo:{owner}/{name} type:pr reviewed-by:{username}"
    count = client.search_count(query)
    time.sleep(SEARCH_THROTTLE_SECONDS)
    return count


def get_issues_authored_count(client, owner, name, username):
    query = f"repo:{owner}/{name} type:issue author:{username}"
    count = client.search_count(query)
    time.sleep(SEARCH_THROTTLE_SECONDS)
    return count
