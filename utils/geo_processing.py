import geopandas as gpd
import pandas as pd
from pykml import parser
from shapely.geometry import Polygon, MultiPolygon
import zipfile
import tempfile
import os

class GeoProcessor:
    """Procesador de datos geográficos"""
    
    def read_kml(self, file_path):
        """Lee archivo KML y convierte a GeoDataFrame"""
        try:
            # Método 1: Usando geopandas (para KML simples)
            gdf = gpd.read_file(file_path, driver='KML')
            return gdf
        except:
            # Método 2: Parsing manual para KML más complejos
            return self._parse_kml_manual(file_path)
    
    def _parse_kml_manual(self, file_path):
        """Parsing manual de KML usando pykml"""
        with open(file_path, 'r', encoding='utf-8') as f:
            doc = parser.parse(f).getroot()
        
        features = []
        for placemark in doc.Document.Placemark:
            try:
                name = str(placemark.name) if placemark.name else "Sin nombre"
                coords_text = str(placemark.Polygon.outerBoundaryIs.LinearRing.coordinates)
                
                # Parsear coordenadas
                coords = []
                for coord_str in coords_text.strip().split():
                    if coord_str:
                        lon, lat, _ = map(float, coord_str.split(','))
                        coords.append((lon, lat))
                
                if len(coords) >= 3:
                    polygon = Polygon(coords)
                    features.append({
                        'name': name,
                        'geometry': polygon
                    })
            except AttributeError:
                continue
        
        return gpd.GeoDataFrame(features, crs='EPSG:4326')
    
    def read_shapefile(self, zip_path):
        """Lee shapefile desde archivo ZIP"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Extraer ZIP
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Buscar archivo .shp
            shp_files = [f for f in os.listdir(temp_dir) if f.endswith('.shp')]
            if not shp_files:
                raise ValueError("No se encontró archivo .shp en el ZIP")
            
            shp_path = os.path.join(temp_dir, shp_files[0])
            gdf = gpd.read_file(shp_path)
            
            # Asegurar CRS geográfico
            if gdf.crs is None:
                gdf = gdf.set_crs('EPSG:4326')
            else:
                gdf = gdf.to_crs('EPSG:4326')
            
            return gdf
    
    def calculate_area_hectares(self, gdf):
        """Calcula área en hectáreas"""
        gdf_projected = gdf.to_crs('EPSG:3857')  # Proyección métrica
        gdf_projected['area_hectares'] = gdf_projected.geometry.area / 10000
        return gdf_projected
