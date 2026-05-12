# Judge Bias Report

## Bias 1: Position Bias

- First-pass winner counts: A=18, B=12, tie=0
- Swapped-pass positional winner counts: A=10, B=19, tie=1
- Final winner counts after swap reconciliation: A=14, B=6, tie=10
- Same-position winner after swap conflicts: 10 / 30

Mitigation: use swap-and-average for every pairwise comparison and convert the swapped result back to original answer identity before deciding.

## Bias 2: Length Bias

- Average winner length advantage: -16.45 words
- Longer answer win rate among non-ties: 40.00%

Mitigation: keep conciseness as an explicit rubric dimension and penalize unsupported extra detail.

## Monitoring Decision

- Keep both position and length checks as required diagnostics for each judge prompt/model update.
- Re-run calibration when pairwise tie rate or swap conflicts change materially.
