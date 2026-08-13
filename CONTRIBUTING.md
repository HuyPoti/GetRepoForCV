# Contributing

Thanks for considering a contribution to GetRepoForCV.

## Getting set up

```bash
python -m venv venv
venv\Scripts\activate        # Windows; use `source venv/bin/activate` on macOS/Linux
pip install -r requirements.txt
cp .env.example .env         # then fill in your own GITHUB_TOKEN
```

See the main [README](README.md) for the full pipeline (`main.py` →
`analyzer/fetch_readmes.py` → `analyze-github-repos` skill →
`match-job-description` skill) and how the scoring formulas work.

## Ways to contribute

- **Bug reports**: open an issue with the command you ran, the error, and
  (with secrets redacted) the relevant output.
- **New data sources**: e.g. pulling GitLab/Bitbucket repos, or richer
  contribution signals (issue comments, code review comments).
- **Scoring improvements**: the contribution-score and JD-match formulas
  live in the two `SKILL.md` files under `.claude/skills/` — they're plain
  markdown, easy to tune.
- **Bug fixes / refactors** to `collector/` or `analyzer/`.

## Guidelines

- Keep the separation of concerns: `collector/` and `analyzer/` should stay
  deterministic (no LLM calls) — data gathering only. Anything that requires
  judgment (turning evidence into role/technology claims, matching against a
  JD) belongs in the `.claude/skills/` instructions, not in Python.
- **Never fabricate.** Both skills carry an explicit rule that every claim
  must trace back to real evidence (commit/PR/review counts, README text,
  permission level). Contributions that loosen this — e.g. inferring
  achievements from vague signals — will be asked to tighten it back up.
- Don't commit real tokens, `.env` files, or personal data (CVs, emails,
  phone numbers) — check `.gitignore` covers anything you add that contains
  personal or private data.
- Keep PRs focused. Small, reviewable changes over large rewrites.

## Reporting security issues

If you find a way this tool could leak a token, over-request GitHub scopes,
or otherwise behave unsafely, please open an issue describing the concern
(no need for exploit details) so it can be addressed.
