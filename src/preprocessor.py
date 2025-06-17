import pandas as pd
from pathlib import Path
import ast  # For safely evaluating string representation of lists

# Get project root directory (one level up from the script location)
PROJECT_ROOT = Path(__file__).parent.parent

# Input and output file paths relative to project root
INPUT_PATH = PROJECT_ROOT / 'raw_data' / 'san_francisco' / 'listings_detailed.csv'
OUTPUT_PATH = PROJECT_ROOT / 'cleaned_data' / 'san_francisco' / 'listings_detailed_filtered.csv'
AMENITIES_PATH = PROJECT_ROOT / 'cleaned_data' / 'san_francisco' / 'unique_amenities.csv'

# Create output directory if it doesn't exist
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

# This script filters out information so that it's easier for the model to process
# It only keeps rows with estimated_revenue_l365d value, additionally drops columns that are not needed

# Columns to drop
columns_to_drop = [
    'listing_url',
    'picture_url',
    'host_url',
    'host_thumbnail_url',
    'host_picture_url',
    'description',
    'host_id',
    'host_url',
    'host_name',
    'host_since',
    'host_location',
    'host_about',
    'host_response_time',
    'host_response_rate',
    'host_acceptance_rate',
    'host_is_superhost',
    'host_thumbnail_url',
    'host_picture_url',
    'host_neighbourhood',
    'host_listings_count',
    'host_total_listings_count',
    'host_verifications',
    'host_has_profile_pic',
    'host_identity_verified',
    'scrape_id',
    'last_scraped', 
    'source',
    'name',
    'neighborhood_overview',
    'neighbourhood',
    'neighbourhood_group_cleansed',
    'calculated_host_listings_count',
    'calculated_host_listings_count_entire_homes',
    'calculated_host_listings_count_private_rooms',
    'calculated_host_listings_count_shared_rooms',
    'number_of_reviews',
    'number_of_reviews_ltm',
    'number_of_reviews_l30d',
    'number_of_reviews_ly',
    'first_review',
    'last_review',
    'review_scores_rating',
    'review_scores_accuracy',
    'review_scores_cleanliness',
    'review_scores_checkin',
    'review_scores_communication',
    'review_scores_location',
    'review_scores_value',
    'reviews_per_month',
    'license',
    'instant_bookable',
    'calendar_updated',
    'has_availability',
    'availability_30',
    'availability_60',
    'availability_90',
    'availability_365',
    'calendar_last_scraped',
    'minimum_nights',
    'maximum_nights',
    'minimum_minimum_nights',
    'maximum_minimum_nights',
    'minimum_maximum_nights',
    'maximum_maximum_nights',
    'minimum_nights_avg_ntm',
    "maximum_nights_avg_ntm",
    "availability_eoy",
]

# Read in chunks to handle large file
chunksize = 100_000
filtered_chunks = []

for chunk in pd.read_csv(INPUT_PATH, chunksize=chunksize):
    # Filter out rows where 'estimated_revenue_l365d' is missing, empty, or zero
    filtered_chunk = chunk[chunk['estimated_revenue_l365d'].notna() & 
                         (chunk['estimated_revenue_l365d'] != '') & 
                         (chunk['estimated_revenue_l365d'] > 0)]
    # Drop specified columns
    filtered_chunk = filtered_chunk.drop(columns=columns_to_drop)
    filtered_chunks.append(filtered_chunk)

# Concatenate all filtered chunks and write to new CSV
filtered_df = pd.concat(filtered_chunks)
filtered_df.to_csv(OUTPUT_PATH, index=False)

# Extract unique amenities
print("\nExtracting unique amenities...")
all_amenities = set()

# Read the original file in chunks to process amenities
for chunk in pd.read_csv(INPUT_PATH, chunksize=chunksize):
    for amenities_str in chunk['amenities']:
        try:
            # Convert string representation of list to actual list
            amenities_list = ast.literal_eval(amenities_str)
            # Clean each amenity string and add to set
            cleaned_amenities = [amenity.strip('"') for amenity in amenities_list]
            all_amenities.update(cleaned_amenities)
        except (ValueError, SyntaxError):
            continue

# Convert set to DataFrame and save
amenities_df = pd.DataFrame(sorted(all_amenities), columns=['amenity'])
amenities_df.to_csv(AMENITIES_PATH, index=False, quoting=1)  # quoting=1 means quote only non-numeric values

print(f"Input file: {INPUT_PATH}")
print(f"Output file: {OUTPUT_PATH}")
print(f"Amenities file: {AMENITIES_PATH}")
print(f"Total unique amenities found: {len(amenities_df)}")
print(f"Total entries processed: {sum(len(chunk) for chunk in pd.read_csv(INPUT_PATH, chunksize=chunksize))}")
print(f"Entries kept: {len(filtered_df)}")
print(f"Percentage kept: {(len(filtered_df) / sum(len(chunk) for chunk in pd.read_csv(INPUT_PATH, chunksize=chunksize)) * 100):.2f}%")


