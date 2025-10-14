"""Sentinel satellite data ingestion."""
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import ee
import numpy as np
import rasterio
from loguru import logger
from sentinelsat import SentinelAPI, read_geojson, geojson_to_wkt


class SentinelIngester:
    """Ingest Sentinel-2 and Sentinel-5P data for Pennsylvania."""

    def __init__(
        self,
        sentinel_user: Optional[str] = None,
        sentinel_password: Optional[str] = None,
        gee_service_account: Optional[str] = None,
    ):
        """Initialize Sentinel ingester.
        
        Args:
            sentinel_user: Copernicus Open Access Hub username
            sentinel_password: Copernicus Open Access Hub password
            gee_service_account: Google Earth Engine service account
        """
        self.sentinel_user = sentinel_user or os.getenv("SENTINEL_USER")
        self.sentinel_password = sentinel_password or os.getenv("SENTINEL_PASSWORD")
        
        # Initialize Sentinel API
        if self.sentinel_user and self.sentinel_password:
            self.api = SentinelAPI(self.sentinel_user, self.sentinel_password)
        
        # Initialize Google Earth Engine
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
        """Get Pennsylvania bounding box.
        
        Returns:
            Tuple of (min_lon, min_lat, max_lon, max_lat)
        """
        # Pennsylvania approximate bounds
        return (-80.5195, 39.7198, -74.6895, 42.2694)

    def search_sentinel2_scenes(
        self,
        start_date: datetime,
        end_date: datetime,
        cloud_cover_max: int = 20,
        bounds: Optional[Tuple[float, float, float, float]] = None,
    ) -> List[Dict]:
        """Search for Sentinel-2 scenes over Pennsylvania.
        
        Args:
            start_date: Start date for search
            end_date: End date for search
            cloud_cover_max: Maximum cloud cover percentage
            bounds: Optional custom bounds (min_lon, min_lat, max_lon, max_lat)
            
        Returns:
            List of scene metadata dictionaries
        """
        if not hasattr(self, 'api'):
            logger.error("Sentinel API not initialized")
            return []
        
        bounds = bounds or self.get_pennsylvania_bounds()
        footprint = f"POLYGON(({bounds[0]} {bounds[1]}, {bounds[2]} {bounds[1]}, " \
                   f"{bounds[2]} {bounds[3]}, {bounds[0]} {bounds[3]}, {bounds[0]} {bounds[1]}))"
        
        products = self.api.query(
            footprint,
            date=(start_date.strftime("%Y%m%d"), end_date.strftime("%Y%m%d")),
            platformname='Sentinel-2',
            cloudcoverpercentage=(0, cloud_cover_max),
            producttype='S2MSI2A'  # Level-2A (atmospherically corrected)
        )
        
        logger.info(f"Found {len(products)} Sentinel-2 scenes")
        return list(products.values())

    def get_sentinel2_gee(
        self,
        start_date: str,
        end_date: str,
        bounds: Optional[Tuple[float, float, float, float]] = None,
        cloud_cover_max: int = 20,
    ) -> ee.ImageCollection:
        """Get Sentinel-2 imagery from Google Earth Engine.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            bounds: Optional custom bounds
            cloud_cover_max: Maximum cloud cover percentage
            
        Returns:
            Earth Engine ImageCollection
        """
        bounds = bounds or self.get_pennsylvania_bounds()
        roi = ee.Geometry.Rectangle(bounds)
        
        collection = (
            ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
            .filterDate(start_date, end_date)
            .filterBounds(roi)
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', cloud_cover_max))
        )
        
        logger.info(f"GEE collection size: {collection.size().getInfo()}")
        return collection

    def get_sentinel5p_no2(
        self,
        start_date: str,
        end_date: str,
        bounds: Optional[Tuple[float, float, float, float]] = None,
    ) -> ee.ImageCollection:
        """Get Sentinel-5P NO2 data from GEE.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            bounds: Optional custom bounds
            
        Returns:
            Earth Engine ImageCollection
        """
        bounds = bounds or self.get_pennsylvania_bounds()
        roi = ee.Geometry.Rectangle(bounds)
        
        collection = (
            ee.ImageCollection('COPERNICUS/S5P/NRTI/L3_NO2')
            .filterDate(start_date, end_date)
            .filterBounds(roi)
            .select('NO2_column_number_density')
        )
        
        logger.info(f"Sentinel-5P NO2 collection size: {collection.size().getInfo()}")
        return collection

    def compute_ndvi(self, image: ee.Image) -> ee.Image:
        """Compute NDVI from Sentinel-2 image.
        
        Args:
            image: Sentinel-2 image
            
        Returns:
            Image with NDVI band
        """
        ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
        return image.addBands(ndvi)

    def export_to_geotiff(
        self,
        image: ee.Image,
        output_path: str,
        scale: int = 10,
        bounds: Optional[Tuple[float, float, float, float]] = None,
    ) -> None:
        """Export Earth Engine image to GeoTIFF.
        
        Args:
            image: Earth Engine image
            output_path: Output file path
            scale: Resolution in meters
            bounds: Optional custom bounds
        """
        bounds = bounds or self.get_pennsylvania_bounds()
        roi = ee.Geometry.Rectangle(bounds)
        
        # Get download URL
        url = image.getDownloadURL({
            'scale': scale,
            'region': roi,
            'format': 'GEO_TIFF'
        })
        
        logger.info(f"Download URL generated: {url}")
        logger.info(f"Use this URL to download to {output_path}")


def main():
    """Example usage."""
    ingester = SentinelIngester()
    
    # Get last 30 days of Sentinel-2 data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    # Search via Copernicus Hub
    # scenes = ingester.search_sentinel2_scenes(start_date, end_date)
    
    # Or use Google Earth Engine
    collection = ingester.get_sentinel2_gee(
        start_date.strftime("%Y-%m-%d"),
        end_date.strftime("%Y-%m-%d")
    )
    
    # Get NO2 data
    no2_collection = ingester.get_sentinel5p_no2(
        start_date.strftime("%Y-%m-%d"),
        end_date.strftime("%Y-%m-%d")
    )
    
    logger.info("Ingestion complete")


if __name__ == "__main__":
    main()

