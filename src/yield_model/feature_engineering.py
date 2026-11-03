"""Feature engineering and preprocessing pipeline for multi-state crop yield forecasting."""

from typing import List, Tuple
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline

CATEGORICAL_FEATURES: List[str] = [
    "state",
    "crop",
    "district",
    "soil_type",
    "irrigation_source",
    "sowing_window",
]

NUMERICAL_FEATURES: List[str] = [
    "plot_acres",
    "seasonal_rainfall_mm",
    "march_max_temp_c",
    "nitrogen_kg_acre",
    "phosphorus_kg_acre",
    "potassium_kg_acre",
]

TARGET_COLUMN: str = "yield_quintals_per_acre"


def get_preprocessor() -> ColumnTransformer:
    """Creates a ColumnTransformer pipeline that imputes missing values,
    scales numerical inputs, and one-hot encodes categorical attributes.
    """
    numeric_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, NUMERICAL_FEATURES),
            ("cat", categorical_transformer, CATEGORICAL_FEATURES),
        ]
    )

    return preprocessor


def get_feature_names() -> Tuple[List[str], List[str]]:
    """Returns numerical and categorical feature lists."""
    return NUMERICAL_FEATURES, CATEGORICAL_FEATURES
