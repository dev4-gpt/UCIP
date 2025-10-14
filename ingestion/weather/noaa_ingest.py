"""NOAA weather data ingestion."""
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import pandas as pd
import requests
from loguru import logger


class NOAAIngester:
    """Ingest weather data from NOAA APIs."""

    def __init__(self, api_token: Optional[str] = None):
        """Initialize NOAA ingester.
        
        Args:
            api_token: NOAA API token (get from https://www.ncdc.noaa.gov/cdo-web/token)
        """
        self.api_token = api_token or os.getenv("NOAA_API_TOKEN")
        self.base_url = "https://www.ncei.noaa.gov/cdo-web/api/v2"
        self.headers = {"token": self.api_token} if self.api_token else {}

    def get_stations(
        self,
        state: str = "PA",
        dataset: str = "GHCND",
    ) -> List[Dict]:
        """Get weather stations for Pennsylvania.
        
        Args:
            state: State code
            dataset: Dataset ID (GHCND = Daily Summaries)
            
        Returns:
            List of station dictionaries
        """
        if not self.api_token:
            logger.warning("NOAA API token not set")
            return []
        
        url = f"{self.base_url}/stations"
        params = {
            "locationid": f"FIPS:{self._get_state_fips(state)}",
            "datasetid": dataset,
            "limit": 1000
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            stations = data.get("results", [])
            logger.info(f"Found {len(stations)} stations in {state}")
            return stations
        except Exception as e:
            logger.error(f"Error fetching stations: {e}")
            return []

    def get_weather_data(
        self,
        station_id: str,
        start_date: datetime,
        end_date: datetime,
        datatypes: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """Get weather data for a station.
        
        Args:
            station_id: Station identifier
            start_date: Start date
            end_date: End date
            datatypes: List of data types (TMAX, TMIN, PRCP, SNOW, etc.)
            
        Returns:
            DataFrame with weather observations
        """
        if not self.api_token:
            logger.warning("NOAA API token not set, returning synthetic data")
            return self._generate_synthetic_weather(start_date, end_date)
        
        if datatypes is None:
            datatypes = ["TMAX", "TMIN", "PRCP", "SNOW", "AWND"]
        
        url = f"{self.base_url}/data"
        params = {
            "datasetid": "GHCND",
            "stationid": station_id,
            "startdate": start_date.strftime("%Y-%m-%d"),
            "enddate": end_date.strftime("%Y-%m-%d"),
            "datatypeid": ",".join(datatypes),
            "limit": 1000,
            "units": "standard"
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            results = data.get("results", [])
            
            df = pd.DataFrame(results)
            logger.info(f"Retrieved {len(df)} weather records")
            return df
        except Exception as e:
            logger.error(f"Error fetching weather data: {e}")
            return pd.DataFrame()

    def _generate_synthetic_weather(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> pd.DataFrame:
        """Generate synthetic weather data for demo purposes.
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            DataFrame with synthetic weather data
        """
        import numpy as np
        
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # Simulate Pennsylvania weather patterns
        day_of_year = date_range.dayofyear
        
        # Temperature (Fahrenheit)
        temp_base = 50 + 25 * np.sin(2 * np.pi * (day_of_year - 80) / 365)
        temp_max = temp_base + np.random.normal(10, 5, len(date_range))
        temp_min = temp_base - np.random.normal(10, 5, len(date_range))
        
        # Precipitation (inches)
        precip = np.random.exponential(0.1, len(date_range))
        
        # Wind speed (mph)
        wind = np.random.gamma(2, 5, len(date_range))
        
        df = pd.DataFrame({
            'date': date_range,
            'temp_max_f': temp_max,
            'temp_min_f': temp_min,
            'temp_avg_f': (temp_max + temp_min) / 2,
            'precipitation_in': precip,
            'wind_speed_mph': wind,
        })
        
        return df

    def calculate_heating_cooling_degree_days(
        self,
        weather_data: pd.DataFrame,
        base_temp: float = 65.0,
    ) -> pd.DataFrame:
        """Calculate heating and cooling degree days.
        
        Args:
            weather_data: DataFrame with temperature data
            base_temp: Base temperature in Fahrenheit
            
        Returns:
            DataFrame with degree day calculations
        """
        df = weather_data.copy()
        
        # Heating degree days (HDD)
        df['hdd'] = (base_temp - df['temp_avg_f']).clip(lower=0)
        
        # Cooling degree days (CDD)
        df['cdd'] = (df['temp_avg_f'] - base_temp).clip(lower=0)
        
        logger.info(f"Total HDD: {df['hdd'].sum():.1f}, Total CDD: {df['cdd'].sum():.1f}")
        
        return df

    def _get_state_fips(self, state_code: str) -> str:
        """Get FIPS code for state.
        
        Args:
            state_code: Two-letter state code
            
        Returns:
            FIPS code
        """
        fips_codes = {
            "PA": "42",
            "NY": "36",
            "OH": "39",
            "WV": "54",
            "MD": "24",
            "NJ": "34",
            "DE": "10"
        }
        return fips_codes.get(state_code.upper(), "42")


def main():
    """Example usage."""
    ingester = NOAAIngester()
    
    # Get weather data for last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    # Get stations (requires API token)
    # stations = ingester.get_stations(state="PA")
    
    # Get weather data (will use synthetic data if no token)
    weather_data = ingester.get_weather_data(
        station_id="GHCND:USC00368449",  # State College station
        start_date=start_date,
        end_date=end_date
    )
    
    # Calculate degree days
    if not weather_data.empty:
        degree_days = ingester.calculate_heating_cooling_degree_days(weather_data)
        logger.info("Weather ingestion complete")


if __name__ == "__main__":
    main()

