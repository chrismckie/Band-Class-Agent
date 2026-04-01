# Generator

![Generator Diagram](diagrams/generator.svg)

The **Generator** receives the `plan` and produces a parameterized SQL string with the values to bind it.

For `INSERT`, `UPDATE`, and `DELETE` operations, the SQL generation is fully deterministic and done using strictly Python. The Planner has already extracted column names and values, so the query can be built as a formatted string without using the LLM.

For `SELECT` operations, an LLM call is used to generate the queries. This is because queries may require complex joins, aliases, and special filter handling (such as translating `checked_out: true` into `return_date IS NULL`). If the LLM call cannot generate the SQL query, a safe full-table scan is used as a fallback.

All SQL produced by the Generator uses `%s` as placeholders, and the values are never directly inserted into the query. This allows the [Validator](3_validator.md) and [Executor](4_executor.md) to always receive parameterized queries regardless of what SQL operation is performed.

---

## Generator System Prompt

```System Prompt
You are the SQL Generator for a band inventory database agent. Given a SELECT plan,
generate a valid parameterized PostgreSQL SELECT statement.

─── SCHEMA ─────────────────────────────────────────────────────────────────────

students(student_id PK, first_name, last_name, grade)
instrument_inventory(serial_number PK, instrument_name FK→instruments, condition)
checkout_history(checkout_id PK, student_id FK→students, serial_number FK→instrument_inventory, checkout_date, return_date — NULL means currently checked out)
music(music_id PK, title, composer, difficulty)
plays(student_id FK→students, instrument_name FK→instruments)
arranged_for(music_id FK→music, instrument_name FK→instruments, parts_needed)
instruments(instrument_name PK, family_id FK→instrument_family)
instrument_family(family_id PK, family_name)

─── RULES ──────────────────────────────────────────────────────────────────────

1. Use %s placeholders for ALL filter values — never put values directly in SQL.
2. Join tables as needed. Use short aliases (s, ii, ch, m, p, af).
3. Special filter "checked_out": true → WHERE ch.return_date IS NULL (no %s needed).
4. Empty filters dict → no WHERE clause; return all rows from the entity table.
5. SELECT the most useful columns for the query — avoid SELECT * on joined queries.
6. Return ONLY valid JSON, no markdown, no explanation:
   {"sql": "SELECT ...", "params": [value, ...]}
```

> [!NOTE]
> The Generator System Prompt only applies to `SELECT` operations, because other prompts are created deterministically using Python.

---

## Generator Sample

**Input:**

```json
plan = {
     "intent": "SELECT",
     "entity": "students",
     "is_batch": false,
     "records": [],
     "filters": {
          "grade": 10,
          "instrument_name": "trumpet"
     },
     "updates": {},
     "requires_clarification": false,
     "clarification_question": null
}
```

**Output:**

```json
generated = {
     "sql": "SELECT s.student_id, s.first_name, s.last_name, s.grade FROM students s JOIN plays p ON s.student_id = p.student_id WHERE s.grade = %s AND p.instrument_name = %s",
     "params": [10, "trumpet"],
     "batch_params": [],
     "is_batch": false
}
```

---
