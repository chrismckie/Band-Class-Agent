# Band-Class-Agent

Most people think that the job of a band director is to teach students how to play instruments and conduct the students as they perform at concerts. While this is certainly an important part of the job, many people don't realize that the job has many more administrative responsibilities that happen behind the scenes, completely unnoticed. In addition to teaching and conducting during class time, countless hours outside of teaching hours are spent:

- Tracking hundreds of instruments and consumable equipment, repairs, and checkouts to students
- Selecting performance music based on student skills and instrumentation
- Financial and logistic planning for performances

The administrative role of a band director is incredibly time consuming, and often more time is spent on this than actually teaching. In addition, most band directors do not have the technical knowledge to automate these tasks, so they are often done manually and tracked in spreadsheets, where redundancy and data integrity problems can arise.

The goal of this project is to create an agent that helps band directors manage their instrument inventory, music selection, and ensemble planning. The band director simply tells the agent what to do through natural language, and the agent handles the task, with no technical or programming knowledge needed.

---

## How to Run the Demo

The [demo](/demo/demo.ipynb) has been designed to be run either in Google Colab or locally in a code editor like Visual Studio Code.

The system uses the Anthropic API for LLM functionality and Neon Postgres as a database, so those credentials must be provided in order to run the demo.

> [!WARNING]
> Do **not** share your credentials/secrets or commit them.

### If Running in Colab

Add `LLM_API_KEY` and `DATABASE_URL` to your Colab Secrets before running.

- Click the key icon in the left sidebar
- Select "Add New Secret"
- Enter `LLM_API_KEY` as the secret name and your Anthropic credentials as the value
- Select "Add New Secret" again
- Enter `DATABASE_URL` as the secret name and your Neon Postgres credentials as the value

Toggle "Notebook Access" for each Secret, and your credentials will be ready. Simply run each Setup cell in the demo, and the credentials will connect to the demo.

### If Running Locally

Create a `.env` file in the same directory as `src/` with your credentials:

```.env
DATABASE_URL=<YOUR_POSTGRES_CREDENTIALS>
LLM_API_KEY=<YOUR_ANTHROPIC_CREDENTIALS>
```

> [!WARNING]
> Do **not** push your `.env` file ever.
> *Always* add `.env` to your `.gitignore` file.

With `.env` and `.src` inthe same directory, your credentials will be ready. Simply run each Setup cell in the demo, and the credentials will connect to the demo.

### Using Other LLM APIs with the Demo

This system is designed to run with the Anthropic APIs. If you do not have those API keys, but you do have other LLM APIs (such as Open AI, for example), you *can* add use it, but will need to change some configurations:

1. Open [llm_client.py](/src/agent/llm_client.py)
2. Replace line 2 with: `import <your_own_API_library_name>`
3. Rewrite the last line in `get_client()` to return your API key
4. Rewrite `call_llm()` to provide a `response` value compatible with your API
5. Update the `MODEL` constant on line 7 to your respective model

Note that you will need to read your own API's documentation for this for exactly what to replace. It is recommended to use Anthropic if possible, since that simplifies the setup significantly.

---

## Documentation

To learn more about how the Band Class Agent works, read the documentation:

- [Agent Architecture & Design](/docs/agent_architecture.md)
  - [Planner](/docs/1_planner.md)
  - [Generator](/docs/2_generator.md)
  - [Validator](/docs/3_validator.md)
  - [Executor](/docs/4_executor.md)
  - [Formatter](/docs/5_formatter.md)
- [Database Architecture & Design](/docs/database_architecture.md)

---
