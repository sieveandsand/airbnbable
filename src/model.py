# Feifan Qiao

from sklearn.cluster import KMeans
import pandas as pd
from pathlib import Path
from xgboost import XGBRegressor
from config.data_config import COLUMNS_TO_DROP_CLUSTERING
from config.model_config import AREA_TO_INCLUDE
import joblib


class ListingModeler:
    def __init__(self, file_path: Path, n_clusters: int = 10, random_state: int = 42):
        self.file_path = file_path
        self.n_clusters = n_clusters
        self.random_state = random_state
        self.df = None
        self.clustered = False
        self.xgb_model = None

    def _load_data(self):
        """
        Load cleaned csv listing data
        """
        self.df = pd.read_csv(self.file_path)

    def _cluster(self, exclude_columns=None):
        """
        Implements K-Means clustering on the data

        Args:
            exclude_columns: list of columns to exclude from clustering

        Output:
            self.df: pandas DataFrame containing the result of clustering
        """
        # Convert boolean columns to integers
        for col in self.df.select_dtypes(include=['bool']).columns:
            self.df[col] = self.df[col].astype(int)
        
        # Determine columns to exclude
        if exclude_columns is None:
            exclude_columns = []
        
        # Use all numeric and boolean (now int) columns except those in exclude_columns
        features = self.df.select_dtypes(include=['number']).drop(columns=exclude_columns, errors='ignore')
        kmeans = KMeans(n_clusters=self.n_clusters, random_state=self.random_state)

        # here the result of clustering is added back to the dataframe
        self.df['cluster'] = kmeans.fit_predict(features)
        self.clustered = True

        print("Clustering complete. Example output:")
        print(self.df.head())

        return self.df
    
    def convert_neighborhood(self):
        """
        One-hot encodes the neighborhood_cleansed column

        Args:
            None
        
        Output:
            self.df: pandas DataFrame containing the one-hot encoded neighborhood column
        """
        self.df = pd.get_dummies(self.df, columns=['neighbourhood_cleansed'])
        return self.df
    
    def train_xgboost(self, target_column: str, feature_columns=None, **xgb_kwargs):
        """
        Train an XGBoost regressor on the given target and features.
        Args:
            target_column (str): The name of the target column.
            feature_columns (list or None): List of feature columns to use. If None, use all except target.
            xgb_kwargs: Additional keyword arguments for XGBRegressor.
        Returns:
            model: Trained XGBRegressor model.
        """
        if feature_columns is None:
            feature_columns = [col for col in self.df.columns if col != target_column]

        X = self.df[feature_columns]
        y = self.df[target_column]

        model = XGBRegressor(**xgb_kwargs)
        model.fit(X, y)

        self.xgb_model = model
        self.xgb_features = feature_columns
        
        print("XGBoost model trained.")
        return model

    def run_clustering(self):
        """
        Runs clustering on the data

        Args:
            None
        """
        self._load_data()
        self._cluster(exclude_columns=COLUMNS_TO_DROP_CLUSTERING)

    def run_xgboost(self, target_column: str, feature_columns=None, **xgb_kwargs):
        """
        Runs XGBoost training on the data

        Args:
            target_column: str, name of the target column
            feature_columns: list, names of the feature columns
        
        Output:
            None
        """
        if self.df is None:
            self._load_data()
        self.train_xgboost(target_column, feature_columns, **xgb_kwargs)

    def predict_xgboost(self, feature_dict):
        """
        Predict using the trained XGBoost model for a single sample.
        feature_dict: dict mapping feature names to values (must match training features)
        """
        if not hasattr(self, 'xgb_model'):
            raise ValueError("XGBoost model not trained yet.")

        # Ensure all features are present, fill missing with 0 or np.nan as appropriate
        sample = []
        for col in self.xgb_features:
            sample.append(feature_dict.get(col, 0))

        sample_df = pd.DataFrame([sample], columns=self.xgb_features)
        pred = self.xgb_model.predict(sample_df)
        print(f"XGBoost prediction for input: {pred[0]}")
        return pred[0]

    def save_xgboost_model(self, path):
        """
        Saves the XGBoost model and the feature list

        Args:
            path: str, path to save the model and features

        Output:
            None
        """
        if self.xgb_model is None:
            raise ValueError("No XGBoost model to save.")
        # Save both the model and the feature list
        joblib.dump({
            'model': self.xgb_model,
            'features': self.xgb_features
        }, path)
        print(f"Model and features saved to {path}")

    def load_xgboost_model(self, path):
        """
        Loads the XGBoost model and the feature list

        Args:
            path: str, path to load the model and features
        """
        data = joblib.load(path)
        self.xgb_model = data['model']
        self.xgb_features = data['features']
        print(f"Model and features loaded from {path}")

if __name__ == "__main__":
    # Check if the files exist for each area that should be included
    for area, include in AREA_TO_INCLUDE.items():
        if include:
            area_path = Path(__file__).parent.parent / 'cleaned_data' / area / 'listings_detailed_filtered.csv'
            if not area_path.exists():
                raise FileNotFoundError(f"Required data file not found for {area}: {area_path}")
    
    # Train and save model for each included area
    PROJECT_ROOT = Path(__file__).parent.parent
    cached_model_dir = PROJECT_ROOT / 'cached_models'
    cached_model_dir.mkdir(exist_ok=True)

    for area, include in AREA_TO_INCLUDE.items():
        if include:
            print(f"\n=== Training model for {area} ===")
            
            # Set up paths
            area_data_path = PROJECT_ROOT / 'cleaned_data' / area / 'listings_detailed_filtered.csv'
            area_model_path = cached_model_dir / area / f'{area}_model.joblib'
            
            # Create and train model
            print(f"Loading data from {area_data_path}")
            modeler = ListingModeler(area_data_path, n_clusters=10, random_state=42)
            
            # Run clustering and prepare neighborhoods
            print("Running clustering...")
            modeler.run_clustering()
            modeler.convert_neighborhood()
            
            # Train XGBoost model
            print("Training XGBoost model...")
            modeler.run_xgboost(
                target_column='estimated_revenue_l365d',
                n_estimators=100,
                learning_rate=0.1,
                max_depth=6,
                random_state=42
            )
            
            # Save the model
            print(f"Saving model to {area_model_path}")
            modeler.save_xgboost_model(str(area_model_path))
            print(f"✓ Completed training for {area}\n")
    