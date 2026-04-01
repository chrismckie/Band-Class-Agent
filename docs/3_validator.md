# Validator

![Validator Diagram](diagrams/validator.svg)

The **Validator** runs three layers of validation and safey checks against the SQL query and plan before any [database](database_architecture.md) operation is executed.

All three layers always run, any errors are collected into a list, and the errors list is evaluated at the end. If any errors are found, the entire operation is rejected, and the error list is returned, where it is sent to the [Formatter](5_formatter.md).

If there are no errors, the SQL query and parameters are sent to the [Executor](4_executor.md).

All validation is done through Python. There are no LLM calls in the Validator, since safety checks should be done with deterministic rules.

---

## Validation Layers

### Layer 1: SQL Safety

- The target table is on a whitelist
- The operation is permitted for the target table
- No dangerous keywords such as `DROP`, `TRUNCATE`, or `ALTER`
- The number of `%s` placeholders matches the number of provided parameters

### Layer 2: Business Logic

- Required fields are present
- Student grade levels are between 9 and 12
- Instrument conditions are one of the four valid values
- Music difficulty is between 1 and 6

### Layer 3: Data Integrity

- Instrument names exist in the table
- Detects duplicate records in a batch
- Blocks deleting a student who currently has an instrument checked out

---

## Validator Sample

**Input:**

```json
generated = {
     "sql": "SELECT s.student_id, s.first_name, s.last_name, s.grade FROM students s JOIN plays p ON s.student_id = p.student_id WHERE s.grade = %s AND p.instrument_name = %s",
     "params": [10, "trumpet"],
     "batch_params": [],
     "is_batch": false
}

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

**Output (Valid):**

```json
validation = {
     "is_valid": true,
     "errors": []
}
```

**Output (Invalid):**

If the input failed the validation checks (such as if if `grade: 7`):

```json
validation = {
     "is_valid": false, 
     "errors": ["Filter grade must be between 9 and 12 (got 7)."] 
}
```

---
