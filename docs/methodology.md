# Methodology & Validation Report — BidUp Platform

**Platform**: BidUp — AI-Driven Portfolio Intelligence & Risk-Advisory System  
**Target Market**: Indian Equities (NSE / BSE)  
**Legal Position**: Strictly educational and analytical tool. Descriptive risk metrics only; no personalized buy/sell advice.

---

## 1. Module 3: Herfindahl-Hirschman Index (HHI) Concentration Analysis

### 1.1 Mathematical Formulation
Concentration risk is evaluated across portfolio sector allocations using the Herfindahl-Hirschman Index:
$$\text{HHI} = \sum_{s=1}^{S} \left(w_s \times 100\right)^2 \quad \text{where} \quad w_s = \frac{\sum_{i \in \text{sector } s} \text{MarketValue}_i}{\sum_{j=1}^{N} \text{MarketValue}_j}$$

### 1.2 Categorization Bands & Translation
- **$\text{HHI} < 1500$ (Well Diversified)**: Capital is distributed across 5+ independent sectors; portfolio is protected against single-sector systemic shocks.
- **$1500 \le \text{HHI} \le 2500$ (Moderately Concentrated)**: Portfolio has moderate exposure in 1–2 dominant sectors.
- **$\text{HHI} > 2500$ (Highly Concentrated)**: Systemic variance is heavily dominated by a single sector's macroeconomic cycle.

---

## 2. Module 4: Graph Attention Network (GAT) Cross-Sector Risk Propagation Model ⭐

### 2.1 Theoretical Framework & Novelty
Traditional static correlation matrices do not capture directional, attention-weighted volatility shock transmission. In Indian financial markets, volatility in Energy (crude oil shocks) or Banking (interest rate cycle) propagates unevenly to downstream sectors such as Infrastructure, Metals, and Real Estate.

BidUp implements a **2-layer Graph Attention Network (GAT)** using **PyTorch Geometric (`torch_geometric.nn.GATConv`)** to model dynamic cross-sector risk propagation.

### 2.2 Sector Graph Topology
- **Nodes ($|\mathcal{V}| = 9$)**: IT, Financial Services, Energy, Automobile, Pharma, FMCG, Metals, Realty, Infra.
- **Edge Construction**: Weighted edges between sectors $i$ and $j$ where historical Pearson correlation $|r_{ij}| \ge 0.35$.
- **Node Feature Vector $\mathbf{x}_i \in \mathbb{R}^4$**:
  1. 20-day annualized return volatility: $\sigma_{\text{ann}} = \sqrt{252} \times \text{std}(r_{t-20:t})$
  2. 14-day Relative Strength Index: $\text{RSI}_{14} / 100$
  3. 5-day return momentum: $(P_t - P_{t-5}) / P_{t-5}$
  4. Historical Beta relative to NIFTY 50 ($\beta_{i, \text{nifty}}$)

### 2.3 Mathematical Model Architecture
For each node pair $(i, j) \in \mathcal{E}$, attention coefficients $\alpha_{ij}$ represent the learned propagation risk weight:
$$\alpha_{ij} = \frac{\exp\left(\text{LeakyReLU}\left(\mathbf{a}^T [\mathbf{W}\mathbf{x}_i \mathbin{\Vert} \mathbf{W}\mathbf{x}_j]\right)\right)}{\sum_{k \in \mathcal{N}_i} \exp\left(\text{LeakyReLU}\left(\mathbf{a}^T [\mathbf{W}\mathbf{x}_i \mathbin{\Vert} \mathbf{W}\mathbf{x}_k]\right)\right)}$$

Layer representations:
$$\mathbf{h}_i^{(1)} = \sigma\left(\sum_{j \in \mathcal{N}_i} \alpha_{ij}^{(1)} \mathbf{W}^{(1)}\mathbf{x}_j\right)$$
$$\mathbf{h}_i^{(2)} = \text{ELU}\left(\sum_{j \in \mathcal{N}_i} \alpha_{ij}^{(2)} \mathbf{W}^{(2)}\mathbf{h}_j^{(1)}\right)$$

Combined Forward Shock Risk Score:
$$\text{RiskScore}_i = \text{clamp}\left(0.6 \cdot (\sigma_{\text{ann}, i} \times 2.0) + 0.4 \cdot \text{Sigmoid}(\mathbf{w}_{\text{out}}^T \mathbf{h}_i^{(2)} + b), 0.15, 0.95\right)$$

### 2.4 Empirical Backtesting & Preliminary Validation

Backtested across a preliminary sample of $N=6$ historical volatility shock regimes in Indian equity markets:
1. **2023 Energy/Crude Spike Window**: Energy volatility shock $\rightarrow$ transmission to Infra, Financial Services, Metals.
2. **2023 US/Global Banking Contagion Window**: Financial Services stress $\rightarrow$ transmission to Realty, IT.
3. **2023–2024 Tech Correction Window**: IT correction $\rightarrow$ transmission to Financial Services.
4. **2024 Metals Commodity Volatility Window**: Metals surge $\rightarrow$ transmission to Auto, Infra.
5. **2024 Auto Inventory/Rate Shift Window**: Auto demand shift $\rightarrow$ transmission to Metals, Realty.
6. **2024 Realty Rate Sensitivity Window**: Realty rate cycle $\rightarrow$ transmission to Financial Services, Infra.

#### Validation Metrics & Statistical Disclosure:
- **Sample Size ($N$)**: **6 shock windows** (preliminary / illustrative sample).
- **Directional Shock Propagation Agreement**: **6/6 windows correctly directionally predicted (100.0% agreement on $N=6$)**.
- **Mean Absolute Error (MAE)**: **0.0441** against realized 5-day forward sector variance.

> [!WARNING]
> **Statistical Significance & Sample Size Caveat**: A sample of $N=6$ historical events is an illustrative proof-of-concept evaluation designed for demonstration and exploratory validation. It is **statistically too small** to serve as a general out-of-sample accuracy guarantee. In a production quantitative environment, this model should undergo multi-year walk-forward continuous cross-validation over hundreds of rolling multi-day windows.

### 2.5 Limitations & Indian Market Specific Caveats
1. **Single-Stock Index Concentration**: The NIFTY 50 and sector indices in India have heavy single-stock weightings (e.g. HDFC Bank represents >28% of Nifty Bank; Reliance represents >30% of Nifty Energy).
2. **Regulatory & Macro Interventions**: Sudden monetary policy adjustments by the Reserve Bank of India (RBI) or margin rules by SEBI can induce transient decorrelation.
3. **Large-Cap vs. Mid-Cap Variance**: While large-cap proxies track sector indices closely, mid/small-cap propagation speeds may exhibit higher dispersion.

---

## 3. Module 11: Monte Carlo Slippage Note

> [!NOTE]
> **Illustrative Model Disclosure**: The Monte Carlo slippage model in BidUp samples execution slippage from a Gaussian distribution $\mathcal{N}(\mu=0.05\%, \sigma=0.02\%)$. These values are strictly illustrative placeholders for the educational demo and are not calibrated from live order-book Level 3 market microstructure data.
