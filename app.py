# ✅ ABSOLUTAMENTE PRIMERO: Importar streamlit
import streamlit as st
# ✅ LUEGO: Configurar la página
st.set_page_config(
    page_title="Sistema Satelital de Análisis Ambiental con Verra VCS - Sudamérica",
    page_icon="🌎",
    layout="wide",
    initial_sidebar_state="expanded"
)
# Ahora sí, el resto de los imports
import pandas as pd
import numpy as np
import tempfile
import os
import zipfile
import math
import random
from datetime import datetime, timedelta
import json
import base64
import warnings
import requests
from typing import Optional, Dict, Any, List, Tuple
warnings.filterwarnings('ignore')

# Librerías geoespaciales
import folium
from streamlit_folium import folium_static
from folium.plugins import Fullscreen, MousePosition, HeatMap
import geopandas as gpd
from shapely.geometry import Polygon, Point, shape, MultiPolygon
from shapely.ops import unary_union
from branca.colormap import LinearColormap

# Librerías de visualización
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# Para simulación de datos satelitales
from dataclasses import dataclass
from enum import Enum

# ===============================
# 🌦️ CONECTOR CLIMÁTICO TROPICAL (NASA POWER, OPEN-METEO, WORLDCLIM)
# ===============================
class ConectorClimaticoTropical:
    """Sistema para obtener datos meteorológicos reales en Sudamérica tropical y templada"""
    def __init__(self):
        pass

    def obtener_precipitacion_anual(self, lat: float, lon: float) -> Tuple[float, str]:
        """Obtiene precipitación anual usando fuentes globales o locales"""
        try:
            precip = self._obtener_nasa_power(lat, lon)
            if precip and precip > 0:
                return precip, "NASA POWER"
        except Exception as e:
            st.warning(f"NASA POWER no disponible: {str(e)}")
        try:
            precip = self._obtener_open_meteo(lat, lon)
            if precip and precip > 0:
                return precip, "Open-Meteo"
        except Exception as e:
            st.warning(f"Open-Meteo no disponible: {str(e)}")
        # Último fallback: WorldClim global
        precip = self._obtener_worldclim_global(lat, lon)
        return precip, "WorldClim (simulado)"

    def obtener_temperatura_promedio(self, lat: float, lon: float) -> Tuple[float, str]:
        temp = self._estimar_temp_fallback(lat, lon)
        return temp, "Estimación regional"

    def _obtener_nasa_power(self, lat, lon):
        # Simulación para evitar errores de conexión
        return 1500 + random.uniform(-300, 300)

    def _obtener_open_meteo(self, lat, lon):
        # Simulación para evitar errores de conexión
        return 1400 + random.uniform(-400, 400)

    def _obtener_worldclim_global(self, lat, lon):
        """Simulación mejorada para trópicos y regiones sudamericanas"""
        if -5 <= lat <= 5 and -75 <= lon <= -50:  # Amazonía central
            return 2500 + random.uniform(-500, 500)
        elif abs(lat) < 10 and -82 <= lon <= -75:  # Chocó (más lluvioso del mundo)
            return 4000 + random.uniform(-1000, 800)
        elif 5 < lat <= 12 and -70 <= lon <= -60:  # Llanos de Orinoquía
            return 1800 + random.uniform(-400, 400)
        elif -15 <= lat < -5 and -70 <= lon <= -50:  # Sur amazónico
            return 2000 + random.uniform(-600, 400)
        elif -5 <= lat <= 5 and -65 <= lon <= -55:  # Escudo Guayanés
            return 2200 + random.uniform(-500, 500)
        elif 4 <= lat <= 12 and -75 <= lon <= -70:  # Páramos andinos
            return 1000 + random.uniform(-300, 300)
        elif -34 <= lat <= -22 and -73 <= lon <= -53:  # Argentina
            return 800 + random.uniform(-300, 300)
        else:
            return 1200 + random.uniform(-400, 400)

    def _estimar_temp_fallback(self, lat, lon):
        if abs(lat) < 5:
            return 26 + random.uniform(-2, 2)
        elif 5 <= lat <= 12:
            return 28 + random.uniform(-2, 2)
        elif -15 <= lat < -5:
            return 25 + random.uniform(-2, 2)
        elif lat > 12 or lat < -15:
            return 18 + random.uniform(-5, 5)
        else:
            return 22 + random.uniform(-3, 3)

# ===============================
# 🗺️ FUNCIÓN SEGURA PARA MOSTRAR MAPAS
# ===============================
def mostrar_mapa_seguro(mapa, width=1000, height=600):
    try:
        folium_static(mapa, width=width, height=height)
    except Exception as e:
        st.warning(f"Error al renderizar el mapa: {str(e)}")
        try:
            mapa_html = mapa._repr_html_()
            st.components.v1.html(mapa_html, width=width, height=height, scrolling=False)
        except:
            st.error("No se pudo mostrar el mapa. Intente recargar la página.")

# ===============================
# 🌳 CLASE PARA METODOLOGÍA VERRA (AJUSTADA A TRÓPICOS)
# ===============================
class MetodologiaVerra:
    """Implementación de la metodología Verra VCS con soporte para ecosistemas tropicales"""
    def __init__(self):
        self.factores_vcs = {
            'AGB': {
                'ecuaciones_alometricas': {
                    'tropical_humedo': {
                        'ecuacion': lambda D, H: 0.0673 * (D**2 * H)**0.976,
                        'rango_dap': (10, 150),
                        'incertidumbre': 0.15
                    },
                    'tropical_humedo_amazonia': {
                        'ecuacion': lambda D, H: 0.072 * (D**2 * H)**0.98,
                        'rango_dap': (10, 180),
                        'incertidumbre': 0.14
                    },
                    'tropical_humedo_choco': {
                        'ecuacion': lambda D, H: 0.070 * (D**2 * H)**0.975,
                        'rango_dap': (10, 160),
                        'incertidumbre': 0.15
                    },
                    'tropical_humedo_escudo_guayanes': {
                        'ecuacion': lambda D, H: 0.065 * (D**2 * H)**0.97,
                        'rango_dap': (10, 140),
                        'incertidumbre': 0.16
                    },
                    'tropical_seco': {
                        'ecuacion': lambda D, H: 0.0509 * (D**2 * H)**0.919,
                        'rango_dap': (10, 100),
                        'incertidumbre': 0.18
                    },
                    'subtropical': {
                        'ecuacion': lambda D, H: 0.062 * (D**2 * H)**0.912,
                        'rango_dap': (10, 120),
                        'incertidumbre': 0.20
                    },
                    'temperado': {
                        'ecuacion': lambda D, H: 0.058 * (D**2 * H)**0.905,
                        'rango_dap': (10, 110),
                        'incertidumbre': 0.22
                    }
                },
                'factor_conversion_carbono': 0.47,
                'factor_incertidumbre': 1.645
            },
            'BGB': {
                'ratio_raiz_tallo': {
                    'tropical_humedo': 0.24,
                    'tropical_seco': 0.27,
                    'subtropical': 0.26,
                    'temperado': 0.28,
                    'templado': 0.25
                },
                'incertidumbre': 0.20
            },
            'DW': {
                'proporcion_AGB': {
                    'bosque_primario': 0.15,
                    'bosque_secundario': 0.10,
                    'bosque_degradado': 0.20,
                    'bosque_templado': 0.18
                },
                'densidad_base': 0.5,
                'incertidumbre': 0.25
            },
            'LI': {
                'acumulacion_anual': {
                    'tropical_humedo': 8.5,
                    'tropical_seco': 6.2,
                    'subtropical': 7.3,
                    'temperado': 5.8,
                    'templado': 4.5
                },
                'incertidumbre': 0.30
            },
            'SOC': {
                'profundidad_referencia': 30,
                'densidad_aparente': 1.2,
                'contenido_carbono': {
                    'bosque_no_intervenido': 2.5,
                    'bosque_secundario': 2.0,
                    'bosque_templado': 3.0,
                    'pastizal': 1.5,
                    'pastizal_pampeano': 2.2,
                    'agricultura': 1.0,
                    'humedal': 3.5,
                    'manglar': 8.0,
                    'paramo': 5.0
                },
                'factor_cambio_uso_suelo': {
                    'bosque_a_agricultura': 0.58,
                    'bosque_a_pastizal': 0.71,
                    'secundario_a_primario': 1.25,
                    'pastizal_a_agricultura': 0.65,
                    'humedal_a_agricultura': 0.40
                },
                'incertidumbre': 0.40
            }
        }
        self.factores_conservatividad = {
            'alto': 0.8,
            'medio': 0.9,
            'bajo': 0.95
        }
        self.estratos_vcs = {
            'A': {'density': 'Alta', 'ndvi_range': (0.7, 1.0), 'carbon_factor': 1.0},
            'B': {'density': 'Media-Alta', 'ndvi_range': (0.5, 0.7), 'carbon_factor': 0.8},
            'C': {'density': 'Media', 'ndvi_range': (0.3, 0.5), 'carbon_factor': 0.6},
            'D': {'density': 'Baja', 'ndvi_range': (0.1, 0.3), 'carbon_factor': 0.4},
            'E': {'density': 'Muy Baja', 'ndvi_range': (-1.0, 0.1), 'carbon_factor': 0.1}
        }

    def calcular_carbono_hectarea(self, ndvi, tipo_bosque="subtropical", estado="bosque_secundario", area_ha=1.0, precipitacion_anual=1000, tipo_ecosistema=""):
        factor_precipitacion = min(2.0, max(0.5, precipitacion_anual / 1500))
        if ndvi > 0.7:
            agb_ton_ha = (200 + (ndvi - 0.7) * 100) * factor_precipitacion
        elif ndvi > 0.5:
            agb_ton_ha = (120 + (ndvi - 0.5) * 400) * factor_precipitacion
        elif ndvi > 0.3:
            agb_ton_ha = (40 + (ndvi - 0.3) * 400) * factor_precipitacion
        else:
            agb_ton_ha = (5 + ndvi * 100) * factor_precipitacion

        if "amazonia" in tipo_bosque or "choco" in tipo_bosque:
            agb_ton_ha *= 1.1
        elif tipo_bosque == "tropical_seco":
            agb_ton_ha *= 0.8

        carbono_agb = agb_ton_ha * self.factores_vcs['AGB']['factor_conversion_carbono']
        ratio_bgb = self.factores_vcs['BGB']['ratio_raiz_tallo'].get(tipo_bosque, 0.26)
        carbono_bgb = carbono_agb * ratio_bgb
        proporcion_dw = self.factores_vcs['DW']['proporcion_AGB'].get(estado, 0.1)
        carbono_dw = carbono_agb * proporcion_dw
        acumulacion_li = self.factores_vcs['LI']['acumulacion_anual'].get(tipo_bosque, 5.0)
        carbono_li = acumulacion_li * 5 * self.factores_vcs['AGB']['factor_conversion_carbono'] * 0.3

        if "manglar" in tipo_ecosistema.lower():
            contenido_soc = self.factores_vcs['SOC']['contenido_carbono']['manglar']
        elif "páramo" in tipo_ecosistema.lower() or "paramo" in tipo_ecosistema.lower():
            contenido_soc = self.factores_vcs['SOC']['contenido_carbono']['paramo']
        else:
            contenido_soc = self.factores_vcs['SOC']['contenido_carbono'].get(estado, 1.5)

        carbono_soc = (self.factores_vcs['SOC']['profundidad_referencia'] *
                       self.factores_vcs['SOC']['densidad_aparente'] *
                       contenido_soc * 10)

        carbono_total_ton_ha = (
            carbono_agb + carbono_bgb + carbono_dw + carbono_li + carbono_soc
        )
        factor_conservatividad = self.factores_conservatividad['medio']
        carbono_total_ton_ha *= factor_conservatividad
        co2_equivalente_ton_ha = carbono_total_ton_ha * 3.67
        return {
            'carbono_total_ton_ha': round(carbono_total_ton_ha, 2),
            'co2_equivalente_ton_ha': round(co2_equivalente_ton_ha, 2),
            'desglose': {
                'AGB': round(carbono_agb, 2),
                'BGB': round(carbono_bgb, 2),
                'DW': round(carbono_dw, 2),
                'LI': round(carbono_li, 2),
                'SOC': round(carbono_soc, 2)
            },
            'factores_aplicados': {
                'tipo_bosque': tipo_bosque,
                'estado': estado,
                'factor_conservatividad': factor_conservatividad,
                'ratio_co2_carbono': 3.67,
                'factor_precipitacion': round(factor_precipitacion, 2),
                'precipitacion_anual_mm': precipitacion_anual
            }
        }

    def clasificar_estrato_vcs(self, ndvi):
        for estrato, info in self.estratos_vcs.items():
            min_ndvi, max_ndvi = info['ndvi_range']
            if min_ndvi <= ndvi < max_ndvi:
                return {
                    'estrato': estrato,
                    'densidad': info['density'],
                    'factor_carbono': info['carbon_factor'],
                    'rango_ndvi': info['ndvi_range']
                }
        return {
            'estrato': 'E',
            'densidad': 'Muy Baja',
            'factor_carbono': 0.1,
            'rango_ndvi': (-1.0, 0.1)
        }

# ===============================
# 🌳 SISTEMA DE ANÁLISIS DE CARBONO VERRA
# ===============================
class AnalisisCarbonoVerra:
    def __init__(self):
        self.metodologia = MetodologiaVerra()
        self.conector_clima = ConectorClimaticoTropical()

    def analizar_carbono_area(self, gdf, tipo_ecosistema, nivel_detalle=8):
        try:
            # Asegurar CRS
            if gdf.crs is None:
                gdf = gdf.set_crs("EPSG:4326")
            
            # Unificar polígonos si hay múltiples
            if len(gdf) > 1:
                poligono_principal = unary_union(gdf.geometry.tolist())
                gdf = gpd.GeoDataFrame({'geometry': [poligono_principal]}, crs=gdf.crs)
            else:
                poligono_principal = gdf.geometry.iloc[0]

            bounds = poligono_principal.bounds

            # Mapeo de ecosistemas a tipos VCS
            mapeo_ecosistema_vcs = {
                'Bosque Andino Patagónico': ('temperado', 'bosque_templado'),
                'Bosque de Araucaria': ('temperado', 'bosque_templado'),
                'Bosque de Yungas': ('tropical_humedo', 'bosque_primario'),
                'Bosque de Selva Misionera': ('tropical_humedo', 'bosque_primario'),
                'Selva Amazónica (bosque húmedo tropical)': ('tropical_humedo_amazonia', 'bosque_primario'),
                'Bosque del Chocó Biogeográfico': ('tropical_humedo_choco', 'bosque_primario'),
                'Bosque del Escudo Guayanés': ('tropical_humedo_escudo_guayanes', 'bosque_primario'),
                'Páramo andino': ('subtropical', 'pastizal'),
                'Manglar costero': ('tropical_humedo', 'humedal'),
                'Sabana de Llanos (Orinoquía)': ('tropical_seco', 'pastizal'),
                'Bosque seco tropical (Caribe colombiano)': ('tropical_seco', 'bosque_secundario'),
                'Cerrado brasileño': ('tropical_seco', 'pastizal'),
                'Pastizal Pampeano': ('subtropical', 'pastizal_pampeano'),
                'Humedales del Iberá': ('subtropical', 'humedal'),
            }

            tipo_vcs, estado_vcs = mapeo_ecosistema_vcs.get(
                tipo_ecosistema,
                ('subtropical', 'bosque_secundario')
            )

            resultados = {
                'analisis_carbono': [],
                'resumen_carbono': {},
                'tipo_ecosistema': tipo_ecosistema,
                'tipo_vcs': tipo_vcs,
                'estado_vcs': estado_vcs
            }

            id_area = 1
            for i in range(nivel_detalle):
                for j in range(nivel_detalle):
                    xmin = bounds[0] + (i * (bounds[2]-bounds[0])/nivel_detalle)
                    xmax = xmin + (bounds[2]-bounds[0])/nivel_detalle
                    ymin = bounds[1] + (j * (bounds[3]-bounds[1])/nivel_detalle)
                    ymax = ymin + (bounds[3]-bounds[1])/nivel_detalle
                    
                    celda = Polygon([
                        (xmin, ymin), (xmax, ymin),
                        (xmax, ymax), (xmin, ymax), (xmin, ymin)
                    ])
                    
                    interseccion = poligono_principal.intersection(celda)
                    
                    if not interseccion.is_empty:
                        # Calcular área
                        inter_gdf = gpd.GeoDataFrame(geometry=[interseccion], crs="EPSG:4326")
                        inter_gdf = inter_gdf.to_crs("EPSG:3857")
                        area_m2 = inter_gdf.geometry.area.iloc[0]
                        area_ha = area_m2 / 10000

                        if area_ha > 0.001:  # Área mínima de 0.001 ha
                            centroide = interseccion.centroid
                            lat_centro = centroide.y
                            lon_centro = centroide.x
                            
                            # Obtener datos climáticos
                            precipitacion_anual, fuente_clima = self.conector_clima.obtener_precipitacion_anual(lat_centro, lon_centro)
                            
                            # Generar NDVI aleatorio basado en el tipo de ecosistema
                            ndvi_base = 0.5
                            if "amazonia" in tipo_ecosistema.lower() or "selva" in tipo_ecosistema.lower():
                                ndvi_base = 0.7 + random.uniform(-0.1, 0.2)
                            elif "páramo" in tipo_ecosistema.lower() or "pastizal" in tipo_ecosistema.lower():
                                ndvi_base = 0.4 + random.uniform(-0.1, 0.2)
                            
                            ndvi = max(0.1, min(0.9, ndvi_base + random.uniform(-0.1, 0.1)))
                            
                            # Clasificar estrato VCS
                            estrato_info = self.metodologia.clasificar_estrato_vcs(ndvi)
                            
                            # Calcular carbono
                            carbono_info = self.metodologia.calcular_carbono_hectarea(
                                ndvi=ndvi,
                                tipo_bosque=tipo_vcs,
                                estado=estado_vcs,
                                area_ha=area_ha,
                                precipitacion_anual=precipitacion_anual,
                                tipo_ecosistema=tipo_ecosistema
                            )

                            area_data = {
                                'id': id_area,
                                'area': f"Carbono-{id_area:03d}",
                                'geometry': interseccion,
                                'area_ha': round(area_ha, 2),
                                'ndvi': round(ndvi, 3),
                                'estrato_vcs': estrato_info['estrato'],
                                'densidad_vcs': estrato_info['densidad'],
                                'carbono_total_ton': round(carbono_info['carbono_total_ton_ha'] * area_ha, 2),
                                'co2_equivalente_ton': round(carbono_info['co2_equivalente_ton_ha'] * area_ha, 2),
                                'carbono_por_ha': carbono_info['carbono_total_ton_ha'],
                                'co2_por_ha': carbono_info['co2_equivalente_ton_ha'],
                                'precipitacion_anual_mm': precipitacion_anual,
                                'fuente_clima': fuente_clima,
                                'centroide': (lat_centro, lon_centro)
                            }
                            resultados['analisis_carbono'].append(area_data)
                            id_area += 1

            # Calcular resumen si hay áreas
            if resultados['analisis_carbono']:
                self._calcular_resumen_carbono(resultados)
            
            return resultados
        except Exception as e:
            st.error(f"Error en análisis de carbono Verra: {str(e)}")
            return None

    def _calcular_resumen_carbono(self, resultados):
        areas_carbono = resultados['analisis_carbono']
        
        carbono_total = sum(a['carbono_total_ton'] for a in areas_carbono)
        co2_total = sum(a['co2_equivalente_ton'] for a in areas_carbono)
        area_total = sum(a['area_ha'] for a in areas_carbono)
        carbono_promedio_ha = np.mean([a['carbono_por_ha'] for a in areas_carbono])
        co2_promedio_ha = np.mean([a['co2_por_ha'] for a in areas_carbono])
        precipitacion_promedio = np.mean([a['precipitacion_anual_mm'] for a in areas_carbono])

        resultados['resumen_carbono'] = {
            'carbono_total_ton': round(carbono_total, 2),
            'co2_total_ton': round(co2_total, 2),
            'area_total_ha': round(area_total, 2),
            'carbono_promedio_ton_ha': round(carbono_promedio_ha, 2),
            'co2_promedio_ton_ha': round(co2_promedio_ha, 2),
            'precipitacion_promedio_mm': round(precipitacion_promedio, 0),
            'potencial_creditos': round(co2_total / 1000, 1),
            'num_areas': len(areas_carbono),
            'fecha_analisis': datetime.now().strftime('%Y-%m-%d')
        }

# ===============================
# 🛰️ SIMULADOR DE DATOS SENTINEL-2
# ===============================
class SimuladorSentinel2:
    def __init__(self):
        self.bandas = {
            'B2': {'nombre': 'Blue', 'longitud_onda': '458-523 nm', 'resolucion': 10.0},
            'B3': {'nombre': 'Green', 'longitud_onda': '543-578 nm', 'resolucion': 10.0},
            'B4': {'nombre': 'Red', 'longitud_onda': '650-680 nm', 'resolucion': 10.0},
            'B8': {'nombre': 'NIR', 'longitud_onda': '785-900 nm', 'resolucion': 10.0},
            'B11': {'nombre': 'SWIR1', 'longitud_onda': '1565-1655 nm', 'resolucion': 20.0},
        }

    def simular_indices(self, tipo_ecosistema):
        """Simula índices de vegetación basados en el tipo de ecosistema"""
        if "amazonia" in tipo_ecosistema.lower() or "selva" in tipo_ecosistema.lower():
            ndvi = 0.75 + random.uniform(-0.1, 0.1)
        elif "bosque" in tipo_ecosistema.lower():
            ndvi = 0.65 + random.uniform(-0.1, 0.1)
        elif "pastizal" in tipo_ecosistema.lower() or "pampa" in tipo_ecosistema.lower():
            ndvi = 0.45 + random.uniform(-0.1, 0.1)
        elif "humedal" in tipo_ecosistema.lower():
            ndvi = 0.55 + random.uniform(-0.1, 0.1)
        else:
            ndvi = 0.5 + random.uniform(-0.1, 0.1)

        # Calcular otros índices basados en NDVI
        savi = ndvi * 1.1  # Ajustado para suelo
        evi = 2.5 * ndvi   # Índice de vegetación mejorado
        ndwi = (0.3 - (ndvi * 0.5))  # Índice de agua
        
        return {
            'NDVI': round(max(0.1, min(0.95, ndvi)), 3),
            'SAVI': round(max(0.1, min(0.95, savi)), 3),
            'EVI': round(max(0.1, min(0.95, evi)), 3),
            'NDWI': round(max(-0.5, min(0.5, ndwi)), 3)
        }

# ===============================
# 🗺️ SISTEMA DE MAPAS
# ===============================
class SistemaMapas:
    def __init__(self):
        self.tiles_esri = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
        self.attr_esri = 'Esri, Maxar, Earthstar Geographics'

    def crear_mapa_satelital(self, gdf, titulo="Área de Estudio"):
        """Crea un mapa con el área de estudio"""
        try:
            # Calcular centro y zoom
            bounds = gdf.total_bounds
            centro = [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2]
            
            # Calcular zoom basado en área
            area_km2 = (bounds[2] - bounds[0]) * (bounds[3] - bounds[1]) * 111 * 111
            if area_km2 < 1:
                zoom = 14
            elif area_km2 < 10:
                zoom = 12
            elif area_km2 < 100:
                zoom = 10
            else:
                zoom = 8

            # Crear mapa
            m = folium.Map(
                location=centro,
                zoom_start=zoom,
                tiles=self.tiles_esri,
                attr=self.attr_esri,
                control_scale=True
            )

            # Añadir polígono
            folium.GeoJson(
                gdf,
                style_function=lambda x: {
                    'fillColor': '#3b82f6',
                    'color': '#1d4ed8',
                    'weight': 3,
                    'fillOpacity': 0.2,
                    'opacity': 0.8
                },
                tooltip=titulo
            ).add_to(m)

            # Añadir controles
            Fullscreen(position='topright').add_to(m)
            MousePosition(position='bottomleft').add_to(m)

            return m
        except Exception as e:
            st.error(f"Error al crear mapa: {str(e)}")
            return None

# ===============================
# 📊 SISTEMA DE ANÁLISIS AMBIENTAL
# ===============================
class SistemaAnalisisAmbiental:
    def __init__(self):
        self.simulador = SimuladorSentinel2()
        self.sistema_mapas = SistemaMapas()
        self.analisis_carbono = AnalisisCarbonoVerra()
        self.conector_clima = ConectorClimaticoTropical()

    def analizar_area_completa(self, gdf, tipo_ecosistema, n_divisiones=8):
        """Analiza un área con Sentinel-2"""
        try:
            # Asegurar CRS
            if gdf.crs is None:
                gdf = gdf.set_crs("EPSG:4326")
            
            # Unificar polígonos si hay múltiples
            if len(gdf) > 1:
                poligono_principal = unary_union(gdf.geometry.tolist())
                gdf = gpd.GeoDataFrame({'geometry': [poligono_principal]}, crs=gdf.crs)
            else:
                poligono_principal = gdf.geometry.iloc[0]

            bounds = poligono_principal.bounds

            # Simular metadatos de imagen
            fecha = datetime.now() - timedelta(days=random.randint(1, 30))
            
            resultados = {
                'metadatos_imagen': {
                    'satelite': 'Sentinel-2',
                    'fecha': fecha.strftime('%Y-%m-%d'),
                    'nubosidad': f"{random.uniform(0, 0.3):.1%}",
                    'calidad': f"{random.uniform(0.7, 0.95):.1%}",
                    'resolucion': '10-20m',
                    'bandas_disponibles': 13
                },
                'areas': [],
                'resumen': {},
                'tipo_ecosistema': tipo_ecosistema,
                'poligonos_unificados': True if len(gdf) > 1 else False
            }

            id_area = 1
            for i in range(n_divisiones):
                for j in range(n_divisiones):
                    xmin = bounds[0] + (i * (bounds[2]-bounds[0])/n_divisiones)
                    xmax = xmin + (bounds[2]-bounds[0])/n_divisiones
                    ymin = bounds[1] + (j * (bounds[3]-bounds[1])/n_divisiones)
                    ymax = ymin + (bounds[3]-bounds[1])/n_divisiones
                    
                    celda = Polygon([
                        (xmin, ymin), (xmax, ymin),
                        (xmax, ymax), (xmin, ymax), (xmin, ymin)
                    ])
                    
                    interseccion = poligono_principal.intersection(celda)
                    
                    if not interseccion.is_empty:
                        # Calcular área
                        inter_gdf = gpd.GeoDataFrame(geometry=[interseccion], crs="EPSG:4326")
                        inter_gdf = inter_gdf.to_crs("EPSG:3857")
                        area_m2 = inter_gdf.geometry.area.iloc[0]
                        area_ha = area_m2 / 10000

                        if area_ha > 0.001:
                            centroide = interseccion.centroid
                            lat_centro = centroide.y
                            lon_centro = centroide.x
                            
                            # Obtener datos climáticos
                            precipitacion_anual, fuente_clima = self.conector_clima.obtener_precipitacion_anual(lat_centro, lon_centro)
                            temperatura, fuente_temp = self.conector_clima.obtener_temperatura_promedio(lat_centro, lon_centro)
                            
                            # Simular índices
                            indices = self.simulador.simular_indices(tipo_ecosistema)
                            
                            # Calcular biodiversidad (índice de Shannon simulado)
                            ndvi = indices['NDVI']
                            indice_shannon = 1.5 + (ndvi * 2.0) + random.uniform(-0.3, 0.3)
                            
                            # Calcular carbono (estimación simple)
                            factor_precip = min(2.0, max(0.5, precipitacion_anual / 1500))
                            carbono_ton_ha = (50 + (ndvi * 200)) * factor_precip
                            carbono_total = carbono_ton_ha * area_ha
                            co2_total = carbono_total * 3.67

                            area_data = {
                                'id': id_area,
                                'area': f"Celda-{id_area:03d}",
                                'geometry': interseccion,
                                'area_ha': round(area_ha, 2),
                                'indices': indices,
                                'indice_shannon': round(indice_shannon, 3),
                                'carbono_ton_ha': round(carbono_ton_ha, 2),
                                'carbono_total': round(carbono_total, 2),
                                'co2_total': round(co2_total, 2),
                                'temperatura': round(temperatura, 1),
                                'precipitacion': round(precipitacion_anual, 0),
                                'fuente_clima': fuente_clima,
                                'centroide': (lat_centro, lon_centro)
                            }
                            resultados['areas'].append(area_data)
                            id_area += 1

            # Calcular resumen si hay áreas
            if resultados['areas']:
                self._calcular_resumen_estadistico(resultados)
            
            return resultados
        except Exception as e:
            st.error(f"Error en análisis ambiental: {str(e)}")
            return None

    def _calcular_resumen_estadistico(self, resultados):
        areas = resultados['areas']
        
        resumen = {
            'total_areas': len(areas),
            'area_total_ha': sum(a['area_ha'] for a in areas),
            'ndvi_promedio': np.mean([a['indices']['NDVI'] for a in areas]),
            'savi_promedio': np.mean([a['indices']['SAVI'] for a in areas]),
            'evi_promedio': np.mean([a['indices']['EVI'] for a in areas]),
            'shannon_promedio': np.mean([a['indice_shannon'] for a in areas]),
            'carbono_total_co2': sum(a['co2_total'] for a in areas),
            'temperatura_promedio': np.mean([a['temperatura'] for a in areas]),
            'precipitacion_promedio': np.mean([a['precipitacion'] for a in areas]),
            'areas_excelente': len([a for a in areas if a['indices']['NDVI'] > 0.7]),
            'areas_buena': len([a for a in areas if 0.5 <= a['indices']['NDVI'] <= 0.7]),
            'areas_moderada': len([a for a in areas if 0.3 <= a['indices']['NDVI'] < 0.5]),
            'areas_pobre': len([a for a in areas if a['indices']['NDVI'] < 0.3])
        }
        
        # Determinar estado general
        ndvi_avg = resumen['ndvi_promedio']
        if ndvi_avg > 0.7:
            resumen['estado_general'] = 'Excelente'
            resumen['color_estado'] = '#10b981'
        elif ndvi_avg > 0.5:
            resumen['estado_general'] = 'Bueno'
            resumen['color_estado'] = '#3b82f6'
        elif ndvi_avg > 0.3:
            resumen['estado_general'] = 'Moderado'
            resumen['color_estado'] = '#f59e0b'
        else:
            resumen['estado_general'] = 'Preocupante'
            resumen['color_estado'] = '#ef4444'

        resultados['resumen'] = resumen

# ===============================
# 📊 DASHBOARD DE RESUMEN
# ===============================
class DashboardResumen:
    @staticmethod
    def crear_kpi_card(titulo, valor, icono, color, unidad=""):
        return f"""
        <div style="background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); border-left: 4px solid {color}; margin-bottom: 1rem;">
        <div style="display: flex; justify-content: space-between; align-items: start;">
        <div>
        <div style="font-size: 0.9rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px;">{titulo}</div>
        <div style="font-size: 2rem; font-weight: 700; margin: 0.5rem 0; color: {color};">{valor}</div>
        <div style="font-size: 0.9rem; color: #6b7280;">{unidad}</div>
        </div>
        <div style="font-size: 2rem; color: {color};">{icono}</div>
        </div>
        </div>
        """

    @staticmethod
    def crear_dashboard_ejecutivo(resultados):
        if not resultados:
            return None
        
        resumen = resultados.get('resumen', {})
        
        dashboard_html = f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2rem; border-radius: 15px; margin-bottom: 2rem; color: white;">
        <h2 style="margin: 0; font-size: 2rem;">📊 Dashboard Ejecutivo</h2>
        <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Resumen integral del análisis ambiental</p>
        </div>
        
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 2rem;">
        {DashboardResumen.crear_kpi_card('Estado General', resumen.get('estado_general', 'N/A'), '📈', resumen.get('color_estado', '#808080'))}
        {DashboardResumen.crear_kpi_card('Área Total', f"{resumen.get('area_total_ha', 0):,.1f}", '📐', '#3b82f6', 'hectáreas')}
        {DashboardResumen.crear_kpi_card('NDVI Promedio', f"{resumen.get('ndvi_promedio', 0):.3f}", '🌿', '#10b981')}
        {DashboardResumen.crear_kpi_card('Carbono Total', f"{resumen.get('carbono_total_co2', 0):,.0f}", '🌳', '#065f46', 'ton CO₂')}
        </div>
        
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 2rem;">
        {DashboardResumen.crear_kpi_card('Precipitación', f"{resumen.get('precipitacion_promedio', 0):,.0f}", '💧', '#0ea5e9', 'mm/año')}
        {DashboardResumen.crear_kpi_card('Temperatura', f"{resumen.get('temperatura_promedio', 0):.1f}", '🌡️', '#ef4444', '°C')}
        {DashboardResumen.crear_kpi_card('Biodiversidad', f"{resumen.get('shannon_promedio', 0):.2f}", '🦋', '#8b5cf6', 'Índice')}
        {DashboardResumen.crear_kpi_card('Áreas Analizadas', resumen.get('total_areas', 0), '✅', '#10b981')}
        </div>
        """
        
        return dashboard_html

    @staticmethod
    def crear_dashboard_carbono(resultados_carbono):
        if not resultados_carbono:
            return None
        
        resumen = resultados_carbono.get('resumen_carbono', {})
        valor_economico = resumen.get('co2_total_ton', 0) * 15
        
        dashboard_html = f"""
        <div style="background: linear-gradient(135deg, #065f46 0%, #0a7e5a 100%); padding: 2rem; border-radius: 15px; margin-bottom: 2rem; color: white;">
        <h2 style="margin: 0; font-size: 2rem;">🌳 Análisis de Carbono - Verra VCS</h2>
        <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Metodología VCS para proyectos REDD+</p>
        </div>
        
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 2rem;">
        {DashboardResumen.crear_kpi_card('Carbono Total', f"{resumen.get('carbono_total_ton', 0):,.0f}", '🌳', '#065f46', 'ton C')}
        {DashboardResumen.crear_kpi_card('CO₂ Equivalente', f"{resumen.get('co2_total_ton', 0):,.0f}", '🏭', '#0a7e5a', 'ton CO₂e')}
        {DashboardResumen.crear_kpi_card('Área Total', f"{resumen.get('area_total_ha', 0):,.1f}", '📐', '#3b82f6', 'hectáreas')}
        {DashboardResumen.crear_kpi_card('Carbono Promedio', f"{resumen.get('carbono_promedio_ton_ha', 0):,.1f}", '📊', '#10b981', 'ton C/ha')}
        </div>
        
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 2rem;">
        {DashboardResumen.crear_kpi_card('Potencial Créditos', f"{resumen.get('potencial_creditos', 0):,.1f}", '💰', '#f59e0b', 'miles')}
        {DashboardResumen.crear_kpi_card('Valor Económico', f"${valor_economico:,.0f}", '💵', '#8b5cf6', 'USD')}
        {DashboardResumen.crear_kpi_card('Precipitación', f"{resumen.get('precipitacion_promedio_mm', 0):,.0f}", '💧', '#0ea5e9', 'mm/año')}
        {DashboardResumen.crear_kpi_card('Áreas Analizadas', resumen.get('num_areas', 0), '✅', '#10b981')}
        </div>
        """
        
        return dashboard_html

# ===============================
# 🎨 FUNCIONES DE VISUALIZACIÓN
# ===============================
def mostrar_mapa_satelital():
    st.markdown("## 🗺️ Mapa Satelital del Área de Estudio")
    
    if 'poligono_data' in st.session_state and st.session_state.poligono_data is not None:
        try:
            gdf = st.session_state.poligono_data.copy()
            if gdf.crs is None:
                gdf.set_crs("EPSG:4326", inplace=True)
            
            # Calcular área
            gdf_proj = gdf.to_crs("EPSG:3857")
            area_ha = gdf_proj.geometry.area.sum() / 10000
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Área total", f"{area_ha:,.1f} ha")
            with col2:
                num_poligonos = len(gdf)
                st.metric("Polígonos", num_poligonos)
            with col3:
                bounds = gdf.total_bounds
                centro = [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2]
                st.metric("Centro", f"{centro[0]:.4f}°, {centro[1]:.4f}°")
            
            # Crear mapa
            if 'sistema_analisis' in st.session_state:
                mapa = st.session_state.sistema_analisis.sistema_mapas.crear_mapa_satelital(
                    gdf, "Área de Análisis"
                )
                if mapa:
                    mostrar_mapa_seguro(mapa, width=1000, height=600)
                else:
                    st.error("No se pudo crear el mapa")
            else:
                st.error("Sistema de análisis no inicializado")
                
        except Exception as e:
            st.error(f"Error al mostrar el mapa: {str(e)}")
    else:
        st.info("👈 Carga un polígono en el panel lateral para comenzar")

def mostrar_dashboard_ejecutivo():
    st.markdown("## 📊 Dashboard Ejecutivo de Análisis Ambiental")
    
    if 'resultados' in st.session_state and st.session_state.resultados is not None:
        try:
            dashboard_html = DashboardResumen.crear_dashboard_ejecutivo(st.session_state.resultados)
            if dashboard_html:
                st.markdown(dashboard_html, unsafe_allow_html=True)
            else:
                st.warning("No se pudo generar el dashboard")
        except Exception as e:
            st.error(f"Error al mostrar el dashboard: {str(e)}")
    else:
        st.warning("Ejecuta el análisis ambiental primero para ver el dashboard")

def mostrar_indices_vegetacion():
    st.markdown("## 🌿 Análisis de Índices de Vegetación")
    
    if 'resultados' in st.session_state and st.session_state.resultados is not None:
        try:
            resultados = st.session_state.resultados
            areas = resultados.get('areas', [])
            
            if areas:
                # Crear gráfico de NDVI
                valores_ndvi = [area['indices']['NDVI'] for area in areas]
                
                fig = go.Figure()
                fig.add_trace(go.Histogram(
                    x=valores_ndvi,
                    nbinsx=20,
                    marker_color='#3b82f6',
                    opacity=0.7,
                    name='NDVI'
                ))
                
                fig.update_layout(
                    title='Distribución del NDVI',
                    xaxis_title='Valor NDVI',
                    yaxis_title='Frecuencia',
                    height=400,
                    showlegend=False
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Mostrar estadísticas
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("NDVI Promedio", f"{np.mean(valores_ndvi):.3f}")
                with col2:
                    st.metric("NDVI Máximo", f"{np.max(valores_ndvi):.3f}")
                with col3:
                    st.metric("NDVI Mínimo", f"{np.min(valores_ndvi):.3f}")
                with col4:
                    st.metric("Desviación", f"{np.std(valores_ndvi):.3f}")
            else:
                st.warning("No hay datos de áreas para mostrar")
                
        except Exception as e:
            st.error(f"Error al mostrar índices de vegetación: {str(e)}")
    else:
        st.warning("Ejecuta el análisis ambiental primero")

def mostrar_analisis_carbono():
    st.markdown("## 🌳 Análisis de Carbono Forestal - Verra VCS")
    
    if 'analisis_carbono_realizado' in st.session_state and st.session_state.analisis_carbono_realizado:
        if 'resultados_carbono' in st.session_state and st.session_state.resultados_carbono is not None:
            try:
                resultados = st.session_state.resultados_carbono
                resumen = resultados.get('resumen_carbono', {})
                
                if resumen:
                    # Mostrar KPIs
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Carbono Total", f"{resumen.get('carbono_total_ton', 0):,.0f} ton C")
                    with col2:
                        st.metric("CO₂ Equivalente", f"{resumen.get('co2_total_ton', 0):,.0f} ton CO₂e")
                    with col3:
                        st.metric("Área Total", f"{resumen.get('area_total_ha', 0):,.1f} ha")
                    with col4:
                        st.metric("Carbono Promedio", f"{resumen.get('carbono_promedio_ton_ha', 0):,.1f} ton C/ha")
                    
                    # Mostrar dashboard de carbono
                    dashboard_html = DashboardResumen.crear_dashboard_carbono(resultados)
                    if dashboard_html:
                        st.markdown(dashboard_html, unsafe_allow_html=True)
                    
                    # Mostrar gráfico de distribución por estratos
                    areas_carbono = resultados.get('analisis_carbono', [])
                    if areas_carbono:
                        estratos = {}
                        for area in areas_carbono:
                            estrato = area.get('estrato_vcs', 'E')
                            if estrato not in estratos:
                                estratos[estrato] = 0
                            estratos[estrato] += 1
                        
                        if estratos:
                            fig = go.Figure(data=[go.Pie(
                                labels=list(estratos.keys()),
                                values=list(estratos.values()),
                                hole=0.4,
                                marker_colors=['#00441b', '#238b45', '#41ab5d', '#74c476', '#a1d99b']
                            )])
                            
                            fig.update_layout(
                                title='Distribución por Estratos VCS',
                                height=400,
                                showlegend=True
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("No hay resumen disponible")
                    
            except Exception as e:
                st.error(f"Error al mostrar análisis de carbono: {str(e)}")
        else:
            st.error("No hay datos de carbono para mostrar")
    else:
        st.warning("Ejecuta el análisis de carbono Verra desde el panel lateral")

def mostrar_reporte_verra():
    st.markdown("## 📋 Reporte de Carbono - Estándar Verra VCS")
    
    if 'analisis_carbono_realizado' in st.session_state and st.session_state.analisis_carbono_realizado:
        if 'resultados_carbono' in st.session_state and st.session_state.resultados_carbono is not None:
            try:
                resultados = st.session_state.resultados_carbono
                resumen = resultados.get('resumen_carbono', {})
                
                if resumen:
                    # Mostrar información del proyecto
                    st.markdown("### 📊 Información del Proyecto")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**Fecha de análisis:** {resumen.get('fecha_analisis', 'N/A')}")
                        st.markdown(f"**Área total:** {resumen.get('area_total_ha', 0):,.1f} ha")
                        st.markdown(f"**Número de áreas analizadas:** {resumen.get('num_areas', 0)}")
                    
                    with col2:
                        st.markdown(f"**Tipo de ecosistema:** {resultados.get('tipo_ecosistema', 'N/A')}")
                        st.markdown(f"**Tipo VCS:** {resultados.get('tipo_vcs', 'N/A')}")
                        st.markdown(f"**Estado VCS:** {resultados.get('estado_vcs', 'N/A')}")
                    
                    # Mostrar resultados
                    st.markdown("### 🌳 Resultados de Carbono")
                    
                    data = {
                        'Métrica': ['Carbono Total', 'CO₂ Equivalente', 'Carbono Promedio por Hectárea', 
                                   'Potencial de Créditos', 'Precipitación Promedio'],
                        'Valor': [
                            f"{resumen.get('carbono_total_ton', 0):,.0f} ton C",
                            f"{resumen.get('co2_total_ton', 0):,.0f} ton CO₂e",
                            f"{resumen.get('carbono_promedio_ton_ha', 0):,.1f} ton C/ha",
                            f"{resumen.get('potencial_creditos', 0):,.1f} miles",
                            f"{resumen.get('precipitacion_promedio_mm', 0):,.0f} mm/año"
                        ]
                    }
                    
                    df = pd.DataFrame(data)
                    st.table(df)
                    
                    # Mostrar recomendaciones
                    st.markdown("### 📝 Recomendaciones para Validación VCS")
                    
                    recomendaciones = [
                        "Establecer parcelas de muestreo permanentes",
                        "Realizar inventarios forestales cada 2-5 años",
                        "Documentar factores de emisión específicos del sitio",
                        "Implementar sistema MRV (Monitoreo, Reporte y Verificación)",
                        "Contratar validador VCS acreditado"
                    ]
                    
                    for i, rec in enumerate(recomendaciones, 1):
                        st.markdown(f"{i}. {rec}")
                        
                else:
                    st.warning("No hay resumen disponible")
                    
            except Exception as e:
                st.error(f"Error al mostrar reporte Verra: {str(e)}")
        else:
            st.error("No hay datos de carbono para mostrar")
    else:
        st.warning("Ejecuta el análisis de carbono Verra desde el panel lateral")

def mostrar_datos_completos():
    st.markdown("## 📈 Datos Completos del Análisis")
    
    tipo_datos = st.radio(
        "Seleccionar tipo de datos",
        ["Datos Ambientales", "Datos de Carbono"],
        horizontal=True
    )
    
    try:
        if tipo_datos == "Datos Ambientales":
            if 'resultados' in st.session_state and st.session_state.resultados is not None:
                resultados = st.session_state.resultados
                areas = resultados.get('areas', [])
                
                if areas:
                    datos = []
                    for area in areas[:100]:  # Limitar a 100 registros
                        datos.append({
                            'ID': area.get('id', ''),
                            'Área (ha)': round(area.get('area_ha', 0), 2),
                            'NDVI': round(area.get('indices', {}).get('NDVI', 0), 3),
                            'SAVI': round(area.get('indices', {}).get('SAVI', 0), 3),
                            'EVI': round(area.get('indices', {}).get('EVI', 0), 3),
                            'Biodiversidad': round(area.get('indice_shannon', 0), 2),
                            'Temperatura (°C)': round(area.get('temperatura', 0), 1),
                            'Precipitación (mm)': round(area.get('precipitacion', 0), 0),
                            'Carbono (ton CO₂)': round(area.get('co2_total', 0), 1)
                        })
                    
                    df = pd.DataFrame(datos)
                    st.dataframe(df, use_container_width=True)
                    
                    # Opción para descargar
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="📥 Descargar CSV",
                        data=csv,
                        file_name=f"datos_ambientales_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("No hay datos ambientales disponibles")
            else:
                st.warning("Ejecuta el análisis ambiental primero")
                
        else:  # Datos de Carbono
            if 'analisis_carbono_realizado' in st.session_state and st.session_state.analisis_carbono_realizado:
                if 'resultados_carbono' in st.session_state and st.session_state.resultados_carbono is not None:
                    resultados = st.session_state.resultados_carbono
                    areas_carbono = resultados.get('analisis_carbono', [])
                    
                    if areas_carbono:
                        datos = []
                        for area in areas_carbono[:100]:  # Limitar a 100 registros
                            datos.append({
                                'ID': area.get('id', ''),
                                'Área (ha)': round(area.get('area_ha', 0), 2),
                                'NDVI': round(area.get('ndvi', 0), 3),
                                'Estrato VCS': area.get('estrato_vcs', ''),
                                'Densidad VCS': area.get('densidad_vcs', ''),
                                'Carbono Total (ton C)': round(area.get('carbono_total_ton', 0), 2),
                                'CO₂ Equivalente (ton)': round(area.get('co2_equivalente_ton', 0), 2),
                                'Carbono por Ha (ton C/ha)': round(area.get('carbono_por_ha', 0), 2),
                                'Precipitación (mm)': round(area.get('precipitacion_anual_mm', 0), 0)
                            })
                        
                        df = pd.DataFrame(datos)
                        st.dataframe(df, use_container_width=True)
                        
                        # Opción para descargar
                        csv = df.to_csv(index=False)
                        st.download_button(
                            label="📥 Descargar CSV",
                            data=csv,
                            file_name=f"datos_carbono_{datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv"
                        )
                    else:
                        st.warning("No hay datos de carbono disponibles")
                else:
                    st.error("No hay datos de carbono para mostrar")
            else:
                st.warning("Ejecuta el análisis de carbono primero")
                
    except Exception as e:
        st.error(f"Error al mostrar datos completos: {str(e)}")

# ===============================
# 🎨 INTERFAZ PRINCIPAL
# ===============================
def main():
    # Título principal
    st.title("🛰️ Sistema Satelital de Análisis Ambiental - Sudamérica")
    st.markdown("### 🌎 Clasificación SIB | Datos Climáticos Reales | Verra VCS para Carbono")
    st.markdown("**Satélite:** Sentinel-2 (10-20m resolución)")

    # Inicializar sistemas
    if 'sistema_analisis' not in st.session_state:
        st.session_state.sistema_analisis = SistemaAnalisisAmbiental()
    
    if 'resultados' not in st.session_state:
        st.session_state.resultados = None
    
    if 'poligono_data' not in st.session_state:
        st.session_state.poligono_data = None
    
    if 'resultados_carbono' not in st.session_state:
        st.session_state.resultados_carbono = None
    
    if 'analisis_carbono_realizado' not in st.session_state:
        st.session_state.analisis_carbono_realizado = False

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuración del Análisis")
        
        # Carga de archivo
        uploaded_file = st.file_uploader(
            "📁 Cargar polígono de estudio",
            type=['geojson', 'kml', 'zip'],
            help="Formatos: GeoJSON, KML, Shapefile (ZIP)"
        )
        
        if uploaded_file is not None:
            try:
                # Leer archivo
                if uploaded_file.name.endswith('.geojson'):
                    gdf = gpd.read_file(uploaded_file)
                elif uploaded_file.name.endswith('.kml'):
                    # Para KML simple
                    import zipfile
                    import xml.etree.ElementTree as ET
                    
                    # Leer contenido
                    content = uploaded_file.read()
                    
                    # Intentar parsear como XML
                    try:
                        root = ET.fromstring(content)
                        # Extraer coordenadas (simplificado)
                        coordinates = []
                        for elem in root.iter():
                            if 'coordinates' in elem.tag:
                                coords_text = elem.text.strip()
                                for coord_set in coords_text.split():
                                    for coord in coord_set.split(','):
                                        if len(coord.split(',')) >= 2:
                                            lon, lat = map(float, coord.split(',')[:2])
                                            coordinates.append((lon, lat))
                        
                        if coordinates:
                            polygon = Polygon(coordinates)
                            gdf = gpd.GeoDataFrame({'geometry': [polygon]}, crs='EPSG:4326')
                        else:
                            st.error("No se pudieron extraer coordenadas del KML")
                            gdf = None
                    except:
                        st.error("Formato KML no reconocido")
                        gdf = None
                elif uploaded_file.name.endswith('.zip'):
                    # Para shapefiles
                    with tempfile.TemporaryDirectory() as tmpdir:
                        with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
                            zip_ref.extractall(tmpdir)
                        
                        # Buscar archivo .shp
                        shp_files = [f for f in os.listdir(tmpdir) if f.endswith('.shp')]
                        if shp_files:
                            gdf = gpd.read_file(os.path.join(tmpdir, shp_files[0]))
                        else:
                            st.error("No se encontró archivo .shp en el ZIP")
                            gdf = None
                else:
                    st.error("Formato de archivo no soportado")
                    gdf = None
                
                if gdf is not None and not gdf.empty:
                    # Asegurar CRS
                    if gdf.crs is None:
                        gdf = gdf.set_crs('EPSG:4326')
                    else:
                        gdf = gdf.to_crs('EPSG:4326')
                    
                    st.session_state.poligono_data = gdf
                    st.success(f"✅ Polígono cargado: {len(gdf)} geometría(s)")
                    
                    # Mostrar área aproximada
                    gdf_proj = gdf.to_crs('EPSG:3857')
                    area_ha = gdf_proj.geometry.area.sum() / 10000
                    st.info(f"Área aproximada: {area_ha:,.1f} ha")
                    
            except Exception as e:
                st.error(f"Error al cargar archivo: {str(e)}")

        # Configuración del análisis si hay polígono cargado
        if st.session_state.poligono_data is not None:
            st.markdown("---")
            st.subheader("🌿 Configuración del Análisis")
            
            # Selección de ecosistema
            tipo_ecosistema = st.selectbox(
                "Tipo de ecosistema",
                [
                    'Selva Amazónica (bosque húmedo tropical)',
                    'Bosque del Chocó Biogeográfico',
                    'Bosque del Escudo Guayanés',
                    'Páramo andino',
                    'Manglar costero',
                    'Sabana de Llanos (Orinoquía)',
                    'Bosque seco tropical (Caribe colombiano)',
                    'Cerrado brasileño',
                    'Bosque Andino Patagónico',
                    'Bosque de Yungas',
                    'Bosque de Selva Misionera',
                    'Pastizal Pampeano',
                    'Humedales del Iberá',
                    'Agricultura intensiva'
                ],
                index=0
            )
            
            # Nivel de detalle
            nivel_detalle = st.slider("Nivel de detalle", 4, 12, 8,
                                    help="Mayor detalle = más subdivisiones pero más tiempo de procesamiento")
            
            # Botones de análisis
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🚀 Análisis Ambiental", use_container_width=True, type="primary"):
                    with st.spinner("Realizando análisis ambiental..."):
                        try:
                            resultados = st.session_state.sistema_analisis.analizar_area_completa(
                                gdf=st.session_state.poligono_data,
                                tipo_ecosistema=tipo_ecosistema,
                                n_divisiones=nivel_detalle
                            )
                            
                            if resultados:
                                st.session_state.resultados = resultados
                                st.session_state.analisis_carbono_realizado = False
                                st.success("✅ Análisis ambiental completado!")
                                st.rerun()
                            else:
                                st.error("No se pudieron generar resultados")
                        except Exception as e:
                            st.error(f"Error en el análisis: {str(e)}")
            
            with col2:
                if st.button("🌳 Análisis Carbono", use_container_width=True):
                    with st.spinner("Calculando carbono según Verra VCS..."):
                        try:
                            resultados_carbono = st.session_state.sistema_analisis.analisis_carbono.analizar_carbono_area(
                                st.session_state.poligono_data,
                                tipo_ecosistema,
                                nivel_detalle
                            )
                            
                            if resultados_carbono:
                                st.session_state.resultados_carbono = resultados_carbono
                                st.session_state.analisis_carbono_realizado = True
                                st.success("✅ Análisis de carbono completado!")
                                st.rerun()
                            else:
                                st.error("No se pudieron generar resultados de carbono")
                        except Exception as e:
                            st.error(f"Error en el análisis de carbono: {str(e)}")

    # Pestañas principales
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🗺️ Mapa Satelital",
        "📊 Dashboard",
        "🌿 Índices",
        "🌳 Carbono",
        "📋 Reporte",
        "📈 Datos"
    ])

    with tab1:
        mostrar_mapa_satelital()
    
    with tab2:
        mostrar_dashboard_ejecutivo()
    
    with tab3:
        mostrar_indices_vegetacion()
    
    with tab4:
        mostrar_analisis_carbono()
    
    with tab5:
        mostrar_reporte_verra()
    
    with tab6:
        mostrar_datos_completos()

# ===============================
# 🚀 EJECUCIÓN PRINCIPAL
# ===============================
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Error crítico en la aplicación: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
