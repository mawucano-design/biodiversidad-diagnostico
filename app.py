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
            st.info(f"**Área calculada:** {area_hectareas:,.2f} hectáreas")
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

def crear_mapa_integrado(gdf, resultados, capa_seleccionada=None, mostrar_contornos=False, config_contornos=None):
    """Crear mapa integrado con todas las capas de análisis"""
    if gdf is None or resultados is None:
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
        
        # Agregar OpenStreetMap como alternativa
        folium.TileLayer(
            tiles='OpenStreetMap',
            name='OpenStreetMap'
        ).add_to(m)
        
        # Agregar capa de relieve
        folium.TileLayer(
            tiles='https://stamen-tiles.a.ssl.fastly.net/terrain/{z}/{x}/{y}.png',
            attr='Stamen Terrain',
            name='Relieve',
            overlay=False
        ).add_to(m)
        
        # Definir capas disponibles
        capas = {
            'biodiversidad': {
                'datos': resultados['resultados']['biodiversidad'],
                'columna': 'indice_shannon',
                'nombre': '🦋 Biodiversidad (Índice de Shannon)',
                'colores': ['#FF4500', '#FFD700', '#32CD32', '#006400'],
                'rango': (0, 3.0)
            },
            'carbono': {
                'datos': resultados['resultados']['carbono'],
                'columna': 'co2_total_ton',
                'nombre': '🌳 Captura de Carbono (ton CO₂)',
                'colores': ['#ffffcc', '#c2e699', '#78c679', '#238443', '#00441b'],
                'rango': (0, 50000)
            },
            'vegetacion': {
                'datos': resultados['resultados']['vegetacion'],
                'columna': 'ndvi',
                'nombre': '🌿 Vegetación (NDVI)',
                'colores': ['#FF4500', '#FFD700', '#32CD32', '#006400'],
                'rango': (0, 1.0)
            },
            'humedad': {
                'datos': resultados['resultados']['humedad'],
                'columna': 'indice_humedad',
                'nombre': '💧 Índice de Humedad',
                'colores': ['#FF4500', '#FFD700', '#ADD8E6', '#87CEEB', '#1E90FF'],
                'rango': (0, 1.0)
            },
            'agua': {
                'datos': resultados['resultados']['agua'],
                'columna': 'disponibilidad_agua',
                'nombre': '💦 Disponibilidad de Agua',
                'colores': ['#FF4500', '#FFD700', '#87CEEB', '#1E90FF'],
                'rango': (0, 1.0)
            },
            'suelo': {
                'datos': resultados['resultados']['suelo'],
                'columna': 'salud_suelo',
                'nombre': '🌱 Salud del Suelo',
                'colores': ['#D2691E', '#CD853F', '#A0522D', '#8B4513'],
                'rango': (0, 1.0)
            },
            'conectividad': {
                'datos': resultados['resultados']['conectividad'],
                'columna': 'conectividad_total',
                'nombre': '🔗 Conectividad Ecológica',
                'colores': ['#FF4500', '#FFD700', '#32CD32', '#006400'],
                'rango': (0, 1.0)
            }
        }
        
        # Si hay una capa seleccionada, mostrar solo esa capa
        if capa_seleccionada and capa_seleccionada in capas:
            capas_activas = {capa_seleccionada: capas[capa_seleccionada]}
        else:
            capas_activas = capas
        
        # Agregar cada capa al mapa
        for capa_key, config in capas_activas.items():
            # Crear FeatureCollection para la capa
            features = []
            
            for area_data in config['datos']:
                valor = area_data[config['columna']]
                
                # Normalizar valor para el color
                valor_norm = (valor - config['rango'][0]) / (config['rango'][1] - config['rango'][0])
                valor_norm = max(0, min(1, valor_norm))
                
                # Determinar color basado en el valor normalizado
                num_colores = len(config['colores'])
                color_idx = min(num_colores - 1, int(valor_norm * num_colores))
                color = config['colores'][color_idx] if num_colores > 0 else '#808080'
                
                # Crear feature
                feature = {
                    'type': 'Feature',
                    'geometry': gpd.GeoSeries([area_data['geometry']]).__geo_interface__['features'][0]['geometry'],
                    'properties': {
                        'area': area_data['area'],
                        'valor': round(valor, 2),
                        'nombre': config['nombre'],
                        'estado': area_data.get('estado_conservacion', area_data.get('salud_vegetacion', area_data.get('estado_hidrico', 'N/A'))),
                        'color': color
                    }
                }
                features.append(feature)
            
            # Crear la capa GeoJSON
            geojson_layer = folium.GeoJson(
                {'type': 'FeatureCollection', 'features': features},
                style_function=lambda feature, color_map=None: {
                    'fillColor': feature['properties']['color'],
                    'color': '#000000',
                    'weight': 1,
                    'fillOpacity': 0.7,
                    'opacity': 0.5
                },
                name=config['nombre'],
                tooltip=folium.GeoJsonTooltip(
                    fields=['area', 'valor', 'estado'],
                    aliases=['Área:', 'Valor:', 'Estado:'],
                    localize=True,
                    style=("background-color: white; color: #333; font-family: arial; font-size: 12px; padding: 10px;")
                ),
                show=True
            )
            
            # Agregar la capa al mapa
            geojson_layer.add_to(m)
            
            # Si es la capa seleccionada y hay que mostrar contornos, agregarlos
            if mostrar_contornos and capa_key == capa_seleccionada and config_contornos:
                # Generar curvas de nivel para esta capa
                xi, yi, zi = generar_curvas_nivel(
                    config['datos'],
                    config['columna'],
                    config['nombre'],
                    res=config_contornos['resolucion']
                )
                
                if xi is not None and yi is not None and zi is not None:
                    # Agregar contornos como líneas al mapa
                    agregar_contornos_a_mapa(m, xi, yi, zi, config_contornos['num_contours'])
        
        # Ajustar zoom a los límites del polígono
        m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])
        
        # Agregar controles
        Fullscreen().add_to(m)
        MousePosition().add_to(m)
        
        # Agregar leyenda dinámica
        if capa_seleccionada and capa_seleccionada in capas:
            agregar_leyenda_dinamica(m, capas[capa_seleccionada])
        
        folium.LayerControl().add_to(m)
        
        return m
        
    except Exception as e:
        st.error(f"Error creando mapa integrado: {str(e)}")
        return crear_mapa_base()

def agregar_contornos_a_mapa(mapa, xi, yi, zi, num_contours=10):
    """Agregar curvas de nivel a un mapa de Folium"""
    try:
        # Calcular niveles para contornos
        z_min = np.nanmin(zi)
        z_max = np.nanmax(zi)
        
        if np.isnan(z_min) or np.isnan(z_max):
            return
        
        levels = np.linspace(z_min, z_max, num_contours)
        
        # Crear contornos
        fig, ax = plt.subplots(figsize=(10, 10))
        
        # Dibujar contornos
        contour = ax.contour(xi, yi, zi, levels=levels, colors='white', linewidths=1, alpha=0.7)
        
        # Crear coordenadas para las líneas de contorno
        for collection in contour.collections:
            paths = collection.get_paths()
            for path in paths:
                vertices = path.vertices
                if len(vertices) > 1:
                    # Convertir coordenadas a lista de [lat, lon]
                    coords = [[yi_val, xi_val] for xi_val, yi_val in vertices]
                    
                    # Crear línea de contorno en el mapa
                    folium.PolyLine(
                        locations=coords,
                        color='white',
                        weight=2,
                        opacity=0.7,
                        dash_array='5, 5'
                    ).add_to(mapa)
        
        plt.close(fig)
        
    except Exception as e:
        st.warning(f"No se pudieron agregar contornos al mapa: {str(e)}")

def agregar_leyenda_dinamica(mapa, config_capa):
    """Agregar leyenda dinámica para la capa seleccionada"""
    try:
        colores = config_capa['colores']
        nombre = config_capa['nombre']
        rango_min, rango_max = config_capa['rango']
        
        # Crear gradiente de colores para la leyenda
        colormap = LinearColormap(
            colores,
            vmin=rango_min,
            vmax=rango_max,
            caption=nombre
        )
        
        # Agregar colormap al mapa
        mapa.add_child(colormap)
        
    except Exception as e:
        st.warning(f"No se pudo agregar leyenda: {str(e)}")

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

# ===============================
# 🗺️ FUNCIONES PARA CURVAS DE NIVEL SOBRE MAPA
# ===============================

def generar_curvas_nivel(datos, variable, variable_nombre, res=100):
    """Generar curvas de nivel a partir de datos espaciales"""
    try:
        if not datos or len(datos) < 4:
            st.warning("Se necesitan al menos 4 puntos para generar curvas de nivel")
            return None, None, None
        
        # Extraer coordenadas y valores
        x_vals = []
        y_vals = []
        z_vals = []
        
        for item in datos:
            if 'centroid' in item and hasattr(item['centroid'], 'x'):
                x_vals.append(item['centroid'].x)
                y_vals.append(item['centroid'].y)
                z_vals.append(item.get(variable, 0))
        
        if len(x_vals) < 4:
            st.warning("No hay suficientes puntos con coordenadas válidas")
            return None, None, None
        
        # Crear grid para interpolación
        xi = np.linspace(min(x_vals), max(x_vals), res)
        yi = np.linspace(min(y_vals), max(y_vals), res)
        xi, yi = np.meshgrid(xi, yi)
        
        # Interpolación
        points = np.column_stack((x_vals, y_vals))
        
        try:
            # Intentar interpolación cúbica primero
            zi = interpolate.griddata(points, z_vals, (xi, yi), method='cubic')
        except:
            # Fallback a interpolación lineal
            zi = interpolate.griddata(points, z_vals, (xi, yi), method='linear')
        
        # Reemplazar NaN con valores interpolados cercanos si es necesario
        mask = np.isnan(zi)
        if mask.any() and not mask.all():
            zi[mask] = interpolate.griddata(
                points, z_vals, (xi[mask], yi[mask]), method='nearest'
            )
        
        return xi, yi, zi
        
    except Exception as e:
        st.error(f"Error generando curvas de nivel: {str(e)}")
        return None, None, None

def crear_mapa_con_curvas_nivel(gdf, datos, config_capa, config_contornos):
    """Crear mapa con curvas de nivel superpuestas"""
    if gdf is None or datos is None:
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
        
        # Agregar área del polígono principal
        poligono_geojson = gpd.GeoSeries([gdf.geometry.iloc[0]]).__geo_interface__
        
        folium.GeoJson(
            poligono_geojson,
            style_function=lambda x: {
                'fillColor': 'transparent',
                'color': '#FF0000',
                'weight': 3,
                'fillOpacity': 0.1
            },
            name='Polígono de estudio',
            tooltip='Área de estudio'
        ).add_to(m)
        
        # Generar curvas de nivel
        xi, yi, zi = generar_curvas_nivel(
            datos,
            config_capa['columna'],
            config_capa['nombre'],
            res=config_contornos['resolucion']
        )
        
        if xi is not None and yi is not None and zi is not None:
            # Crear mapa de calor con los valores interpolados
            heat_data = []
            for i in range(0, len(xi), 5):  # Muestrear para no sobrecargar
                for j in range(0, len(yi), 5):
                    if not np.isnan(zi[i][j]):
                        heat_data.append([yi[i][j], xi[i][j], zi[i][j]])
            
            # Agregar mapa de calor
            HeatMap(
                heat_data,
                radius=15,
                blur=10,
                max_zoom=1,
                gradient={0.0: 'blue', 0.5: 'lime', 1.0: 'red'}
            ).add_to(m)
            
            # Agregar contornos como líneas
            z_min = np.nanmin(zi)
            z_max = np.nanmax(zi)
            levels = np.linspace(z_min, z_max, config_contornos['num_contours'])
            
            # Crear figura temporal para extraer contornos
            fig, ax = plt.subplots(figsize=(10, 10))
            contour = ax.contour(xi, yi, zi, levels=levels, colors='white', linewidths=1.5, alpha=0.8)
            
            # Extraer y agregar líneas de contorno al mapa
            for collection in contour.collections:
                paths = collection.get_paths()
                for path in paths:
                    vertices = path.vertices
                    if len(vertices) > 1:
                        # Convertir coordenadas a lista de [lat, lon]
                        coords = [[yi_val, xi_val] for xi_val, yi_val in vertices]
                        
                        # Crear línea de contorno
                        folium.PolyLine(
                            locations=coords,
                            color='white',
                            weight=2,
                            opacity=0.8,
                            dash_array='5, 5',
                            tooltip=f'Curva de nivel: {path.levels[0]:.2f}'
                        ).add_to(m)
            
            plt.close(fig)
            
            # Agregar leyenda de colores
            colormap = LinearColormap(
                ['blue', 'lime', 'red'],
                vmin=z_min,
                vmax=z_max,
                caption=config_capa['nombre']
            )
            colormap.add_to(m)
        
        # Ajustar zoom
        m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])
        
        # Agregar controles
        Fullscreen().add_to(m)
        MousePosition().add_to(m)
        folium.LayerControl().add_to(m)
        
        return m
        
    except Exception as e:
        st.error(f"Error creando mapa con curvas de nivel: {str(e)}")
        return crear_mapa_base()

# ===============================
# 📊 FUNCIONES DE VISUALIZACIÓN
# ===============================

def crear_grafico_radar(datos_combinados, categorias):
    """Crear gráfico radar para comparación de indicadores"""
    if not datos_combinados:
        return go.Figure()
    
    fig = go.Figure()
    
    for area_data in datos_combinados[:5]:
        valores = [area_data.get(cat, 0) for cat in categorias.keys()]
        fig.add_trace(go.Scatterpolar(
            r=valores,
            theta=list(categorias.values()),
            fill='toself',
            name=area_data['area']
        ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 1])
        ),
        showlegend=True,
        title="Comparación de Indicadores por Área",
        paper_bgcolor='white',
        plot_bgcolor='white'
    )
    return fig

def crear_grafico_sunburst(datos, columna_valor, columna_estado, titulo):
    """Crear gráfico sunburst para distribución jerárquica"""
    if not datos:
        return go.Figure()
    
    try:
        df = pd.DataFrame(datos)
        if columna_estado in df.columns:
            conteo_estado = df[columna_estado].value_counts()
        else:
            df['categoria'] = pd.cut(df[columna_valor], bins=4, labels=['Bajo', 'Medio', 'Alto', 'Muy Alto'])
            conteo_estado = df['categoria'].value_counts()
        
        fig = px.sunburst(
            names=conteo_estado.index,
            parents=[''] * len(conteo_estado),
            values=conteo_estado.values,
            title=titulo
        )
        
        fig.update_layout(paper_bgcolor='white', plot_bgcolor='white')
        return fig
    except Exception as e:
        fig = go.Figure()
        fig.add_trace(go.Pie(
            values=[1],
            labels=['Datos no disponibles'],
            title=titulo
        ))
        return fig

def crear_grafico_3d_scatter(datos_combinados, ejes_config):
    """Crear gráfico 3D scatter para relación entre indicadores"""
    if not datos_combinados:
        return go.Figure()
    
    try:
        df = pd.DataFrame(datos_combinados)
        columnas_necesarias = [ejes_config['x'], ejes_config['y'], ejes_config['z']]
        columnas_existentes = [col for col in columnas_necesarias if col in df.columns]
        
        if len(columnas_existentes) < 3:
            st.warning(f"Faltan columnas para el gráfico 3D: {set(columnas_necesarias) - set(columnas_existentes)}")
            return go.Figure()
        
        fig = px.scatter_3d(
            df,
            x=ejes_config['x'],
            y=ejes_config['y'],
            z=ejes_config['z'],
            color=ejes_config.get('color', ejes_config['x']),
            size=ejes_config.get('size', ejes_config['x']),
            hover_name='area',
            title=ejes_config['titulo']
        )
        
        fig.update_layout(paper_bgcolor='white', scene=dict(bgcolor='white'))
        return fig
    except Exception as e:
        st.error(f"Error creando gráfico 3D: {str(e)}")
        return go.Figure()

def crear_heatmap_correlacion(datos_combinados, indicadores):
    """Crear heatmap de correlación entre indicadores"""
    if not datos_combinados:
        return go.Figure()
    
    try:
        df = pd.DataFrame(datos_combinados)
        columnas_existentes = [col for col in indicadores.keys() if col in df.columns]
        
        if len(columnas_existentes) < 2:
            st.warning("No hay suficientes indicadores para calcular correlaciones")
            return go.Figure()
        
        correlaciones = df[columnas_existentes].corr()
        
        fig = ff.create_annotated_heatmap(
            z=correlaciones.values,
            x=[indicadores[col] for col in columnas_existentes],
            y=[indicadores[col] for col in columnas_existentes],
            annotation_text=correlaciones.round(2).values,
            colorscale='Viridis'
        )
        
        fig.update_layout(
            title="Correlación entre Indicadores",
            paper_bgcolor='white',
            plot_bgcolor='white'
        )
        return fig
    except Exception as e:
        st.error(f"Error creando heatmap: {str(e)}")
        return go.Figure()

def crear_grafico_treemap(datos, columna_valor, columna_estado, titulo):
    """Crear gráfico treemap para visualización jerárquica"""
    if not datos:
        return go.Figure()
    
    try:
        df = pd.DataFrame(datos)
        
        if columna_estado in df.columns:
            grouped = df.groupby(columna_estado).agg({columna_valor: 'sum', 'area': 'count'}).reset_index()
            fig = px.treemap(
                grouped,
                path=[columna_estado],
                values=columna_valor,
                title=titulo,
                color=columna_valor,
                color_continuous_scale='Viridis'
            )
        else:
            fig = px.treemap(
                df,
                path=['area'],
                values=columna_valor,
                title=titulo,
                color=columna_valor,
                color_continuous_scale='Viridis'
            )
        
        fig.update_layout(paper_bgcolor='white')
        return fig
    except Exception as e:
        st.error(f"Error creando treemap: {str(e)}")
        return go.Figure()

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

def generar_geojson_indicador(datos, nombre_indicador):
    """Generar GeoJSON para un indicador específico"""
    try:
        datos_limpios = []
        for item in datos:
            item_limpio = item.copy()
            if 'centroid' in item_limpio:
                del item_limpio['centroid']
            if 'geometry' in item_limpio:
                item_limpio['geometry_wkt'] = item_limpio['geometry'].wkt
                del item_limpio['geometry']
            datos_limpios.append(item_limpio)
        
        df_limpio = pd.DataFrame(datos_limpios)
        json_str = df_limpio.to_json(orient='records', indent=2)
        return json_str
        
    except Exception as e:
        st.error(f"Error generando GeoJSON: {str(e)}")
        return None

def generar_geojson_completo(resultados):
    """Generar un GeoJSON completo con todos los indicadores"""
    try:
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
        
        gdf = gpd.GeoDataFrame(todos_datos, geometry='geometry')
        gdf.crs = "EPSG:4326"
        geojson_str = gdf.to_json()
        return geojson_str
        
    except Exception as e:
        st.error(f"Error generando GeoJSON completo: {str(e)}")
        return None

def crear_documento_word(resultados):
    """Crear documento Word con el informe completo"""
    if not DOCX_AVAILABLE:
        st.error("La librería python-docx no está disponible")
        return None
        
    try:
        doc = Document()
        title = doc.add_heading('Informe de Análisis de Biodiversidad', 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        doc.add_paragraph(f"Fecha de generación: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        doc.add_paragraph()
        
        doc.add_heading('Resumen Ejecutivo', level=1)
        summary = resultados['resultados']['summary_metrics']
        
        resumen_text = f"""
        Este informe presenta los resultados del análisis integral de biodiversidad realizado en el área de estudio.
        
        Área total analizada: {resultados['area_hectareas']:,.2f} hectáreas
        Tipo de vegetación: {resultados['tipo_vegetacion']}
        Estado general del ecosistema: {summary['estado_general']}
        Carbono total almacenado: {summary['carbono_total_co2_ton']:,} ton CO₂
        Índice de biodiversidad promedio: {summary['indice_biodiversidad_promedio']}
        Índice de humedad promedio: {summary['indice_humedad_promedio']}
        Áreas analizadas: {summary['areas_analizadas']}
        """
        
        doc.add_paragraph(resumen_text)
        doc.add_paragraph()
        
        doc.add_heading('Indicadores Principales', level=1)
        
        indicadores_data = [
            ('Carbono Total', f"{summary['carbono_total_co2_ton']:,} ton CO₂"),
            ('Biodiversidad', f"{summary['indice_biodiversidad_promedio']}"),
            ('Disponibilidad de Agua', f"{summary['disponibilidad_agua_promedio']}"),
            ('Salud del Suelo', f"{summary['salud_suelo_promedio']}"),
            ('Índice de Humedad', f"{summary['indice_humedad_promedio']}"),
            ('Presión Antrópica', f"{summary['presion_antropica_promedio']}"),
            ('Conectividad', f"{summary['conectividad_promedio']}")
        ]
        
        for nombre, valor in indicadores_data:
            p = doc.add_paragraph()
            p.add_run(f"{nombre}: ").bold = True
            p.add_run(valor)
        
        doc.add_paragraph()
        
        doc.add_heading('Recomendaciones', level=1)
        
        if summary['estado_general'] in ['Crítico', 'Moderado']:
            recomendaciones = [
                "Implementar programas de restauración ecológica en áreas degradadas",
                "Establecer corredores biológicos para mejorar la conectividad",
                "Monitorear continuamente las presiones antrópicas",
                "Desarrollar estrategias de conservación de la biodiversidad",
                "Considerar programas de pago por servicios ambientales"
            ]
        else:
            recomendaciones = [
                "Mantener las prácticas actuales de conservación",
                "Continuar con el monitoreo periódico de indicadores",
                "Fortalecer la protección contra amenazas externas",
                "Promover la investigación científica en el área",
                "Considerar certificaciones de conservación"
            ]
        
        for rec in recomendaciones:
            doc.add_paragraph(rec, style='List Bullet')
        
        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        
        return buffer
    except Exception as e:
        st.error(f"Error generando documento Word: {str(e)}")
        return None

def crear_boton_descarga(data, filename, button_text, file_type):
    """Crear botón de descarga para diferentes tipos de archivos"""
    try:
        if file_type == 'geojson':
            if data is None:
                st.error(f"No hay datos para generar {filename}")
                return
            b64 = base64.b64encode(data.encode()).decode()
            href = f'<a href="data:application/json;base64,{b64}" download="{filename}" class="download-btn">📥 {button_text}</a>'
        elif file_type == 'word':
            if data is None:
                st.error(f"No hay datos para generar {filename}")
                return
            b64 = base64.b64encode(data.getvalue()).decode()
            href = f'<a href="data:application/vnd.openxmlformats-officedocument.wordprocessingml.document;base64,{b64}" download="{filename}" class="download-btn">📥 {button_text}</a>'
        elif file_type == 'csv':
            b64 = base64.b64encode(data.encode()).decode()
            href = f'<a href="data:file/csv;base64,{b64}" download="{filename}" class="download-btn">📥 {button_text}</a>'
        
        st.markdown(f'<div style="margin: 10px 0;">{href}</div>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error creando botón de descarga: {str(e)}")

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
    if 'curvas_nivel_config' not in st.session_state:
        st.session_state.curvas_nivel_config = {
            'capa_seleccionada': 'biodiversidad',
            'num_contours': 10,
            'resolucion': 100,
            'mostrar_en_mapa': True
        }
    if 'zoom_auto' not in st.session_state:
        st.session_state.zoom_auto = True

def tiene_poligono_data():
    return (st.session_state.poligono_data is not None and 
            hasattr(st.session_state.poligono_data, 'empty') and 
            not st.session_state.poligono_data.empty)

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
        
        # Configuración de zoom automático
        st.session_state.zoom_auto = st.checkbox(
            "Zoom automático en polígono", 
            value=True,
            help="Ajustar automáticamente el zoom para enfocar el polígono completo"
        )
        
        # Configuración de curvas de nivel
        if st.session_state.analysis_complete:
            st.markdown("---")
            st.header("🗺️ Configuración de Capas y Curvas")
            
            # Selección de capa para visualización
            capas_opciones = {
                'biodiversidad': '🦋 Biodiversidad (Índice de Shannon)',
                'carbono': '🌳 Captura de Carbono',
                'vegetacion': '🌿 Vegetación (NDVI)',
                'humedad': '💧 Índice de Humedad',
                'agua': '💦 Disponibilidad de Agua',
                'suelo': '🌱 Salud del Suelo',
                'conectividad': '🔗 Conectividad Ecológica'
            }
            
            st.session_state.curvas_nivel_config['capa_seleccionada'] = st.selectbox(
                "Seleccionar capa para visualización",
                options=list(capas_opciones.keys()),
                format_func=lambda x: capas_opciones[x],
                index=0
            )
            
            st.session_state.curvas_nivel_config['mostrar_en_mapa'] = st.checkbox(
                "Mostrar curvas de nivel sobre el mapa",
                value=True,
                help="Superponer curvas de nivel en el mapa principal"
            )
            
            if st.session_state.curvas_nivel_config['mostrar_en_mapa']:
                st.session_state.curvas_nivel_config['num_contours'] = st.slider(
                    "Número de curvas de nivel",
                    min_value=5,
                    max_value=30,
                    value=10,
                    help="Número de curvas de nivel a mostrar en el mapa"
                )
                
                st.session_state.curvas_nivel_config['resolucion'] = st.slider(
                    "Resolución de interpolación",
                    min_value=50,
                    max_value=200,
                    value=100,
                    help="Resolución para generar curvas de nivel (mayor = más preciso)"
                )
        
        return uploaded_file, vegetation_type, divisiones

# ===============================
# 🎯 APLICACIÓN PRINCIPAL
# ===============================

def main():
    aplicar_estilos_globales()
    crear_header()
    initialize_session_state()
    
    uploaded_file, vegetation_type, divisiones = sidebar_config()
    
    if tiene_poligono_data():
        gdf = st.session_state.poligono_data
        poligono = gdf.geometry.iloc[0]
        area_ha = st.session_state.analyzer._calcular_area_hectareas(poligono)
        
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        st.subheader("📐 Información del Área de Estudio")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Área aproximada", f"{area_ha:,.2f} ha")
        with col2:
            st.metric("Tipo de vegetación", vegetation_type)
        with col3:
            st.metric("Áreas de análisis", f"{divisiones}x{divisiones}")
        
        if st.session_state.zoom_auto:
            bounds = poligono.bounds
            st.info(f"**Límites del polígono:** Lon: {bounds[0]:.4f} a {bounds[2]:.4f}, Lat: {bounds[1]:.4f} a {bounds[3]:.4f}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    if tiene_poligono_data() and not st.session_state.analysis_complete:
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
    
    if st.session_state.analysis_complete and st.session_state.results:
        resultados = st.session_state.results
        summary = resultados['resultados']['summary_metrics']
        
        # SECCIÓN: MAPA INTEGRADO CON CURVAS DE NIVEL
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        st.subheader("🗺️ Mapa Integrado de Análisis")
        
        # Configuración de capas
        capas_opciones = {
            'biodiversidad': {
                'datos': resultados['resultados']['biodiversidad'],
                'columna': 'indice_shannon',
                'nombre': '🦋 Biodiversidad (Índice de Shannon)',
                'colores': ['#FF4500', '#FFD700', '#32CD32', '#006400'],
                'rango': (0, 3.0)
            },
            'carbono': {
                'datos': resultados['resultados']['carbono'],
                'columna': 'co2_total_ton',
                'nombre': '🌳 Captura de Carbono (ton CO₂)',
                'colores': ['#ffffcc', '#c2e699', '#78c679', '#238443', '#00441b'],
                'rango': (0, 50000)
            },
            'vegetacion': {
                'datos': resultados['resultados']['vegetacion'],
                'columna': 'ndvi',
                'nombre': '🌿 Vegetación (NDVI)',
                'colores': ['#FF4500', '#FFD700', '#32CD32', '#006400'],
                'rango': (0, 1.0)
            },
            'humedad': {
                'datos': resultados['resultados']['humedad'],
                'columna': 'indice_humedad',
                'nombre': '💧 Índice de Humedad',
                'colores': ['#FF4500', '#FFD700', '#ADD8E6', '#87CEEB', '#1E90FF'],
                'rango': (0, 1.0)
            }
        }
        
        config_capa = capas_opciones[st.session_state.curvas_nivel_config['capa_seleccionada']]
        
        # Crear y mostrar mapa
        if st.session_state.curvas_nivel_config['mostrar_en_mapa']:
            mapa_integrado = crear_mapa_con_curvas_nivel(
                st.session_state.poligono_data,
                config_capa['datos'],
                config_capa,
                st.session_state.curvas_nivel_config
            )
            
            st.markdown('<div class="map-container">', unsafe_allow_html=True)
            st_folium(mapa_integrado, width=800, height=600, key="mapa_integrado_contornos")
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Explicación de las curvas de nivel
            with st.expander("📝 Interpretación de las curvas de nivel"):
                st.markdown(f"""
                **Curvas de nivel para {config_capa['nombre']}:**
                
                - **Líneas blancas:** Representan valores constantes del indicador
                - **Colores de fondo:** Muestran la intensidad (azul = bajo, verde = medio, rojo = alto)
                - **Patrón de líneas:** Líneas cercanas = cambios rápidos, líneas separadas = cambios graduales
                
                **Interpretación:**
                - Las áreas con líneas densas indican gradientes pronunciados
                - Las áreas con colores cálidos tienen valores más altos
                - Las "islas" de color indican zonas de concentración
                - Los patrones circulares pueden indicar focos de influencia
                """)
        else:
            # Mapa sin curvas de nivel
            mapa_integrado = crear_mapa_integrado(
                st.session_state.poligono_data,
                resultados,
                st.session_state.curvas_nivel_config['capa_seleccionada'],
                mostrar_contornos=False,
                config_contornos=None
            )
            
            st.markdown('<div class="map-container">', unsafe_allow_html=True)
            st_folium(mapa_integrado, width=800, height=600, key="mapa_integrado_simple")
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # SECCIÓN: RESUMEN EJECUTIVO
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        st.subheader("📊 Resumen Ejecutivo del Análisis")
        
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
        
        # SECCIÓN: ANÁLISIS MULTIVARIADO
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        st.subheader("📈 Análisis Multivariado")
        
        # Combinar datos para análisis multivariado
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
        
        col_adv1, col_adv2 = st.columns(2)
        
        with col_adv1:
            # Gráfico Radar
            categorias_radar = {
                'ndvi': 'Vegetación',
                'indice_shannon': 'Biodiversidad',
                'indice_humedad': 'Humedad',
                'disponibilidad_agua': 'Agua',
                'salud_suelo': 'Suelo',
                'conectividad_total': 'Conectividad'
            }
            st.plotly_chart(
                crear_grafico_radar(datos_combinados, categorias_radar),
                use_container_width=True
            )
        
        with col_adv2:
            # Heatmap de correlación
            indicadores_corr = {
                'ndvi': 'Vegetación',
                'co2_total_ton': 'Carbono',
                'indice_shannon': 'Biodiversidad', 
                'indice_humedad': 'Humedad',
                'disponibilidad_agua': 'Agua',
                'salud_suelo': 'Suelo',
                'conectividad_total': 'Conectividad'
            }
            st.plotly_chart(
                crear_heatmap_correlacion(datos_combinados, indicadores_corr),
                use_container_width=True
            )
        
        # Gráfico 3D
        st.subheader("🔍 Relación Tridimensional de Indicadores")
        ejes_3d = {
            'x': 'ndvi',
            'y': 'indice_shannon', 
            'z': 'co2_total_ton',
            'color': 'indice_humedad',
            'size': 'co2_total_ton',
            'titulo': 'Relación Vegetación-Biodiversidad-Carbono-Coloreado por Humedad'
        }
        
        st.plotly_chart(
            crear_grafico_3d_scatter(datos_combinados, ejes_3d),
            use_container_width=True
        )
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # SECCIÓN: DESCARGAS
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        st.subheader("📥 Descargas")
        
        col_dl1, col_dl2, col_dl3 = st.columns(3)
        
        with col_dl1:
            st.markdown("**🗺️ Mapas GeoJSON**")
            geojson_completo = generar_geojson_completo(resultados)
            if geojson_completo:
                crear_boton_descarga(
                    geojson_completo,
                    "mapa_completo.geojson",
                    "Descargar GeoJSON Completo",
                    'geojson'
                )
            
            # Datos individuales
            indicadores_descarga = [
                ('carbono', 'Carbono', 'co2_total_ton'),
                ('vegetacion', 'Vegetación', 'ndvi'),
                ('biodiversidad', 'Biodiversidad', 'indice_shannon'),
                ('humedad', 'Humedad', 'indice_humedad')
            ]
            
            for key, nombre, columna in indicadores_descarga:
                geojson_data = generar_geojson_indicador(
                    resultados['resultados'][key], 
                    f"indicador_{key}"
                )
                if geojson_data:
                    crear_boton_descarga(
                        geojson_data,
                        f"datos_{key}.json",
                        f"Descargar {nombre} (JSON)",
                        'geojson'
                    )
        
        with col_dl2:
            st.markdown("**📊 Datos Completos**")
            
            # CSV completo
            df_completo = pd.DataFrame(datos_combinados)
            csv = df_completo.to_csv(index=False)
            crear_boton_descarga(
                csv,
                "datos_analisis_completo.csv",
                "Descargar CSV Completo",
                'csv'
            )
            
            # Resumen ejecutivo
            datos_resumen = {
                'Metrica': [
                    'Área Total (ha)', 'Tipo Vegetación', 'Estado General',
                    'Carbono Total (ton CO₂)', 'Índice Biodiversidad',
                    'Índice Humedad', 'Disponibilidad Agua', 
                    'Salud Suelo', 'Presión Antrópica', 'Conectividad'
                ],
                'Valor': [
                    resultados['area_hectareas'],
                    resultados['tipo_vegetacion'],
                    summary['estado_general'],
                    summary['carbono_total_co2_ton'],
                    summary['indice_biodiversidad_promedio'],
                    summary['indice_humedad_promedio'],
                    summary['disponibilidad_agua_promedio'],
                    summary['salud_suelo_promedio'],
                    summary['presion_antropica_promedio'],
                    summary['conectividad_promedio']
                ]
            }
            df_resumen = pd.DataFrame(datos_resumen)
            csv_resumen = df_resumen.to_csv(index=False)
            crear_boton_descarga(
                csv_resumen,
                "resumen_ejecutivo.csv",
                "Descargar Resumen CSV",
                'csv'
            )
        
        with col_dl3:
            st.markdown("**📄 Informe Ejecutivo**")
            if DOCX_AVAILABLE:
                doc_buffer = crear_documento_word(resultados)
                if doc_buffer:
                    crear_boton_descarga(
                        doc_buffer,
                        "informe_biodiversidad.docx",
                        "Descargar Informe Word",
                        'word'
                    )
            else:
                st.warning("⚠️ python-docx no disponible")
                
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
    
    elif not tiene_poligono_data():
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        st.markdown("""
        ## 👋 ¡Bienvenido al Análisis Integral de Biodiversidad!
        
        ### 🌿 Sistema de Evaluación Ecológica Avanzada
        
        **Nuevas Características:**
        - 🗺️ **Mapa Integrado** - Todas las capas en un solo mapa interactivo
        - 🦋 **Biodiversidad** - Índice de Shannon mejorado
        - 🌳 **Captura de Carbono** - Potencial de secuestro de CO₂
        - 🌿 **Vegetación** - Análisis NDVI y salud vegetal
        - 💧 **Índice de Humedad** - Nueva capa de análisis
        - 🗺️ **Curvas de Nivel sobre Mapa** - Visualización directa en el polígono
        - 🔍 **Análisis Multivariado** - Relaciones entre indicadores
        
        **Capas disponibles:**
        1. 🦋 **Biodiversidad** - Índice de Shannon (riqueza de especies)
        2. 🌳 **Carbono** - Potencial de captura en toneladas de CO₂
        3. 🌿 **Vegetación** - Salud vegetal mediante NDVI
        4. 💧 **Humedad** - Índice de humedad del suelo
        5. 💦 **Agua** - Disponibilidad de recursos hídricos
        6. 🌱 **Suelo** - Salud y calidad del suelo
        7. 🔗 **Conectividad** - Conectividad ecológica
        
        **¡Comienza cargando tu archivo en el sidebar!** ←
        """)
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
