---
description: Translate text into English with multiple style variations
disable-model-invocation: true
allowed-tools:
  - AskUserQuestion
---

# Korean to English Translation

First, use AskUserQuestion to ask the user which translation style(s) they want. Present the following options with multiSelect enabled:

```
Question: "Which translation style(s) would you like?"
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

After receiving the user's selection, translate the text ONLY in the selected style(s).


## Important Notes
- **IMPORTANT: Return ONLY the translations for selected styles without any explanations, commentary, or additional text.**

---

# Text to Translate
$ARGUMENTS
