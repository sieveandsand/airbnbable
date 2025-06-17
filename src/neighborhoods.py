import geopandas as gpd
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from typing import Optional, Tuple
import time
import os

class NeighborhoodFinder:
    def __init__(self, geojson_path: str, force_reload: bool = False):
        """
        Initialize the NeighborhoodFinder with neighborhood boundaries.
        Will use cached Parquet file if available, otherwise convert from GeoJSON.
        
        Args:
            geojson_path (str): Path to the GeoJSON file containing neighborhood boundaries
            force_reload (bool): If True, force reload from GeoJSON even if Parquet exists
        """
        # Create Parquet path by replacing .geojson with .parquet
        parquet_path = geojson_path.replace('.geojson', '.parquet')
        
        # Load from Parquet if it exists and we're not forcing a reload
        if os.path.exists(parquet_path) and not force_reload:
            self.gdf = gpd.read_parquet(parquet_path)
        else:
            # Load from GeoJSON and save as Parquet
            self.gdf = gpd.read_file(geojson_path)
            if self.gdf.crs is None:
                self.gdf.set_crs(epsg=4326, inplace=True)
            # Save as Parquet for future use
            self.gdf.to_parquet(parquet_path)
            
        self.geocoder = Nominatim(user_agent="neighborhood_finder")
        
    def _geocode_address(self, address: str) -> Optional[Tuple[float, float]]:
        """
        Convert an address to (latitude, longitude) coordinates.
        
        Args:
            address (str): The address to geocode
            
        Returns:
            Optional[Tuple[float, float]]: (latitude, longitude) tuple if successful, None if failed
        """
        try:
            # Add a small delay to respect geocoding service rate limits
            time.sleep(1)
            location = self.geocoder.geocode(address)
            if location:
                return (location.latitude, location.longitude)
            return None
        except GeocoderTimedOut:
            return None
            
    def get_neighborhood(self, address: str) -> Optional[str]:
        """
        Find the neighborhood for a given address.
        
        Args:
            address (str): The address to look up
            
        Returns:
            Optional[str]: The name of the neighborhood if found, None if not found
        """
        coords = self._geocode_address(address)
        if not coords:
            return None
            
        # Create a GeoDataFrame with the point
        point_gdf = gpd.GeoDataFrame(
            geometry=[gpd.points_from_xy([coords[1]], [coords[0]])[0]],
            crs="EPSG:4326"
        )
        
        # Perform spatial join
        joined = gpd.sjoin(
            point_gdf,
            self.gdf,
            how="left",
            predicate="within"
        )
        
        # If we found a match, return the neighborhood name
        if not joined.empty and 'neighbourhood' in joined.columns:
            return joined.iloc[0]['neighbourhood']
            
        return None

def test_address(finder: NeighborhoodFinder, address: str, expected_neighborhood: str = None) -> None:
    """
    Test the neighborhood finder with a given address.
    
    Args:
        finder: NeighborhoodFinder instance
        address: Address to test
        expected_neighborhood: Expected neighborhood name (optional)
    """
    print(f"\nTesting address: {address}")
    neighborhood = finder.get_neighborhood(address)
    if neighborhood:
        print(f"Found neighborhood: {neighborhood}")
        if expected_neighborhood:
            if neighborhood.lower() == expected_neighborhood.lower():
                print("✓ Test passed: Found expected neighborhood")
            else:
                print(f"✗ Test failed: Expected {expected_neighborhood}, got {neighborhood}")
    else:
        print("Could not determine the neighborhood")
        if expected_neighborhood:
            print("✗ Test failed: Expected to find a neighborhood")

# Example usage
if __name__ == "__main__":
    finder = NeighborhoodFinder("../data/san_francisco/neighborhoods.geojson")
    
    # Test cases with known locations
    test_cases = [
        # Downtown/Financial District
        ("1 Ferry Building, San Francisco, CA 94111", "Financial District"),
        ("555 California Street, San Francisco, CA 94104", "Financial District"),
        
        # North Beach
        ("Columbus Avenue & Broadway, San Francisco, CA 94133", "North Beach"),
        ("Washington Square Park, San Francisco, CA 94133", "North Beach"),
        
        # Mission District
        ("Mission Dolores Park, San Francisco, CA 94114", "Mission"),
        ("Valencia Street & 16th Street, San Francisco, CA 94103", "Mission"),
        
        # Golden Gate Park
        ("Golden Gate Park, San Francisco, CA 94122", "Golden Gate Park"),
        ("California Academy of Sciences, San Francisco, CA 94118", "Golden Gate Park"),
        
        # Marina
        ("Palace of Fine Arts, San Francisco, CA 94123", "Marina"),
        ("Chestnut Street & Fillmore Street, San Francisco, CA 94123", "Marina"),
        
        # Edge cases
        ("San Francisco International Airport, San Francisco, CA 94128", None),  # Outside city limits
        ("Invalid Address, San Francisco, CA", None),  # Invalid address
    ]
    
    for address, expected in test_cases:
        test_address(finder, address, expected) 