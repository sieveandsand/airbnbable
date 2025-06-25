# Feifan Qiao

import streamlit as st
import pandas as pd
from pathlib import Path
from src.model import ListingModeler
import plotly.express as px
import plotly.graph_objects as go
from geocoder import validate_and_geocode_address
from data_types import property_type_values, room_type_values, bathroom_type_values

# Page configuration
st.set_page_config(
    page_title="Airbnb Revenue Predictor",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .prediction-result {
        background-color: #e8f5e8;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 2px solid #28a745;
    }
    .address-input {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #dee2e6;
        margin-bottom: 1rem;
    }
    .address-input p {
        color: #495057;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    .address-input ul {
        color: #6c757d;
        margin: 0;
        padding-left: 1.2rem;
    }
    .address-input li {
        margin-bottom: 0.25rem;
    }
</style>
""", unsafe_allow_html=True)

# Map county display names to folder names (as used in cached_models)
COUNTY_TO_FOLDER = {
    "San Francisco County, CA, USA": "san_francisco",
    "San Mateo County, CA, USA": "san_mateo_county",
    "Santa Clara County, CA, USA": "santa_clara_county",
}

@st.cache_resource
def load_county_model(county_folder):
    """Load the ListingModeler and XGBoost model for a given county folder."""
    PROJECT_ROOT = Path(__file__).parent.parent
    model_path = PROJECT_ROOT / 'cached_models' / county_folder / f'{county_folder}_model.joblib'
    data_path = PROJECT_ROOT / 'cleaned_data' / county_folder / 'listings_detailed_filtered.csv'
    if not model_path.exists() or not data_path.exists():
        return None, f"Model or data not found for {county_folder}"
    modeler = ListingModeler(data_path)
    modeler.load_xgboost_model(str(model_path))
    return modeler, f"Model loaded for {county_folder.replace('_', ' ').title()}"

def create_feature_dict(lat, lon, accommodates, bedrooms, beds, bathrooms, property_type, room_type, bathroom_type, amenities):
    """Create feature dictionary for prediction"""
    feature_dict = {
        'latitude': lat,
        'longitude': lon,
        'accommodates': accommodates,
        'bedrooms': bedrooms,
        'beds': beds,
        'bathrooms': bathrooms,
        'estimated_occupancy_l365d': 0.7,  # Default occupancy rate
    }
    
    # Add amenities
    for amenity in amenities:
        feature_dict[amenity] = 1
    
    # Add one-hot encoded property type
    property_type_col = f'property_type_{property_type}'
    feature_dict[property_type_col] = 1
    
    # Add one-hot encoded room type
    room_type_col = f'room_type_{room_type}'
    feature_dict[room_type_col] = 1
    
    # Add one-hot encoded bathroom type
    bathroom_type_col = f'bathrooms_text_{bathrooms} {bathroom_type}'
    feature_dict[bathroom_type_col] = 1
    
    return feature_dict

def main():
    # Header
    st.markdown('<h1 class="main-header">🏠 Airbnb Revenue Predictor</h1>', unsafe_allow_html=True)
    
    # Sidebar for inputs
    with st.sidebar:
        # Address input section
        st.header("📍 Property Address")
        st.markdown("""
        <div class="address-input">
            <p><strong>📍 Supported Areas:</strong></p>
            <ul>
                <li>San Francisco County</li>
                <li>San Mateo County</li>
                <li>Santa Clara County</li>
            </ul>
            <p style="font-size: 0.9em; color: #6c757d; margin-top: 0.5rem; margin-bottom: 0;">
                <em>Enter any address within these counties to get started</em>
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        address = st.text_input(
            "Enter property address",
            placeholder="e.g., 123 Main St, San Francisco, CA",
            help="Enter the full address of the property"
        )
        
        # Geocode button
        geocode_button = st.button("🔍 Find Location", use_container_width=True)
        
        # Initialize session state for coordinates
        if 'coordinates' not in st.session_state:
            st.session_state.coordinates = None
        if 'address_status' not in st.session_state:
            st.session_state.address_status = ""
        if 'county_folder' not in st.session_state:
            st.session_state.county_folder = None
        
        # Handle geocoding
        if geocode_button and address:
            with st.spinner("🔍 Finding location..."):
                success, coords, message = validate_and_geocode_address(address)
                st.session_state.coordinates = coords if success else None
                st.session_state.address_status = message
                
                if success:
                    st.success(message)
                    st.info(f"📍 {coords['formatted_address']}")
                    # Determine county folder
                    county_folder = COUNTY_TO_FOLDER.get(coords['county'])
                    st.session_state.county_folder = county_folder
                else:
                    st.error(message)
                    st.session_state.county_folder = None
        
        # Property details
        st.markdown("---")
        st.header("🏡 Property Details")
        
        # Basic property details
        accommodates = st.selectbox("Accommodates", range(1, 17), index=1, help="Number of guests the property can accommodate")
        bedrooms = st.selectbox("Bedrooms", range(0, 11), index=1, help="Number of bedrooms")
        beds = st.selectbox("Beds", range(1, 17), index=1, help="Number of beds")
        bathrooms = st.selectbox("Bathrooms", range(1, 11), index=1, help="Number of bathrooms")
        
        # Property type
        property_type = st.selectbox(
            "Property Type",
            options=property_type_values,
            index=property_type_values.index("Entire home") if "Entire home" in property_type_values else 0,
            help="Type of property"
        )
        
        # Room type
        room_type = st.selectbox(
            "Room Type",
            options=room_type_values,
            index=room_type_values.index("Entire home/apt") if "Entire home/apt" in room_type_values else 0,
            help="Type of room"
        )
        
        # Bathroom type
        bathroom_type = st.selectbox(
            "Bathroom Type",
            options=bathroom_type_values,
            index=bathroom_type_values.index("bath") if "bath" in bathroom_type_values else 0,
            help="Type of bathroom"
        )
        
        # Amenities
        st.header("✨ Amenities")
        amenities = st.multiselect(
            "Select amenities",
            options=[
                "has_tv", "has_wifi", "has_kitchen_appliances", "has_air_conditioning",
                "has_washer", "has_dryer", "has_toiletries", "has_coffee",
                "has_breakfast", "has_free_parking", "has_pool", "has_gym"
            ],
            default=["has_wifi", "has_tv"],
            format_func=lambda x: x.replace("_", " ").title()
        )
        
        # Predict button
        predict_button = st.button("🚀 Predict Revenue", type="primary", use_container_width=True, disabled=not (st.session_state.coordinates and st.session_state.county_folder))
        
        if not st.session_state.coordinates:
            st.warning("⚠️ Please enter and validate an address first")
        elif not st.session_state.county_folder:
            st.warning("⚠️ This address is not in a supported county")
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📈 Revenue Prediction")
        
        if predict_button and st.session_state.coordinates and st.session_state.county_folder:
            with st.spinner(f"Loading model for {st.session_state.county_folder.replace('_', ' ').title()}..."):
                modeler, status = load_county_model(st.session_state.county_folder)
            if modeler and hasattr(modeler, 'xgb_model') and hasattr(modeler, 'xgb_features'):
                try:
                    lat = st.session_state.coordinates['latitude']
                    lon = st.session_state.coordinates['longitude']
                    feature_dict = create_feature_dict(
                        lat, lon, accommodates, bedrooms, beds, bathrooms,
                        property_type, room_type, bathroom_type, amenities
                    )
                    prediction = modeler.predict_xgboost(feature_dict)
                    st.markdown('<div class="prediction-result">', unsafe_allow_html=True)
                    col1_metric, col2_metric, col3_metric = st.columns(3)
                    with col1_metric:
                        st.metric("Annual Revenue", f"${prediction:,.0f}")
                    with col2_metric:
                        st.metric("Monthly Average", f"${prediction/12:,.0f}")
                    with col3_metric:
                        st.metric("Daily Average", f"${prediction/365:,.0f}")
                    st.markdown('</div>', unsafe_allow_html=True)
                    st.subheader("📋 Property Summary")
                    summary_data = {
                        "Property": [
                            "Address", "County", "Property Type", "Room Type",
                            "Accommodates", "Bedrooms", "Beds", "Bathrooms", "Bathroom Type", "Amenities"
                        ],
                        "Value": [
                            st.session_state.coordinates['formatted_address'],
                            st.session_state.coordinates['county'],
                            property_type,
                            room_type,
                            str(accommodates),
                            str(bedrooms),
                            str(beds),
                            str(bathrooms),
                            bathroom_type,
                            ", ".join([a.replace("_", " ").title() for a in amenities]) if amenities else "None"
                        ]
                    }
                    st.table(pd.DataFrame(summary_data))
                except Exception as e:
                    st.error(f"❌ Prediction failed: {str(e)}")
            else:
                st.error(f"❌ Model or feature list not available for this county. {status}")
        elif not st.session_state.coordinates:
            st.info("👈 Enter a property address in the sidebar and click 'Find Location' to get started.")
        elif not st.session_state.county_folder:
            st.info("👈 This address is not in a supported county.")
        else:
            st.info("👈 Use the sidebar to enter property details and click 'Predict Revenue' to get started.")
    
    with col2:
        st.header("🗺️ Location Map")
        
        # Get coordinates for map display
        if st.session_state.coordinates:
            lat = st.session_state.coordinates['latitude']
            lon = st.session_state.coordinates['longitude']
        else:
            lat, lon = 37.7749, -122.4194  # Default to San Francisco
        
        # Create a simple map
        map_data = pd.DataFrame({
            'lat': [lat],
            'lon': [lon]
        })
        
        st.map(map_data)
        
        # Location info
        st.markdown("**📍 Current Location:**")
        if st.session_state.coordinates:
            st.write(f"**Address:** {st.session_state.coordinates['formatted_address']}")
            st.write(f"**County:** {st.session_state.coordinates['county']}")
        else:
            st.write("**Address:** Enter an address to see location details")
        st.write(f"**Latitude:** {lat:.6f}")
        st.write(f"**Longitude:** {lon:.6f}")

if __name__ == "__main__":
    main() 