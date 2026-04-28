# Research Wrap Up

End only when the user says the research is done. Never conclude unilaterally.

When the user indicates completion:

1. **Final checkpoint write** — ensure every confirmed finding is in the file.

2. **Flip `status:`** from `draft` to the terminal value that fits:
   - `final` — research is complete and may feed a decision (default).
   - `standalone` — research is complete and intentionally won't feed any decision (terminal; the SessionStart staleness courtesy never nudges `standalone` files).

   Leave `status: draft` if more iterations are expected; flip to `archived` later when the research becomes irrelevant.

3. **Bump `updated:`** to today.

4. **Report the path** and how to reference it:
   - From `/a4:spec`: cite this research via `scripts/register_research_citation.py`, which writes the citation in four places (spec frontmatter `research:`, spec body `<research>`, research frontmatter `cited_by:`, research body `<cited-by>`).
   - Optional review pass: `/a4:research-review ./research/<slug>.md` before relying on it for a decision.
