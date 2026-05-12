"""Generate Phase D production blueprint document."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
PHASE_A = ROOT_DIR / "phase-a"
PHASE_B = ROOT_DIR / "phase-b"
PHASE_C = ROOT_DIR / "phase-c"
PHASE_D = ROOT_DIR / "phase-d"


def read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []


def metric_status(score: float, threshold: float, direction: str = "min") -> str:
    if direction == "max":
        return "pass" if score <= threshold else "alert"
    return "pass" if score >= threshold else "alert"


def latest_latency(layer: str, rows: list[dict[str, str]], key: str = "p95_ms") -> float:
    for row in rows:
        if row.get("layer") == layer:
            try:
                return float(row.get(key, 0.0))
            except Exception:
                return 0.0
    return 0.0


def ratio_from_summary_row(rows: list[dict[str, str]], prefix: str) -> float:
    summary = rows[-1] if rows else {}
    text = f"{summary.get('correct', '')};{summary.get('findings', '')};{summary.get('reason', '')}"
    for part in text.split(";"):
        if part.startswith(prefix):
            try:
                return float(part.split("=", 1)[1])
            except Exception:
                return 0.0
    return 0.0


def build_cost_table() -> list[dict[str, str | float]]:
    monthly_queries = 100_000
    assumptions = [
        {
            "component": "Input PII guard",
            "unit_cost": "$0.00 / query",
            "volume": monthly_queries,
            "monthly_cost": 0.0,
        },
        {
            "component": "Topic + injection guard",
            "unit_cost": "$0.00 / query",
            "volume": monthly_queries,
            "monthly_cost": 0.0,
        },
        {
            "component": "RAG generation gpt-4o-mini",
            "unit_cost": "$0.00025 / query",
            "volume": monthly_queries,
            "monthly_cost": 25.0,
        },
        {
            "component": "RAGAS nightly sample",
            "unit_cost": "$0.012 / eval",
            "volume": 1_500,
            "monthly_cost": 18.0,
        },
        {
            "component": "LLM judge calibration",
            "unit_cost": "$0.010 / pair",
            "volume": 1_000,
            "monthly_cost": 10.0,
        },
        {
            "component": "Llama Guard API",
            "unit_cost": "$0.0005 / output",
            "volume": monthly_queries,
            "monthly_cost": 50.0,
        },
        {
            "component": "Langfuse/LangSmith logging",
            "unit_cost": "free tier / sampled",
            "volume": monthly_queries,
            "monthly_cost": 0.0,
        },
    ]
    return assumptions


def write_cost_csv(rows: list[dict[str, str | float]]) -> None:
    PHASE_D.mkdir(parents=True, exist_ok=True)
    with (PHASE_D / "cost_model.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["component", "unit_cost", "volume", "monthly_cost"])
        writer.writeheader()
        writer.writerows(rows)


def generate_blueprint() -> str:
    ragas = read_json(PHASE_A / "ragas_summary.json", {})
    kappa = read_json(PHASE_B / "kappa_summary.json", {})
    latency_rows = read_csv_rows(PHASE_C / "latency_summary.csv")
    pii_rows = read_csv_rows(PHASE_C / "pii_test_results.csv")
    topic_rows = read_csv_rows(PHASE_C / "topic_test_results.csv")
    adversarial_rows = read_csv_rows(PHASE_C / "adversarial_test_results.csv")
    output_rows = read_csv_rows(PHASE_C / "output_guard_results.csv")

    aggregate = ragas.get("aggregate", {})
    targets = ragas.get("targets", {})
    pii_recall = ratio_from_summary_row(pii_rows, "recall")
    topic_accuracy = ratio_from_summary_row(topic_rows, "accuracy")
    adversarial_detection = ratio_from_summary_row(adversarial_rows, "detection")
    output_detection = ratio_from_summary_row(output_rows, "detection")
    output_fp = ratio_from_summary_row(output_rows, "fp_rate")
    total_p95 = latest_latency("total_ms", latency_rows)
    guard_p95 = (
        latest_latency("l1_input_pii_ms", latency_rows)
        + latest_latency("l2_policy_ms", latency_rows)
        + latest_latency("l3_output_ms", latency_rows)
    )
    cost_rows = build_cost_table()
    write_cost_csv(cost_rows)
    total_cost = sum(float(row["monthly_cost"]) for row in cost_rows)

    lines = [
        "# Phase D - Production Blueprint",
        "",
        "## 1. SLO Definition",
        "",
        "| Metric | Current | Alert Threshold | Severity | Status |",
        "|--------|---------|-----------------|----------|--------|",
    ]
    slo_rows = [
        ("Faithfulness", aggregate.get("faithfulness", 0.0), targets.get("faithfulness", 0.75), "P1", "min"),
        ("Answer Relevancy", aggregate.get("answer_relevancy", 0.0), targets.get("answer_relevancy", 0.70), "P1", "min"),
        ("Context Precision", aggregate.get("context_precision", 0.0), targets.get("context_precision", 0.60), "P2", "min"),
        ("Context Recall", aggregate.get("context_recall", 0.0), targets.get("context_recall", 0.65), "P1", "min"),
        ("Judge Cohen Kappa", kappa.get("cohens_kappa", 0.0), 0.60, "P2", "min"),
        ("PII Recall", pii_recall, 0.80, "P1", "min"),
        ("Adversarial Detection", adversarial_detection, 0.70, "P1", "min"),
        ("Output Unsafe Detection", output_detection, 0.80, "P1", "min"),
        ("Output False Positive Rate", output_fp, 0.05, "P2", "max"),
        ("Total P95 Latency ms", total_p95, 5000.0, "P2", "max"),
        ("Guardrail P95 Latency ms", guard_p95, 1200.0, "P2", "max"),
    ]
    for name, current, threshold, severity, direction in slo_rows:
        current_f = float(current or 0.0)
        threshold_f = float(threshold or 0.0)
        status = metric_status(current_f, threshold_f, direction)
        lines.append(f"| {name} | {current_f:.4f} | {threshold_f:.4f} | {severity} | {status} |")

    lines.extend([
        "",
        "## 2. Architecture Diagram",
        "",
        "```mermaid",
        "graph TD",
        "  U[User Input] --> L1[Input Guard Layer]",
        "  L1 --> PII[PII Redaction: Presidio + VN regex]",
        "  L1 --> TOPIC[Topic Scope Validator]",
        "  L1 --> INJ[Prompt Injection Detection]",
        "  PII --> GATE{Allowed?}",
        "  TOPIC --> GATE",
        "  INJ --> GATE",
        "  GATE -- No --> BLOCK[Blocked Response]",
        "  GATE -- Yes --> RAG[Day 18 RAG Pipeline]",
        "  RAG --> RET[Hybrid Retrieval + Rerank]",
        "  RET --> LLM[Generation LLM]",
        "  LLM --> OUT[Output Guard: Llama Guard or Heuristic]",
        "  OUT --> SAFE{Safe?}",
        "  SAFE -- No --> OBLOCK[Blocked Output]",
        "  SAFE -- Yes --> RESP[Response to User]",
        "  L1 -. async .-> AUDIT[Audit Log]",
        "  OUT -. async .-> AUDIT",
        "  RAG -. eval sample .-> RAGAS[RAGAS Nightly Eval]",
        "  RAGAS --> ALERT[Alerting + Failure Analysis]",
        "  LLM -. judge sample .-> JUDGE[LLM-as-Judge Calibration]",
        "  JUDGE --> ALERT",
        "```",
        "",
        "## 3. Alert Playbook",
        "",
        "### Incident: Faithfulness drops below 0.75",
        "",
        "- Severity: P1",
        "- Detection: nightly RAGAS eval or pull-request eval gate",
        "- Likely causes: weak context, prompt drift, stale index, model behavior change",
        "- Investigation steps: inspect bottom questions, compare retrieved contexts, check recent prompt/index changes, verify API/model version",
        "- Resolution: rollback prompt/model, rebuild index, increase retrieval candidates, add answer verifier",
        "- SLO impact: answer trust degradation",
        "",
        "### Incident: Context Recall drops below 0.65",
        "",
        "- Severity: P1",
        "- Detection: RAGAS context_recall aggregate or cluster analysis",
        "- Likely causes: chunking regression, missing corpus ingestion, dense embedding mismatch, Qdrant collection drift",
        "- Investigation steps: check corpus count, inspect retriever top-k, validate embedding model, compare BM25 vs dense hits",
        "- Resolution: re-index corpus, restore embedding model, raise retrieval top-k, add query expansion",
        "- SLO impact: system cannot find supporting evidence",
        "",
        "### Incident: PII recall below 0.80",
        "",
        "- Severity: P1",
        "- Detection: Phase C PII guard regression suite",
        "- Likely causes: disabled Presidio model, regex regression, new local identifier format",
        "- Investigation steps: review failed examples, check dependency installation, compare regex patterns",
        "- Resolution: add recognizer pattern, restore Presidio install, expand multilingual test set",
        "- SLO impact: privacy leakage risk",
        "",
        "### Incident: Output guard latency P95 above 1200ms",
        "",
        "- Severity: P2",
        "- Detection: latency benchmark or production trace sampling",
        "- Likely causes: external Llama Guard API latency, network instability, sequential guard calls",
        "- Investigation steps: compare provider latency, check timeout/retry logs, validate async execution",
        "- Resolution: run output guard in parallel where possible, lower max tokens, switch to local/cheaper guard for low-risk traffic",
        "- SLO impact: degraded user experience",
        "",
        "## 4. Cost Analysis",
        "",
        "Assumption: 100,000 production queries per month plus nightly eval sampling.",
        "",
        "| Component | Unit Cost | Volume | Monthly Cost |",
        "|-----------|-----------|--------|--------------|",
    ])
    for row in cost_rows:
        lines.append(f"| {row['component']} | {row['unit_cost']} | {row['volume']} | ${float(row['monthly_cost']):.2f} |")
    lines.extend([
        f"| **Total** |  |  | **${total_cost:.2f}** |",
        "",
        "## 5. Cost Optimization Opportunities",
        "",
        "- Run deterministic PII/topic/injection checks before any LLM call to block bad requests early.",
        "- Sample RAGAS and judge calibration instead of evaluating every production query.",
        "- Route low-risk responses through heuristic output guard and reserve Llama Guard for risky topics.",
        "- Cache embeddings and retrieval results for repeated test/eval questions.",
        "- Use pairwise judge only for candidate comparisons; use absolute scoring for periodic monitoring.",
        "",
        "## 6. Production Readiness Notes",
        "",
        f"- RAGAS source: `{ragas.get('metric_source', 'unknown')}` over {ragas.get('num_questions', 0)} questions.",
        f"- Judge calibration: kappa `{float(kappa.get('cohens_kappa', 0.0)):.3f}` ({kappa.get('interpretation', 'unknown')}).",
        f"- Guardrails benchmark: total P95 `{total_p95:.1f}ms`, guardrail P95 estimate `{guard_p95:.1f}ms`.",
        "- Current highest-risk gaps should be addressed before production: answer relevancy and judge calibration agreement.",
    ])
    return "\n".join(lines) + "\n"


def main() -> None:
    PHASE_D.mkdir(parents=True, exist_ok=True)
    blueprint = generate_blueprint()
    (PHASE_D / "blueprint.md").write_text(blueprint, encoding="utf-8")
    print(f"[D] wrote {PHASE_D / 'blueprint.md'}")


if __name__ == "__main__":
    main()
