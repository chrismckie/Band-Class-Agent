# Architecture

## Table of Contents

- [Architecture](#architecture)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [System Diagram](#system-diagram)
  - [LLM Call Sequence](#llm-call-sequence)
  - [Step-by-Step Sequence of Tools and LLM Calls](#step-by-step-sequence-of-tools-and-llm-calls)
    - [Step 1: Planner](#step-1-planner)
    - [Step 2: Generator](#step-2-generator)
    - [Step 3: Validator](#step-3-validator)
    - [Step 4: Executor](#step-4-executor)
    - [Step 5: Formatter](#step-5-formatter)

## Overview

The agent processes each request through a five-stage pipeline:

1. **[Planner]((1_planner.md)):** Classifies the request intent and produces structured data from the request.
2. **[Generator](2_generator.md):** Produces paramaterized SQL from the structured data.
3. **[Validator](3_validator.md):** Enforces safety and business rules on the SQL.
4. **[Executor](4_executor.md):** Runs the SQL query in the [database](database_architecture.md).
5. **[Formatter](5_formatter.md):** Turns the raw query result into a natural language response.

Each stage has a defined input and output, making each component extendable and easy to debug.

---

## System Diagram

![High Level Diagram](diagrams/high_level.svg)

---

## LLM Call Sequence

Three of the five stages use LLM calls:

- **Planner:** Interprets natural language from user input.
- **Generator:** Used for `SELECT` queries only (to handle joins and complex filtering).
- **Formatter:** Produce natural language response from the queries.

The Validator and Executor are intentionally pure Python. Validation needs to be fast and deterministic, and execution is handled psycopg2. The Generator also uses pure Python for `INSERT`, `UPDATE`, and delete`DELETE`, since those queries are simpler, and the Planner already extracts the necessary values.

---

## Step-by-Step Sequence of Tools and LLM Calls

<!-- Step-by-step sequence of which LLM calls happen, in what order,
     what each one receives as input, and what it returns.
     Cover all four intents (INSERT, SELECT, UPDATE, DELETE) and note
     which stages skip the LLM entirely. -->

### Step 1: Planner

*See the [Planner Documentation](1_planner.md) for more information*

**Input:** User input as string
**Tool:** LLM to process intent into stuctured Python dictionary
**Output:** Python dictionary of user intent

### Step 2: Generator

*See the [Generator Documentation](2_generator.md) for more information*

**Input:** Python dictionary of user intent
**Tool:** Determined by intent

- `INSERT`: Python to build SQL
- `UPDATE`: Python to build SQL
- `DELETE`: Python to build SQL
- `SELECT`: LLM to to handle joins and complex filtering

**Output:** Python dictionary of generated SQL

### Step 3: Validator

*See the [Validator Documentation](3_validator.md) for more information*

**Input:** Python dictionaries of generated SQL and parameters
**Tool:** Python to check built-in rules
**Output:** Boolean value of validation

### Step 4: Executor

*See the [Executor Documentation](4_executor.md) for more information*

**Input:** Validated SQL and parameters in Python dictionaries
**Tool:** psycopg2 to run SQL in Neon Postgres
**Output:** SQL result in a Python dictionary

### Step 5: Formatter

*See the [Formatter Documentation](5_formatter.md) for more information*

**Input:** SQL result in a Python dictionary
**Tool:** LLM to translate SQL result into natural language response
**Output:** Natural language response as a string

---
