# Validation Methodology & Scoring Formula

## 5-Stage Equivalence Framework

Equivalence between source dataset \(D_S\) and target dataset \(D_T\) is proven across 5 complementary dimensions:

### 1. Schema Integrity
Ensure column set \(C_S \subseteq C_T\) and datatype mapping compatibility:
\[
\text{Score}_{\text{schema}} = \begin{cases} 100 & \text{if } C_S \subseteq C_T \\ 0 & \text{otherwise} \end{cases}
\]

### 2. Row-Level Hash Equivalence
For each row \(r\), compute MD5 hash \(h(r)\). Matched row ratio:
\[
\text{MatchRatio} = \frac{|H_S \cap H_T|}{\max(|H_S|, |H_T|)}
\]

### 3. Aggregate Invariants
Verify numeric sums and averages within tolerance \(\epsilon = 10^{-4}\):
\[
|\sum x_S - \sum x_T| \le \epsilon
\]

### 4. Assurance Score Formula
The composite Assurance Score \(A \in [0, 100]\) is calculated as:
\[
A = 0.25 \cdot S_{\text{schema}} + 0.30 \cdot S_{\text{rows}} + 0.25 \cdot S_{\text{agg}} + 0.10 \cdot S_{\text{rules}} + 0.10 \cdot S_{\text{edge}}
\]
Deployment Gate Approval passes if \(A \ge 85.0\).
