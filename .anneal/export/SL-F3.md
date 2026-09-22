# SL-F3 — Extract live quote bodies and attachments

**Status:** done

**Path:** SL

## Body

Live quotes use different line shapes than the fixture qty/`**USD**` regex, and attachments are not downloaded before extract. Next live ingest should parse the body we already saw and pass att_02_0001 into extract.
