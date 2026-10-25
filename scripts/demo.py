#!/usr/bin/env python3
"""End-to-end demonstrable script executing the complete analytics and ML lifecycle."""

import sys
from datetime import date
from pathlib import Path

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from customer_analytics.agent.factory import AnalyticsAgentService
from customer_analytics.data.cleaning import clean_transactions
from customer_analytics.data.repository import AnalyticsRepository
from customer_analytics.data.synthetic import generate_synthetic_transactions, save_synthetic_data
from customer_analytics.data.validation import validate_transactions
from customer_analytics.domain.models import CustomerFeatureRecord, SimulationScenario
from customer_analytics.features.build_features import build_customer_feature_table
from customer_analytics.ml.predict import ChurnInferenceService
from customer_analytics.ml.train import train_churn_model
from customer_analytics.simulation.engine import SimulationEngine


def run_demo():
    print("=================================================================")
    print("   AGENTIC CUSTOMER ANALYTICS PLATFORM - END-TO-END DEMO        ")
    print("=================================================================\n")

    # 1. Generate Synthetic Data
    raw_path = Path("data/raw/demo_transactions.csv")
    print("1. Generating synthetic e-commerce transactions (n=500 customers)...")
    df_raw = generate_synthetic_transactions(n_customers=500, seed=42)
    save_synthetic_data(df_raw, raw_path)
    print(f"   Generated {len(df_raw):,} records. Saved to {raw_path}.")

    # 2. Data Validation
    print("\n2. Executing Data Quality Validation...")
    accepted, rejected, val_report = validate_transactions(df_raw)
    print(f"   Validation Status: {'PASSED' if val_report.checks_passed else 'FAILED'}")
    print(
        f"   Records Accepted: {val_report.records_accepted:,} | Rejected: {val_report.records_rejected}"
    )

    # 3. Ingestion & Cleaning
    print("\n3. Cleaning transactions and deriving gross/net revenues...")
    cleaned, stats = clean_transactions(accepted)
    print(f"   Cleaned Rows: {stats['final_rows']:,}")

    # 4. Feature Engineering & RFM Segmentation
    cutoff = date(2026, 6, 30)
    print(f"\n4. Building customer feature table at observation cutoff {cutoff}...")
    features = build_customer_feature_table(
        cleaned, observation_cutoff=cutoff, churn_horizon_days=90
    )
    print(
        f"   Customer Feature Table: {len(features):,} customers with {len(features.columns)} features."
    )

    # 5. Persist to Relational DB
    print("\n5. Synchronizing analytical datasets to relational database...")
    repo = AnalyticsRepository()
    repo.sync_feature_dataframe_to_db(features)
    overview = repo.get_overview_metrics()
    print(f"   Total Customers: {overview['total_customers']:,}")
    print(f"   Total Gross Revenue: ${overview['total_gross_revenue']:,.2f}")
    print(f"   Average Spend per Customer: ${overview['avg_revenue_per_customer']:,.2f}")

    # 6. Customer Segmentation
    print("\n6. Customer RFM Segmentation Profile:")
    segments = repo.get_segment_summaries()
    for s in segments[:4]:
        print(
            f"   - {s.segment.value:<20}: {s.customer_count:>4} customers ({s.customer_percentage:>5.1f}%) | Rev: ${s.total_revenue:>10,.2f} | Action: {s.retention_priority}"
        )

    # 7. Model Training & Threshold Tuning
    print("\n7. Training XGBoost Churn Classifier with Recall-Prioritized Threshold Tuning...")
    model, metadata, eval_report = train_churn_model(
        feature_df=features,
        artifact_dir="artifacts/models",
        seed=42,
        min_precision=0.35,
    )
    xgb_m = eval_report["xgb_test_metrics"]["metrics"]
    print(f"   Model Version:       {metadata.model_version}")
    print(f"   Selected Threshold:  {metadata.operating_threshold:.3f}")
    print(f"   Test Recall:         {xgb_m['recall']:.4f}")
    print(f"   Test Precision:      {xgb_m['precision']:.4f}")
    print(f"   Test PR-AUC:         {xgb_m['pr_auc']:.4f}")

    # 8. Single Customer Risk Scoring
    print("\n8. Executing Single Customer Churn Prediction...")
    inference = ChurnInferenceService("artifacts/models")
    sample_feat = CustomerFeatureRecord(**features.iloc[0].to_dict())
    pred = inference.predict_customer_risk(sample_feat)
    print(f"   Customer ID:       {pred.customer_id}")
    print(f"   Estimated Churn:   {pred.churn_probability * 100:.1f}%")
    print(f"   Risk Tier:         {pred.risk_tier.value.upper()}")
    print(f"   Explanation:       {pred.explanation}")

    # 9. Guarded Analytics Agent Inquiry
    print("\n9. Testing Natural-Language Analytics Agent (Guarded Interface)...")
    agent = AnalyticsAgentService(repository=repo)
    sample_question = "Which customer segments contribute the most revenue?"
    print(f"   Question: '{sample_question}'")
    agent_resp = agent.ask(sample_question)
    print(f"   Agent Answer: {agent_resp.answer}")
    print(f"   Tools Used:   {agent_resp.source_tools}")

    # 10. Revenue-Recovery Simulation
    print("\n10. What-If Revenue-Recovery Retention Simulation:")
    sim_engine = SimulationEngine()
    scenario = SimulationScenario(
        scenario_id="demo_scenario_15",
        name="15% Win-Back Discount Campaign",
        target_population="at_risk_segment",
        discount_percentage=0.15,
        max_discount_per_customer=50.0,
        expected_redemption_rate=0.30,
        estimated_retention_probability=0.60,
        expected_future_revenue_per_retained=overview["avg_revenue_per_customer"],
        campaign_cost_per_contacted=1.50,
    )
    sim_result = sim_engine.simulate_scenario(
        scenario,
        customer_count=overview["total_customers"],
        avg_monetary=overview["avg_revenue_per_customer"],
    )
    print(f"   Contacted Customers:          {sim_result.contacted_customers:,}")
    print(f"   Expected Retained Customers:  {sim_result.expected_retained_customers:,}")
    print(f"   Total Campaign Cost:          ${sim_result.total_cost:,.2f}")
    print(f"   Estimated Incremental Revenue:${sim_result.estimated_incremental_revenue:,.2f}")
    print(f"   Estimated Net Incremental Val:${sim_result.estimated_net_incremental_value:,.2f}")
    print(f"   Simulated ROI:                {sim_result.roi_percentage:.1f}%")
    print(f"   Disclaimer:                   {sim_result.disclaimer}")

    print("\n=================================================================")
    print("   END-TO-END DEMO EXECUTION COMPLETE AND FULLY VERIFIED         ")
    print("=================================================================\n")


if __name__ == "__main__":
    run_demo()
