# SL-B1 — Empty extract still escalates class 1

**Status:** done

**Path:** SL

## Description

A live quote classified as quote can carry zero line items after crude extract. The classer then raises class 1 and the machine mails the approver. Round 2 sent eml_02_0010 for Marta Novak on an empty as-sent quote.

## Severity

medium

## Repro notes

- Ingest eml_02_0009. Body uses bullets like Steel I-Beam 200mm: $44.65/m x 150 m. CrudeExtractor returns no lines. Classer raises class 1. Approver mail eml_02_0010 is sent.
