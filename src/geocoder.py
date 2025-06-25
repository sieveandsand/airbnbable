import streamlit as st
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
import time
from typing import Optional, Tuple, Dict

class AddressGeocoder:
    def __init__(self):
        self.geolocator = Nominatim(user_agent="airbnb_revenue_predictor")
        
        # Define the supported counties and their boundaries
        # coordinates comes from geojson file provided in the dataset from inside airbnb
        self.supported_counties = {
            "San Francisco": {
                "name": "San Francisco County, CA, USA",
                "bounds": {
                    "lat_min": 37.7073, "lat_max": 37.8100,
                    "lon_min": -122.5173, "lon_max": -122.3562
                }
            },
            "San Mateo": {
                "name": "San Mateo County, CA, USA", 
                "bounds": {
                    "lat_min": 37.1052, "lat_max": 37.7073,
                    "lon_min": -122.5173, "lon_max": -122.0817
                }
            },
            "Santa Clara": {
                "name": "Santa Clara County, CA, USA",
                "bounds": {
                    "lat_min": 36.8925, "lat_max": 37.4688,
                    "lon_min": -122.0817, "lon_max": -121.2083
                }
            }
        }
    
    def geocode_address(self, address: str) -> Optional[Dict]:
        """
        Geocode an address and check if it's within supported counties.
        
        Args:
            address (str): The address to geocode
            
        Returns:
            Optional[Dict]: Dictionary with lat, lon, and county info, or None if not supported
        """
        try:
            # rate limit so that we don't spam the service
            time.sleep(1)
            
            # Geocode the address
            location = self.geolocator.geocode(address)
            
            if not location:
                return None
            
            lat, lon = location.latitude, location.longitude
            
            # Check if the coordinates are within any supported county
            county_info = self._check_county_bounds(lat, lon)
            
            if county_info:
                return {
                    "latitude": lat,
                    "longitude": lon,
                    "county": county_info["name"],
                    "formatted_address": location.address
                }
            else:
                return None
                
        except (GeocoderTimedOut, GeocoderUnavailable) as e:
            st.error(f"Geocoding service error: {e}")
            return None
        except Exception as e:
            st.error(f"Unexpected error during geocoding: {e}")
            return None
    
    def _check_county_bounds(self, lat: float, lon: float) -> Optional[Dict]:
        """
        Check if coordinates are within any supported county bounds.
        
        Args:
            lat (float): Latitude
            lon (float): Longitude
            
        Returns:
            Optional[Dict]: County info if within bounds, None otherwise
        """
        for county_name, county_data in self.supported_counties.items():
            bounds = county_data["bounds"]
            
            if (bounds["lat_min"] <= lat <= bounds["lat_max"] and 
                bounds["lon_min"] <= lon <= bounds["lon_max"]):
                return county_data
        
        return None
    
    def get_supported_areas(self) -> str:
        """Get a formatted string of supported areas for display."""
        areas = list(self.supported_counties.keys())
        if len(areas) == 1:
            return areas[0]
        elif len(areas) == 2:
            return f"{areas[0]} and {areas[1]}"
        else:
            return f"{', '.join(areas[:-1])}, and {areas[-1]}"

def validate_and_geocode_address(address: str) -> Tuple[bool, Optional[Dict], str]:
    """
    Validate an address and convert it to coordinates.
    
    Args:
        address (str): The address to validate and geocode
        
    Returns:
        Tuple[bool, Optional[Dict], str]: (success, coordinates_dict, message)
    """
    if not address or not address.strip():
        return False, None, "Please enter a valid address."
    
    geocoder = AddressGeocoder()
    result = geocoder.geocode_address(address.strip())
    
    if result:
        return True, result, f"✅ Address found in {result['county']}"
    else:
        supported_areas = geocoder.get_supported_areas()
        return False, None, f"❌ Address not found or not in supported areas ({supported_areas})" 