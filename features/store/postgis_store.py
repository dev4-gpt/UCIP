"""PostGIS-based geospatial feature store."""
import os
from typing import Any, Dict, List, Optional, Tuple

import geopandas as gpd
import pandas as pd
from geoalchemy2 import Geometry
from loguru import logger
from shapely.geometry import Point, Polygon
from sqlalchemy import Column, DateTime, Float, Integer, String, create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class Building(Base):
    """Building model."""
    __tablename__ = "buildings"
    
    id = Column(String, primary_key=True)
    name = Column(String)
    campus = Column(String)
    geometry = Column(Geometry('POINT', srid=4326))
    area_sqft = Column(Float)
    year_built = Column(Integer)
    primary_use = Column(String)
    created_at = Column(DateTime)


class EmissionHotspot(Base):
    """Emission hotspot model."""
    __tablename__ = "emission_hotspots"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    geometry = Column(Geometry('POLYGON', srid=4326))
    emission_value = Column(Float)
    emission_type = Column(String)
    confidence = Column(Float)
    detected_at = Column(DateTime)
    source = Column(String)


class PostGISStore:
    """PostGIS feature store for geospatial data."""

    def __init__(self, database_url: Optional[str] = None):
        """Initialize PostGIS store.
        
        Args:
            database_url: PostgreSQL connection URL
        """
        self.database_url = database_url or os.getenv(
            "DATABASE_URL",
            "postgresql://ucip:ucip_dev_password@localhost:5432/ucip"
        )
        
        self.engine = create_engine(self.database_url)
        self.Session = sessionmaker(bind=self.engine)
        
        try:
            # Test connection and ensure PostGIS is enabled
            with self.engine.connect() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
                conn.commit()
            logger.info("Connected to PostGIS database")
        except Exception as e:
            logger.error(f"Failed to connect to PostGIS: {e}")

    def create_tables(self):
        """Create database tables."""
        try:
            Base.metadata.create_all(self.engine)
            logger.info("Created database tables")
        except Exception as e:
            logger.error(f"Error creating tables: {e}")

    def store_buildings(self, buildings_gdf: gpd.GeoDataFrame) -> int:
        """Store building geometries and metadata.
        
        Args:
            buildings_gdf: GeoDataFrame with building data
            
        Returns:
            Number of buildings stored
        """
        try:
            # Ensure CRS is WGS84
            if buildings_gdf.crs != "EPSG:4326":
                buildings_gdf = buildings_gdf.to_crs("EPSG:4326")
            
            # Store to PostGIS
            buildings_gdf.to_postgis(
                "buildings",
                self.engine,
                if_exists="append",
                index=False
            )
            
            count = len(buildings_gdf)
            logger.info(f"Stored {count} buildings")
            return count
        except Exception as e:
            logger.error(f"Error storing buildings: {e}")
            return 0

    def store_hotspots(self, hotspots_gdf: gpd.GeoDataFrame) -> int:
        """Store emission hotspot geometries.
        
        Args:
            hotspots_gdf: GeoDataFrame with hotspot data
            
        Returns:
            Number of hotspots stored
        """
        try:
            if hotspots_gdf.crs != "EPSG:4326":
                hotspots_gdf = hotspots_gdf.to_crs("EPSG:4326")
            
            hotspots_gdf.to_postgis(
                "emission_hotspots",
                self.engine,
                if_exists="append",
                index=False
            )
            
            count = len(hotspots_gdf)
            logger.info(f"Stored {count} hotspots")
            return count
        except Exception as e:
            logger.error(f"Error storing hotspots: {e}")
            return 0

    def query_buildings_in_bbox(
        self,
        min_lon: float,
        min_lat: float,
        max_lon: float,
        max_lat: float,
    ) -> gpd.GeoDataFrame:
        """Query buildings within a bounding box.
        
        Args:
            min_lon: Minimum longitude
            min_lat: Minimum latitude
            max_lon: Maximum longitude
            max_lat: Maximum latitude
            
        Returns:
            GeoDataFrame with buildings
        """
        query = f"""
        SELECT *
        FROM buildings
        WHERE ST_Intersects(
            geometry,
            ST_MakeEnvelope({min_lon}, {min_lat}, {max_lon}, {max_lat}, 4326)
        )
        """
        
        try:
            gdf = gpd.read_postgis(query, self.engine, geom_col="geometry")
            logger.info(f"Found {len(gdf)} buildings in bbox")
            return gdf
        except Exception as e:
            logger.error(f"Error querying buildings: {e}")
            return gpd.GeoDataFrame()

    def query_hotspots_near_point(
        self,
        lon: float,
        lat: float,
        radius_meters: float = 1000,
    ) -> gpd.GeoDataFrame:
        """Query hotspots near a point.
        
        Args:
            lon: Longitude
            lat: Latitude
            radius_meters: Search radius in meters
            
        Returns:
            GeoDataFrame with hotspots
        """
        query = f"""
        SELECT *,
               ST_Distance(
                   geometry::geography,
                   ST_SetSRID(ST_MakePoint({lon}, {lat}), 4326)::geography
               ) as distance_m
        FROM emission_hotspots
        WHERE ST_DWithin(
            geometry::geography,
            ST_SetSRID(ST_MakePoint({lon}, {lat}), 4326)::geography,
            {radius_meters}
        )
        ORDER BY distance_m
        """
        
        try:
            gdf = gpd.read_postgis(query, self.engine, geom_col="geometry")
            logger.info(f"Found {len(gdf)} hotspots within {radius_meters}m")
            return gdf
        except Exception as e:
            logger.error(f"Error querying hotspots: {e}")
            return gpd.GeoDataFrame()

    def spatial_join_buildings_hotspots(self) -> gpd.GeoDataFrame:
        """Perform spatial join between buildings and hotspots.
        
        Returns:
            GeoDataFrame with joined data
        """
        query = """
        SELECT 
            b.id as building_id,
            b.name as building_name,
            b.geometry as building_geom,
            h.id as hotspot_id,
            h.emission_value,
            h.emission_type,
            ST_Distance(b.geometry::geography, h.geometry::geography) as distance_m
        FROM buildings b
        JOIN emission_hotspots h
        ON ST_DWithin(b.geometry::geography, h.geometry::geography, 500)
        ORDER BY b.id, distance_m
        """
        
        try:
            gdf = gpd.read_postgis(query, self.engine, geom_col="building_geom")
            logger.info(f"Found {len(gdf)} building-hotspot pairs")
            return gdf
        except Exception as e:
            logger.error(f"Error performing spatial join: {e}")
            return gpd.GeoDataFrame()


def main():
    """Example usage."""
    store = PostGISStore()
    store.create_tables()
    
    # Create sample building data
    buildings = gpd.GeoDataFrame({
        'id': ['B001', 'B002'],
        'name': ['Pattee Library', 'Thomas Building'],
        'campus': ['University Park', 'University Park'],
        'area_sqft': [250000, 150000],
        'year_built': [1940, 1931],
        'primary_use': ['Library', 'Academic'],
        'geometry': [
            Point(-77.8611, 40.7982),
            Point(-77.8625, 40.7955)
        ]
    }, crs="EPSG:4326")
    
    # Store buildings
    store.store_buildings(buildings)
    
    # Query buildings
    results = store.query_buildings_in_bbox(-77.87, 40.79, -77.85, 40.80)
    logger.info(f"Query results: {len(results)} buildings")


if __name__ == "__main__":
    main()

