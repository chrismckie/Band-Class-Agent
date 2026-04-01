# Band-Class-Agent

This agent will enable band directors to manage their instrument inventory, music selection, and ensemble planning, all through natural language. No SQL or technical knowledge needed.

<!-- 
    Band directors manage instrument inventory, student rosters, and music libraries but shouldn't need to know SQL to do it. Band-Class-Agent lets a director interact with a Neon Postgres database entirely in plain English — describing what they want in natural language and receiving a plain English response back.

    Consider this or the info from the presentation
 -->

In practice the overlap is:

||architecture.md|README.md|
|---|---|---|
|What the project does|✓ (design focus)|✓ (1-2 sentences, brief)|
|Why it's interesting|✓|maybe 1 line|
|How to run it|✗|✓|
|API keys / .env setup|✗|✓|
|LLM vs Python tradeoffs|✓|✗|
|Pipeline design decisions|✓|✗|
|Links to other docs|✗|✓|

So the overview paragraphs I suggested belong in `architecture.md`. The README's description of the project should be much shorter — a sentence or two — and immediately pivot to "here's how to run it."
