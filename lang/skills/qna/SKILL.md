---
name: qna
description: Translate Korean question to English, wait user confirmation and answer in English
disable-model-invocation: true
context: fork
---

# Translate and Confirm

You must follow these steps in order:

1. **First, translate the Korean question to English**
   - Show the translated English question clearly

2. **Then, ask the user if they want you to answer the question**
   - Use the AskUserQuestion tool to confirm whether to proceed with answering
   - Wait for user confirmation before providing the answer

3. **If confirmed, answer the translated English question**
   - Provide a comprehensive answer based on the English version
   - Use clear, professional English

## Important Notes
- **IMPORTANT: Always show the translated question first**
- **IMPORTANT: Ask for confirmation before answering**
- **Use professional, clear English**

---

# Korean Question
$ARGUMENTS
