---
name: rs
description: Revise English with a user-selected style.
argument-hint: <English text to revise>
disable-model-invocation: true
context: fork
model: sonnet
---

# Revise English Text with Style Selection

First, use AskUserQuestion to ask which refinement style(s) to apply. Present the following options with multiSelect enabled:

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

After receiving the selection, revise the text ONLY in the selected style(s). Do NOT explain the changes.

- Review for grammatical accuracy, natural flow, and clarity
- Keep the original meaning intact

Output in this exact format:

```
<revised text>
```

---

# English Text
$ARGUMENTS
