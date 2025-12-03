import streamlit as st
import pandas as pd
import numpy as np
import tempfile
import os
import zipfile
import math
from math import log
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff
from io import BytesIO
from datetime import datetime, timedelta
import json
import base64
from scipy import interpolate
import warnings
warnings.filterwarnings('ignore')
# Librerías para análisis geoespacial
import folium
from streamlit_folium import st_folium
from folium.plugins import Fullscreen, MousePosition, HeatMap
import geopandas as gpd
from shapely.geometry import Polygon, Point
import pyproj
from branca.colormap import LinearColormap
import matplotlib.cm as cm
# Manejo de la librería docx con fallback
try:
    from docx import Document
    from docx.shared import Inches
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    st.warning("⚠️ La librería python-docx no está instalada. La generación de informes Word estará deshabilitada.")

# ===============================
# 🌿 CONFIGURACIÓN Y ESTILOS GLOBALES
# ===============================
st.set_page_config(
    page_title="Análisis Integral de Biodiversidad",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

def aplicar_estilos_globales():
    st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stApp {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    }
    .custom-header {
        background: linear-gradient(135deg, #2E8B57 0%, #228B22 100%);
        padding: 3rem 1rem;
        border-radius: 0 0 25px 25px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        position: relative;
        overflow: hidden;
    }
    .custom-header::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="leaf" x="0" y="0" width="20" height="20" patternUnits="userSpaceOnUse"><path d="M10,5 C15,2 18,8 15,12 C12,15 5,15 5,10 C5,5 8,2 10,5 Z" fill="white" opacity="0.1"/></pattern></defs><rect width="100" height="100" fill="url(%23leaf)"/></svg>');
    }
    .custom-header h1 {
        font-size: 2.8rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
    }
    .custom-card {
        background: white;
        padding: 2rem;
        border-radius: 16px;
        box-shadow: 0 6px 20px rgba(0,0,0,0.08);
        border: 1px solid #e9ecef;
        margin-bottom: 2rem;
    }
    .stButton button {
        background: linear-gradient(135deg, #2E8B57 0%, #228B22 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 2rem;
        font-weight: 600;
    }
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 4px solid #2E8B57;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    .download-btn {
        background: linear-gradient(135deg, #1E90FF 0%, #00BFFF 100%) !important;
        margin: 5px;
        padding: 10px 15px;
        border-radius: 8px;
        color: white;
        text-decoration: none;
        display: inline-block;
        font-weight: 600;
        border: none;
        cursor: pointer;
        font-size: 14px;
    }
    .download-btn:hover {
        background: linear-gradient(135deg, #0066CC 0%, #0099FF 100%) !important;
    }
    .warning-box {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
    .contour-plot {
        background: white;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    .map-container {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    /* Nuevos estilos para las capas */
    .layer-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border: 1px solid #e0e0e0;
        transition: all 0.3s ease;
    }
    .layer-card:hover {
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        transform: translateY(-2px);
        border-color: #2E8B57;
    }
    .layer-header {
        display: flex;
        align-items: center;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #f0f0f0;
    }
    .layer-icon {
        font-size: 2rem;
        margin-right: 1rem;
    }
    .layer-title {
        font-size: 1.3rem;
        font-weight: 600;
        color: #2E8B57;
        margin: 0;
    }
    .layer-description {
        color: #666;
        font-size: 0.95rem;
        margin-bottom: 1rem;
    }
    .layer-content {
        margin-top: 1rem;
    }
    .indicator-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 1rem;
        margin-top: 1rem;
    }
    .indicator-item {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        border: 1px solid #e0e0e0;
    }
    .indicator-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #2E8B57;
    }
    .indicator-label {
        font-size: 0.85rem;
        color: #666;
        margin-top: 0.5rem;
    }
    .toggle-switch {
        display: flex;
        align-items: center;
        margin-bottom: 1rem;
    }
    .toggle-label {
        margin-left: 0.5rem;
        font-weight: 500;
    }
    </style>
    """, unsafe_allow_html=True)

def crear_header():
    st.markdown("""
    <div class="custom-header">
        <h1>🌿 Análisis Integral de Biodiversidad</h1>
        <p>Sistema de evaluación ecológica con múltiples indicadores ambientales</p>
    </div>
    """, unsafe_allow_html=True)

# ===============================
# 🧩 CLASE PRINCIPAL DE ANÁLISIS MEJORADA
# ===============================
class AnalizadorBiodiversidad:
    """Analizador integral de biodiversidad para el polígono cargado"""
    def __init__(self):
        self.parametros_ecosistemas = {
            'Bosque Denso Primario': {
                'carbono': {'min': 180, 'max': 320},
                'biodiversidad': 0.85,
                'ndvi_base': 0.85,
                'resiliencia': 0.8,
                'humedad': 0.9
            },
            'Bosque Secundario': {
                'carbono': {'min': 80, 'max': 160},
                'biodiversidad': 0.65,
                'ndvi_base': 0.75,
                'resiliencia': 0.6,
                'humedad': 0.8
            },
            'Bosque Ripario': {
                'carbono': {'min': 120, 'max': 220},
                'biodiversidad': 0.75,
                'ndvi_base': 0.80,
                'resiliencia': 0.7,
                'humedad': 0.95
            },
            'Matorral Denso': {
                'carbono': {'min': 40, 'max': 70},
                'biodiversidad': 0.45,
                'ndvi_base': 0.65,
                'resiliencia': 0.5,
                'humedad': 0.6
            },
            'Matorral Abierto': {
                'carbono': {'min': 20, 'max': 40},
                'biodiversidad': 0.25,
                'ndvi_base': 0.45,
                'resiliencia': 0.4,
                'humedad': 0.5
            },
            'Sabana Arborizada': {
                'carbono': {'min': 25, 'max': 45},
                'biodiversidad': 0.35,
                'ndvi_base': 0.35,
                'resiliencia': 0.5,
                'humedad': 0.4
            },
            'Herbazal Natural': {
                'carbono': {'min': 8, 'max': 18},
                'biodiversidad': 0.15,
                'ndvi_base': 0.25,
                'resiliencia': 0.3,
                'humedad': 0.7
            },
            'Zona de Transición': {
                'carbono': {'min': 15, 'max': 30},
                'biodiversidad': 0.25,
                'ndvi_base': 0.30,
                'resiliencia': 0.4,
                'humedad': 0.6
            },
            'Área de Restauración': {
                'carbono': {'min': 30, 'max': 90},
                'biodiversidad': 0.50,
                'ndvi_base': 0.55,
                'resiliencia': 0.7,
                'humedad': 0.75
            }
        }

    def _calcular_area_hectareas(self, poligono):
        """Calcular área en hectáreas de forma precisa usando proyección UTM"""
        try:
            if poligono.is_valid:
                gdf_temp = gpd.GeoDataFrame([1], geometry=[poligono], crs="EPSG:4326")
                centroid = poligono.centroid
                utm_zone = self._determinar_zona_utm(centroid.y, centroid.x)
                gdf_projected = gdf_temp.to_crs(utm_zone)
                area_m2 = gdf_projected.geometry.area.iloc[0]
                area_hectareas = area_m2 / 10000
                return round(area_hectareas, 2)
            else:
                return self._calcular_area_aproximada(poligono)
        except Exception as e:
            st.warning(f"Usando cálculo aproximado debido a: {str(e)}")
            return self._calcular_area_aproximada(poligono)

    def _determinar_zona_utm(self, lat, lon):
        """Determinar la zona UTM automáticamente"""
        zona = int((lon + 180) / 6) + 1
        hemisferio = 'north' if lat >= 0 else 'south'
        return f"EPSG:326{zona:02d}" if hemisferio == 'north' else f"EPSG:327{zona:02d}"

    def _calcular_area_aproximada(self, poligono):
        """Cálculo aproximado mejorado cuando falla la proyección"""
        try:
            bounds = poligono.bounds
            minx, miny, maxx, maxy = bounds
            lat_media = (miny + maxy) / 2
            metros_por_grado_lat = 111320
            metros_por_grado_lon = 111320 * math.cos(math.radians(lat_media))
            ancho_m = (maxx - minx) * metros_por_grado_lon
            alto_m = (maxy - miny) * metros_por_grado_lat
            area_bbox_m2 = ancho_m * alto_m
            bbox_area_grados = (maxx - minx) * (maxy - miny)
            if bbox_area_grados > 0:
                relacion_aproximada = 0.75
                area_m2_ajustada = area_bbox_m2 * relacion_aproximada
            else:
                area_m2_ajustada = area_bbox_m2
            area_hectareas = area_m2_ajustada / 10000
            return round(max(area_hectareas, 0.01), 2)
        except Exception as e:
            st.error(f"Error en cálculo aproximado: {str(e)}")
            return 1000

    def procesar_poligono(self, gdf, vegetation_type, divisiones=5):
        """Procesar el polígono cargado dividiéndolo en áreas regulares"""
        if gdf is None or gdf.empty:
            return None
        try:
            poligono = gdf.geometry.iloc[0]
            area_hectareas = self._calcular_area_hectareas(poligono)
            areas_data = self._generar_areas_regulares(poligono, divisiones)
            resultados = self._analisis_integral(areas_data, vegetation_type, area_hectareas)
            return {
                'poligono': poligono,
                'area_hectareas': area_hectareas,
                'areas_analisis': areas_data,
                'resultados': resultados,
                'centroide': poligono.centroid,
                'tipo_vegetacion': vegetation_type,
                'bounds': poligono.bounds
            }
        except Exception as e:
            st.error(f"Error procesando polígono: {str(e)}")
            return None

    def _generar_areas_regulares(self, poligono, divisiones):
        """Generar áreas regulares (grid) dentro del polígono"""
        areas = []
        bounds = poligono.bounds
        minx, miny, maxx, maxy = bounds
        delta_x = (maxx - minx) / divisiones
        delta_y = (maxy - miny) / divisiones
        for i in range(divisiones):
            for j in range(divisiones):
                cell_minx = minx + i * delta_x
                cell_maxx = minx + (i + 1) * delta_x
                cell_miny = miny + j * delta_y
                cell_maxy = miny + (j + 1) * delta_y
                cell_polygon = Polygon([
                    (cell_minx, cell_miny),
                    (cell_maxx, cell_miny),
                    (cell_maxx, cell_maxy),
                    (cell_minx, cell_maxy),
                    (cell_minx, cell_miny)
                ])
                if poligono.intersects(cell_polygon):
                    intersection = poligono.intersection(cell_polygon)
                    if not intersection.is_empty:
                        centroid = intersection.centroid
                        areas.append({
                            'id': f"Area_{i+1}_{j+1}",
                            'geometry': intersection,
                            'centroid': centroid,
                            'area_ha': self._calcular_area_hectareas(intersection),
                            'bounds': intersection.bounds
                        })
        return areas

    def _analisis_integral(self, areas_data, vegetation_type, area_total):
        """Realizar análisis integral con todos los indicadores"""
        params = self.parametros_ecosistemas.get(vegetation_type, self.parametros_ecosistemas['Bosque Secundario'])
        carbono_data = []
        vegetacion_data = []
        biodiversidad_data = []
        agua_data = []
        suelo_data = []
        clima_data = []
        presiones_data = []
        conectividad_data = []
        humedad_data = []
        for area in areas_data:
            centroid = area['centroid']
            carbono_info = self._analizar_carbono(area, params, area['area_ha'])
            carbono_data.append(carbono_info)
            vegetacion_info = self._analizar_vegetacion(area, params)
            vegetacion_data.append(vegetacion_info)
            biodiversidad_info = self._analizar_biodiversidad(area, params, area['area_ha'])
            biodiversidad_data.append(biodiversidad_info)
            agua_info = self._analizar_recursos_hidricos(area)
            agua_data.append(agua_info)
            suelo_info = self._analizar_suelo(area)
            suelo_data.append(suelo_info)
            clima_info = self._analizar_clima(area)
            clima_data.append(clima_info)
            presiones_info = self._analizar_presiones(area)
            presiones_data.append(presiones_info)
            conectividad_info = self._analizar_conectividad(area)
            conectividad_data.append(conectividad_info)
            humedad_info = self._analizar_humedad(area, params)
            humedad_data.append(humedad_info)

        summary_metrics = self._calcular_metricas_resumen(
            carbono_data, vegetacion_data, biodiversidad_data, agua_data,
            suelo_data, clima_data, presiones_data, conectividad_data, humedad_data
        )
        return {
            'carbono': carbono_data,
            'vegetacion': vegetacion_data,
            'biodiversidad': biodiversidad_data,
            'agua': agua_data,
            'suelo': suelo_data,
            'clima': clima_data,
            'presiones': presiones_data,
            'conectividad': conectividad_data,
            'humedad': humedad_data,
            'summary_metrics': summary_metrics
        }

    def _analizar_carbono(self, area, params, area_ha):
        """Analizar indicadores de carbono"""
        base_carbon = np.random.uniform(params['carbono']['min'], params['carbono']['max'])
        ndvi = max(0.1, min(0.9, np.random.normal(params['ndvi_base'], 0.08)))
        carbono_ajustado = base_carbon * (0.3 + ndvi * 0.7)
        co2_potencial = carbono_ajustado * 3.67
        return {
            'area': area['id'],
            'carbono_almacenado_tha': round(carbono_ajustado, 1),
            'co2_capturado_tha': round(co2_potencial, 1),
            'co2_total_ton': round(co2_potencial * area_ha, 1),
            'potencial_secuestro': 'Alto' if carbono_ajustado > 100 else 'Medio' if carbono_ajustado > 50 else 'Bajo',
            'ndvi': ndvi,
            'geometry': area['geometry'],
            'centroid': area['centroid']
        }

    def _analizar_vegetacion(self, area, params):
        """Analizar estado de la vegetación"""
        ndvi = max(0.1, min(0.9, np.random.normal(params['ndvi_base'], 0.08)))
        evi = ndvi * 0.9 + np.random.normal(0, 0.03)
        if ndvi > 0.7:
            salud = "Excelente"
            color = '#006400'
        elif ndvi > 0.5:
            salud = "Buena"
            color = '#32CD32'
        elif ndvi > 0.3:
            salud = "Moderada"
            color = '#FFD700'
        else:
            salud = "Degradada"
            color = '#FF4500'
        return {
            'area': area['id'],
            'ndvi': ndvi,
            'evi': evi,
            'salud_vegetacion': salud,
            'color_salud': color,
            'biomasa_tha': round(ndvi * 200 + np.random.uniform(0, 50), 1),
            'geometry': area['geometry'],
            'centroid': area['centroid']
        }

    def _analizar_biodiversidad(self, area, params, area_ha):
        """Analizar indicadores de biodiversidad de forma más realista"""
        factor_area = min(1.0, math.log(area_ha + 1) / 6)
        factor_conectividad = np.random.uniform(0.6, 0.9)
        factor_perturbacion = np.random.uniform(0.7, 0.95)
        if params['biodiversidad'] > 0.7:
            riqueza_base = 150
        elif params['biodiversidad'] > 0.5:
            riqueza_base = 80
        elif params['biodiversidad'] > 0.3:
            riqueza_base = 40
        else:
            riqueza_base = 20
        riqueza_especies = int(riqueza_base * factor_area * factor_conectividad * factor_perturbacion)
        if params['biodiversidad'] > 0.7:
            shannon_base = 3.0
        elif params['biodiversidad'] > 0.5:
            shannon_base = 2.2
        elif params['biodiversidad'] > 0.3:
            shannon_base = 1.5
        else:
            shannon_base = 0.8
        shannon_index = shannon_base * factor_conectividad * factor_perturbacion
        if shannon_index > 2.5:
            estado = "Muy Alto"
            color = '#006400'
        elif shannon_index > 2.0:
            estado = "Alto"
            color = '#32CD32'
        elif shannon_index > 1.5:
            estado = "Moderado"
            color = '#FFD700'
        elif shannon_index > 1.0:
            estado = "Bajo"
            color = '#FFA500'
        else:
            estado = "Muy Bajo"
            color = '#FF4500'
        return {
            'area': area['id'],
            'riqueza_especies': riqueza_especies,
            'indice_shannon': round(shannon_index, 2),
            'estado_conservacion': estado,
            'color_estado': color,
            'factor_area': round(factor_area, 2),
            'factor_conectividad': round(factor_conectividad, 2),
            'geometry': area['geometry'],
            'centroid': area['centroid']
        }

    def _analizar_recursos_hidricos(self, area):
        """Analizar indicadores hídricos"""
        disponibilidad_agua = np.random.uniform(0.2, 0.9)
        if disponibilidad_agua > 0.7:
            estado_agua = "Alta"
            color_agua = '#1E90FF'
        elif disponibilidad_agua > 0.5:
            estado_agua = "Moderada"
            color_agua = '#87CEEB'
        elif disponibilidad_agua > 0.3:
            estado_agua = "Baja"
            color_agua = '#FFA500'
        else:
            estado_agua = "Crítica"
            color_agua = '#FF4500'
        return {
            'area': area['id'],
            'disponibilidad_agua': round(disponibilidad_agua, 2),
            'estado_hidrico': estado_agua,
            'color_estado_agua': color_agua,
            'geometry': area['geometry'],
            'centroid': area['centroid']
        }

    def _analizar_humedad(self, area, params):
        """Analizar índice de humedad"""
        humedad_base = params.get('humedad', 0.5)
        humedad = max(0.1, min(0.95, np.random.normal(humedad_base, 0.1)))
        if humedad > 0.7:
            estado_humedad = "Muy Húmedo"
            color_humedad = '#1E90FF'
        elif humedad > 0.5:
            estado_humedad = "Húmedo"
            color_humedad = '#87CEEB'
        elif humedad > 0.3:
            estado_humedad = "Moderado"
            color_humedad = '#ADD8E6'
        elif humedad > 0.2:
            estado_humedad = "Seco"
            color_humedad = '#FFD700'
        else:
            estado_humedad = "Muy Seco"
            color_humedad = '#FF4500'
        return {
            'area': area['id'],
            'indice_humedad': round(humedad, 2),
            'estado_humedad': estado_humedad,
            'color_humedad': color_humedad,
            'geometry': area['geometry'],
            'centroid': area['centroid']
        }

    def _analizar_suelo(self, area):
        """Analizar calidad del suelo"""
        materia_organica = np.random.uniform(1.0, 8.0)
        salud_suelo = materia_organica / 8.0 * 0.6 + np.random.uniform(0, 0.4)
        if salud_suelo > 0.7:
            estado_suelo = "Excelente"
            color_suelo = '#8B4513'
        elif salud_suelo > 0.5:
            estado_suelo = "Buena"
            color_suelo = '#A0522D'
        elif salud_suelo > 0.3:
            estado_suelo = "Moderada"
            color_suelo = '#CD853F'
        else:
            estado_suelo = "Degradado"
            color_suelo = '#D2691E'
        return {
            'area': area['id'],
            'salud_suelo': round(salud_suelo, 2),
            'estado_suelo': estado_suelo,
            'color_estado_suelo': color_suelo,
            'geometry': area['geometry'],
            'centroid': area['centroid']
        }

    def _analizar_presiones(self, area):
        """Analizar presiones antrópicas"""
        presion_total = np.random.uniform(0, 1)
        if presion_total < 0.3:
            nivel_presion = "Bajo"
            color_presion = '#32CD32'
        elif presion_total < 0.6:
            nivel_presion = "Moderado"
            color_presion = '#FFD700'
        else:
            nivel_presion = "Alto"
            color_presion = '#FF4500'
        return {
            'area': area['id'],
            'presion_total': round(presion_total, 2),
            'nivel_presion': nivel_presion,
            'color_presion': color_presion,
            'geometry': area['geometry'],
            'centroid': area['centroid']
        }

    def _analizar_conectividad(self, area):
        """Analizar conectividad ecológica"""
        conectividad = np.random.uniform(0.2, 0.9)
        if conectividad > 0.7:
            estado_conectividad = "Alta"
            color_conectividad = '#006400'
        elif conectividad > 0.5:
            estado_conectividad = "Moderada"
            color_conectividad = '#32CD32'
        elif conectividad > 0.3:
            estado_conectividad = "Baja"
            color_conectividad = '#FFD700'
        else:
            estado_conectividad = "Crítica"
            color_conectividad = '#FF4500'
        return {
            'area': area['id'],
            'conectividad_total': round(conectividad, 2),
            'estado_conectividad': estado_conectividad,
            'color_conectividad': color_conectividad,
            'geometry': area['geometry'],
            'centroid': area['centroid']
        }

    def _analizar_clima(self, area):
        """Analizar indicadores climáticos"""
        temperatura = np.random.uniform(15, 35)
        vulnerabilidad = (temperatura - 15) / 20
        if vulnerabilidad < 0.3:
            riesgo_climatico = "Bajo"
            color_clima = '#32CD32'
        elif vulnerabilidad < 0.6:
            riesgo_climatico = "Moderado"
            color_clima = '#FFD700'
        else:
            riesgo_climatico = "Alto"
            color_clima = '#FF4500'
        return {
            'area': area['id'],
            'vulnerabilidad_climatica': round(vulnerabilidad, 2),
            'riesgo_climatico': riesgo_climatico,
            'color_riesgo_clima': color_clima,
            'geometry': area['geometry'],
            'centroid': area['centroid']
        }

    def _calcular_metricas_resumen(self, carbono, vegetacion, biodiversidad, agua, suelo, clima, presiones, conectividad, humedad):
        """Calcular métricas resumen para el dashboard"""
        avg_carbono = np.mean([p['co2_total_ton'] for p in carbono])
        avg_biodiversidad = np.mean([p['indice_shannon'] for p in biodiversidad])
        avg_agua = np.mean([p['disponibilidad_agua'] for p in agua])
        avg_suelo = np.mean([p['salud_suelo'] for p in suelo])
        avg_presiones = np.mean([p['presion_total'] for p in presiones])
        avg_conectividad = np.mean([p['conectividad_total'] for p in conectividad])
        avg_humedad = np.mean([p['indice_humedad'] for p in humedad])
        return {
            'carbono_total_co2_ton': round(avg_carbono * len(carbono), 1),
            'indice_biodiversidad_promedio': round(avg_biodiversidad, 2),
            'disponibilidad_agua_promedio': round(avg_agua, 2),
            'salud_suelo_promedio': round(avg_suelo, 2),
            'presion_antropica_promedio': round(avg_presiones, 2),
            'conectividad_promedio': round(avg_conectividad, 2),
            'indice_humedad_promedio': round(avg_humedad, 2),
            'areas_analizadas': len(carbono),
            'estado_general': self._calcular_estado_general(avg_biodiversidad, avg_presiones, avg_conectividad)
        }

    def _calcular_estado_general(self, biodiversidad, presiones, conectividad):
        score = (biodiversidad / 3.0 * 0.4 + (1 - presiones) * 0.4 + conectividad * 0.2)
        if score > 0.7: return "Excelente"
        elif score > 0.5: return "Bueno"
        elif score > 0.3: return "Moderado"
        else: return "Crítico"

# ===============================
# 🗺️ FUNCIONES DE MAPAS MEJORADAS
# ===============================
def crear_mapa_base():
    """Crear mapa base con ESRI Satellite"""
    m = folium.Map(location=[-14.0, -60.0], zoom_start=4, tiles=None)
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Satélite ESRI'
    ).add_to(m)
    folium.TileLayer('OpenStreetMap').add_to(m)
    folium.LayerControl().add_to(m)
    return m

def crear_mapa_para_capa(gdf, datos_capa, config_capa):
    """Crear un mapa específico para una capa"""
    if gdf is None or datos_capa is None:
        return crear_mapa_base()
    try:
        centroide = gdf.geometry.iloc[0].centroid
        bounds = gdf.geometry.iloc[0].bounds
        m = folium.Map(
            location=[centroide.y, centroide.x], 
            zoom_start=12, 
            tiles=None,
            control_scale=True
        )
        # Agregar ESRI Satellite como capa base
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='Satélite ESRI',
            overlay=False
        ).add_to(m)
        # Agregar áreas de análisis
        for area_data in datos_capa:
            valor = area_data[config_capa['columna']]
            # Normalizar valor para el color
            valor_norm = (valor - config_capa['rango'][0]) / (config_capa['rango'][1] - config_capa['rango'][0])
            valor_norm = max(0, min(1, valor_norm))
            # Determinar color basado en el valor normalizado
            num_colores = len(config_capa['colores'])
            color_idx = min(num_colores - 1, int(valor_norm * num_colores))
            color = config_capa['colores'][color_idx] if num_colores > 0 else '#808080'
            # Crear tooltip
            tooltip_text = f"""
            <div style='font-family: Arial; font-size: 12px;'>
                <b>{config_capa['nombre']}</b><br>
                Área: {area_data['area']}<br>
                Valor: {valor:.2f}<br>
                Estado: {area_data.get('estado_conservacion', area_data.get('salud_vegetacion', area_data.get('estado_hidrico', 'N/A')))}
            </div>
            """
            folium.GeoJson(
                area_data['geometry'],
                style_function=lambda feature, color=color: {
                    'fillColor': color,
                    'color': '#000000',
                    'weight': 1,
                    'fillOpacity': 0.7,
                    'opacity': 0.5
                },
                tooltip=folium.Tooltip(tooltip_text, sticky=True)
            ).add_to(m)
        # Agregar el polígono principal
        folium.GeoJson(
            gdf.geometry.iloc[0],
            style_function=lambda x: {
                'fillColor': 'transparent',
                'color': '#FF0000',
                'weight': 3,
                'fillOpacity': 0
            },
            name='Polígono de estudio'
        ).add_to(m)
        # Agregar leyenda (versión segura)
        agregar_leyenda_al_mapa(m, config_capa)
        # Ajustar zoom
        m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])
        # Agregar controles
        Fullscreen().add_to(m)
        MousePosition().add_to(m)
        folium.LayerControl().add_to(m)
        return m
    except Exception as e:
        st.error(f"Error creando mapa para capa {config_capa['nombre']}: {str(e)}")
        return crear_mapa_base()

# ✅ FUNCIÓN CORREGIDA: usar LinearColormap (seguro con Streamlit)
def agregar_leyenda_al_mapa(mapa, config_capa):
    """Agregar leyenda segura usando LinearColormap (compatible con Streamlit)"""
    try:
        colores = config_capa['colores']
        rango_min, rango_max = config_capa['rango']
        nombre = config_capa['nombre']

        # Asegurar que haya al menos 2 colores para LinearColormap
        if len(colores) == 1:
            colores = [colores[0], colores[0]]
        elif len(colores) == 0:
            colores = ['#cccccc', '#666666']

        # Crear colormap de branca
        colormap = LinearColormap(
            colors=colores,
            vmin=rango_min,
            vmax=rango_max,
            caption=nombre
        )
        mapa.add_child(colormap)
    except Exception as e:
        st.warning(f"No se pudo agregar leyenda segura: {str(e)}")

# ===============================
# 📊 FUNCIONES DE VISUALIZACIÓN MEJORADAS
# ===============================
def crear_grafico_barras_horizontales(datos, titulo, columna_valor, columna_etiqueta):
    """Crear gráfico de barras horizontales para comparar áreas"""
    df = pd.DataFrame(datos)
    df = df.sort_values(by=columna_valor, ascending=True)
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df[columna_etiqueta],
        x=df[columna_valor],
        orientation='h',
        marker=dict(
            color=df[columna_valor],
            colorscale='Viridis',
            showscale=True
        ),
        text=df[columna_valor].round(2),
        textposition='auto'
    ))
    fig.update_layout(
        title=titulo,
        xaxis_title=columna_valor,
        yaxis_title="Áreas",
        template='plotly_white',
        height=max(300, len(datos) * 30)
    )
    return fig

def crear_grafico_distribucion(datos, titulo, columna_valor):
    """Crear gráfico de distribución (histograma + boxplot)"""
    valores = [d[columna_valor] for d in datos]
    fig = go.Figure()
    # Histograma
    fig.add_trace(go.Histogram(
        x=valores,
        nbinsx=20,
        name="Distribución",
        marker_color='#2E8B57',
        opacity=0.7
    ))
    # Boxplot
    fig.add_trace(go.Box(
        x=valores,
        name="Resumen",
        boxpoints='outliers',
        marker_color='#228B22',
        line_color='#006400'
    ))
    fig.update_layout(
        title=f"{titulo} - Distribución",
        xaxis_title=columna_valor,
        yaxis_title="Frecuencia",
        template='plotly_white',
        showlegend=False,
        height=300
    )
    return fig

# ===============================
# 📁 MANEJO DE ARCHIVOS Y DESCARGAS
# ===============================
def procesar_archivo_cargado(uploaded_file):
    """Procesar archivo KML/ZIP cargado"""
    try:
        if uploaded_file.name.endswith('.kml'):
            gdf = gpd.read_file(uploaded_file, driver='KML')
            return gdf
        elif uploaded_file.name.endswith('.zip'):
            with tempfile.TemporaryDirectory() as tmpdir:
                with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
                    zip_ref.extractall(tmpdir)
                shp_files = [f for f in os.listdir(tmpdir) if f.endswith('.shp')]
                if shp_files:
                    gdf = gpd.read_file(os.path.join(tmpdir, shp_files[0]))
                    return gdf
        return None
    except Exception as e:
        st.error(f"Error procesando archivo: {str(e)}")
        return None

def crear_boton_descarga(data, filename, button_text, file_type):
    """Crear botón de descarga para diferentes tipos de archivos"""
    try:
        if file_type == 'geojson':
            b64 = base64.b64encode(data.encode()).decode()
            href = f'<a href="data:application/json;base64,{b64}" download="{filename}" class="download-btn">📥 {button_text}</a>'
        elif file_type == 'word':
            b64 = base64.b64encode(data.getvalue()).decode()
            href = f'<a href="data:application/vnd.openxmlformats-officedocument.wordprocessingml.document;base64,{b64}" download="{filename}" class="download-btn">📥 {button_text}</a>'
        elif file_type == 'csv':
            b64 = base64.b64encode(data.encode()).decode()
            href = f'<a href="data:file/csv;base64,{b64}" download="{filename}" class="download-btn">📥 {button_text}</a>'
        st.markdown(f'<div style="margin: 10px 0;">{href}</div>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error creando botón de descarga: {str(e)}")

# ===============================
# 🎨 COMPONENTES DE INTERFAZ MEJORADOS
# ===============================
def crear_capa_ui(capa_key, capa_config, datos, resultados, gdf):
    """Crear interfaz de usuario para una capa específica"""
    if capa_key not in datos:
        return
    st.markdown(f"""
    <div class="layer-card">
        <div class="layer-header">
            <div class="layer-icon">{capa_config['icono']}</div>
            <div>
                <h3 class="layer-title">{capa_config['nombre']}</h3>
                <p class="layer-description">{capa_config['descripcion']}</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    # Calcular estadísticas
    valores = [d[capa_config['columna']] for d in datos[capa_key]]
    promedio = np.mean(valores)
    maximo = np.max(valores)
    minimo = np.min(valores)
    estado = datos[capa_key][0].get('estado_conservacion', 
                                   datos[capa_key][0].get('salud_vegetacion',
                                   datos[capa_key][0].get('estado_hidrico',
                                   datos[capa_key][0].get('estado_suelo',
                                   datos[capa_key][0].get('nivel_presion',
                                   datos[capa_key][0].get('estado_conectividad',
                                   datos[capa_key][0].get('estado_humedad', 'N/A')))))))
    # Mostrar estadísticas
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Promedio", f"{promedio:.2f}")
    with col2:
        st.metric("Máximo", f"{maximo:.2f}")
    with col3:
        st.metric("Mínimo", f"{minimo:.2f}")
    with col4:
        st.metric("Estado", estado)
    # Crear pestañas para esta capa
    tab1, tab2, tab3 = st.tabs(["🗺️ Mapa", "📊 Gráficos", "📁 Datos"])
    with tab1:
        # Crear y mostrar mapa específico para esta capa
        mapa_capa = crear_mapa_para_capa(gdf, datos[capa_key], capa_config)
        st_folium(mapa_capa, width=800, height=500, key=f"mapa_{capa_key}")
    with tab2:
        # Gráfico de barras horizontales
        fig_barras = crear_grafico_barras_horizontales(
            datos[capa_key],
            f"Comparación por Área - {capa_config['nombre']}",
            capa_config['columna'],
            'area'
        )
        st.plotly_chart(fig_barras, use_container_width=True)
        # Gráfico de distribución
        fig_dist = crear_grafico_distribucion(
            datos[capa_key],
            capa_config['nombre'],
            capa_config['columna']
        )
        st.plotly_chart(fig_dist, use_container_width=True)
    with tab3:
        # Mostrar tabla de datos
        df_capa = pd.DataFrame(datos[capa_key])
        columnas_a_mostrar = ['area', capa_config['columna']] + [c for c in df_capa.columns if 'estado' in c or 'color' in c]
        columnas_a_mostrar = [c for c in columnas_a_mostrar if c in df_capa.columns]
        st.dataframe(
            df_capa[columnas_a_mostrar].style.format({
                capa_config['columna']: '{:.2f}'
            }),
            use_container_width=True,
            height=300
        )
        # Botones de descarga
        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            csv = df_capa.to_csv(index=False)
            crear_boton_descarga(csv, f"datos_{capa_key}.csv", f"Descargar CSV {capa_config['nombre']}", 'csv')
        with col_dl2:
            json_str = df_capa.to_json(orient='records', indent=2)
            crear_boton_descarga(json_str, f"datos_{capa_key}.json", f"Descargar JSON {capa_config['nombre']}", 'geojson')
    st.markdown("---")

# ===============================
# 🚀 CONFIGURACIÓN PRINCIPAL
# ===============================
def initialize_session_state():
    if 'analysis_complete' not in st.session_state:
        st.session_state.analysis_complete = False
    if 'results' not in st.session_state:
        st.session_state.results = None
    if 'poligono_data' not in st.session_state:
        st.session_state.poligono_data = None
    if 'file_processed' not in st.session_state:
        st.session_state.file_processed = False
    if 'analyzer' not in st.session_state:
        st.session_state.analyzer = AnalizadorBiodiversidad()
    if 'capas_config' not in st.session_state:
        st.session_state.capas_config = {
            'biodiversidad': {
                'nombre': '🦋 Biodiversidad',
                'descripcion': 'Índice de Shannon que mide la diversidad de especies en el área',
                'icono': '🦋',
                'columna': 'indice_shannon',
                'colores': ['#FF4500', '#FFD700', '#32CD32', '#006400'],
                'rango': (0, 3.0)
            },
            'carbono': {
                'nombre': '🌳 Carbono',
                'descripcion': 'Potencial de captura de carbono en toneladas de CO₂ equivalente',
                'icono': '🌳',
                'columna': 'co2_total_ton',
                'colores': ['#ffffcc', '#c2e699', '#78c679', '#238443', '#00441b'],
                'rango': (0, 50000)
            },
            'vegetacion': {
                'nombre': '🌿 Vegetación',
                'descripcion': 'Índice de vegetación de diferencia normalizada (NDVI)',
                'icono': '🌿',
                'columna': 'ndvi',
                'colores': ['#FF4500', '#FFD700', '#32CD32', '#006400'],
                'rango': (0, 1.0)
            },
            'humedad': {
                'nombre': '💧 Humedad',
                'descripcion': 'Índice de humedad del suelo y disponibilidad hídrica',
                'icono': '💧',
                'columna': 'indice_humedad',
                'colores': ['#FF4500', '#FFD700', '#ADD8E6', '#87CEEB', '#1E90FF'],
                'rango': (0, 1.0)
            },
            'agua': {
                'nombre': '💦 Recursos Hídricos',
                'descripcion': 'Disponibilidad de agua y estado de los recursos hídricos',
                'icono': '💦',
                'columna': 'disponibilidad_agua',
                'colores': ['#FF4500', '#FFD700', '#87CEEB', '#1E90FF'],
                'rango': (0, 1.0)
            },
            'suelo': {
                'nombre': '🌱 Suelo',
                'descripcion': 'Salud y calidad del suelo, materia orgánica',
                'icono': '🌱',
                'columna': 'salud_suelo',
                'colores': ['#D2691E', '#CD853F', '#A0522D', '#8B4513'],
                'rango': (0, 1.0)
            },
            'conectividad': {
                'nombre': '🔗 Conectividad',
                'descripcion': 'Conectividad ecológica y fragmentación del hábitat',
                'icono': '🔗',
                'columna': 'conectividad_total',
                'colores': ['#FF4500', '#FFD700', '#32CD32', '#006400'],
                'rango': (0, 1.0)
            }
        }

def sidebar_config():
    with st.sidebar:
        st.markdown("""
        <div style='text-align: center; margin-bottom: 2rem; padding: 1rem; background: linear-gradient(135deg, #2E8B57 0%, #228B22 100%); border-radius: 12px;'>
            <h2 style='color: white; margin-bottom: 0;'>🌿</h2>
            <h3 style='color: white; margin: 0;'>Análisis de Biodiversidad</h3>
        </div>
        """, unsafe_allow_html=True)
        st.header("🗺️ Cargar Polígono")
        uploaded_file = st.file_uploader("Sube tu archivo territorial", type=['kml', 'zip'])
        if uploaded_file is not None and not st.session_state.file_processed:
            with st.spinner("Procesando archivo..."):
                gdf = procesar_archivo_cargado(uploaded_file)
                if gdf is not None:
                    st.session_state.poligono_data = gdf
                    st.session_state.file_processed = True
                    st.session_state.analysis_complete = False
                    st.success(f"✅ Polígono cargado: {uploaded_file.name}")
                    st.rerun()
        st.markdown("---")
        st.header("📊 Configuración de Análisis")
        vegetation_type = st.selectbox("🌿 Tipo de vegetación predominante", [
            'Bosque Denso Primario', 'Bosque Secundario', 'Bosque Ripario',
            'Matorral Denso', 'Matorral Abierto', 'Sabana Arborizada',
            'Herbazal Natural', 'Zona de Transición', 'Área de Restauración'
        ])
        divisiones = st.slider("🔲 Divisiones del área", 3, 8, 5,
                             help="Número de divisiones para crear la grilla de análisis")
        return uploaded_file, vegetation_type, divisiones

# ===============================
# 🎯 APLICACIÓN PRINCIPAL
# ===============================
def main():
    aplicar_estilos_globales()
    crear_header()
    initialize_session_state()
    uploaded_file, vegetation_type, divisiones = sidebar_config()

    # Verificar si hay polígono cargado
    if st.session_state.poligono_data is not None:
        gdf = st.session_state.poligono_data
        poligono = gdf.geometry.iloc[0]
        area_ha = st.session_state.analyzer._calcular_area_hectareas(poligono)

        # Mostrar información del área
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        st.subheader("📐 Información del Área de Estudio")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Área aproximada", f"{area_ha:,.2f} ha")
        with col2:
            st.metric("Tipo de vegetación", vegetation_type)
        with col3:
            st.metric("Áreas de análisis", f"{divisiones}x{divisiones}")
        st.markdown('</div>', unsafe_allow_html=True)

    # Botón para ejecutar análisis
    if st.session_state.poligono_data is not None and not st.session_state.analysis_complete:
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        if st.button("🚀 EJECUTAR ANÁLISIS INTEGRAL", type="primary", use_container_width=True):
            with st.spinner("Realizando análisis integral de biodiversidad..."):
                resultados = st.session_state.analyzer.procesar_poligono(
                    st.session_state.poligono_data, vegetation_type, divisiones
                )
                if resultados:
                    st.session_state.results = resultados
                    st.session_state.analysis_complete = True
                    st.success("✅ Análisis completado exitosamente!")
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # Mostrar resultados si el análisis está completo
    if st.session_state.analysis_complete and st.session_state.results:
        resultados = st.session_state.results
        summary = resultados['resultados']['summary_metrics']

        # SECCIÓN: RESUMEN EJECUTIVO
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        st.subheader("📊 Resumen Ejecutivo")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🌳 Carbono Total", f"{summary['carbono_total_co2_ton']:,} ton CO₂")
        with col2:
            st.metric("🦋 Biodiversidad", f"{summary['indice_biodiversidad_promedio']}")
        with col3:
            st.metric("💧 Índice Humedad", f"{summary['indice_humedad_promedio']}")
        with col4:
            st.metric("📈 Estado General", summary['estado_general'])
        col5, col6, col7, col8 = st.columns(4)
        with col5:
            st.metric("🌿 NDVI Promedio", f"{resultados['resultados']['vegetacion'][0]['ndvi']:.2f}")
        with col6:
            st.metric("💦 Disponibilidad Agua", f"{summary['disponibilidad_agua_promedio']}")
        with col7:
            st.metric("🔗 Conectividad", f"{summary['conectividad_promedio']}")
        with col8:
            st.metric("🔍 Áreas Analizadas", summary['areas_analizadas'])
        st.markdown('</div>', unsafe_allow_html=True)

        # SECCIÓN: TODAS LAS CAPAS
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        st.subheader("🗺️ Capas de Análisis")
        st.markdown("Selecciona cada capa para ver detalles, mapas y gráficos específicos.")
        # Crear un contenedor para todas las capas
        for capa_key, capa_config in st.session_state.capas_config.items():
            crear_capa_ui(
                capa_key,
                capa_config,
                resultados['resultados'],
                resultados,
                st.session_state.poligono_data
            )
        st.markdown('</div>', unsafe_allow_html=True)

        # SECCIÓN: DESCARGAS COMPLETAS
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        st.subheader("📥 Descargas Completas")
        col_dl1, col_dl2, col_dl3 = st.columns(3)
        with col_dl1:
            st.markdown("**🗺️ Datos Geoespaciales**")
            # Preparar datos completos para descarga
            todos_datos = []
            for i in range(len(resultados['resultados']['vegetacion'])):
                area_id = resultados['resultados']['vegetacion'][i]['area']
                geometry = None
                for area in resultados['areas_analisis']:
                    if area['id'] == area_id:
                        geometry = area['geometry']
                        break
                if geometry:
                    area_data = {
                        'area': area_id,
                        'geometry': geometry,
                        'ndvi': resultados['resultados']['vegetacion'][i]['ndvi'],
                        'salud_vegetacion': resultados['resultados']['vegetacion'][i]['salud_vegetacion'],
                        'co2_total_ton': resultados['resultados']['carbono'][i]['co2_total_ton'],
                        'indice_shannon': resultados['resultados']['biodiversidad'][i]['indice_shannon'],
                        'disponibilidad_agua': resultados['resultados']['agua'][i]['disponibilidad_agua'],
                        'salud_suelo': resultados['resultados']['suelo'][i]['salud_suelo'],
                        'conectividad_total': resultados['resultados']['conectividad'][i]['conectividad_total'],
                        'indice_humedad': resultados['resultados']['humedad'][i]['indice_humedad'],
                        'presion_total': resultados['resultados']['presiones'][i]['presion_total']
                    }
                    todos_datos.append(area_data)
            if todos_datos:
                gdf_completo = gpd.GeoDataFrame(todos_datos, geometry='geometry')
                gdf_completo.crs = "EPSG:4326"
                geojson_str = gdf_completo.to_json()
                crear_boton_descarga(
                    geojson_str,
                    "datos_completos.geojson",
                    "Descargar GeoJSON Completo",
                    'geojson'
                )
        with col_dl2:
            st.markdown("**📊 Datos Tabulares**")
            # CSV completo
            datos_combinados = []
            for i in range(len(resultados['resultados']['vegetacion'])):
                combo = {
                    'area': resultados['resultados']['vegetacion'][i]['area'],
                    'ndvi': resultados['resultados']['vegetacion'][i]['ndvi'],
                    'co2_total_ton': resultados['resultados']['carbono'][i]['co2_total_ton'],
                    'indice_shannon': resultados['resultados']['biodiversidad'][i]['indice_shannon'],
                    'indice_humedad': resultados['resultados']['humedad'][i]['indice_humedad'],
                    'disponibilidad_agua': resultados['resultados']['agua'][i]['disponibilidad_agua'],
                    'salud_suelo': resultados['resultados']['suelo'][i]['salud_suelo'],
                    'conectividad_total': resultados['resultados']['conectividad'][i]['conectividad_total'],
                    'presion_total': resultados['resultados']['presiones'][i]['presion_total']
                }
                datos_combinados.append(combo)
            df_completo = pd.DataFrame(datos_combinados)
            csv = df_completo.to_csv(index=False)
            crear_boton_descarga(
                csv,
                "datos_analisis_completo.csv",
                "Descargar CSV Completo",
                'csv'
            )
        with col_dl3:
            st.markdown("**📄 Informes**")
            # Informe en texto
            informe_texto = f"""
INFORME DE ANÁLISIS DE BIODIVERSIDAD
Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}
RESUMEN EJECUTIVO:
Área analizada: {resultados['area_hectareas']:,.2f} ha
Tipo de vegetación: {resultados['tipo_vegetacion']}
Estado general: {summary['estado_general']}
INDICADORES PRINCIPALES:
- Carbono total: {summary['carbono_total_co2_ton']:,} ton CO₂
- Biodiversidad: {summary['indice_biodiversidad_promedio']}
- Índice de humedad: {summary['indice_humedad_promedio']}
- Disponibilidad agua: {summary['disponibilidad_agua_promedio']}
- Salud suelo: {summary['salud_suelo_promedio']}
- Presión antrópica: {summary['presion_antropica_promedio']}
- Conectividad: {summary['conectividad_promedio']}
Áreas analizadas: {summary['areas_analizadas']}
"""
            crear_boton_descarga(
                informe_texto,
                "informe_biodiversidad.txt",
                "Descargar Informe Texto",
                'csv'
            )
        st.markdown('</div>', unsafe_allow_html=True)
    elif st.session_state.poligono_data is None or st.session_state.poligono_data.empty:
        # Pantalla de inicio
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        st.markdown("""
        ## 👋 ¡Bienvenido al Análisis Integral de Biodiversidad!
        ### 🌿 Sistema de Evaluación Ecológica Mejorado
        **Características de la nueva interfaz:**
        - 🎯 **Sin pestañas** - Todas las capas visibles en la página principal
        - 🗺️ **Mapas individuales** - Cada capa tiene su propio mapa interactivo
        - 📊 **Gráficos específicos** - Visualizaciones adaptadas a cada indicador
        - 📱 **Interfaz limpia** - Diseño moderno y fácil de entender
        - 🔍 **Navegación simple** - Scroll para explorar todas las capas
        **Capas disponibles:**
        1. 🦋 **Biodiversidad** - Índice de Shannon y riqueza de especies
        2. 🌳 **Carbono** - Potencial de captura en toneladas de CO₂
        3. 🌿 **Vegetación** - NDVI y salud vegetal
        4. 💧 **Humedad** - Índice de humedad del suelo
        5. 💦 **Recursos Hídricos** - Disponibilidad de agua
        6. 🌱 **Suelo** - Salud y calidad del suelo
        7. 🔗 **Conectividad** - Conectividad ecológica
        **¡Comienza cargando tu archivo en el sidebar!** ←
        """)
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
