import streamlit as st
import pandas as pd
import plotly.express as px

# STUDENT NOTE: Setting up the main page configuration and title for the BI tool.
st.set_page_config(page_title="Supply Chain Performance Tool", layout="wide")
st.title("Supply Chain On-Time Delivery Performance Index")
st.write("Upload your supply chain data to identify which regions and products are causing late deliveries.")

# --- DATA LOADING AND VALIDATION ---
# STUDENT NOTE: Using Streamlit's file uploader to allow users to input their own CSV file.
uploaded_file = st.file_uploader("Upload your dataset (CSV)", type="csv")

# STUDENT NOTE: Defining the exact columns needed to compute Metric 07. 
# If a user uploads a file without these, the app will stop and warn them instead of crashing.
REQUIRED_COLUMNS = [
    "Days for shipping (real)", 
    "Days for shipment (scheduled)", 
    "Category Name", 
    "Order Region"
]

if uploaded_file is not None:
    # STUDENT NOTE: Loading the CSV into a pandas DataFrame. 
    # Using ISO-8859-1 encoding to prevent errors with special characters in international shipping data.
    df = pd.read_csv(uploaded_file, encoding='ISO-8859-1')

    # STUDENT NOTE: Validating that all required columns are present.
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        st.error(f"Missing required columns: {missing}. Please check your file.")
        st.stop()

    # STUDENT NOTE: Showing a quick preview of the raw data to the user.
    st.subheader("Data Preview")
    st.dataframe(df.head(10))

    # --- INTERACTIVE FILTER ---
    st.subheader("Filter Dashboard")
    
    # STUDENT NOTE: Creating an interactive filter for 'Order Region'. 
    # Adding 'All Regions' as the default option so the user can see the macro view first.
    regions = ["All Regions"] + list(df['Order Region'].unique())
    selected_region = st.selectbox("Select an Order Region to analyze:", regions)

    # STUDENT NOTE: Filtering the DataFrame based on the user's dropdown selection.
    if selected_region != "All Regions":
        df = df[df['Order Region'] == selected_region]

    # --- METRIC COMPUTATION ---
    # STUDENT NOTE: Calculating the delay by subtracting scheduled days from real days.
    df['Delivery_Delay'] = df['Days for shipping (real)'] - df['Days for shipment (scheduled)']

    # STUDENT NOTE: Creating a binary flag (1 = On Time, 0 = Late).
    # If the delay is 0 or less, it arrived on or before the scheduled date.
    df['Is_On_Time'] = df['Delivery_Delay'].apply(lambda x: 1 if x <= 0 else 0)

    # STUDENT NOTE: Calculating the overall on-time rate as a percentage for the KPI card.
    total_orders = len(df)
    on_time_rate = (df['Is_On_Time'].sum() / total_orders) * 100

    # STUDENT NOTE: Calculating the average days late, but only for orders that were actually late (Delay > 0).
    late_orders = df[df['Delivery_Delay'] > 0]
    avg_days_late = late_orders['Delivery_Delay'].mean() if not late_orders.empty else 0

    # --- HEADLINE METRICS ---
    st.subheader("Key Performance Indicators")
    col1, col2, col3 = st.columns(3)
    
    # STUDENT NOTE: Displaying the core computed metrics using st.metric cards.
    col1.metric(label="Overall On-Time Rate", value=f"{on_time_rate:.1f}%")
    col2.metric(label="Total Shipments Analyzed", value=f"{total_orders:,}")
    col3.metric(label="Avg Days Late (for delayed orders)", value=f"{avg_days_late:.1f} days")

    # --- CHARTS ---
    st.subheader("Performance Visualizations")
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        # STUDENT NOTE: Grouping data to calculate the on-time rate per product category.
        category_perf = df.groupby('Category Name')['Is_On_Time'].mean().reset_index()
        category_perf['On-Time Rate (%)'] = category_perf['Is_On_Time'] * 100
        category_perf = category_perf.sort_values('On-Time Rate (%)', ascending=True).head(10) # Show bottom 10 for actionability
        
        # STUDENT NOTE: Creating a bar chart to show the worst performing categories.
        fig1 = px.bar(category_perf, x="On-Time Rate (%)", y="Category Name", orientation='h',
                      title="Bottom 10 Categories by On-Time Rate")
        st.plotly_chart(fig1, use_container_width=True)

    with col_chart2:
        # STUDENT NOTE: Creating a pivot table to build a heatmap of delivery delays.
        # This shows average delay across Regions and Categories.
        heatmap_data = df.groupby(['Order Region', 'Category Name'])['Delivery_Delay'].mean().reset_index()
        
        # STUDENT NOTE: Rendering the heatmap using Plotly Express density heatmap.
        fig2 = px.density_heatmap(heatmap_data, x="Order Region", y="Category Name", z="Delivery_Delay", 
                                  histfunc="avg", title="Average Delay Heatmap (Region vs. Category)",
                                  color_continuous_scale="Reds")
        st.plotly_chart(fig2, use_container_width=True)

    # --- INTERPRETATION ---
    st.subheader("Analyst Interpretation")
    # STUDENT NOTE: Providing a plain-English explanation of the metrics and visuals.
    st.info("""
    **What this tells us:** This dashboard evaluates the reliability of our supply chain. The **On-Time Rate** shows the percentage of shipments that arrive on or before their promised date. 
    
    **How to use this:**
    Look at the 'Bottom 10 Categories' bar chart to see which specific product lines are failing to meet delivery standards. Use the Heatmap to identify 'hot spots' (dark red areas) where specific regions are struggling to deliver specific categories on time. If a route consistently shows an average delay of several days, logistics managers should investigate carrier performance or update expected delivery windows for those specific routes.
    """)
