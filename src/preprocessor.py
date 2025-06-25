import pandas as pd
from pathlib import Path
import ast 
from config.data_config import COLUMNS_TO_DROP_PREPROCESSOR
from features import extract_amenity_flags

class DataPreprocessor:
    def __init__(self, input_path: Path, output_path: Path, amenities_path: Path):
        """
        Initialize the DataPreprocessor with file paths.
        
        Args:
            input_path (Path): Path to the input CSV file
            output_path (Path): Path to save the filtered data
            amenities_path (Path): Path to save the unique amenities
        """
        self.input_path = input_path
        self.output_path = output_path
        self.amenities_path = amenities_path
        self.chunksize = 100_000
        
        # Create output directory if it doesn't exist
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Columns to drop
        self.columns_to_drop = COLUMNS_TO_DROP_PREPROCESSOR

    def filter_data(self) -> pd.DataFrame:
        """
        Filter the data by removing rows with missing or zero revenue and dropping specified columns.
        
        Returns:
            pd.DataFrame: Filtered dataframe
        """
        filtered_chunks = []
        
        for chunk in pd.read_csv(self.input_path, chunksize=self.chunksize):
            # Filter out rows where 'estimated_revenue_l365d' is missing, empty, or zero
            filtered_chunk = chunk[chunk['estimated_revenue_l365d'].notna() & 
                                (chunk['estimated_revenue_l365d'] != '') & 
                                (chunk['estimated_revenue_l365d'] > 0)]
            
            # Drop specified columns
            filtered_chunk = filtered_chunk.drop(columns=self.columns_to_drop)

            # for bathrooms, bedrooms, beds columnn if there is no number, replace with 0
            filtered_chunk['bathrooms'] = filtered_chunk['bathrooms'].fillna(0)
            filtered_chunk['bedrooms'] = filtered_chunk['bedrooms'].fillna(0)
            filtered_chunk['beds'] = filtered_chunk['beds'].fillna(0)

            # extract amenitites
            # Apply the feature extraction to each row
            amenity_flags_df = filtered_chunk['amenities'].apply(extract_amenity_flags).apply(pd.Series)

            # Concatenate the new columns to the original DataFrame and optionally drop the old 'amenities' column
            filtered_chunk = pd.concat([filtered_chunk, amenity_flags_df], axis=1)
            filtered_chunk = filtered_chunk.drop(columns=['amenities'])

            filtered_chunks.append(filtered_chunk)
        
        filtered_df = pd.concat(filtered_chunks)
        # One-hot encode
        categorical_cols = ['property_type', 'room_type', "bathrooms_text"]
        filtered_df = pd.get_dummies(filtered_df, columns=categorical_cols)

        return filtered_df

    def extract_amenities(self) -> pd.DataFrame:
        """
        Extract unique amenities from the data.

        The amenities file is not directly used by the model.
        It's used to better understand the data during development.
        
        Returns:
            pd.DataFrame: DataFrame containing unique amenities
        """
        all_amenities = set()
        
        for chunk in pd.read_csv(self.input_path, chunksize=self.chunksize):
            for amenities_str in chunk['amenities']:
                try:
                    # Convert string representation of list to actual list
                    amenities_list = ast.literal_eval(amenities_str)
                    # Clean each amenity string and add to set
                    cleaned_amenities = [amenity.strip('"') for amenity in amenities_list]
                    all_amenities.update(cleaned_amenities)
                except (ValueError, SyntaxError):
                    continue
        
        return pd.DataFrame(sorted(all_amenities), columns=['amenity'])

    def process(self) -> None:
        """
        Process the data and save the results.
        """
        print("\nProcessing data...")
        filtered_df = self.filter_data()
        filtered_df.to_csv(self.output_path, index=False)
        
        print("\nExtracting unique amenities...")
        amenities_df = self.extract_amenities()
        amenities_df.to_csv(self.amenities_path, index=False, quoting=1)
        
        # Print statistics
        total_entries = sum(len(chunk) for chunk in pd.read_csv(self.input_path, chunksize=self.chunksize))
        print(f"\nInput file: {self.input_path}")
        print(f"Output file: {self.output_path}")
        print(f"Amenities file: {self.amenities_path}")
        print(f"Total unique amenities found: {len(amenities_df)}")
        print(f"Total entries processed: {total_entries}")
        print(f"Entries kept: {len(filtered_df)}")
        print(f"Percentage kept: {(len(filtered_df) / total_entries * 100):.2f}%")

if __name__ == "__main__":
    # Get project root directory
    PROJECT_ROOT = Path(__file__).parent.parent
    
    # Get all subfolders in raw_data
    raw_data_path = PROJECT_ROOT / 'raw_data'
    subfolders = [f for f in raw_data_path.iterdir() if f.is_dir() and not f.name.startswith('.')]
    
    print(f"Found {len(subfolders)} subfolders to process:")
    for folder in subfolders:
        print(f"  - {folder.name}")
    
    for subfolder in subfolders:
        print(f"\n{'='*60}")
        print(f"Processing: {subfolder.name}")
        print(f"{'='*60}")
        
        
        input_path = subfolder / 'listings_detailed.csv'
        output_path = PROJECT_ROOT / 'cleaned_data' / subfolder.name / 'listings_detailed_filtered.csv'
        amenities_path = PROJECT_ROOT / 'cleaned_data' / subfolder.name / 'unique_amenities.csv'
        
        # Check if input file exists
        if not input_path.exists():
            print(f"Input file not found: {input_path}")
            print(f"Skipping {subfolder.name}")
            continue
        
        try:
            # Create preprocessor and process data
            preprocessor = DataPreprocessor(input_path, output_path, amenities_path)
            preprocessor.process()
            print(f"Successfully processed {subfolder.name}")
        except Exception as e:
            print(f"Error processing {subfolder.name}: {e}")
            continue
    
    print(f"\n{'='*60}")
    print("Processing complete!")
    print(f"{'='*60}")


