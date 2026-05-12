# Failure Cluster Analysis

## Bottom 10 Questions

| # | Question | Type | F | AR | CP | CR | Avg | Diagnosis |
|---|----------|------|---|----|----|----|-----|-----------|
| 1 | Ai đã gửi Hồ sơ đánh giá tác động chuyển dữ liệu cá nhân ra nước ngoài cho Bộ Công an? | simple | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | Answer not fully grounded |
| 2 | Có bao nhiêu tài liệu kèm theo? | simple | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | Answer not fully grounded |
| 3 | Việc bảo vệ dữ liệu cá nhân ở Việt Nam được thực hiện theo quy định nào? | simple | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | Answer not fully grounded |
| 4 | Chương nào được đề cập trong tài liệu? | simple | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | Answer not fully grounded |
| 5 | Chương nào được đề cập trong văn bản? | simple | 0.00 | 0.00 | 0.58 | 0.00 | 0.15 | Answer not fully grounded |
| 6 | Mẫu số 05 thuộc về tổ chức nào? | simple | 0.00 | 0.74 | 0.00 | 0.00 | 0.18 | Answer not fully grounded |
| 7 | Có bao nhiêu chỉ tiêu điều chỉnh thuế GTGT trong bảng trên? | reasoning | 0.00 | 0.44 | 0.83 | 0.00 | 0.32 | Answer not fully grounded |
| 8 | Hoạt động bảo vệ dữ liệu cá nhân là gì? | simple | 0.00 | 0.00 | 0.33 | 1.00 | 0.33 | Answer not fully grounded |
| 9 | Ai là người gửi hồ sơ đánh giá tác động xử lý dữ liệu cá nhân đến Bộ Công an? | reasoning | 1.00 | 0.43 | 0.00 | 0.00 | 0.36 | Off-topic retrievals |
| 10 | Mẫu số 03 thuộc tổ chức nào? | simple | 0.00 | 1.00 | 0.50 | 0.00 | 0.38 | Answer not fully grounded |

## Clusters Identified

### Cluster C1: Answer not fully grounded

- Count: 9
- Pattern: Ai đã gửi Hồ sơ đánh giá tác động chuyển dữ liệu cá nhân ra nước ngoài cho Bộ Cô; Có bao nhiêu tài liệu kèm theo?
- Root cause: weakest observed metric and query type indicate `answer not fully grounded`.
- Proposed technical fix: Tighten system prompt, quote context spans, and return unknown when evidence is missing.

### Cluster C2: Off-topic retrievals

- Count: 1
- Pattern: Ai là người gửi hồ sơ đánh giá tác động xử lý dữ liệu cá nhân đến Bộ Công an?
- Root cause: weakest observed metric and query type indicate `off-topic retrievals`.
- Proposed technical fix: Tune hybrid weights and rerank more candidates before selecting final contexts.

## Next Actions

1. Re-run retrieval with larger candidate set before reranking.
2. Preserve parent chunks as generation context for legal and financial sections.
3. Add an answer verifier that checks whether the answer is supported by retrieved contexts.
