"""VIIRS night lights data ingestion."""
import os
from datetime import datetime
from typing import Optional, Tuple

import ee
import numpy as np
from loguru import logger


class VIIRSIngester:
    """Ingest VIIRS night lights data for energy consumption proxies."""

    def __init__(self, gee_service_account: Optional[str] = None):
        """Initialize VIIRS ingester.
        
        Args:
            gee_service_account: Google Earth Engine service account
        """
        if gee_service_account:
            credentials = ee.ServiceAccountCredentials(
                gee_service_account,
                os.getenv("GEE_PRIVATE_KEY_PATH")
            )
            ee.Initialize(credentials)
        else:
            try:
                ee.Initialize()
            except Exception as e:
                logger.warning(f"GEE initialization failed: {e}")

    def get_pennsylvania_bounds(self) -> Tuple[float, float, float, float]:
        """Get Pennsylvania bounding box."""
        return (-80.5195, 39.7198, -74.6895, 42.2694)

    def get_viirs_nightlights(
        self,
        start_date: str,
        end_date: str,
        bounds: Optional[Tuple[float, float, float, float]] = None,
    ) -> ee.ImageCollection:
        """Get VIIRS night lights data from GEE.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            bounds: Optional custom bounds
            
        Returns:
            Earth Engine ImageCollection
        """
        bounds = bounds or self.get_pennsylvania_bounds()
        roi = ee.Geometry.Rectangle(bounds)
        
        # VIIRS DNB (Day/Night Band) monthly composites
        collection = (
            ee.ImageCollection('NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG')
            .filterDate(start_date, end_date)
            .filterBounds(roi)
            .select(['avg_rad', 'cf_cvg'])  # Average radiance and cloud-free coverage
        )
        
        logger.info(f"VIIRS collection size: {collection.size().getInfo()}")
        return collection

    def compute_night_light_change(
        self,
        baseline_start: str,
        baseline_end: str,
        current_start: str,
        current_end: str,
        bounds: Optional[Tuple[float, float, float, float]] = None,
    ) -> ee.Image:
        """Compute change in night lights between two periods.
        
        Args:
            baseline_start: Baseline period start date
            baseline_end: Baseline period end date
            current_start: Current period start date
            current_end: Current period end date
            bounds: Optional custom bounds
            
        Returns:
            Image showing night light change
        """
        baseline = self.get_viirs_nightlights(baseline_start, baseline_end, bounds)
        current = self.get_viirs_nightlights(current_start, current_end, bounds)
        
        baseline_mean = baseline.select('avg_rad').mean()
        current_mean = current.select('avg_rad').mean()
        
        change = current_mean.subtract(baseline_mean).rename('night_light_change')
        percent_change = change.divide(baseline_mean).multiply(100).rename('percent_change')
        
        return change.addBands(percent_change)

    def detect_after_hours_anomalies(
        self,
        image: ee.Image,
        threshold_percentile: int = 90,
    ) -> ee.Image:
        """Detect after-hours energy usage anomalies.
        
        Args:
            image: VIIRS night lights image
            threshold_percentile: Percentile threshold for anomaly detection
            
        Returns:
            Binary image of anomalies
        """
        radiance = image.select('avg_rad')
        
        # Compute threshold
        threshold = radiance.reduceRegion(
            reducer=ee.Reducer.percentile([threshold_percentile]),
            scale=500,
            maxPixels=1e9
        ).get('avg_rad')
        
        # Identify anomalies
        anomalies = radiance.gt(ee.Number(threshold)).rename('anomaly')
        
        return anomalies


def main():
    """Example usage."""
    ingester = VIIRSIngester()
    
    # Get last 3 months of night lights
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = "2024-10-01"
    
    collection = ingester.get_viirs_nightlights(start_date, end_date)
    
    # Compute change from previous year
    change = ingester.compute_night_light_change(
        "2023-10-01", "2023-12-31",
        "2024-10-01", end_date
    )
    
    logger.info("VIIRS ingestion complete")


if __name__ == "__main__":
    main()

