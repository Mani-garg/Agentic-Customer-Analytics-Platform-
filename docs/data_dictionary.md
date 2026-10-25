# Data Dictionary

## 1. Raw Transaction Dataset (`data/raw/transactions.csv`)

| Column Name | Data Type | Required | Description | Validation Rules | Model Feature? | Processing Stage |
|:---|:---|:---:|:---|:---|:---:|:---|
| `order_id` | String | Yes | Unique order or invoice transaction identifier | Non-null, non-empty string | No (Identifier) | Ingestion |
| `customer_id` | String | Yes | Unique persistent customer identifier | Non-null, non-empty string | No (Identifier) | Ingestion |
| `order_date` | Timestamp | Yes | Date and time the transaction was recorded | Valid datetime between 2000-01-01 and present | No (Used for temporal slicing) | Ingestion & Cleaning |
| `product_id` | String | No | Stock keeping unit or product identifier | String | No (Identifier) | Ingestion |
| `category` | String | No | Merchandise department or product category | String (e.g. Electronics, Apparel) | No (Analytical dimension) | Cleaning |
| `quantity` | Integer | Yes | Count of items purchased in line item | Integer > 0 | No (Aggregated) | Ingestion & Cleaning |
| `unit_price` | Float | Yes | Price per item unit in transaction currency | Float >= 0.0 | No (Aggregated) | Ingestion & Cleaning |
| `discount` | Float | No | Transaction line item discount percentage | Float between 0.0 and 1.0 (defaults to 0.0) | No (Aggregated) | Ingestion & Cleaning |
| `country` | String | No | Billing or shipping country of transaction | Alpha-2 country code (e.g., US, CA, GB) | No (Analytical dimension) | Cleaning |
| `order_status` | String | No | Fulfillment lifecycle state of order | Must be in `completed`, `shipped`, `pending`, `cancelled`, `refunded` | No (Filtering) | Ingestion & Cleaning |
| `currency` | String | No | Three-letter currency code | Permitted currencies: USD, EUR, GBP, CAD, AUD | No (Validation) | Ingestion & Cleaning |

---

## 2. Customer Feature Table (`data/processed/customer_features.parquet`)

Evaluated strictly at observation cutoff date $T$.

| Column Name | Data Type | Required | Definition | Feature Derivation | Model Feature? |
|:---|:---|:---:|:---|:---|:---:|
| `customer_id` | String | Yes | Unique customer identifier | Grouping key | No (Join key) |
| `observation_date` | Date | Yes | Historical observation cutoff date $T$ | Static configuration date | No (Lineage metadata) |
| `recency_days` | Integer | Yes | Days elapsed between cutoff $T$ and customer's most recent order | $T - \max(\text{order\_date})$ | **Yes** |
| `frequency` | Integer | Yes | Total count of distinct orders placed at or before $T$ | $\text{count}(\text{distinct } \text{order\_id})$ | **Yes** |
| `monetary_value` | Float | Yes | Cumulative gross revenue generated at or before $T$ | $\sum (\text{quantity} \times \text{unit\_price})$ | **Yes** |
| `average_order_value` | Float | Yes | Average gross revenue per order placed before $T$ | $\text{monetary\_value} / \text{frequency}$ | **Yes** |
| `customer_tenure_days` | Integer | Yes | Total days elapsed since the customer's first purchase | $T - \min(\text{order\_date})$ | **Yes** |
| `days_since_first_purchase`| Integer | Yes | Synonym for customer tenure | $T - \min(\text{order\_date})$ | **Yes** |
| `purchase_gap_mean` | Float | Yes | Mean elapsed days between consecutive customer orders | Average of inter-purchase day intervals | **Yes** |
| `purchase_gap_std` | Float | Yes | Standard deviation of elapsed days between orders | Standard deviation of purchase gaps | **Yes** |
| `historical_order_count` | Integer | Yes | Total historical order volume | $\text{frequency}$ | **Yes** |
| `historical_revenue` | Float | Yes | Total historical dollar volume | $\text{monetary\_value}$ | **Yes** |
| `segment` | String | No | Assigned RFM segment label | Quantile matrix mapping rule | No (Analytical label) |
| `churn_label` | Integer | Training Only | Churn indicator over future horizon $(T, T + H]$ | $1$ if $0$ orders placed in $(T, T + H]$, else $0$ | **Target Label** |
| `label_window_end` | Date | Training Only | End date of target observation horizon | $T + H$ (e.g. $T + 90\text{ days}$) | No (Lineage metadata) |
| `feature_generation_version`| String | Yes | Feature pipeline code version tag | Pipeline release string | No (Lineage metadata) |
