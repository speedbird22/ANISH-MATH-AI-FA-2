import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Last Mile Delivery Dashboard",
    page_icon="🚚",
    layout="wide"
)

# --- 1. DATA LOADING ---
@st.cache_data
def load_data():
    filename = 'Last mile Delivery Data.csv'
    
    if not os.path.exists(filename):
        st.error(f"Error: The file '{filename}' was not found in the directory. Please upload it.")
        st.stop()
        
    df = pd.read_csv(filename)
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# --- 2. DATA PREPARATION (Cleaning & Metrics) ---

# Cleaning: Ensure numeric columns are actually numeric
df['Delivery_Time'] = pd.to_numeric(df['Delivery_Time'], errors='coerce')
df['Agent_Rating'] = pd.to_numeric(df['Agent_Rating'], errors='coerce')
df['Agent_Age'] = pd.to_numeric(df['Agent_Age'], errors='coerce')

# Handle Missing Values (Drop rows with missing crucial data for visuals)
df_clean = df.dropna(subset=['Delivery_Time', 'Weather', 'Traffic', 'Vehicle', 'Area'])

# Metric Calculation: "Late" Deliveries
# Since 'Promised Time' isn't in the dataset, we define 'Late' as > 120 mins (2 hours)
# You can adjust this threshold or make it dynamic
LATE_THRESHOLD = 120
df_clean['Is_Late'] = df_clean['Delivery_Time'] > LATE_THRESHOLD

# --- SIDEBAR FILTERS ---
st.sidebar.header("Filter Data")

# Filter by Area (Urban, Metropolitan, etc.)
areas = sorted(df_clean['Area'].unique())
selected_area = st.sidebar.multiselect("Select Area", areas, default=areas)

# Filter by Vehicle Type
vehicles = sorted(df_clean['Vehicle'].unique())
selected_vehicle = st.sidebar.multiselect("Select Vehicle", vehicles, default=vehicles)

# Apply Filters
if selected_area:
    df_filtered = df_clean[df_clean['Area'].isin(selected_area)]
else:
    df_filtered = df_clean

if selected_vehicle:
    df_filtered = df_filtered[df_filtered['Vehicle'].isin(selected_vehicle)]

# --- MAIN DASHBOARD ---
st.title("🚚 Last Mile Delivery Performance")
st.markdown("Analyzing delivery times, agent performance, and operational efficiency.")

# --- TOP LEVEL METRICS ---
total_orders = len(df_filtered)
avg_delivery_time = df_filtered['Delivery_Time'].mean()
avg_rating = df_filtered['Agent_Rating'].mean()
late_percentage = (df_filtered['Is_Late'].sum() / total_orders) * 100 if total_orders > 0 else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Orders", total_orders)
col2.metric("Avg. Delivery Time", f"{avg_delivery_time:.1f} min")
col3.metric("Avg. Agent Rating", f"{avg_rating:.1f} / 5.0")
col4.metric("Late Deliveries (>120m)", f"{late_percentage:.1f}%")

st.markdown("---")

# --- VISUALIZATIONS (5 Compulsory Charts for FA-2) ---

col_row1_1, col_row1_2 = st.columns(2)

# Chart 1: Bar Chart - Average Delivery Time by Weather
# (Shows impact of external factors on performance)
with col_row1_1:
    st.subheader("1. Impact of Weather on Speed")
    weather_impact = df_filtered.groupby('Weather')['Delivery_Time'].mean().reset_index()
    fig1 = px.bar(weather_impact, x='Weather', y='Delivery_Time', 
                  color='Delivery_Time', color_continuous_scale='RdYlGn_r', # Red is slower
                  title="Average Delivery Time (min) by Weather Condition")
    st.plotly_chart(fig1, use_container_width=True)

# Chart 2: Pie Chart - Order Composition by Category
# (Shows what type of items are being delivered)
with col_row1_2:
    st.subheader("2. Delivery Volume by Category")
    fig2 = px.pie(df_filtered, names='Category', title="Distribution of Orders by Category",
                  hole=0.4)
    st.plotly_chart(fig2, use_container_width=True)

col_row2_1, col_row2_2 = st.columns(2)

# Chart 3: Histogram - Delivery Time Distribution
# (Shows if delivery times are consistent or skewed)
with col_row2_1:
    st.subheader("3. Delivery Time Distribution")
    fig3 = px.histogram(df_filtered, x="Delivery_Time", nbins=30, 
                        title="Frequency of Delivery Times",
                        color_discrete_sequence=['#3366CC'])
    fig3.add_vline(x=LATE_THRESHOLD, line_dash="dash", line_color="red", annotation_text="Late Threshold")
    st.plotly_chart(fig3, use_container_width=True)

# Chart 4: Scatter Plot - Agent Age vs Rating
# (Investigating if age correlates with performance rating)
with col_row2_2:
    st.subheader("4. Agent Age vs. Rating")
    fig4 = px.scatter(df_filtered, x="Agent_Age", y="Agent_Rating", 
                      color="Vehicle", size="Delivery_Time",
                      title="Does Age impact Rating?",
                      hover_data=['Order_ID'])
    st.plotly_chart(fig4, use_container_width=True)

# Chart 5: Map - Store Locations
# (Visualizing geographic spread using Latitude/Longitude)
st.subheader("5. Geographic Distribution of Stores")
# We need to rename columns to 'lat' and 'lon' for st.map to pick them up automatically
map_data = df_filtered[['Store_Latitude', 'Store_Longitude']].rename(
    columns={'Store_Latitude': 'lat', 'Store_Longitude': 'lon'}
).dropna()

if not map_data.empty:
    st.map(map_data)
else:
    st.warning("No location data available for map.")

# --- RAW DATA VIEW ---
with st.expander("View Raw Data"):
    st.dataframe(df_filtered)
