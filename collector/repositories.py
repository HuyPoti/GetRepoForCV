def get_authenticated_user(client):
    return client.get_json("/user")


def list_accessible_repos(client):
    """Repos the token's user owns, collaborates on, or has via org membership."""
    repos = client.paginate(
        "/user/repos",
        params={"affiliation": "owner,collaborator,organization_member"},
    )
    return list(repos)


def get_languages(client, owner, name):
    return client.get_json(f"/repos/{owner}/{name}/languages")
