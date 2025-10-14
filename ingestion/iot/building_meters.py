"""Building energy meter data ingestion."""
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import pandas as pd
from loguru import logger


class BuildingMeterIngester:
    """Ingest building energy meter data."""

    def __init__(self, api_endpoint: Optional[str] = None, api_key: Optional[str] = None):
        """Initialize building meter ingester.
        
        Args:
            api_endpoint: Building automation system API endpoint
            api_key: API authentication key
        """
        self.api_endpoint = api_endpoint or os.getenv("BUILDING_API_ENDPOINT")
        self.api_key = api_key or os.getenv("BUILDING_API_KEY")

    def get_building_list(self, campus: str = "University Park") -> List[Dict]:
        """Get list of buildings with meters.
        
        Args:
            campus: Campus name
            
        Returns:
            List of building metadata dictionaries
        """
        logger.info(f"Fetching building list for {campus}")
        
        # Placeholder - would connect to PSU OPP or BAS API
        buildings = [
            {
                'building_id': 'PSU-001',
                'building_name': 'Pattee Library',
                'campus': 'University Park',
                'latitude': 40.7982,
                'longitude': -77.8611,
                'gross_area_sqft': 250000,
                'year_built': 1940,
                'primary_use': 'Library',
                'meters': ['electric', 'gas', 'steam']
            },
            {
                'building_id': 'PSU-002',
                'building_name': 'Thomas Building',
                'campus': 'University Park',
                'latitude': 40.7955,
                'longitude': -77.8625,
                'gross_area_sqft': 150000,
                'year_built': 1931,
                'primary_use': 'Academic',
                'meters': ['electric', 'gas']
            }
        ]
        
        return buildings

    def get_meter_data(
        self,
        building_id: str,
        meter_type: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "15min",
    ) -> pd.DataFrame:
        """Get interval meter data for a building.
        
        Args:
            building_id: Building identifier
            meter_type: Meter type (electric, gas, steam, water)
            start_date: Start datetime
            end_date: End datetime
            interval: Data interval (15min, hourly, daily)
            
        Returns:
            DataFrame with meter readings
        """
        logger.info(f"Fetching {meter_type} data for {building_id}")
        
        # Generate synthetic data for demo purposes
        # In production, this would query the BAS API
        date_range = pd.date_range(start=start_date, end=end_date, freq=interval)
        
        # Simulate typical building energy patterns
        import numpy as np
        
        base_load = 100  # kW
        peak_load = 300  # kW
        
        # Add daily and weekly patterns
        hour_of_day = date_range.hour
        day_of_week = date_range.dayofweek
        
        # Higher during business hours (8 AM - 6 PM)
        business_hours = ((hour_of_day >= 8) & (hour_of_day <= 18)).astype(float)
        
        # Lower on weekends
        weekend = (day_of_week >= 5).astype(float)
        
        # Generate load profile
        load = (
            base_load
            + (peak_load - base_load) * business_hours * (1 - 0.5 * weekend)
            + np.random.normal(0, 20, len(date_range))
        )
        load = np.maximum(load, base_load * 0.5)  # Minimum load
        
        df = pd.DataFrame({
            'timestamp': date_range,
            'building_id': building_id,
            'meter_type': meter_type,
            'value': load,
            'unit': 'kW' if meter_type == 'electric' else 'therms'
        })
        
        return df

    def detect_after_hours_usage(
        self,
        meter_data: pd.DataFrame,
        business_hours: tuple = (8, 18),
        threshold_percentile: float = 75,
    ) -> pd.DataFrame:
        """Detect after-hours energy usage anomalies.
        
        Args:
            meter_data: DataFrame with meter readings
            business_hours: Tuple of (start_hour, end_hour)
            threshold_percentile: Percentile threshold for anomaly detection
            
        Returns:
            DataFrame with anomaly flags
        """
        df = meter_data.copy()
        df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
        
        # Identify after-hours periods
        df['after_hours'] = ~df['hour'].between(business_hours[0], business_hours[1])
        
        # Calculate threshold for after-hours usage
        after_hours_data = df[df['after_hours']]['value']
        threshold = after_hours_data.quantile(threshold_percentile / 100)
        
        # Flag anomalies
        df['anomaly'] = (df['after_hours']) & (df['value'] > threshold)
        
        anomaly_count = df['anomaly'].sum()
        logger.info(f"Detected {anomaly_count} after-hours anomalies")
        
        return df

    def calculate_emissions(
        self,
        meter_data: pd.DataFrame,
        emission_factors: Optional[Dict[str, float]] = None,
    ) -> pd.DataFrame:
        """Calculate CO2 emissions from meter data.
        
        Args:
            meter_data: DataFrame with meter readings
            emission_factors: Optional dict of emission factors by fuel type
            
        Returns:
            DataFrame with emissions calculations
        """
        if emission_factors is None:
            # Default emission factors (kg CO2 per unit)
            # These are for Pennsylvania grid mix (PJM) and natural gas
            emission_factors = {
                'electric': 0.385,  # kg CO2 per kWh (PJM average)
                'gas': 5.3,  # kg CO2 per therm
                'steam': 80.0,  # kg CO2 per MMBtu (depends on source)
            }
        
        df = meter_data.copy()
        
        # Apply emission factors
        df['emission_factor'] = df['meter_type'].map(emission_factors)
        df['co2_kg'] = df['value'] * df['emission_factor']
        
        total_emissions = df['co2_kg'].sum()
        logger.info(f"Total emissions: {total_emissions:.2f} kg CO2")
        
        return df


def main():
    """Example usage."""
    ingester = BuildingMeterIngester()
    
    # Get building list
    buildings = ingester.get_building_list()
    logger.info(f"Found {len(buildings)} buildings")
    
    # Get meter data for first building
    if buildings:
        building_id = buildings[0]['building_id']
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        meter_data = ingester.get_meter_data(
            building_id=building_id,
            meter_type='electric',
            start_date=start_date,
            end_date=end_date,
            interval='15min'
        )
        
        # Detect anomalies
        anomalies = ingester.detect_after_hours_usage(meter_data)
        
        # Calculate emissions
        emissions = ingester.calculate_emissions(meter_data)
        
        logger.info(f"Processed {len(meter_data)} meter readings")


if __name__ == "__main__":
    main()

