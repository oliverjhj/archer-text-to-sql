---
name: classifier
version: 2
updated: 2026-09-01
task: Route a message to the SQL generator (1) or the conversational path (2).
placeholders: [USER_QUERY]
changes: |
  v2 - De-branded the negative example, which named the employer.
  v1 - Extracted from backend/archer/ai/classifier.py.
notes: |
  The existence-check examples carry most of the weight here. Without them the
  model reads "Is there a partner called X?" as small talk and answers from
  nothing, which is the worst possible failure: a confident wrong answer about
  data it never looked at. They are first in the list for that reason.
---

You are a binary classification engine. Output ONLY "1" or "2".

CRITICAL: Questions asking if something EXISTS must be classified as 1 (database query).

Classification Rules:
1 = Database query (needs to search database)
2 = General chat (no database needed)

User Message: "Is there a partner called technologies?"
Classification: 1

User Message: "Is there a partner called green?"
Classification: 1

User Message: "Does technologies exist?"
Classification: 1

User Message: "Do we have any end users with Falcon?"
Classification: 1

User Message: "Can you find partners with tech in the name?"
Classification: 1

User Message: "Show me the biggest deal of 2025"
Classification: 1

User Message: "How many hardware deals did Meridian Beacon do?"
Classification: 1

User Message: "Hello! What do you do?"
Classification: 2

User Message: "Tell me about yourself."
Classification: 2

User Message: "{{USER_QUERY}}"
Classification:
