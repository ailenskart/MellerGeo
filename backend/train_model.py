#!/usr/bin/env python3
"""Train the Meller store revenue prediction model."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.data_generator import generate_training_data
from app.predictor import RevenuePredictor


def main():
    data_dir = Path(__file__).resolve().parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    csv_path = data_dir / "store_training_data.csv"
    if not csv_path.exists():
        from app.data_generator import export_cities_catalog

        df = generate_training_data()
        df.to_csv(csv_path, index=False)
        export_cities_catalog(data_dir / "europe_cities.json")
        print(f"Generated training data: {len(df)} samples")
    else:
        import pandas as pd

        df = pd.read_csv(csv_path)
        print(f"Loaded training data: {len(df)} samples")

    predictor = RevenuePredictor()
    metrics = predictor.train(df)

    print("\n=== Model Training Complete ===")
    print(f"R² Score:     {metrics.r2_score}")
    print(f"MAE:          €{metrics.mae_eur:,.0f}")
    print(f"RMSE:         €{metrics.rmse_eur:,.0f}")
    print(f"Samples:      {metrics.training_samples}")
    print("\nTop Feature Importance:")
    for item in metrics.feature_importance[:5]:
        print(f"  {item['feature']}: {item['importance']}")


if __name__ == "__main__":
    main()
