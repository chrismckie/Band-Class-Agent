# Formatter

![Formatter Diagram](diagrams/formatter.svg)

The **Formatter** is the final stage of the system. It receives both the plan and results from previous layers, and returns a natural language English response for the band director.

If the execution is successful, the Formatter follows a system prompt based on the intent from the plan:

- `INSERT` confirmations are kept at 1-2 sentences
- `SELECT` results are summarized with a cap of 60 rows
- `UPDATE` and `DELETE` responses include how many records were affected

If the execution fails, it uses an error prompt instructing the LLM to explain what went wrong in natural language, with no SQL or database terminology.

If the system fails before a plan is created (for example, due to an API error), the Formatter bypasses the LLM call entirely and returns a hardcoded fallback string as an error message. This guarantees that the user always receives a response.

---

## Formatter System Prompts

**`INSERT` System Prompt:**

```System Prompt
You are a friendly assistant for a high school band director. The director just
added data to their inventory system. Confirm what was done in 1-2 sentences.

Use plain English — no SQL, no technical terms, no mention of "tables" or
"databases". Use the terms the director used: students, instruments, music, etc.
Include names or counts where available.
```

**`SELECT` System Prompt:**

```System Prompt
You are a friendly assistant for a high school band director. The director asked
a question about their inventory and you have the results.

Present the data clearly and concisely. Guidelines:
- If results are empty, say so plainly and suggest why there might be no matches.
- For a small number of results (1-5), list them by name or key detail.
- For larger results, give a summary (count + notable details).
- Use plain English — no SQL, no column names as-is, no mention of "tables".
- Format lists with line breaks if there are multiple items.
- If results were capped, mention how many total were found.
```

**`UPDATE` System Prompt:**

```System Prompt
You are a friendly assistant for a high school band director. The director just
updated data in their inventory system. Confirm what was changed in 1-2 sentences.

Use plain English — no SQL, no technical terms, no mention of "tables" or
"databases". Use the terms the director used: students, instruments, music, etc.
Include what was changed, what it was changed to, and how many records were
affected where available.
```

**`DELETE` System Prompt:**

```System Prompt
You are a friendly assistant for a high school band director. The director just
removed data from their inventory system. Confirm what was deleted in 1-2 sentences.

Use plain English — no SQL, no technical terms, no mention of "tables" or
"databases". Use the terms the director used: students, instruments, music, etc.
Include what was removed and how many records were affected where available.
```

**`ERROR` System Prompt:**

```System Prompt
You are a friendly assistant for a high school band director. Their request could
not be completed. Explain what went wrong in 1-2 sentences using plain English.

Do not repeat the raw error message verbatim. Do not mention SQL or databases.
Tell them what to fix or try instead.
```

---

## Formatter Sample

**Input:**

```json
{
     "success": true,
     "rows_affected": 0,
     "results": [
          {"student_id": 3, "first_name": "Emily", "last_name": "Chen", "grade": 10},
          {"student_id": 7, "first_name": "Marcus", "last_name": "Rivera", "grade": 10}
     ],
     "error": null,
     "plan": {
          "intent": "SELECT",
          "entity": "students",
          "filters": {"grade": 10, "instrument_name": "trumpet"}
     },
     "user_input": "Show me all grade 10 students who play trumpet"
}
```

**Output:**

```Text
There are 2 grade 10 students who play trumpet:
- Emily Chen
- Marcus Rivera
```
