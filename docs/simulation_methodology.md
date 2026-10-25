# What-If Revenue-Recovery Simulation Methodology

## 1. Objective and Boundary of the Simulation

The What-If Simulator is a deterministic financial modeling tool designed to help marketing, retention, and finance teams evaluate the economic trade-offs of customer retention discount strategies before allocating real outreach budgets.

> **CRITICAL METHODOLOGICAL DISTINCTION**:
> The simulator is a scenario-planning model, **not** a causal uplift engine. It calculates projected outcomes based on user-supplied assumptions regarding redemption and retention probabilities. It does not prove that an intervention caused customer retention. Defensible causal attribution requires randomized controlled trials (A/B testing).

---

## 2. Core Economic Accounting Formulas

For any scenario $S$ with eligible customer count $N_{\text{eligible}}$:

### 2.1 Contact Funnel
1. **Contacted Population**:
   $$N_{\text{contacted}} = \min(N_{\text{eligible}}, \text{max\_customers\_to\_contact})$$
2. **Expected Redeemed Customers**:
   $$N_{\text{redeemed}} = \text{round}(N_{\text{contacted}} \times P_{\text{redemption}})$$
3. **Expected Retained Customers**:
   $$N_{\text{retained}} = \text{round}(N_{\text{redeemed}} \times P_{\text{retention}})$$

### 2.2 Cost Accounting
1. **Per-Customer Discount Subsidy**:
   $$D_{\text{unit}} = \min(\text{Baseline ARPU} \times \text{discount\_pct}, \text{max\_discount\_cap})$$
2. **Total Discount Expenditure**:
   $$C_{\text{discount}} = N_{\text{redeemed}} \times D_{\text{unit}}$$
3. **Total Outreach Campaign Cost**:
   $$C_{\text{campaign}} = N_{\text{contacted}} \times \text{cost\_per\_contacted}$$
4. **Total Scenario Cost**:
   $$C_{\text{total}} = C_{\text{discount}} + C_{\text{campaign}}$$

### 2.3 Revenue & Value Realization
1. **Gross Incremental Revenue**:
   $$R_{\text{incremental}} = N_{\text{retained}} \times \text{Baseline ARPU}$$
2. **Net Incremental Value**:
   $$V_{\text{net}} = R_{\text{incremental}} - C_{\text{total}}$$
3. **Simulated Return on Investment (ROI)**:
   $$\text{ROI} = \left( \frac{V_{\text{net}}}{C_{\text{total}}} \right) \times 100\%$$

---

## 3. Fully Worked Numerical Example

Consider an e-commerce campaign targeting the **At Risk** customer segment:

### Inputs:
- Eligible At-Risk Customers ($N_{\text{eligible}}$): **500**
- Outreach Capacity Cap: **None (contact all 500)**
- Discount Percentage: **15% (0.15)**
- Max Discount Cap per Customer: **$50.00**
- Expected Redemption Rate ($P_{\text{redemption}}$): **30% (0.30)**
- Expected Retention Rate ($P_{\text{retention}}$): **60% (0.60)**
- Historical Baseline Spend per Customer (ARPU): **$450.00**
- Campaign Outreach Cost per Contacted: **$1.50**

### Step-by-Step Accounting:
1. $N_{\text{contacted}} = 500$
2. $N_{\text{redeemed}} = 500 \times 0.30 = \mathbf{150\text{ customers}}$
3. $N_{\text{retained}} = 150 \times 0.60 = \mathbf{90\text{ customers}}$
4. Discount per customer = $\min(450 \times 0.15, 50.00) = \min(67.50, 50.00) = \mathbf{\$50.00}$
5. Total Discount Cost = $150 \times \$50.00 = \mathbf{\$7,500.00}$
6. Total Campaign Cost = $500 \times \$1.50 = \mathbf{\$750.00}$
7. Total Cost ($C_{\text{total}}$) = $\$7,500 + \$750 = \mathbf{\$8,250.00}$
8. Gross Incremental Revenue ($R_{\text{incremental}}$) = $90 \times \$450.00 = \mathbf{\$40,500.00}$
9. Net Incremental Value ($V_{\text{net}}$) = $\$40,500 - \$8,250 = \mathbf{\$32,250.00}$
10. Projected ROI = $(\$32,250 / \$8,250) \times 100\% = \mathbf{390.9\%}$

---

## 4. Sensitivity Analysis & Boundary Defense

The platform includes a 2D parameter grid evaluator (`/api/v1/simulations/sensitivity`) that evaluates outcomes across variations in discount size (e.g. 5% to 25%) and redemption rates (e.g. 10% to 50%).
- **Boundary Handling**: Negative populations, probabilities outside $[0, 1]$, and negative costs are strictly rejected by Pydantic validation before computation.
- **Negative Value Warnings**: If total costs exceed incremental revenue, the output attaches an explicit warning advising against the scenario.
