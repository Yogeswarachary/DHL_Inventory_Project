## DHL Inventory Optimization Dashboard
#### Project Overview
- **End-to-End Data Science Project**: Complete analytics pipeline from raw data ingestion to interactive business intelligence dashboard for DHL's global inventory operations.
- **Business Context**: Analyzes 180,519 order records across 53 features to optimize inventory management, reduce late delivery risk, and maximize profitability across regions, customer segments, and product categories.

#### Technical Implementation
- **Data Cleaning**: Handled missing values (forward-fill for time-series, mode for categoricals), dropped PII columns, normalized 53 messy column names to snake_case
- **Feature Engineering**: Created lead_time_days (shipping_date - order_date), order_month for temporal analysis.​
- **Data Quality**: Outlier detection (IQR method), skewness/kurtosis analysis for key metrics.

#### Statistical Analysis
- **Hypothesis Tests**: Chi-square tests for categorical independence, t-tests for lead time differences
- **Distribution Analysis**: Modeled order quantities (Binomial), lead times (Poisson)
- **Key Findings**: Identified high-risk regions, profitable customer segments, shipping mode impact

#### Production Dashboard
- **Streamlit App**: Interactive filters (region/category/segment) with 3-tab interface:
- Executive Summary: KPI metrics, monthly trends
- Operations: Lead time distributions, late delivery risk heatmaps
- Profitability: Category/segment revenue analysis, profit margins

KPIs:
              |  #  | **Metric**         | **Value**                 |
| :-: | ------------------ | ------------------------- |
|  1  | Avg Lead Time      | 3.5 d                     |
|  2  | Delay %            | 54.8 %                    |
|  3  | 90th Lead time     | 6.0 d                     |
|  4  | 90th Quantity      | 36,347                    |
|  5  | High-Risk Corridor | Central Africa (Consumer) |
|  6  | Stockout Risk      | 95.0 %                    |

#### Recommendations:
1. Safety Stock: Use 90th Lead Time buffer in high-risk regions.
2. Reorder Quantity: Optimize based on Poisson 90th percentile batches.
3. Modes: Prioritize Express shipping (statistically significant via t-test).
4. Regions: Reengineer processes for high Chi-square risk zones.
5. Products: Promote fast-movers and consolidate slow-moving stock.
