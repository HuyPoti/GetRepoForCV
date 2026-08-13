"""Fetches README content for repos that show real contribution activity.

Deterministic data-gathering step. The actual understanding (turning README +
stats into role/technology/evidence) is done by the analyze-github-repos skill,
not here — this script only fetches raw text.
"""
import json
import sys
from pathlib import Path

from collector.github_client import GitHubClient

OUTPUT_DIR = Path(__file__).parent.parent / "output"


def find_latest(pattern):
    matches = sorted(OUTPUT_DIR.glob(pattern))
    if not matches:
        raise FileNotFoundError(f"No file matching {pattern} in {OUTPUT_DIR}")
    return matches[-1]


def has_contribution(repo):
    c = repo["your_contributions"]
    return (
        c["commits"]["count"] > 0
        or c["pull_requests_authored"] > 0
        or c["pull_requests_reviewed"] > 0
        or c["issues_authored"] > 0
    )


def main():
    repos_path = find_latest("github_repos_*.json")
    with open(repos_path, encoding="utf-8") as f:
        data = json.load(f)

    client = GitHubClient()
    readmes = {}
    contributed = [r for r in data["repositories"] if has_contribution(r)]
    print(f"Fetching READMEs for {len(contributed)} repos with real contribution "
          f"(out of {len(data['repositories'])} total)")

    for i, repo in enumerate(contributed, 1):
        full_name = repo["repo"]
        owner, name = full_name.split("/")
        print(f"[{i}/{len(contributed)}] {full_name}")
        try:
            text = client.get_readme_text(owner, name)
        except Exception as exc:
            print(f"  ! README fetch failed: {exc}")
            text = None
        readmes[full_name] = text

    out_path = OUTPUT_DIR / "repo_readmes.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(readmes, f, indent=2, ensure_ascii=False)

    print(f"\nSaved {len(readmes)} README entries to {out_path}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Fatal error: {exc}", file=sys.stderr)
        sys.exit(1)
