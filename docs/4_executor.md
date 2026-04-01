# Executor

![Executor Diagram](diagrams/executor.svg)

The **Executor** receives the validated, parameterized SQL and executes the query. It is the only component that directly communicates with the [Neon Postgres database](database_architecture.md). No LLM call is used, since this component is purely a database query.

The results are stored in a Python dictionary and has the following shape:

``` Dictionary
result = {
     "success": bool,
     "rows_affected": int, # INSERT / UPDATE / DELETE
     "results": list[dict], # SELECT rows; empty for write operations
     "error": str | None
}
```

The result is sent to the [Formatter](5_formatter.md) to be formatted into a final response output.

The execution process varies based on the query type:

- `SELECT` queries run with `cursor.execute()` and the results are returned as a list of dictionaries, keyed by column name.
- Single write operations (`INSERT`, `UPDATE`, `DELETE`) run with `cursor.execute()` followed by a commit.
- Batch write operations run with `cursor.executemany()` inside a transaction. A failure on any record triggers a full rollback.

All execution is done inside a try/except block. If an exception occurs, the connection is rolled back and the Executor returns a result with `success: False` and the error message. The error is then sent to the Formatter where it is processed into an error response to the user.

---

## Executor Sample

**Input:**

```json
generated = {
     "sql": "SELECT s.student_id, s.first_name, s.last_name, s.grade FROM students s JOIN plays p ON s.student_id = p.student_id WHERE s.grade = %s AND p.instrument_name = %s",
     "params": [10, "trumpet"],
     "batch_params": [],
     "is_batch": false
}
```

**Output:**

```json
result = {
     "success": true,
     "rows_affected": 0,
     "results": [
          {"student_id": 3, "first_name": "Emily", "last_name": "Chen", "grade": 10},
          {"student_id": 7, "first_name": "Marcus", "last_name": "Rivera", "grade": 10}
     ],
     "error": null
}
```

---
