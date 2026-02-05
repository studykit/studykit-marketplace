---
description: Revise and enhance English text
disable-model-invocation: true
allowed-tools:
  - AskUserQuestion
---

# English Text Revision and Enhancement

First, use AskUserQuestion to ask the user which refinement style(s) they want. Present the following options with multiSelect enabled:

```
Question: "Which refinement style(s) would you like?"
Header: "Styles"
Options:
1. "Professional (Written)" - Clear, direct, business-appropriate with logical flow
2. "Technical (Written)" - Precise, structured, objective with consistent terminology
3. "Formal (Written)" - Professional, business-appropriate tone
4. "Friendly (Written)" - Warm, approachable language
5. "Academic (Written)" - Scholarly, research-oriented style
6. "Concise (Spoken)" - Brief, direct communication
7. "Casual (Spoken)" - Relaxed, everyday conversation
8. "Friendly (Spoken)" - Warm, personal interaction
9. "Polite (Spoken)" - Courteous, respectful manner
10. "Professional (Spoken)" - Business meeting appropriate
```

After receiving the user's selection, revise the text ONLY in the selected style(s).

For each refinement:
- Review for grammatical accuracy, natural flow, and clarity
- Provide the refined version with the style name as heading

## Important Notes
- **IMPORTANT: Return ONLY the refinements for selected styles without any explanations, commentary, or additional text.**

---

# Text to Refine

$ARGUMENTS
