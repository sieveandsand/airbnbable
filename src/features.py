# Amenity keyword groups

KITCHEN_KEYWORDS = [
    "oven", "microwave", "stove", "convection", "cooktop",
    "fridge", "refrigerator", "freezer",
    "toaster", "blender", "rice cooker", "coffee maker",
    "dishwasher", "baking sheet", "cooking basics",
    "kitchen", "kitchenette"
]
TV_KEYWORDS = ["tv", "netflix", "hulu", "smart tv"]
WIFI_KEYWORDS = ["wifi", "internet"]
AIR_CONDITIONING_KEYWORDS = ["air conditioning", "ac"]
WASHER_KEYWORDS = ["washer", "laundry"]
DRYER_KEYWORDS = ["dryer"]
TOILETRIES_KEYWORDS = ["shampoo", "conditioner", "body soap", "body wash", "toiletries"]
COFFEE_KEYWORDS = ["coffee", "coffee maker"]
BREAKFAST_KEYWORDS = ["breakfast"]
FREE_PARKING_KEYWORDS = ["free parking"]
PAID_PARKING_KEYWORDS = ["paid parking"]
POOL_KEYWORDS = ["pool"]
GYM_KEYWORDS = ["gym", "fitness"]
HOT_TUB_KEYWORDS = ["hot tub", "jacuzzi"]
DISHWASHER_KEYWORDS = ["dishwasher"]
PATIO_KEYWORDS = ["patio", "balcony"]
BACKYARD_KEYWORDS = ["backyard", "garden"]

# Rule-based feature extractor
def extract_amenity_flags(amenity_list: list[str]) -> dict[str, bool]:
    amenity_text = " ".join([a.lower() for a in amenity_list])

    return {
        "has_tv": any(keyword in amenity_text for keyword in TV_KEYWORDS),
        "has_wifi": any(keyword in amenity_text for keyword in WIFI_KEYWORDS),
        "has_kitchen_appliances": any(keyword in amenity_text for keyword in KITCHEN_KEYWORDS),
        "has_air_conditioning": any(keyword in amenity_text for keyword in AIR_CONDITIONING_KEYWORDS),
        "has_washer": any(keyword in amenity_text for keyword in WASHER_KEYWORDS),
        "has_dryer": any(keyword in amenity_text for keyword in DRYER_KEYWORDS),
        "has_toiletries": any(keyword in amenity_text for keyword in TOILETRIES_KEYWORDS),
        "has_coffee": any(keyword in amenity_text for keyword in COFFEE_KEYWORDS),
        "has_breakfast": any(keyword in amenity_text for keyword in BREAKFAST_KEYWORDS),
        "has_free_parking": any(keyword in amenity_text for keyword in FREE_PARKING_KEYWORDS),
        "has_paid_parking": any(keyword in amenity_text for keyword in PAID_PARKING_KEYWORDS),
        "has_pool": any(keyword in amenity_text for keyword in POOL_KEYWORDS),
        "has_gym": any(keyword in amenity_text for keyword in GYM_KEYWORDS),
        "has_hot_tub": any(keyword in amenity_text for keyword in HOT_TUB_KEYWORDS),
        "has_dishwasher": any(keyword in amenity_text for keyword in DISHWASHER_KEYWORDS),
        "has_patio": any(keyword in amenity_text for keyword in PATIO_KEYWORDS),
        "has_backyard": any(keyword in amenity_text for keyword in BACKYARD_KEYWORDS),
    }
