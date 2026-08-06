STORY: FracPro Live+- Minifrac- Display and Update Magenta Circle on LogLog Plot
US: 116566
STATE: New
COUNT: 0
STATUS: BLOCKED — Rule 12
NOTE: No test cases generated. Feature is not implemented in configured local codebases.

## AC (summary)
- Scenario 1: On LogLog plot, show a single magenta circle at Closure (magenta vertical line) × Meas'd Btmh Press.
- Scenario 2: When Closure moves, update the same circle immediately (no refresh; do not create a second circle).

## Codebase scan
- Minifrac (`...\Minifrac\fracpro-agile`): no LogLog / magenta-circle / Closure-intersection implementation found.
- Live_Plus_UAT: Meas'd Btmh Press exists elsewhere; no magenta circle on LogLog for this US.

Do not generate TCs until the US feature is present in at least one configured codebase.
