---
name: rna
description: Revise English text in technical style, wait for user confirmation, then answer questions about the revision
disable-model-invocation: true
context: fork
---

# Revise and Confirm

Follow these steps in order:

1. **Revise the English text**
   - Revise for grammatical accuracy, natural flow, clarity, and technical precision
   - Use technical written style: precise, structured, and objective
   - Use consistent terminology throughout
   - Keep the original meaning intact
   - Show the revised text clearly

2. **Ask the user if they have questions about the revision**
   - Use the AskUserQuestion tool to confirm whether to proceed with explanation
   - Wait for user confirmation before providing any explanation

3. **If confirmed, explain the changes**
   - Describe what was changed and why
   - Use clear, professional English

## Important Notes
- **IMPORTANT: Always show the revised text first**
- **IMPORTANT: Ask for confirmation before explaining**
- **Return only the revised text in step 1, without explanations**

---

# English Text
$ARGUMENTS
