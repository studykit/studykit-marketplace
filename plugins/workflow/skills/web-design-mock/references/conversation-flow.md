# Conversation Flow

Adapt your conversation depth based on the specificity of the user's input. The core principle: **generate as soon as there is enough information. Only ask about what's missing.**

## Assessing Input Specificity

- **Vague request** ("make me a landing page") — Ask about purpose, audience, and mood one question at a time. Keep it to 2-3 questions max before generating a first draft.
- **Moderate detail** ("SaaS landing page, clean look") — Confirm the overall structure briefly, then generate immediately.
- **Highly specific** ("dark dashboard with sidebar and card grid layout") — Generate immediately without asking questions.
- **Reference provided** (image attached or URL mentioned) — Analyze the reference, confirm the direction, then generate.

When in doubt, lean toward generating early. A concrete mockup drives better feedback than abstract discussion.
