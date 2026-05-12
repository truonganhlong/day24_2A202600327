# Submission Checklist

## Required Files

- [x] `README.md`
- [x] `requirements.txt`
- [x] `prompts.md`
- [x] `.env.example`
- [x] `.github/workflows/eval-ragas.yml`

## Phase A - RAGAS

- [x] `phase-a/test_set_v1.csv`
- [x] `phase-a/test_set_review_notes.md`
- [x] `phase-a/rag_answers.csv`
- [x] `phase-a/ragas_results.csv`
- [x] `phase-a/ragas_summary.json`
- [x] `phase-a/failure_analysis.md`
- [x] `phase-a/run_phase_a.py`

## Phase B - LLM-as-Judge

- [x] `phase-b/answer_variants.csv`
- [x] `phase-b/judge_pairwise_results.csv`
- [x] `phase-b/absolute_scores.csv`
- [x] `phase-b/pairwise_sample.csv`
- [x] `phase-b/human_labels.csv`
- [x] `phase-b/kappa_report.md`
- [x] `phase-b/kappa_summary.json`
- [x] `phase-b/judge_bias_report.md`
- [x] `phase-b/run_phase_b.py`

## Phase C - Guardrails

- [x] `phase-c/input_guard.py`
- [x] `phase-c/output_guard.py`
- [x] `phase-c/full_pipeline.py`
- [x] `phase-c/pii_test_results.csv`
- [x] `phase-c/topic_test_results.csv`
- [x] `phase-c/adversarial_test_results.csv`
- [x] `phase-c/output_guard_results.csv`
- [x] `phase-c/latency_benchmark.csv`
- [x] `phase-c/latency_summary.csv`
- [x] `phase-c/audit_log.jsonl`
- [x] `phase-c/run_phase_c.py`

## Phase D - Blueprint

- [x] `phase-d/blueprint.md`
- [x] `phase-d/cost_model.csv`
- [x] `phase-d/run_phase_d.py`

## Demo

- [x] `demo/demo_notes.md`
- [ ] Demo video link or local video file added before final submission.

## Last Verification Commands

```powershell
python -m compileall phase-a phase-b phase-c phase-d
python phase-a\run_phase_a.py --n 50 --rag-mode light --no-llm --allow-fallback-metrics
python phase-b\run_phase_b.py --no-llm --limit 30 --sample-size 10
python phase-c\run_phase_c.py --n 100
python phase-d\run_phase_d.py
```

## Notes Before Submit

- Do not commit `.env`.
- Re-run non-dry-run scripts with API keys if final metrics are required.
- Replace or supplement `demo/demo_notes.md` with the actual video URL after recording.
