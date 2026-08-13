---
name: match-job-description
description: Rank your analyzed GitHub projects against a job description and draft CV bullet points from real evidence only. Run analyze-github-repos first to build the knowledge base. Usage: /match-job-description path/to/jd.txt
---

# Match Job Description

## Purpose

Take a job description and `output/project_knowledge_base.json` (built by
the `analyze-github-repos` skill) and produce a ranked list of your most
relevant projects plus draft CV bullet points — grounded strictly in the
`evidence` field of each project, never invented.

## Steps

1. If `output/project_knowledge_base.json` doesn't exist, tell the user to
   run the `analyze-github-repos` skill first, and stop.

2. Read the job description from the path given as the skill argument (ask
   for it if not provided). Extract a short structured requirement list:
   - required technologies/tools
   - responsibility/domain keywords (e.g. "REST API", "team leadership",
     "system architecture")
   - seniority signals (e.g. "3+ years", "lead", "senior")

   Show this extracted list to the user briefly so they can sanity-check it.

3. For every project in the knowledge base, score it against the JD:

   ```
   technology_match      (0-100): overlap between JD technologies and project.technologies
   responsibility_match  (0-100): overlap between JD responsibility keywords and
                                   project.responsibilities / evidence text
   contribution_strength = project.contribution_score   (already 0-100)
   role_relevance         (0-100): higher if project.role is owner_or_lead or
                                   maintainer_reviewer and the JD asks for
                                   ownership/leadership language; lower for
                                   minor_contributor
   recency                (0-100): 100 if updated within 6 months, 70 within
                                   1 year, 40 within 2 years, 10 otherwise
   quality                (0-100): based on stars, readme_available, and
                                   archived == false (archived repos score low)

   final_score = round(
       0.30 * technology_match +
       0.25 * responsibility_match +
       0.20 * contribution_strength +
       0.15 * role_relevance +
       0.05 * recency +
       0.05 * quality
   )
   ```

4. Rank projects by `final_score` descending. Take the top 5 (or fewer if
   there aren't 5 with a nonzero score).

5. For each of the top projects, write 2-3 CV bullet points. **Every claim in
   a bullet must trace back to that project's `evidence` list or
   `responsibilities`.** Quantify only with numbers that actually appear in
   `evidence` (e.g. "reviewed 4 PRs" is fine; "led a team of 10" is not,
   unless evidence says so). If evidence is thin for a project, write shorter,
   more conservative bullets rather than padding them.

6. Save a report to `output/cv_recommendations.md` containing:
   - the extracted JD requirements
   - the ranked table (repo, final_score, key sub-scores)
   - the draft CV bullets per top project
   Then print the ranked table and bullets to the chat.

**Do not fabricate.** If no project matches a JD requirement well, say so
explicitly in the report rather than stretching a weak match into a strong
bullet.
