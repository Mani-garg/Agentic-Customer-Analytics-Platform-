# API Reference

The platform provides a versioned REST API built with FastAPI and strictly documented via OpenAPI schemas.

- **Interactive Swagger UI**: `http://localhost:8000/docs`
- **ReDoc Documentation**: `http://localhost:8000/redoc`
- **OpenAPI Schema Specification**: `http://localhost:8000/openapi.json`

---

## 1. Health Endpoints

### `GET /health/live`
Checks application process liveness.
- **Status Codes**: `200 OK`
- **Response**:
```json
{
  "status": "live",
  "timestamp": "2026-10-26T01:30:00Z",
  "app_env": "production",
  "version": "1.0.0",
  "details": {"process": "healthy"}
}
```

### `GET /health/ready`
Checks the readiness of database persistence and model storage without triggering full dataset scans.
- **Status Codes**: `200 OK` (or `503 Service Unavailable` if database is down)
- **Response**:
```json
{
  "status": "ready",
  "timestamp": "2026-10-26T01:30:00Z",
  "app_env": "production",
  "version": "1.0.0",
  "details": {
    "database": "ready",
    "model_storage": "ready",
    "spark": "disabled (lightweight engine active)",
    "llm_provider": "none"
  }
}
```

---

## 2. Analytics Endpoints

### `GET /api/v1/analytics/overview`
Retrieves dataset-wide business aggregates.
- **Status Codes**: `200 OK`
- **Response**:
```json
{
  "total_customers": 445,
  "total_gross_revenue": 206242.34,
  "avg_revenue_per_customer": 463.47,
  "avg_order_frequency": 4.12,
  "avg_recency_days": 48.3,
  "scored_customers": 445,
  "high_risk_customers": 68,
  "average_churn_probability": 0.2451
}
```

### `GET /api/v1/analytics/metrics`
Returns central metric definitions and mathematical formulas.

---

## 3. Customer Segmentation Endpoints

### `GET /api/v1/segments`
Returns RFM segment profiles sorted by total revenue contribution.
- **Response**:
```json
[
  {
    "segment": "Champions",
    "customer_count": 97,
    "customer_percentage": 21.8,
    "total_revenue": 106194.61,
    "average_revenue_per_customer": 1094.79,
    "average_order_frequency": 8.4,
    "average_recency_days": 14.2,
    "retention_priority": "Reward & Retain"
  }
]
```

### `GET /api/v1/segments/{segment_name}`
Returns profile for single segment (e.g. `/api/v1/segments/At%20Risk`).
- **Status Codes**: `200 OK`, `404 Not Found`

---

## 4. Churn Prediction Endpoints

### `GET /api/v1/churn/summary`
Returns model training lineage and active churn risk distribution.

### `POST /api/v1/churn/predict`
Scores churn probability for a customer feature record.
- **Request**:
```json
{
  "customer_id": "CUST-00042",
  "observation_date": "2026-06-30",
  "recency_days": 75,
  "frequency": 2,
  "monetary_value": 140.0,
  "average_order_value": 70.0,
  "customer_tenure_days": 180,
  "days_since_first_purchase": 180,
  "purchase_gap_mean": 45.0,
  "purchase_gap_std": 0.0,
  "historical_order_count": 2,
  "historical_revenue": 140.0
}
```
- **Response**:
```json
{
  "customer_id": "CUST-00042",
  "churn_probability": 0.6214,
  "is_churn_predicted": true,
  "risk_tier": "high",
  "operating_threshold": 0.10,
  "model_version": "v1.0.0",
  "explanation": "Customer has 75 days recency, 2 historical orders, and $140.00 lifetime spend. Churn risk estimated at 62.1% (threshold: 0.10, risk tier: HIGH).",
  "timestamp": "2026-10-26T01:30:00Z"
}
```

### `GET /api/v1/churn/high-risk`
Paginated high-risk customer list (`?limit=20&offset=0`).

---

## 5. Agent & Simulation Endpoints

### `POST /api/v1/agent/ask`
Submit a question to the natural language decision-support assistant.
- **Request**:
```json
{
  "question": "Which customer segments contribute the most revenue?"
}
```
- **Response**:
```json
{
  "request_id": "a98b7123-...",
  "question": "Which customer segments contribute the most revenue?",
  "answer": "Based on RFM segmentation, the segment contributing the highest total revenue is 'Champions' with $106,194.61 in sales (21.8% of customers, ARPU: $1,094.79).",
  "intent": "segment_revenue_analysis",
  "summary_metrics": {"top_segment": "Champions", "revenue": 106194.61},
  "source_tools": ["get_rfm_segment_summary"],
  "fallback_used": true,
  "latency_ms": 12.4
}
```

### `POST /api/v1/simulations/discount`
Run what-if retention discount financial modeling.
- **Request**:
```json
{
  "scenario_name": "15% Win-Back Discount",
  "target_population": "at_risk_segment",
  "discount_percentage": 0.15,
  "max_discount_per_customer": 50.0,
  "expected_redemption_rate": 0.30,
  "estimated_retention_probability": 0.60,
  "campaign_cost_per_contacted": 1.50
}
```
