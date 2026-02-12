---
name: rsna
description: Revise English text with user-selected style, then optionally explain the changes
disable-model-invocation: true
context: fork
allowed-tools:
  - AskUserQuestion
---

# Revise with Style Selection and Explanation

Follow these steps in order:

1. **Ask which refinement style(s) to apply**

   Use AskUserQuestion with multiSelect enabled:

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

2. **Revise the text in the selected style(s)**
   - Review for grammatical accuracy, natural flow, and clarity
   - Keep the original meaning intact
   - Show the refined version with the style name as heading

3. **Ask if the user wants an explanation of the changes**
   - Use AskUserQuestion to confirm whether to proceed with explanation
   - Wait for user confirmation

4. **If confirmed, explain the changes**
   - Describe what was changed and why
   - Use clear, professional English

## Important Notes
- **IMPORTANT: Return ONLY the refinements in step 2 without explanations**
- **IMPORTANT: Ask for confirmation before explaining**

---

# English Text
$ARGUMENTS
