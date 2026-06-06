import os
import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster, HeatMap

# Database configuration with Docker path fallback
DB_PATH = "/app/database/radar.db"
if not os.path.exists(DB_PATH):
    # Local fallback
    DB_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "radar.db")
    DB_PATH = os.path.abspath(DB_PATH)

st.set_page_config(
    page_title="Monster Radar & Portfolio Telemetry",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Enterprise Dark Styling
st.markdown("""
<style>
    /* Global Styles */
    .stApp {
        background-color: #0b0c10;
        color: #c5c6c7;
    }
    
    /* Title and Headers */
    h1, h2, h3, h4, h5, h6 {
        color: #66fcf1 !important;
        font-family: 'Inter', sans-serif;
    }
    
    /* Metrics and Card backgrounds */
    div[data-testid="stMetricValue"] {
        color: #66fcf1 !important;
        font-size: 28px;
    }
    
    div[data-testid="metric-container"] {
        background-color: #1f2833;
        border: 1px solid #45f3ff;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #1f2833 !important;
        border-right: 2px solid #45f3ff;
    }
    
    section[data-testid="stSidebar"] .stMarkdown {
        color: #c5c6c7;
    }
    
    /* Tabs styling */
    button[data-baseweb="tab"] {
        color: #c5c6c7 !important;
        font-size: 16px !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #66fcf1 !important;
        border-bottom-color: #66fcf1 !important;
        font-weight: bold !important;
    }
</style>
""", unsafe_allow_html=True)

# Data Loading Functions
@st.cache_data(ttl=60)
def load_price_data():
    if not os.path.exists(DB_PATH):
        return pd.DataFrame()
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT timestamp, store, brand, itemName, price FROM price_history", conn)
        conn.close()
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    except Exception as e:
        st.error(f"Error loading price history: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_visitor_data():
    if not os.path.exists(DB_PATH):
        return pd.DataFrame()
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT event, ip, city, country, latitude, longitude, org, timestamp FROM visitor_logs", conn)
        conn.close()
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    except Exception as e:
        st.error(f"Error loading visitor logs: {e}")
        return pd.DataFrame()

# Title
st.title("📡 Enterprise Geo-Radar & Portfolio Analytics")
st.markdown("Real-time monitoring suite for supermarket retail scraping and website visitor telemetry.")

# Sidebar Filters
st.sidebar.header("🎯 Filter Configuration")

# Load data
price_df = load_price_data()
visitor_df = load_visitor_data()

# Check database connection state
if price_df.empty and visitor_df.empty:
    st.warning(f"Database at `{DB_PATH}` is empty or not found. Please execute the mock generator first.")
else:
    # Sidebar: Price Filters
    if not price_df.empty:
        st.sidebar.subheader("🥤 Retail Prices")
        all_stores = sorted(price_df['store'].unique())
        selected_stores = st.sidebar.multiselect("Select Supermarkets", all_stores, default=all_stores)
        
        all_brands = sorted(price_df['brand'].unique())
        selected_brands = st.sidebar.multiselect("Select Brands", all_brands, default=all_brands)
    else:
        selected_stores = []
        selected_brands = []

    # Sidebar: Map Filter
    if not visitor_df.empty:
        st.sidebar.subheader("📡 Spatial Logs")
        all_events = sorted(visitor_df['event'].unique())
        selected_events = st.sidebar.multiselect("Filter Visitor Events", all_events, default=all_events)
    else:
        selected_events = []

    # Tabs
    tab1, tab2 = st.tabs(["📊 Retail Analytics", "🌍 Spatial Telemetry"])

    # Tab 1: Retail Price Analytics
    with tab1:
        st.subheader("🥤 Supermarket Price Tracking")
        if price_df.empty:
            st.info("No retail price tracking data available.")
        else:
            # Filtering
            filtered_price = price_df[
                (price_df['store'].isin(selected_stores)) & 
                (price_df['brand'].isin(selected_brands))
            ]
            
            if filtered_price.empty:
                st.info("No records match the selected sidebar filters.")
            else:
                # Key Metrics Row
                m1, m2, m3 = st.columns(3)
                with m1:
                    st.metric("Total Tracked Products", f"{len(filtered_price['itemName'].unique())}")
                with m2:
                    st.metric("Lowest Promo Price Found", f"€{filtered_price['price'].min():.2f}")
                with m3:
                    st.metric("Average Registered Price", f"€{filtered_price['price'].mean():.2f}")
                
                st.write("")
                
                # Plotly express timeline
                st.subheader("📈 Energy Drink Price History")
                fig = px.line(
                    filtered_price,
                    x="timestamp",
                    y="price",
                    color="itemName",
                    line_group="store",
                    hover_data=["store", "brand"],
                    labels={"price": "Price (€)", "timestamp": "Date", "itemName": "Product Name"},
                    template="plotly_dark"
                )
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font_color='#c5c6c7',
                    xaxis=dict(showgrid=True, gridcolor='#1f2833'),
                    yaxis=dict(showgrid=True, gridcolor='#1f2833'),
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Price Table breakdown
                st.subheader("📋 Price Breakdown by Product")
                summary_df = filtered_price.groupby(['store', 'brand', 'itemName']).agg(
                    Min_Price=('price', 'min'),
                    Avg_Price=('price', 'mean'),
                    Max_Price=('price', 'max')
                ).reset_index()
                # Format floats for cleaner look
                summary_df['Min_Price'] = summary_df['Min_Price'].map('€{:.2f}'.format)
                summary_df['Avg_Price'] = summary_df['Avg_Price'].map('€{:.2f}'.format)
                summary_df['Max_Price'] = summary_df['Max_Price'].map('€{:.2f}'.format)
                st.dataframe(summary_df, use_container_width=True)

    # Tab 2: Spatial Telemetry
    with tab2:
        st.subheader("🌍 Website Traffic Geolocation Map")
        if visitor_df.empty:
            st.info("No visitor telemetry logs available.")
        else:
            # Filtering
            filtered_visitor = visitor_df[visitor_df['event'].isin(selected_events)]
            
            if filtered_visitor.empty:
                st.info("No spatial records match the selected event filters.")
            else:
                # Key Metrics Row
                mv1, mv2, mv3 = st.columns(3)
                with mv1:
                    st.metric("Total Telemetry Logs", f"{len(filtered_visitor)}")
                with mv2:
                    st.metric("Unique Visitors (IPs)", f"{len(filtered_visitor['ip'].unique())}")
                with mv3:
                    st.metric("Represented ISP Entities", f"{len(filtered_visitor['org'].unique())}")
                
                st.write("")
                
                # Render Map using Folium
                st.subheader("📍 Interactive Density & Clustering Map")
                st.markdown("Center point: Bratislava, Slovakia. Clustered markers show exact events, and HeatMap shows traffic density.")
                
                # Initialize map centered on Bratislava
                m = folium.Map(location=[48.1486, 17.1077], zoom_start=11, tiles="Cartodb dark_matter")
                
                # Add HeatMap layer
                heat_data = [[row['latitude'], row['longitude']] for index, row in filtered_visitor.iterrows() if not pd.isna(row['latitude']) and not pd.isna(row['longitude'])]
                if heat_data:
                    HeatMap(heat_data, radius=15, blur=10, min_opacity=0.4).add_to(m)
                
                # Add Clustered Markers
                marker_cluster = MarkerCluster().add_to(m)
                for idx, row in filtered_visitor.iterrows():
                    if pd.isna(row['latitude']) or pd.isna(row['longitude']):
                        continue
                    
                    # HTML styled popup
                    popup_content = f"""
                    <div style="font-family: Arial, sans-serif; font-size: 12px; color: #333;">
                        <strong>Event:</strong> <span style="color:#e67e22;">{row['event']}</span><br>
                        <strong>City:</strong> {row['city']}<br>
                        <strong>IP:</strong> {row['ip']}<br>
                        <strong>ISP:</strong> {row['org']}<br>
                        <strong>Time:</strong> {row['timestamp'].strftime('%Y-%m-%d %H:%M')}<br>
                    </div>
                    """
                    
                    folium.Marker(
                        location=[row['latitude'], row['longitude']],
                        popup=folium.Popup(popup_content, max_width=250),
                        tooltip=f"{row['org']} ({row['city']})",
                        icon=folium.Icon(color="orange" if row['event'] == 'cv_download' else "blue", icon="info-sign")
                    ).add_to(marker_cluster)
                
                # Render map to streamlit page
                st_folium(m, width="100%", height=600, returned_objects=[])
                
                # Telemetry Records Grid
                st.subheader("📋 Raw Visitor Logs")
                st.dataframe(
                    filtered_visitor[['timestamp', 'event', 'ip', 'city', 'org']].sort_values(by='timestamp', ascending=False),
                    use_container_width=True
                )
