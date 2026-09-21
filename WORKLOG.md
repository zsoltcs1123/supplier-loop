# Worklog

## 2026-09-21

Runtime extract now uses OpenRouter (`openai/gpt-4o-mini` by default). PDF text is read in code before extract. Photos go to vision. Spend is recorded in `.artifacts/llm-spend.json` against the $100 cap.

`openai/gpt-4o-mini` reads the Tanaka PDF fixture correctly. It misreads the Alsayed screenshot (quantities, SKU digits, grand total). Round 3 submitted Tanaka and Fatima empty after quiet; they never quoted.
