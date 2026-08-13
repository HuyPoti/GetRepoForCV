# GetRepoForCV

Scan every GitHub repo you're a member/owner/collaborator of, turn real
contribution data into an evidence-grounded project knowledge base, then
match it against a job description to draft CV bullet points — grounded in
actual commits/PRs/reviews, not invented achievements.

Runs as a small Python collector + two Claude Code skills. No external LLM
API key needed — the "analysis" and "matching" steps run as Claude Code
skills, using whatever Claude Code session/model you already have.

## Why

LLMs asked to "read my GitHub and write my CV" tend to turn small
permissions and thin activity into inflated bullet points. This project
separates concerns:

- **Code does discovery**: repo listing, permissions, commit/PR/review
  counts, README fetching — all deterministic, via the GitHub API.
- **Claude does understanding**: turning that evidence into role/technology/
  responsibility claims (via the `analyze-github-repos` skill), and matching
  those claims against a job description (via the `match-job-description`
  skill) — with an explicit no-fabrication rule at every step.

## Requirements

- Python 3.9+
- [Claude Code](https://claude.com/claude-code) (to run the two skills)
- A GitHub personal access token

## Setup

```bash
python -m venv venv
venv\Scripts\activate        # Windows; `source venv/bin/activate` on macOS/Linux
pip install -r requirements.txt
cp .env.example .env         # then edit .env and fill in your token
```

Generate a token at github.com/settings/tokens (classic) with scopes:
`repo`, `read:org`, `read:user`.

**Never commit `.env`** — it's already in `.gitignore`. If you ever paste a
real token into a terminal, a log, or a chat session, treat it as
compromised and revoke/regenerate it at
github.com/settings/tokens before relying on this tool for anything real.

## Usage

1. **Collect** — scan every repo you can access and tally your real
   contribution to each:
   ```bash
   python main.py
   ```
   Writes `output/github_repos_<timestamp>.json`.

2. **Fetch READMEs** — for repos where you actually have activity
   (nonzero commits/PRs/reviews):
   ```bash
   python -m analyzer.fetch_readmes
   ```
   Writes `output/repo_readmes.json`.

3. **Analyze** (Claude Code skill) — turn the raw data into a knowledge
   base of role/technologies/responsibilities per repo, grounded in the
   evidence:
   ```
   /analyze-github-repos
   ```
   Writes `output/project_knowledge_base.json`.

4. **Match against a job description** (Claude Code skill):
   ```
   /match-job-description path/to/job_description.txt
   ```
   Writes `output/cv_recommendations.md` — ranked projects plus draft CV
   bullets, each traceable back to real evidence.

## How scoring works

**Contribution score** (per repo, 0-100): weighted combination of
permission level, commit count, PRs authored, and PRs reviewed. See
[`.claude/skills/analyze-github-repos/SKILL.md`](.claude/skills/analyze-github-repos/SKILL.md)
for the exact formula.

**JD match score** (per repo, 0-100): weighted combination of technology
overlap, responsibility overlap, contribution strength, role relevance,
recency, and repo quality. See
[`.claude/skills/match-job-description/SKILL.md`](.claude/skills/match-job-description/SKILL.md)
for the exact formula.

Both skills carry an explicit rule: **never claim what the evidence doesn't
support.** Thin evidence produces a conservative, flagged entry instead of
an inflated bullet point.

## Project layout

```
collector/          GitHub API client, repo listing, contribution counts
analyzer/           README fetching (deterministic data gathering)
.claude/skills/      analyze-github-repos, match-job-description
output/              generated data — gitignored, regenerate anytime
```

## Notes

- Search API calls (PRs authored/reviewed, issues authored) are throttled to
  stay under GitHub's ~30 requests/minute secondary rate limit — expect the
  collector to take a few seconds per repo.
- Commit counts are capped (default 300) via the `Link` header's last-page
  trick to avoid burning rate limit on huge histories; a `capped: true` flag
  is recorded when this happens.

## Contributing

Bug reports, scoring-formula tweaks, and new data sources are welcome — see
[CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE)
