"""Anomaly detection for emissions and energy data."""
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from loguru import logger
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


class AnomalyDetector:
    """Detect anomalies in emissions and energy time series."""

    def __init__(
        self,
        method: str = "isolation_forest",
        contamination: float = 0.1,
    ):
        """Initialize anomaly detector.
        
        Args:
            method: Detection method ('isolation_forest', 'statistical', 'threshold')
            contamination: Expected proportion of anomalies
        """
        self.method = method
        self.contamination = contamination
        self.model = None
        self.scaler = StandardScaler()
        self.is_fitted = False

    def prepare_features(
        self,
        data: pd.DataFrame,
        value_col: str = "value",
        timestamp_col: str = "timestamp",
    ) -> np.ndarray:
        """Prepare features for anomaly detection.
        
        Args:
            data: Input DataFrame
            value_col: Name of value column
            timestamp_col: Name of timestamp column
            
        Returns:
            Feature matrix
        """
        df = data.copy()
        df[timestamp_col] = pd.to_datetime(df[timestamp_col])
        
        # Extract temporal features
        df['hour'] = df[timestamp_col].dt.hour
        df['day_of_week'] = df[timestamp_col].dt.dayofweek
        df['day_of_month'] = df[timestamp_col].dt.day
        df['month'] = df[timestamp_col].dt.month
        
        # Calculate rolling statistics
        df['rolling_mean'] = df[value_col].rolling(window=24, min_periods=1).mean()
        df['rolling_std'] = df[value_col].rolling(window=24, min_periods=1).std()
        df['rolling_min'] = df[value_col].rolling(window=24, min_periods=1).min()
        df['rolling_max'] = df[value_col].rolling(window=24, min_periods=1).max()
        
        # Calculate rate of change
        df['rate_of_change'] = df[value_col].diff()
        
        # Fill NaN values
        df = df.fillna(method='bfill').fillna(0)
        
        # Select features
        feature_cols = [
            value_col, 'hour', 'day_of_week', 'day_of_month', 'month',
            'rolling_mean', 'rolling_std', 'rolling_min', 'rolling_max',
            'rate_of_change'
        ]
        
        features = df[feature_cols].values
        return features

    def fit(
        self,
        data: pd.DataFrame,
        value_col: str = "value",
        timestamp_col: str = "timestamp",
    ) -> None:
        """Fit anomaly detection model.
        
        Args:
            data: Training data
            value_col: Name of value column
            timestamp_col: Name of timestamp column
        """
        features = self.prepare_features(data, value_col, timestamp_col)
        
        # Scale features
        features_scaled = self.scaler.fit_transform(features)
        
        if self.method == "isolation_forest":
            self.model = IsolationForest(
                contamination=self.contamination,
                random_state=42,
                n_estimators=100
            )
            self.model.fit(features_scaled)
        
        self.is_fitted = True
        logger.info(f"Anomaly detector fitted using {self.method}")

    def detect(
        self,
        data: pd.DataFrame,
        value_col: str = "value",
        timestamp_col: str = "timestamp",
    ) -> pd.DataFrame:
        """Detect anomalies in data.
        
        Args:
            data: Input data
            value_col: Name of value column
            timestamp_col: Name of timestamp column
            
        Returns:
            DataFrame with anomaly flags and scores
        """
        df = data.copy()
        features = self.prepare_features(df, value_col, timestamp_col)
        
        if self.method == "isolation_forest":
            if not self.is_fitted:
                # Fit on the fly if not fitted
                self.fit(df, value_col, timestamp_col)
            
            features_scaled = self.scaler.transform(features)
            
            # Predict anomalies (-1 for anomaly, 1 for normal)
            predictions = self.model.predict(features_scaled)
            scores = self.model.score_samples(features_scaled)
            
            df['anomaly'] = (predictions == -1)
            df['anomaly_score'] = -scores  # Higher score = more anomalous
            
        elif self.method == "statistical":
            # Z-score based detection
            mean = df[value_col].mean()
            std = df[value_col].std()
            z_scores = np.abs((df[value_col] - mean) / std)
            
            df['anomaly'] = z_scores > 3
            df['anomaly_score'] = z_scores
            
        elif self.method == "threshold":
            # Simple threshold-based detection
            # Detect values outside expected range
            q1 = df[value_col].quantile(0.25)
            q3 = df[value_col].quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            df['anomaly'] = (df[value_col] < lower_bound) | (df[value_col] > upper_bound)
            df['anomaly_score'] = np.abs(df[value_col] - df[value_col].median())
        
        anomaly_count = df['anomaly'].sum()
        anomaly_pct = (anomaly_count / len(df)) * 100
        logger.info(f"Detected {anomaly_count} anomalies ({anomaly_pct:.1f}%)")
        
        return df

    def detect_after_hours_anomalies(
        self,
        data: pd.DataFrame,
        value_col: str = "value",
        timestamp_col: str = "timestamp",
        business_hours: Tuple[int, int] = (8, 18),
        threshold_percentile: float = 75,
    ) -> pd.DataFrame:
        """Detect after-hours usage anomalies.
        
        Args:
            data: Input data
            value_col: Name of value column
            timestamp_col: Name of timestamp column
            business_hours: Tuple of (start_hour, end_hour)
            threshold_percentile: Percentile threshold
            
        Returns:
            DataFrame with after-hours anomaly flags
        """
        df = data.copy()
        df[timestamp_col] = pd.to_datetime(df[timestamp_col])
        df['hour'] = df[timestamp_col].dt.hour
        df['day_of_week'] = df[timestamp_col].dt.dayofweek
        
        # Identify after-hours periods (including weekends)
        df['after_hours'] = (
            ~df['hour'].between(business_hours[0], business_hours[1]) |
            (df['day_of_week'] >= 5)
        )
        
        # Calculate threshold for after-hours usage
        after_hours_data = df[df['after_hours']][value_col]
        if len(after_hours_data) > 0:
            threshold = after_hours_data.quantile(threshold_percentile / 100)
            
            # Flag anomalies
            df['after_hours_anomaly'] = (
                df['after_hours'] & (df[value_col] > threshold)
            )
        else:
            df['after_hours_anomaly'] = False
        
        anomaly_count = df['after_hours_anomaly'].sum()
        logger.info(f"Detected {anomaly_count} after-hours anomalies")
        
        return df

    def get_anomaly_summary(
        self,
        data: pd.DataFrame,
        timestamp_col: str = "timestamp",
    ) -> Dict:
        """Get summary statistics of anomalies.
        
        Args:
            data: DataFrame with anomaly flags
            timestamp_col: Name of timestamp column
            
        Returns:
            Dictionary with summary statistics
        """
        if 'anomaly' not in data.columns:
            logger.warning("No anomaly column found")
            return {}
        
        df = data.copy()
        df[timestamp_col] = pd.to_datetime(df[timestamp_col])
        
        anomalies = df[df['anomaly']]
        
        summary = {
            'total_anomalies': len(anomalies),
            'anomaly_percentage': (len(anomalies) / len(df)) * 100,
            'first_anomaly': anomalies[timestamp_col].min() if len(anomalies) > 0 else None,
            'last_anomaly': anomalies[timestamp_col].max() if len(anomalies) > 0 else None,
            'mean_anomaly_score': anomalies['anomaly_score'].mean() if 'anomaly_score' in anomalies.columns else None,
        }
        
        # Anomalies by hour
        if len(anomalies) > 0:
            anomalies['hour'] = anomalies[timestamp_col].dt.hour
            summary['anomalies_by_hour'] = anomalies['hour'].value_counts().to_dict()
        
        return summary


def main():
    """Example usage."""
    # Generate synthetic data with anomalies
    dates = pd.date_range(start='2024-10-01', end='2024-10-13', freq='H')
    
    # Normal pattern
    hour = dates.hour
    base_load = 100 + 50 * ((hour >= 8) & (hour <= 18))
    noise = np.random.normal(0, 10, len(dates))
    values = base_load + noise
    
    # Inject anomalies
    anomaly_indices = np.random.choice(len(values), size=20, replace=False)
    values[anomaly_indices] += np.random.uniform(100, 200, size=20)
    
    data = pd.DataFrame({
        'timestamp': dates,
        'value': values
    })
    
    # Detect anomalies using Isolation Forest
    detector = AnomalyDetector(method="isolation_forest", contamination=0.05)
    results = detector.detect(data)
    
    logger.info(f"Anomalies detected: {results['anomaly'].sum()}")
    
    # Detect after-hours anomalies
    after_hours_results = detector.detect_after_hours_anomalies(data)
    logger.info(f"After-hours anomalies: {after_hours_results['after_hours_anomaly'].sum()}")
    
    # Get summary
    summary = detector.get_anomaly_summary(results)
    logger.info(f"Summary: {summary}")


if __name__ == "__main__":
    main()

