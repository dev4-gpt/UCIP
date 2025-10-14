"""Tests for emissions forecasting."""
import numpy as np
import pandas as pd
import pytest
from datetime import datetime, timedelta

from models.time_series.emissions_forecast import EmissionsForecaster


def generate_test_data(days=100):
    """Generate synthetic emissions data for testing."""
    dates = pd.date_range(start='2024-01-01', periods=days, freq='D')
    trend = np.linspace(100, 120, days)
    seasonal = 10 * np.sin(2 * np.pi * np.arange(days) / 365)
    noise = np.random.normal(0, 5, days)
    emissions = trend + seasonal + noise
    
    return pd.DataFrame({
        'timestamp': dates,
        'emissions': emissions
    })


def test_forecaster_initialization():
    """Test forecaster initialization."""
    forecaster = EmissionsForecaster(model_type="prophet")
    assert forecaster.model_type == "prophet"
    assert not forecaster.is_fitted


def test_prepare_data():
    """Test data preparation."""
    forecaster = EmissionsForecaster()
    data = generate_test_data()
    
    prepared = forecaster.prepare_data(data)
    assert len(prepared) == len(data)
    assert 'timestamp' in prepared.columns
    assert 'emissions' in prepared.columns


def test_fit_prophet():
    """Test Prophet model fitting."""
    forecaster = EmissionsForecaster(model_type="prophet")
    data = generate_test_data()
    
    forecaster.fit(data)
    assert forecaster.is_fitted


def test_forecast_prophet():
    """Test Prophet forecasting."""
    forecaster = EmissionsForecaster(model_type="prophet")
    data = generate_test_data()
    
    forecaster.fit(data)
    forecast = forecaster.forecast(periods=30, freq='D')
    
    assert len(forecast) > 0
    assert 'timestamp' in forecast.columns
    assert 'forecast' in forecast.columns
    assert 'lower_bound' in forecast.columns
    assert 'upper_bound' in forecast.columns


def test_detect_forecast_anomalies():
    """Test forecast anomaly detection."""
    forecaster = EmissionsForecaster(model_type="prophet")
    data = generate_test_data()
    
    forecaster.fit(data)
    forecast = forecaster.forecast(periods=30, freq='D')
    
    anomalies = forecaster.detect_forecast_anomalies(forecast)
    assert 'anomaly' in anomalies.columns


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

