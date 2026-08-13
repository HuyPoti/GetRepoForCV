---
name: analyze-github-repos
description: Turn raw GitHub repo/contribution data (from main.py + analyzer/fetch_readmes.py) into an evidence-grounded project knowledge base — role, technologies, responsibilities, contribution score per repo. Run this after collecting data, before matching against a job description.
---

# Analyze GitHub Repos

## Purpose

Convert the raw data sitting in `output/github_repos_*.json` and
`output/repo_readmes.json` into a structured, evidence-grounded knowledge
base at `output/project_knowledge_base.json`. This is the "understanding"
step: turning numbers and README text into role/technology/responsibility
claims that a later step can safely put on a CV.

**Core rule: only claim what the data supports.** Commit/PR/review counts
and README text are ground truth. Never invent features, achievements, or
responsibilities that aren't stated in the README or directly implied by the
contribution numbers. If evidence is thin, say so — a low-confidence entry is
more useful than a fabricated one.

## Steps

1. Find the most recently modified `output/github_repos_*.json` and read it,
   along with `output/repo_readmes.json`. If either is missing, tell the user
   to run `python main.py` and `python -m analyzer.fetch_readmes` first, and
   stop.

2. For each repo in the collected data, skip it if it has zero contribution
   (`commits.count == 0 and pull_requests_authored == 0 and
   pull_requests_reviewed == 0 and issues_authored == 0`) — no evidence, no
   entry.

3. For each remaining repo, compute:

   **Role tier** (pick the highest that applies):
   - `owner_or_lead` — `permission.admin` is true AND (commits ≥ 20 OR PRs
     authored ≥ 5)
   - `maintainer_reviewer` — `permission.maintain` or `permission.push` is
     true AND PRs reviewed ≥ 3
   - `core_contributor` — `permission.push` is true AND commits ≥ 5
   - `minor_contributor` — any other case with nonzero activity

   **Contribution score (0-100)**, using only these inputs (don't
   improvise a different formula):
   ```
   permission_score = 100 if admin, 80 if maintain, 60 if push, 20 if pull-only
   commit_score      = min(100, commits.count * 2)
   pr_score           = min(100, pull_requests_authored * 10)
   review_score       = min(100, pull_requests_reviewed * 15)

   contribution_score = round(
       0.25 * permission_score +
       0.35 * commit_score +
       0.25 * pr_score +
       0.15 * review_score
   )
   ```
   Note when `commits.capped` is true (very high commit count truncated by
   the collector) — treat commit_score as a floor, not exact.

   **Technologies**: union of the repo's `languages` keys and any
   frameworks/libraries/tools *explicitly named* in the README (e.g. "React",
   "PostgreSQL", "Docker"). Do not infer a technology from vague wording.

   **Responsibilities**: 2-5 short phrases describing what was actually done,
   grounded in the README's stated purpose/features and the role tier (e.g.
   "backend API development", "CI/CD pipeline setup" — only if the README or
   repo topics actually indicate this). If the README is missing or empty,
   base responsibilities only on role tier + tech stack and mark
   `"readme_available": false`.

   **Evidence**: list the concrete facts used to justify the above, e.g.
   `"23 commits"`, `"reviewed 4 pull requests"`, `"permission: push"`,
   `"README describes REST API for order management"`.

4. Write the full list to `output/project_knowledge_base.json` as a JSON
   array, one object per repo:
   ```json
   {
     "repo": "owner/name",
     "role": "core_contributor",
     "contribution_score": 74,
     "technologies": ["TypeScript", "React", "PostgreSQL"],
     "responsibilities": ["backend API development", "database schema design"],
     "evidence": ["23 commits", "permission: push", "README describes REST API"],
     "readme_available": true,
     "stars": 0,
     "updated_at": "2025-10-01T12:22:18Z",
     "archived": false
   }
   ```

5. Print a short summary table to the chat (repo, role, contribution_score) —
   do not dump the full JSON into the conversation. Tell the user the
   knowledge base is ready for the `match-job-description` skill.
