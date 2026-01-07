import streamlit as st
import pandas as pd
import numpy as np

# BASIC CONFIG
st.set_page_config(
    page_title="DHL Inventory Optimization",
    layout="wide",
)

# DATA LAYER
@st.cache_data
def load_raw():
    url = "https://raw.githubusercontent.com/Yogeswarachary/DHL_Inventory_Project/main/Data/DHL_Project.parquet"
    response = requests.get(url)
    response.raise_for_status()  # ensure file downloaded
    df = pd.read_parquet(io.BytesIO(response.content))
    return df

@st.cache_data
def build_dataset():
    df = load_raw()

    # Drop sensitive / unused columns (just like code notebook)
    drop_cols = [
        "Customer Password", "Customer Street", "Customer Zipcode",
        "Order zipcode", "Product Image", "Product Description",
        "Product Card Id",
    ]
    df_clean = df.drop(columns=[c for c in drop_cols if c in df.columns])

    # Handle missing values (same strategy as notebook)
    num_cols = df_clean.select_dtypes(np.number).columns
    for c in num_cols:
        # future‑proof fillna
        df_clean[c] = df_clean[c].ffill().fillna(0)

    cat_cols = df_clean.select_dtypes("object").columns
    for c in cat_cols:
        df_clean[c] = df_clean[c].fillna(df_clean[c].mode()[0])

    # Convert to proper dates using ORIGINAL column names
    df_clean["order_date"] = pd.to_datetime(
        df_clean["order date (DateOrders)"], errors="coerce"
    )
    df_clean["shipping_date"] = pd.to_datetime(
        df_clean["shipping date (DateOrders)"], errors="coerce"
    )

    # Lead time days (still with original col names available)
    df_clean["lead_time_days"] = (df_clean["shipping_date"] - df_clean["order_date"]).dt.days
    df_clean["lead_time_days"] = (
        df_clean["lead_time_days"]
        .fillna(df_clean["Days for shipping (real)"])
        .clip(lower=0)
    )

    # Normalize column names (snake_case) AFTER creating new columns
    df_clean.columns = (
        df_clean.columns
        .str.lower()
        .str.replace(r"[^\w\s]", "", regex=True)
        .str.replace(" ", "_")
        .str.strip()
    )

    # After this, columns are: order_date, shipping_date, days_for_shipping_real, etc.

    # Add order_month using the NEW normalized name
    df_clean["order_month"] = df_clean["order_date"].dt.to_period("M")

    return df_clean

df_clean = build_dataset()

# SIDEBAR FILTERS
st.sidebar.title("DHL Inventory Controls")

regions = sorted(df_clean["order_region"].dropna().unique())
categories = sorted(df_clean["category_name"].dropna().unique())
segments = sorted(df_clean["customer_segment"].dropna().unique())

region_filter = st.sidebar.multiselect(
    "Order Region", options=regions, default=regions
)
category_filter = st.sidebar.multiselect(
    "Product Category", options=categories, default=categories
)
segment_filter = st.sidebar.multiselect(
    "Customer Segment", options=segments, default=segments
)

# Apply filters
mask = (
    df_clean["order_region"].isin(region_filter)
    & df_clean["category_name"].isin(category_filter)
    & df_clean["customer_segment"].isin(segment_filter)
)
data = df_clean[mask]

st.sidebar.markdown("---")
st.sidebar.write(f"Filtered rows: **{len(data):,}**")

# TOP-LEVEL TITLE
st.title("DHL Inventory Optimization Analytics Workspace")

st.caption(
    "Interactive view of shipping lead times, late delivery risk, and profitability "
    "by region, customer segment, and product category."
)

# TABS
tab_summary, tab_ops, tab_profit = st.tabs(
    ["Executive Summary", "Operations & Risk", "Profitability"]
)

# TAB 1: EXECUTIVE SUMMARY
with tab_summary:
    st.subheader("Portfolio KPIs (after filters)")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            "Total Sales (USD)",
            f"{data['sales'].sum():,.0f}",
        )
    with col2:
        st.metric(
            "Total Profit (USD)",
            f"{data['order_profit_per_order'].sum():,.0f}",
        )
    with col3:
        st.metric(
            "Avg Lead Time (days)",
            round(data["lead_time_days"].mean(), 2),
        )
    with col4:
        st.metric(
            "Late Delivery Risk (mean)",
            round(data["late_delivery_risk"].mean(), 3),
        )

    st.markdown("### Monthly trend Sales & Lead Time")

    if not data.empty:
        monthly = (
            data.groupby("order_month")
            .agg(
                total_sales=("sales", "sum"),
                avg_lead_time=("lead_time_days", "mean"),
                orders=("order_id", "nunique"),
            )
            .reset_index()
        )
        monthly["order_month"] = monthly["order_month"].astype(str)

        col_a, col_b = st.columns(2)
        with col_a:
            st.line_chart(
                monthly.set_index("order_month")["total_sales"],
                height=260,
            )
        with col_b:
            st.line_chart(
                monthly.set_index("order_month")["avg_lead_time"],
                height=260,
            )

        st.markdown("#### Data snapshot")
        st.dataframe(
            data[
                [
                    "order_id",
                    "order_date",
                    "shipping_date",
                    "order_region",
                    "customer_segment",
                    "category_name",
                    "lead_time_days",
                    "sales",
                    "order_profit_per_order",
                    "late_delivery_risk",
                ]
            ].head(20),
            use_container_width=True,
        )
    else:
        st.info("No data available for current filter selection.")

# TAB 2: OPERATIONS & RISK
with tab_ops:
    st.subheader("Lead Time & Late Delivery Risk")

    col1, col2 = st.columns(2)

    # Lead time distribution
    with col1:
        st.markdown("#### Lead Time distribution (days)")
        st.bar_chart(
            data["lead_time_days"].value_counts().sort_index(),
            height=260,
        )

    # Late risk by region and segment
    with col2:
        st.markdown("#### Late delivery risk region x segment")
        risk_crosstab = (
            pd.crosstab(
                data["order_region"],
                data["customer_segment"],
                values=data["late_delivery_risk"],
                aggfunc="mean",
            )
            .round(3)
            .sort_index()
        )
        st.dataframe(risk_crosstab, use_container_width=True)

    st.markdown("#### Lead time by region and shipping mode")
    lt_region_mode = (
        data.groupby(["order_region", "shipping_mode"])
        .agg(
            avg_lead_time=("lead_time_days", "mean"),
            orders=("order_id", "nunique"),
        )
        .round(2)
        .reset_index()
    )
    st.dataframe(lt_region_mode, use_container_width=True)

# TAB 3: PROFITABILITY
with tab_profit:
    st.subheader("Profitability by Category & Segment")

    # Profit and sales by category/segment
    cat_seg = (
        data.groupby(["category_name", "customer_segment"])
        .agg(
            total_sales=("sales", "sum"),
            total_profit=("order_profit_per_order", "sum"),
            avg_margin=("order_profit_per_order", "mean"),
            orders=("order_id", "nunique"),
        )
        .round(2)
        .reset_index()
    )

    st.markdown("#### Top 15 category x segment by sales")
    st.dataframe(
        cat_seg.sort_values("total_sales", ascending=False).head(15),
        use_container_width=True,
    )

    st.markdown("#### Profitability by region")
    region_profit = (
        data.groupby("order_region")
        .agg(
            total_sales=("sales", "sum"),
            total_profit=("order_profit_per_order", "sum"),
            avg_profit_per_order=("order_profit_per_order", "mean"),
        )
        .round(2)
        .reset_index()
    )
    st.dataframe(region_profit, use_container_width=True)

    st.markdown("#### High revenue, high delay pockets")
    high_delay = (
        data.groupby(["order_region", "shipping_mode"])
        .agg(
            total_sales=("sales", "sum"),
            late_risk=("late_delivery_risk", "mean"),
            avg_lead_time=("lead_time_days", "mean"),
        )
        .round(3)
        .reset_index()
    )
    high_delay = high_delay.sort_values(
        ["late_risk", "total_sales"], ascending=[False, False]
    )
    st.dataframe(high_delay.head(15), use_container_width=True)
