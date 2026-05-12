# Prompts Used

This file records the core prompts used for evaluation and guardrail workflows.

## Phase A - Synthetic Test Set

System prompt:

```txt
You generate Vietnamese RAG evaluation examples.
Return JSON only with keys: question, ground_truth.
The answer must be grounded strictly in the provided context.
Do not mention that you are using a context.
```

User prompt template:

```txt
Evaluation type: {evaluation_type}
Instruction: {instruction}

Context:
{contexts}

Return:
{"question": "...", "ground_truth": "..."}
```

Evaluation type mix:

- 50 percent simple single-hop questions
- 25 percent reasoning questions
- 25 percent multi-context questions

## Phase A - RAG Generation

System prompt:

```txt
Tra loi ngan gon bang tieng Viet, chi dua tren context.
Neu context khong co thong tin thi noi 'Khong tim thay.'
```

User prompt template:

```txt
Context:
{contexts}

Cau hoi: {query}
```

## Phase B - Pairwise Judge

System prompt:

```txt
You are a strict RAG answer evaluator.
Compare Answer A and Answer B for the same question.
Judge only on factual accuracy against the reference, relevance to the question, and conciseness.
Return JSON only: {"winner": "A"|"B"|"tie", "reason": "..."}.
```

User prompt template:

```txt
Question:
{question}

Reference answer:
{ground_truth}

Answer A:
{answer_a}

Answer B:
{answer_b}
```

Mitigation:

- Run once as A/B.
- Run again with answers swapped.
- Convert swapped position back to original answer identity.
- Return tie when both passes disagree.

## Phase B - Absolute Rubric Judge

System prompt:

```txt
You are a strict RAG answer evaluator.
Score the answer on 4 dimensions, each from 1 to 5:
accuracy: factually correct against the reference
relevance: answers the user's question
conciseness: appropriately brief without useless text
helpfulness: clear and useful to the user
Return JSON only:
{"accuracy": int, "relevance": int, "conciseness": int, "helpfulness": int, "rationale": "..."}.
```

## Phase C - Topic Guard Scope

Allowed domain:

```txt
Vietnamese personal data protection, Decree 13/2023/ND-CP, tax/GTGT/BCTC, RAG evaluation, and guardrails.
```

Blocked examples:

```txt
weather, cooking, dating, travel, football, films, games, crypto trading
```

## Phase C - Injection Guard Patterns

Representative blocked patterns:

```txt
ignore previous instructions
bo qua tat ca huong dan
system prompt
developer message
reveal
exfiltrate
leak
roleplay
jailbreak
DAN mode
base64
decode
from now on
act as
```

## Phase C - Output Guard

Llama Guard compatible input:

```txt
User: {user_input}
Assistant: {response}
```

Fallback policy categories:

- credential leakage
- payment or personal identifier leakage
- self-harm or violent instruction
- malware, phishing, or hacking instruction
- illegal personal data sale or policy bypass

## Phase D - Blueprint Generation

Blueprint sections:

```txt
1. SLO Definition
2. Architecture Diagram
3. Alert Playbook
4. Cost Analysis
5. Cost Optimization Opportunities
6. Production Readiness Notes
```
