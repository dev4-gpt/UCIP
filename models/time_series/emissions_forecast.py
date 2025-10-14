"""Emissions forecasting using time series models."""
import warnings
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from loguru import logger
from prophet import Prophet
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX

warnings.filterwarnings('ignore')


class EmissionsForecaster:
    """Forecast emissions using time series models."""

    def __init__(self, model_type: str = "prophet"):
        """Initialize emissions forecaster.
        
        Args:
            model_type: Model type ('prophet', 'arima', 'sarimax')
        """
        self.model_type = model_type
        self.model = None
        self.is_fitted = False

    def prepare_data(
        self,
        data: pd.DataFrame,
        date_col: str = "timestamp",
        value_col: str = "emissions",
    ) -> pd.DataFrame:
        """Prepare data for forecasting.
        
        Args:
            data: Input DataFrame
            date_col: Name of date column
            value_col: Name of value column
            
        Returns:
            Prepared DataFrame
        """
        df = data.copy()
        
        # Ensure datetime
        df[date_col] = pd.to_datetime(df[date_col])
        
        # Sort by date
        df = df.sort_values(date_col)
        
        # Handle missing values
        df[value_col] = df[value_col].fillna(method='ffill').fillna(method='bfill')
        
        return df

    def fit_prophet(
        self,
        data: pd.DataFrame,
        date_col: str = "timestamp",
        value_col: str = "emissions",
        **kwargs
    ) -> None:
        """Fit Prophet model.
        
        Args:
            data: Training data
            date_col: Name of date column
            value_col: Name of value column
            **kwargs: Additional Prophet parameters
        """
        # Prepare data for Prophet
        df = data[[date_col, value_col]].copy()
        df.columns = ['ds', 'y']
        
        # Initialize and fit model
        self.model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False,
            **kwargs
        )
        
        self.model.fit(df)
        self.is_fitted = True
        logger.info("Prophet model fitted")

    def fit_arima(
        self,
        data: pd.DataFrame,
        value_col: str = "emissions",
        order: Tuple[int, int, int] = (1, 1, 1),
    ) -> None:
        """Fit ARIMA model.
        
        Args:
            data: Training data
            value_col: Name of value column
            order: ARIMA order (p, d, q)
        """
        y = data[value_col].values
        
        self.model = ARIMA(y, order=order)
        self.model = self.model.fit()
        self.is_fitted = True
        logger.info(f"ARIMA{order} model fitted")

    def fit_sarimax(
        self,
        data: pd.DataFrame,
        value_col: str = "emissions",
        order: Tuple[int, int, int] = (1, 1, 1),
        seasonal_order: Tuple[int, int, int, int] = (1, 1, 1, 24),
    ) -> None:
        """Fit SARIMAX model.
        
        Args:
            data: Training data
            value_col: Name of value column
            order: ARIMA order (p, d, q)
            seasonal_order: Seasonal order (P, D, Q, s)
        """
        y = data[value_col].values
        
        self.model = SARIMAX(y, order=order, seasonal_order=seasonal_order)
        self.model = self.model.fit(disp=False)
        self.is_fitted = True
        logger.info(f"SARIMAX model fitted")

    def fit(
        self,
        data: pd.DataFrame,
        date_col: str = "timestamp",
        value_col: str = "emissions",
        **kwargs
    ) -> None:
        """Fit the selected model.
        
        Args:
            data: Training data
            date_col: Name of date column
            value_col: Name of value column
            **kwargs: Model-specific parameters
        """
        data = self.prepare_data(data, date_col, value_col)
        
        if self.model_type == "prophet":
            self.fit_prophet(data, date_col, value_col, **kwargs)
        elif self.model_type == "arima":
            self.fit_arima(data, value_col, **kwargs)
        elif self.model_type == "sarimax":
            self.fit_sarimax(data, value_col, **kwargs)
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")

    def forecast(
        self,
        periods: int,
        freq: str = "H",
    ) -> pd.DataFrame:
        """Generate forecast.
        
        Args:
            periods: Number of periods to forecast
            freq: Frequency ('H' for hourly, 'D' for daily, etc.)
            
        Returns:
            DataFrame with forecast
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")
        
        if self.model_type == "prophet":
            future = self.model.make_future_dataframe(periods=periods, freq=freq)
            forecast = self.model.predict(future)
            
            result = pd.DataFrame({
                'timestamp': forecast['ds'],
                'forecast': forecast['yhat'],
                'lower_bound': forecast['yhat_lower'],
                'upper_bound': forecast['yhat_upper']
            })
            
        elif self.model_type in ["arima", "sarimax"]:
            forecast = self.model.forecast(steps=periods)
            
            # Generate timestamps
            last_date = datetime.now()
            timestamps = pd.date_range(
                start=last_date,
                periods=periods,
                freq=freq
            )
            
            result = pd.DataFrame({
                'timestamp': timestamps,
                'forecast': forecast,
                'lower_bound': forecast * 0.9,  # Simplified confidence intervals
                'upper_bound': forecast * 1.1
            })
        
        logger.info(f"Generated forecast for {periods} periods")
        return result

    def detect_forecast_anomalies(
        self,
        forecast: pd.DataFrame,
        threshold_std: float = 2.0,
    ) -> pd.DataFrame:
        """Detect anomalies in forecast.
        
        Args:
            forecast: Forecast DataFrame
            threshold_std: Standard deviation threshold
            
        Returns:
            DataFrame with anomaly flags
        """
        df = forecast.copy()
        
        # Calculate forecast range
        df['forecast_range'] = df['upper_bound'] - df['lower_bound']
        
        # Flag anomalies (large uncertainty)
        mean_range = df['forecast_range'].mean()
        std_range = df['forecast_range'].std()
        threshold = mean_range + threshold_std * std_range
        
        df['anomaly'] = df['forecast_range'] > threshold
        
        anomaly_count = df['anomaly'].sum()
        logger.info(f"Detected {anomaly_count} forecast anomalies")
        
        return df

    def evaluate(
        self,
        test_data: pd.DataFrame,
        value_col: str = "emissions",
    ) -> Dict[str, float]:
        """Evaluate forecast accuracy.
        
        Args:
            test_data: Test data
            value_col: Name of value column
            
        Returns:
            Dictionary of evaluation metrics
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")
        
        # Generate forecast
        forecast = self.forecast(periods=len(test_data))
        
        # Calculate metrics
        y_true = test_data[value_col].values
        y_pred = forecast['forecast'].values[:len(y_true)]
        
        mae = np.mean(np.abs(y_true - y_pred))
        rmse = np.sqrt(np.mean((y_true - y_pred) ** 2))
        mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
        
        metrics = {
            'mae': mae,
            'rmse': rmse,
            'mape': mape
        }
        
        logger.info(f"Evaluation metrics: MAE={mae:.2f}, RMSE={rmse:.2f}, MAPE={mape:.2f}%")
        return metrics


def main():
    """Example usage."""
    # Generate synthetic emissions data
    dates = pd.date_range(start='2024-01-01', end='2024-10-13', freq='D')
    
    # Simulate emissions with trend and seasonality
    trend = np.linspace(100, 120, len(dates))
    seasonal = 10 * np.sin(2 * np.pi * np.arange(len(dates)) / 365)
    noise = np.random.normal(0, 5, len(dates))
    emissions = trend + seasonal + noise
    
    data = pd.DataFrame({
        'timestamp': dates,
        'emissions': emissions
    })
    
    # Fit Prophet model
    forecaster = EmissionsForecaster(model_type="prophet")
    forecaster.fit(data)
    
    # Generate 30-day forecast
    forecast = forecaster.forecast(periods=30, freq='D')
    logger.info(f"Forecast shape: {forecast.shape}")
    logger.info(f"Mean forecast: {forecast['forecast'].mean():.2f}")
    
    # Detect anomalies
    forecast_with_anomalies = forecaster.detect_forecast_anomalies(forecast)
    logger.info(f"Anomalies: {forecast_with_anomalies['anomaly'].sum()}")


if __name__ == "__main__":
    main()

