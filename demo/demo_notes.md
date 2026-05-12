# Demo Notes

Target length: 5 minutes.

## 1. Phase A - RAGAS Evaluation

Commands:

```powershell
python phase-a\run_phase_a.py --n 50 --rag-mode auto --allow-fallback-metrics
```

Show:

- `phase-a/test_set_v1.csv`
- `phase-a/ragas_summary.json`
- `phase-a/failure_analysis.md`

Talking points:

- 50 synthetic questions across simple, reasoning, and multi-context types.
- RAGAS computes faithfulness, answer relevancy, context precision, and context recall.
- Failure clusters identify concrete retrieval/generation fixes.

## 2. Phase B - LLM-as-Judge

Commands:

```powershell
python phase-b\run_phase_b.py --limit 30 --sample-size 10
```

Show:

- `phase-b/judge_pairwise_results.csv`
- `phase-b/absolute_scores.csv`
- `phase-b/kappa_report.md`
- `phase-b/judge_bias_report.md`

Talking points:

- Pairwise judge uses swap-and-average to reduce position bias.
- Absolute judge scores accuracy, relevance, conciseness, and helpfulness.
- Human labels are compared with judge labels using Cohen's kappa.

## 3. Phase C - Guardrails

Commands:

```powershell
python phase-c\run_phase_c.py --n 100
```

Optional with output guard API:

```powershell
python phase-c\run_phase_c.py --n 100 --use-output-api
```

Show:

- `phase-c/pii_test_results.csv`
- `phase-c/adversarial_test_results.csv`
- `phase-c/output_guard_results.csv`
- `phase-c/latency_summary.csv`
- `phase-c/audit_log.jsonl`

Talking points:

- Input layer redacts PII and blocks out-of-domain or injection attempts.
- Output layer blocks unsafe or leaking responses.
- Latency benchmark measures per-layer overhead.

## 4. Phase D - Blueprint

Commands:

```powershell
python phase-d\run_phase_d.py
```

Show:

- `phase-d/blueprint.md`
- `phase-d/cost_model.csv`

Talking points:

- SLO table marks pass/alert status from live artifacts.
- Mermaid architecture shows the 4-layer production path.
- Playbook maps incidents to investigation and resolution steps.

## Demo Close

Show `README.md` and `submission_checklist.md`, then mention that `.env` is excluded and only `.env.example` is committed.
