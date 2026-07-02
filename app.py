import streamlit as st
import joblib
import pandas as pd

# 1. Page Configuration (must be the first Streamlit command)
st.set_page_config(
    page_title="AI Real Estate Valuation",
    page_icon="🏘️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for a more premium look
st.markdown("""
<style>
    /* Main background and text */
    .main {
        background-color: #f8f9fa;
    }
    /* Headers */
    h1, h2, h3 {
        color: #1e3a8a;
        font-family: 'Inter', sans-serif;
    }
    /* Metric container styling */
    div[data-testid="metric-container"] {
        background-color: white;
        border: 1px solid #e2e8f0;
        border-radius: 0.5rem;
        padding: 5% 5% 5% 10%;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }
    /* Segment cards */
    .segment-card {
        padding: 1.5rem;
        border-radius: 0.5rem;
        color: white;
        margin-top: 1rem;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .segment-ultra { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
    .segment-luxury { background: linear-gradient(135deg, #f6d365 0%, #fda085 100%); }
    .segment-mid { background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%); color: #333; }
    .segment-standard { background: linear-gradient(135deg, #e0c3fc 0%, #8ec5fc 100%); color: #333;}
    .segment-economy { background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 99%, #fecfef 100%); color: #333;}
</style>
""", unsafe_allow_html=True)

# 2. Load Model from Cache
@st.cache_resource(show_spinner="Loading valuation models...")
def load_model():
    try:
        model = joblib.load('house_price_model.pkl')
        cols = joblib.load('model_columns.pkl')
        return model, cols
    except Exception as e:
        return None, None

model, model_columns = load_model()

if model is None:
    st.error("⚠️ Valuation models not found! Please ensure 'house_price_model.pkl' and 'model_columns.pkl' are in the project directory.")
    st.stop()

# --- HEADER SECTION ---

col_header1, col_header2 = st.columns([1, 2.5])

with col_header1:
    # A professional, high-quality real estate image
    st.image("https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80", use_container_width=True, caption="Data-Driven Valuation")

with col_header2:
    st.title("AI-Powered Property Valuation")
    st.markdown("""
    **Empowering Real Estate Agents & Buyers with Instant Market Insights.**
    
    This tool utilizes advanced machine learning (XGBoost) to deliver **instant, highly accurate property value estimates** based on key housing features. 
    Adjust the property parameters in the sidebar to see how different characteristics influence the market value in real-time.
    """)

st.divider()

# --- SIDEBAR (INPUT PARAMETERS) ---
st.sidebar.header("⚙️ Property Parameters")
st.sidebar.markdown("Adjust the features below to update the valuation.")

input_total_sf = st.sidebar.slider("Total Area (sq ft)", min_value=500, max_value=5000, value=1500, step=50, help="Total livable area of the property.")
input_quality = st.sidebar.select_slider("Material & Finish Quality", options=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10], value=6, help="Overall material and finish quality of the house (1=Poor, 10=Excellent).")
input_year = st.sidebar.number_input("Year Built", min_value=1900, max_value=2024, value=2010, step=1)

col_sb1, col_sb2 = st.sidebar.columns(2)
with col_sb1:
    input_garage = st.selectbox("Garage Cars", [0, 1, 2, 3, 4], index=2)
with col_sb2:
    input_fireplaces = st.selectbox("Fireplaces", [0, 1, 2, 3], index=1)

input_bath = st.sidebar.radio("Full Bathrooms", [1, 2, 3, 4], index=1, horizontal=True)

# --- PREDICTION LOGIC ---

# Derive logical missing features to prevent model performance drop
garage_area_estimate = input_garage * 250
bsmt_estimate = input_total_sf * 0.4 
first_floor_estimate = input_total_sf * 0.6

user_input = pd.DataFrame({
    "TotalSF": [input_total_sf],
    "OverallQual": [input_quality],
    "YearBuilt": [input_year],
    "GarageCars": [input_garage],
    "FullBath": [input_bath],
    "Fireplaces": [input_fireplaces],
    
    # Derived values to support the model's structure
    "GrLivArea": [input_total_sf],
    "GarageArea": [garage_area_estimate],
    "TotalBsmtSF": [bsmt_estimate],
    "1stFlrSF": [first_floor_estimate]
})

# Reindex to match the 259 columns the model expects
user_input = user_input.reindex(columns=model_columns, fill_value=0)

# Generate prediction
prediction = model.predict(user_input)[0]

# --- DASHBOARD & RESULTS ---

# Average price in the dataset as a baseline reference (~$180,921)
avg_price = 180921 
diff = prediction - avg_price

col_res1, col_res2 = st.columns([1, 1.2])

with col_res1:
    st.subheader("Estimated Market Value")
    st.markdown("Based on current market trends and the specified features:")
    
    st.metric(
        label="Current Valuation",
        value=f"${int(prediction):,}",
        delta=f"{int(diff):,} vs Regional Average",
        delta_color="normal"
    )

with col_res2:
    st.subheader("Market Positioning")
    
    # Cap the progress bar between 0.0 and 1.0 for visual purposes
    progress_val = float(max(0.0, min(prediction / 800000, 1.0))) 
    st.progress(progress_val)
    
    # Advanced Segmentation for Business Use Cases
    if prediction > 450000:
        st.markdown('<div class="segment-card segment-ultra"><h3>💎 Ultra Luxury Segment</h3><p>Top 1% tier. High-end clientele and exclusive listing strategy recommended.</p></div>', unsafe_allow_html=True)
    elif prediction > 300000:
        st.markdown('<div class="segment-card segment-luxury"><h3>🏆 Luxury Segment</h3><p>Premium property. Focus marketing on high living standards and premium features.</p></div>', unsafe_allow_html=True)
    elif prediction > 200000:
        st.markdown('<div class="segment-card segment-mid"><h3>🏡 Upper-Mid Market</h3><p>Highly sought-after family home. Excellent for broad market appeal.</p></div>', unsafe_allow_html=True)
    elif prediction > 120000:
        st.markdown('<div class="segment-card segment-standard"><h3>✅ Standard Market</h3><p>Matches regional averages. Fast liquidity and ideal for first-time buyers.</p></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="segment-card segment-economy"><h3>📉 Value / Investment</h3><p>Budget-friendly tier. Strong potential for flippers and ROI-focused investors.</p></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

with st.expander("🛠️ View Underlying Model Payload"):
    st.markdown("This is the transformed data array being passed to the XGBoost model in the backend:")
    st.dataframe(user_input, use_container_width=True)