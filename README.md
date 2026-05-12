# Lab 24 - Full Evaluation & Guardrail System

## Overview

This repository extends the Day 18 production RAG pipeline into a full evaluation, judge calibration, guardrails, and production blueprint stack.

Built components:

- Phase A: synthetic test set generation, RAG answer collection, RAGAS scoring, and failure cluster analysis.
- Phase B: LLM-as-judge pairwise comparison, absolute rubric scoring, human calibration, Cohen's kappa, and judge bias report.
- Phase C: input/output guardrails, PII redaction, topic validation, adversarial tests, Llama Guard compatible output guard, and latency benchmark.
- Phase D: production blueprint with SLOs, Mermaid architecture diagram, alert playbook, and cost analysis.

## Setup

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
copy .env.example .env
```

Fill the relevant keys in `.env`:

```env
OPENAI_API_KEY=...
HF_TOKEN=...
HUGGINGFACEHUB_API_KEY=...
GROQ_API_KEY=...
LANGFUSE_PUBLIC_KEY=...
LANGFUSE_SECRET_KEY=...
```

`OPENAI_API_KEY` is required for real RAGAS/judge/LLM runs. `GROQ_API_KEY` is optional for the Llama Guard API path. The scripts also include deterministic fallbacks so the full artifact flow can run without external APIs.

## Run Everything

Fast dry-run without LLM calls:

```powershell
python phase-a\run_phase_a.py --n 50 --rag-mode light --no-llm --allow-fallback-metrics
python phase-b\run_phase_b.py --no-llm --limit 30 --sample-size 10
python phase-c\run_phase_c.py --n 100
python phase-d\run_phase_d.py
```

Full run with configured APIs:

```powershell
python phase-a\run_phase_a.py --n 50 --rag-mode auto --allow-fallback-metrics
python phase-b\run_phase_b.py --limit 30 --sample-size 10
python phase-c\run_phase_c.py --n 100 --use-output-api
python phase-d\run_phase_d.py
```

## Results Summary

### Phase A - RAGAS

Current `phase-a/ragas_summary.json`:

- Faithfulness: 0.7287
- Answer relevancy: 0.4510
- Context precision: 0.7450
- Context recall: 0.7500

Main artifact files:

- `phase-a/test_set_v1.csv`
- `phase-a/test_set_review_notes.md`
- `phase-a/rag_answers.csv`
- `phase-a/ragas_results.csv`
- `phase-a/ragas_summary.json`
- `phase-a/failure_analysis.md`

### Phase B - LLM-as-Judge

Current calibration:

- Pairwise comparisons: `phase-b/judge_pairwise_results.csv`
- Absolute rubric scores: `phase-b/absolute_scores.csv`
- Human calibration sample: `phase-b/human_labels.csv`
- Cohen's kappa: 0.2754
- Bias report: `phase-b/judge_bias_report.md`

### Phase C - Guardrails

Current guardrail dry-run results:

- PII recall: 1.000
- Topic accuracy: 0.900
- Adversarial detection: 0.929
- Output unsafe detection: 1.000
- Latency benchmark: 100 requests

Main artifact files:

- `phase-c/pii_test_results.csv`
- `phase-c/topic_test_results.csv`
- `phase-c/adversarial_test_results.csv`
- `phase-c/output_guard_results.csv`
- `phase-c/latency_benchmark.csv`
- `phase-c/latency_summary.csv`
- `phase-c/audit_log.jsonl`

### Phase D - Blueprint

Production blueprint:

- `phase-d/blueprint.md`
- `phase-d/cost_model.csv`

The blueprint includes SLO definitions, architecture, alert playbook, cost model, and production readiness notes.

## Repository Structure

```txt
phase-a/
  generate_test_set.py
  run_rag_on_testset.py
  run_ragas.py
  analyze_failures.py
  run_phase_a.py
  test_set_v1.csv
  ragas_results.csv
  ragas_summary.json
  failure_analysis.md

phase-b/
  build_answer_variants.py
  pairwise_judge.py
  absolute_scoring.py
  calibrate_kappa.py
  bias_report.py
  run_phase_b.py
  judge_pairwise_results.csv
  absolute_scores.csv
  human_labels.csv
  kappa_report.md
  judge_bias_report.md

phase-c/
  input_guard.py
  output_guard.py
  full_pipeline.py
  run_phase_c.py
  pii_test_results.csv
  adversarial_test_results.csv
  output_guard_results.csv
  latency_benchmark.csv
  audit_log.jsonl

phase-d/
  generate_blueprint.py
  run_phase_d.py
  blueprint.md
  cost_model.csv

.github/workflows/
  eval-ragas.yml

prompts.md
demo/demo_notes.md
submission_checklist.md
```

## Demo Video

Demo outline is documented in `demo/demo_notes.md`. The expected demo flow is:

1. Show Phase A RAGAS run and summary.
2. Show Phase B judge pairwise comparison and calibration.
3. Show Phase C guardrails blocking PII/prompt injection/unsafe output.
4. Show Phase C latency benchmark.
5. Show Phase D blueprint.

## Notes

The checked-in artifacts reflect the latest local runs. Some scripts support fallback metrics for environments without API/network access; final scoring runs should use configured API keys when available.
