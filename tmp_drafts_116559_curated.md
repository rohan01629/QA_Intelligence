STORY: FracPro Live+ - Reports- Rename Download ASCII Report button and launch ASCII Report dialog
US: 116559
STATE: Code Review
COUNT: 0
STATUS: BLOCKED — Rule 12
NOTE: No test cases generated. Feature is not implemented in configured local codebases.

## Codebase scan
- Live_Plus_UAT: related `report-buttons` exists, but still uses `DOWNLOAD_ASCII_REPORT` + immediate `GenerateASCII` on click. No "ASCII Report" rename, no ASCII modal dialog, no Real-time/FrPro tabs for this flow.
- Minifrac: no ASCII Report implementation.

## AC behaviors missing from source
- Rename label to "ASCII Report"
- Open ASCII Report modal dialog (no COMMAND on button click)
- Real-time / FrPro tabs
- Generate / Cancel dialog actions with dismiss-without-save

Do not generate TCs until the US feature is present in at least one configured codebase.
