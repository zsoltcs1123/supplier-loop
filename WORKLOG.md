# Worklog

## 2026-09-21

Runtime extract uses OpenRouter. PDF text is read in code before extract. Photos go to vision. Spend is recorded in `.artifacts/llm-spend.json` against the $100 cap. Default model is `google/gemini-2.5-pro`.

`openai/gpt-4o-mini` reads the Tanaka PDF fixture correctly. Two prompt passes still misread the Alsayed screenshot (quantity, size codes, grand total). `google/gemini-2.5-pro` reads that screenshot: Aluminum Sheet qty 200 at 57.68, Stainless Bolt M8x40, Brass Fitting 1/2in, Epoxy Resin 5L, Plywood qty 100, grand total 16705.20, validity 14 days, terms Net 20. The same model reads the Tanaka PDF text layer without changing those figures. Runtime default is now `google/gemini-2.5-pro`.

An approver line that says "Not approving" is a rejection. Correction runs, and `auto_approved` stays false.

Quote fingerprints include attachment identity, so the two Fatima photo mails with the same sender and subject stay distinct.

After a correction, the new approver mail describes the quote now on file and does not repeat a defect the revised quote cleared.

Inline and pasted-table suppliers are reminded after 4 sim-days and held 2 sim-days after the reminder. PDF and photo suppliers (`p03`, `p04`) are reminded after 8 sim-days and held 3 sim-days. One quiet sim-day was closing those two before their normal reply window.
