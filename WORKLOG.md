# Worklog

## 2026-09-21

Runtime extract uses OpenRouter. PDF text is read in code before extract. Photos go to vision. Spend is recorded in `.artifacts/llm-spend.json` against the $100 cap. Default model is `google/gemini-2.5-pro`.

`openai/gpt-4o-mini` reads the Tanaka PDF fixture correctly. Two prompt passes still misread the Alsayed screenshot (quantity, size codes, grand total). `google/gemini-2.5-pro` reads that screenshot: Aluminum Sheet qty 200 at 57.68, Stainless Bolt M8x40, Brass Fitting 1/2in, Epoxy Resin 5L, Plywood qty 100, grand total 16705.20, validity 14 days, terms Net 20. The same model reads the Tanaka PDF text layer without changing those figures. Runtime default is now `google/gemini-2.5-pro`.

An approver line that says "Not approving" is a rejection. Correction runs, and `auto_approved` stays false.

Quote fingerprints include attachment identity, so the two Fatima photo mails with the same sender and subject stay distinct.

After a correction, the new approver mail describes the quote now on file and does not repeat a defect the revised quote cleared.

Inline and pasted-table suppliers are reminded after 4 sim-days and held 2 sim-days after the reminder. PDF and photo suppliers (`p03`, `p04`) are reminded after 8 sim-days and held 3 sim-days. One quiet sim-day was closing those two before their normal reply window.

Development round 4 ran unattended from RFQ send through `submit_results` (`uv run python -m supplier_loop run-dev`, then `resume-dev` on the same round). Four suppliers, no simulator warnings. A supplier acceptance phrased "meet you at 4116.00" had been classified as a question, so the negotiation wait never ended. That phrase is now a negotiation reply. A missed reply or a missing approver ruling stops after 1 sim-day. The approver asked for specifics on the class 6 mail and never approved; that supplier submitted `auto_approved` false. One line total in the payload was `231.99999999999997` instead of `232.00`.
