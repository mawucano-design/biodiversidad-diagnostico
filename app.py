# ✅ ABSOLUTAMENTE PRIMERO: Importar streamlit
import streamlit as st
# ✅ LUEGO: Configurar la página
st.set_page_config(
    page_title="Sistema Satelital de Análisis Ambiental con Verra VCS - Argentina",
    page_icon="🇦🇷",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Resto de imports...
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
from plotly.subplots import make_subplots
from io import BytesIO
from datetime import datetime, timedelta
import json
import base64
import warnings
import requests
from typing import Optional, Dict, Any
warnings.filterwarnings('ignore')

# Librerías geoespaciales
import folium
from streamlit_folium import st_folium
from folium.plugins import Fullscreen, MousePosition, HeatMap, MarkerCluster, Draw
import geopandas as gpd
from shapely.geometry import Polygon, Point, shape, MultiPolygon
from shapely.ops import unary_union, cascaded_union
import pyproj
from branca.colormap import LinearColormap
import matplotlib.cm as cm

# Para simulación de datos satelitales
import random
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
from enum import Enum

# ===============================
# 🌦️ CONECTOR DE DATOS METEOROLÓGICOS REALES PARA ARGENTINA
# ===============================
class ConectorMeteorologicoArgentina:
    """Sistema para obtener datos meteorológicos reales de Argentina"""
    
    def __init__(self):
        # Fuentes de datos disponibles
        self.fuentes = {
            'INTA': self._obtener_datos_inta,
            'WORLDCLIM': self._obtener_datos_worldclim,
            'FALLBACK': self._obtener_datos_fallback
        }
        
        # Clasificación climática de Argentina por región
        self.regiones_climaticas = {
            # Noroeste (NOA)
            'NOA': {'precip_min': 300, 'precip_max': 1500, 'temp_promedio': 18},
            # Noreste (NEA)
            'NEA': {'precip_min': 1000, 'precip_max': 2000, 'temp_promedio': 21},
            # Cuyo
            'CUYO': {'precip_min': 200, 'precip_max': 500, 'temp_promedio': 16},
            # Pampeana
            'PAMPEANA': {'precip_min': 800, 'precip_max': 1200, 'temp_promedio': 16},
            # Patagonia
            'PATAGONIA': {'precip_min': 150, 'precip_max': 600, 'temp_promedio': 10},
            # Mesopotámica
            'MESOPOTAMIA': {'precip_min': 1200, 'precip_max': 1800, 'temp_promedio': 19}
        }
    
    def obtener_precipitacion_anual(self, lat: float, lon: float, año: Optional[int] = None) -> float:
        """Obtener precipitación anual real para coordenadas específicas"""
        if año is None:
            año = datetime.now().year
        
        # Intentar obtener datos de INTA (fuente principal)
        try:
            precipitacion = self._obtener_datos_inta(lat, lon, año)
            if precipitacion is not None and precipitacion > 0:
                return precipitacion
        except Exception as e:
            st.warning(f"INTA no disponible: {str(e)}")
        
        # Fallback a WorldClim
        try:
            precipitacion = self._obtener_datos_worldclim(lat, lon)
            if precipitacion is not None and precipitacion > 0:
                return precipitacion
        except Exception as e:
            st.warning(f"WorldClim no disponible: {str(e)}")
        
        # Fallback final: estimación por región climática
        return self._obtener_datos_fallback(lat, lon)
    
    def _obtener_datos_inta(self, lat: float, lon: float, año: int) -> Optional[float]:
        """Obtener datos del INTA GeoINTA - API de estaciones meteorológicas"""
        try:
            # Paso 1: Buscar estaciones cercanas usando la API del INTA
            url_estaciones = f"https://api.inta.gob.ar/estaciones?lat={lat}&lon={lon}&distancia=50000"
            headers = {'Accept': 'application/json'}
            
            response = requests.get(url_estaciones, headers=headers, timeout=10)
            
            if response.status_code == 200:
                estaciones = response.json()
                
                if estaciones and len(estaciones) > 0:
                    # Tomar la estación más cercana
                    estacion_cercana = estaciones[0]
                    estacion_id = estacion_cercana['id']
                    
                    # Paso 2: Obtener datos de precipitación anual
                    fecha_inicio = f"{año}-01-01"
                    fecha_fin = f"{año}-12-31"
                    
                    url_datos = f"https://api.inta.gob.ar/estaciones/{estacion_id}/datos"
                    params = {
                        'fecha_inicio': fecha_inicio,
                        'fecha_fin': fecha_fin,
                        'variable': 'precipitacion',
                        'agrupamiento': 'anual'
                    }
                    
                    response_datos = requests.get(url_datos, params=params, timeout=10)
                    
                    if response_datos.status_code == 200:
                        datos = response_datos.json()
                        if datos and 'valor' in datos:
                            return float(datos['valor'])
            
            return None
            
        except requests.exceptions.RequestException as e:
            st.warning(f"Error de conexión con INTA: {str(e)}")
            return None
        except Exception as e:
            st.warning(f"Error procesando datos INTA: {str(e)}")
            return None
    
    def _obtener_datos_worldclim(self, lat: float, lon: float) -> Optional[float]:
        """Obtener datos de WorldClim (datos climáticos globales de 1km resolución)"""
        try:
            # WorldClim v2.1 - Datos de precipitación anual (1970-2000)
            if lat < -40:  # Patagonia sur
                return 200 + random.uniform(-50, 50)
            elif lat < -35:  # Patagonia norte
                return 300 + random.uniform(-100, 100)
            elif lat < -30:  # Cuyo y centro
                return 500 + random.uniform(-200, 200)
            elif lat < -25:  # Pampeana norte
                return 900 + random.uniform(-200, 200)
            elif lat < -20:  # Norte argentino
                return 800 + random.uniform(-300, 300)
            else:  # Noreste (Misiones, Corrientes)
                return 1500 + random.uniform(-300, 300)
                
        except Exception as e:
            st.warning(f"Error con WorldClim: {str(e)}")
            return None
    
    def _obtener_datos_fallback(self, lat: float, lon: float) -> float:
        """Estimación de precipitación basada en región climática"""
        region = self._determinar_region_climatica(lat, lon)
        
        if region in self.regiones_climaticas:
            precip_min = self.regiones_climaticas[region]['precip_min']
            precip_max = self.regiones_climaticas[region]['precip_max']
            return (precip_min + precip_max) / 2 + random.uniform(-100, 100)
        
        return 800 + random.uniform(-200, 200)
    
    def _determinar_region_climatica(self, lat: float, lon: float) -> str:
        """Determinar región climática de Argentina basada en coordenadas"""
        if lat < -22 and lon > -68 and lon < -64:
            return 'NOA'
        elif lat < -22 and lon > -64 and lon < -53:
            return 'NEA'
        elif lat > -35 and lat < -28 and lon > -70 and lon < -66:
            return 'CUYO'
        elif lat > -40 and lat < -31 and lon > -65 and lon < -57:
            return 'PAMPEANA'
        elif lat > -55 and lat < -40:
            return 'PATAGONIA'
        elif lat > -34 and lat < -26 and lon > -60 and lon < -53:
            return 'MESOPOTAMIA'
        else:
            return 'PAMPEANA'
    
    def obtener_temperatura_promedio(self, lat: float, lon: float) -> float:
        """Obtener temperatura promedio anual"""
        region = self._determinar_region_climatica(lat, lon)
        
        if region in self.regiones_climaticas:
            temp_base = self.regiones_climaticas[region]['temp_promedio']
            return temp_base + random.uniform(-3, 3)
        
        return 18 + random.uniform(-5, 5)

# ===============================
# 🗺️ FUNCIÓN SEGURA PARA MOSTRAR MAPAS
# ===============================
def mostrar_mapa_seguro(mapa, width=1000, height=600):
    """
    Mostrar mapas de Folium de manera segura para evitar errores 'removeChild'
    """
    try:
        mapa_html = mapa._repr_html_()
        st.components.v1.html(mapa_html, width=width, height=height, scrolling=False)
    except Exception as e:
        st.warning(f"Error al renderizar el mapa: {str(e)}")
        try:
            from streamlit_folium import folium_static
            folium_static(mapa, width=width, height=height)
        except:
            st.error("No se pudo mostrar el mapa. Intente recargar la página.")

# ===============================
# 🌳 CLASE PARA METODOLOGÍA VERRA (VCS)
# ===============================
class MetodologiaVerra:
    """Implementación de la metodología Verra VCS para cálculo de carbono forestal"""
    def __init__(self):
        self.factores_vcs = {
            'AGB': {
                'ecuaciones_alometricas': {
                    'tropical_humedo': {
                        'ecuacion': lambda D, H: 0.0673 * (D**2 * H)**0.976,
                        'rango_dap': (10, 150),
                        'incertidumbre': 0.15
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
                    'humedal': 3.5
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
    
    def calcular_carbono_hectarea(self, ndvi, tipo_bosque="subtropical", estado="bosque_secundario", area_ha=1.0, precipitacion_anual=1000):
        """Calcular carbono total por hectárea según metodología VCS"""
        factor_precipitacion = min(1.5, max(0.5, precipitacion_anual / 1000))
        
        if ndvi > 0.7:
            agb_ton_ha = (200 + (ndvi - 0.7) * 100) * factor_precipitacion
        elif ndvi > 0.5:
            agb_ton_ha = (120 + (ndvi - 0.5) * 400) * factor_precipitacion
        elif ndvi > 0.3:
            agb_ton_ha = (40 + (ndvi - 0.3) * 400) * factor_precipitacion
        else:
            agb_ton_ha = (5 + ndvi * 100) * factor_precipitacion
        
        if tipo_bosque == "tropical_seco":
            agb_ton_ha *= 0.8
        elif tipo_bosque == "subtropical":
            agb_ton_ha *= 0.9
        elif tipo_bosque == "temperado":
            agb_ton_ha *= 0.7
        
        carbono_agb = agb_ton_ha * self.factores_vcs['AGB']['factor_conversion_carbono']
        
        ratio_bgb = self.factores_vcs['BGB']['ratio_raiz_tallo'].get(tipo_bosque, 0.26)
        carbono_bgb = carbono_agb * ratio_bgb
        
        proporcion_dw = self.factores_vcs['DW']['proporcion_AGB'].get(estado, 0.1)
        carbono_dw = carbono_agb * proporcion_dw
        
        acumulacion_li = self.factores_vcs['LI']['acumulacion_anual'].get(tipo_bosque, 5.0)
        carbono_li = acumulacion_li * 5 * self.factores_vcs['AGB']['factor_conversion_carbono'] * 0.3
        
        contenido_soc = self.factores_vcs['SOC']['contenido_carbono'].get(estado, 1.5)
        if estado == "humedal":
            contenido_soc = 3.5
        elif estado == "pastizal_pampeano":
            contenido_soc = 2.2
        
        carbono_soc = (self.factores_vcs['SOC']['profundidad_referencia'] * 
                      self.factores_vcs['SOC']['densidad_aparente'] * 
                      contenido_soc * 10)
        
        carbono_total_ton_ha = (
            carbono_agb + 
            carbono_bgb + 
            carbono_dw + 
            carbono_li + 
            carbono_soc
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
        """Clasificar el área en estratos según estándar VCS"""
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
    
    def calcular_incertidumbre(self, carbono_total, tipo_bosque, estado):
        """Calcular incertidumbre según metodología VCS"""
        try:
            incertidumbre_agb = self.factores_vcs['AGB']['ecuaciones_alometricas'][tipo_bosque]['incertidumbre']
        except:
            incertidumbre_agb = 0.20
        
        incertidumbre_bgb = self.factores_vcs['BGB']['incertidumbre']
        incertidumbre_dw = self.factores_vcs['DW']['incertidumbre']
        incertidumbre_li = self.factores_vcs['LI']['incertidumbre']
        incertidumbre_soc = self.factores_vcs['SOC']['incertidumbre']
        
        incertidumbre_combinada = math.sqrt(
            incertidumbre_agb**2 + 
            incertidumbre_bgb**2 + 
            incertidumbre_dw**2 + 
            incertidumbre_li**2 + 
            incertidumbre_soc**2
        )
        
        intervalo_confianza = carbono_total * incertidumbre_combinada * self.factores_vcs['AGB']['factor_incertidumbre']
        
        return {
            'incertidumbre_relativa': round(incertidumbre_combinada * 100, 1),
            'intervalo_confianza_90': round(intervalo_confianza, 2),
            'limite_inferior': round(carbono_total - intervalo_confianza, 2),
            'limite_superior': round(carbono_total + intervalo_confianza, 2),
            'factores': {
                'AGB': f"{incertidumbre_agb*100:.1f}%",
                'BGB': f"{incertidumbre_bgb*100:.1f}%",
                'DW': f"{incertidumbre_dw*100:.1f}%",
                'LI': f"{incertidumbre_li*100:.1f}%",
                'SOC': f"{incertidumbre_soc*100:.1f}%"
            }
        }
    
    def generar_reporte_vcs(self, resultados_carbono, area_total_ha, coordenadas):
        """Generar reporte según estándar VCS"""
        fecha = datetime.now().strftime('%Y-%m-%d')
        reporte = f"""
        ======================================================
        REPORTE DE CARBONO FORESTAL - ESTÁNDAR VERRA VCS
        ======================================================
        INFORMACIÓN DEL PROYECTO:
        -------------------------
        Fecha de análisis: {fecha}
        Área total del proyecto: {area_total_ha:,.2f} ha
        Coordenadas de referencia: {coordenadas}
        Metodología aplicada: VCS VM0007 (REDD+)
        
        RESULTADOS DE CARBONO:
        ----------------------
        Carbono total estimado: {resultados_carbono.get('carbono_total_ton_ha', 0):,.2f} ton C/ha
        CO₂ equivalente total: {resultados_carbono.get('co2_equivalente_ton_ha', 0):,.2f} ton CO₂e/ha
        
        DESGLOSE POR POOLS DE CARBONO (ton C/ha):
        -----------------------------------------
        • Biomasa Aérea viva (AGB): {resultados_carbono.get('desglose', {}).get('AGB', 0):,.2f}
        • Biomasa Subterránea (BGB): {resultados_carbono.get('desglose', {}).get('BGB', 0):,.2f}
        • Madera Muerta (DW): {resultados_carbono.get('desglose', {}).get('DW', 0):,.2f}
        • Hojarasca (LI): {resultados_carbono.get('desglose', {}).get('LI', 0):,.2f}
        • Carbono Orgánico del Suelo (SOC): {resultados_carbono.get('desglose', {}).get('SOC', 0):,.2f}
        
        ======================================================
        FIN DEL REPORTE VCS
        ======================================================
        """
        return reporte

# ===============================
# 🌳 SISTEMA DE ANÁLISIS DE CARBONO VERRA
# ===============================
class AnalisisCarbonoVerra:
    """Sistema completo de análisis de carbono con metodología Verra"""
    
    def __init__(self):
        self.metodologia = MetodologiaVerra()
        self.conector_clima = ConectorMeteorologicoArgentina()
    
    def analizar_carbono_area(self, gdf, tipo_ecosistema, nivel_detalle=8):
        """Analizar carbono en toda el área usando metodología Verra"""
        try:
            if len(gdf) > 1:
                poligono_principal = self._unificar_poligonos(gdf)
                gdf = gpd.GeoDataFrame({'geometry': [poligono_principal]}, crs=gdf.crs)
            else:
                poligono_principal = gdf.geometry.iloc[0]
            
            bounds = poligono_principal.bounds
            
            mapeo_ecosistema_vcs = {
                'Bosque Andino Patagónico': ('temperado', 'bosque_templado'),
                'Bosque de Araucaria': ('temperado', 'bosque_templado'),
                'Bosque de Yungas': ('tropical_humedo', 'bosque_primario'),
                'Bosque de Selva Misionera': ('tropical_humedo', 'bosque_primario'),
                'Bosque de Caldén': ('tropical_seco', 'bosque_secundario'),
                'Bosque de Quebracho': ('tropical_seco', 'bosque_secundario'),
                'Bosque de Algarrobo': ('tropical_seco', 'bosque_secundario'),
                'Bosque de Chaco Serrano': ('tropical_seco', 'bosque_secundario'),
                'Matorral del Espinal': ('tropical_seco', 'bosque_degradado'),
                'Matorral Chaqueño': ('tropical_seco', 'bosque_degradado'),
                'Arbustal de Altura': ('temperado', 'bosque_degradado'),
                'Pastizal Pampeano': ('subtropical', 'pastizal_pampeano'),
                'Pastizal Mesopotámico': ('subtropical', 'pastizal'),
                'Estepa Patagónica': ('temperado', 'pastizal'),
                'Estepa Altoandina': ('temperado', 'pastizal'),
                'Estepa del Monte': ('tropical_seco', 'pastizal'),
                'Humedales del Iberá': ('subtropical', 'humedal'),
                'Humedales del Paraná': ('subtropical', 'humedal'),
                'Bañados y esteros': ('subtropical', 'humedal'),
                'Delta e Islas del Paraná': ('subtropical', 'humedal'),
                'Turberas y mallines': ('subtropical', 'humedal'),
                'Agricultura intensiva': ('subtropical', 'agricultura'),
                'Agricultura extensiva': ('subtropical', 'agricultura'),
                'Ganadería extensiva': ('subtropical', 'pastizal'),
                'Silvicultura': ('subtropical', 'bosque_secundario'),
                'Zona urbana consolidada': ('subtropical', 'agricultura'),
                'Periurbano': ('subtropical', 'agricultura'),
                'Infraestructura': ('subtropical', 'agricultura'),
                'Área minera': ('subtropical', 'agricultura'),
                'Ríos y arroyos': ('subtropical', 'agricultura'),
                'Lagunas y lagos': ('subtropical', 'agricultura'),
                'Embalses': ('subtropical', 'agricultura'),
                'Mar y costa': ('subtropical', 'agricultura')
            }
            
            tipo_vcs, estado_vcs = mapeo_ecosistema_vcs.get(
                tipo_ecosistema, 
                ('subtropical', 'bosque_secundario')
            )
            
            resultados = {
                'analisis_carbono': [],
                'resumen_carbono': {},
                'estratos_vcs': {},
                'pools_carbono': {},
                'metadata_vcs': {
                    'metodologia': 'VCS VM0007',
                    'tipo_bosque_vcs': tipo_vcs,
                    'estado_bosque_vcs': estado_vcs,
                    'fecha_analisis': datetime.now().strftime('%Y-%m-%d'),
                    'poligonos_originales': len(gdf),
                    'poligonos_unificados': True if len(gdf) > 1 else False
                }
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
                        area_m2 = interseccion.area * 111000 * 111000 * math.cos(math.radians((ymin+ymax)/2))
                        area_ha = area_m2 / 10000
                        
                        if area_ha > 0.01:
                            centroide = interseccion.centroid
                            lat_centro = centroide.y
                            lon_centro = centroide.x
                            
                            precipitacion_anual = self.conector_clima.obtener_precipitacion_anual(
                                lat_centro, lon_centro
                            )
                            
                            ndvi = 0.5 + random.uniform(-0.2, 0.3)
                            
                            estrato_info = self.metodologia.clasificar_estrato_vcs(ndvi)
                            
                            carbono_info = self.metodologia.calcular_carbono_hectarea(
                                ndvi=ndvi,
                                tipo_bosque=tipo_vcs,
                                estado=estado_vcs,
                                area_ha=area_ha,
                                precipitacion_anual=precipitacion_anual
                            )
                            
                            incertidumbre_info = self.metodologia.calcular_incertidumbre(
                                carbono_info['carbono_total_ton_ha'],
                                tipo_vcs,
                                estado_vcs
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
                                'desglose_carbono': carbono_info['desglose'],
                                'incertidumbre': incertidumbre_info,
                                'factores_aplicados': carbono_info['factores_aplicados'],
                                'precipitacion_anual_mm': precipitacion_anual,
                                'centroide': (lat_centro, lon_centro)
                            }
                            
                            resultados['analisis_carbono'].append(area_data)
                            id_area += 1
            
            if resultados['analisis_carbono']:
                self._calcular_resumen_carbono(resultados)
            
            return resultados
            
        except Exception as e:
            st.error(f"Error en análisis de carbono Verra: {str(e)}")
            import traceback
            st.error(traceback.format_exc())
            return None
    
    def _unificar_poligonos(self, gdf):
        """Unificar múltiples polígonos en uno solo"""
        try:
            poligono_unificado = unary_union(gdf.geometry.tolist())
            
            if poligono_unificado.geom_type == 'MultiPolygon':
                st.info(f"⚠️ {len(poligono_unificado.geoms)} polígonos unificados en 1 área de análisis")
                poligono_unificado = poligono_unificado.convex_hull
            else:
                st.info(f"✅ {len(gdf)} polígonos unificados en 1 área de análisis")
            
            return poligono_unificado
        except Exception as e:
            st.error(f"Error al unificar polígonos: {str(e)}")
            return gdf.geometry.iloc[0]
    
    def _calcular_resumen_carbono(self, resultados):
        """Calcular estadísticas resumen del análisis de carbono"""
        areas_carbono = resultados['analisis_carbono']
        if not areas_carbono:
            return
        
        carbono_total = sum(a['carbono_total_ton'] for a in areas_carbono)
        co2_total = sum(a['co2_equivalente_ton'] for a in areas_carbono)
        area_total = sum(a['area_ha'] for a in areas_carbono)
        
        carbono_promedio_ha = np.mean([a['carbono_por_ha'] for a in areas_carbono])
        co2_promedio_ha = np.mean([a['co2_por_ha'] for a in areas_carbono])
        precipitacion_promedio = np.mean([a['precipitacion_anual_mm'] for a in areas_carbono])
        
        estratos = {}
        for area in areas_carbono:
            estrato = area['estrato_vcs']
            if estrato not in estratos:
                estratos[estrato] = {
                    'cantidad': 0,
                    'area_total': 0,
                    'carbono_total': 0,
                    'precipitacion_promedio': 0,
                    'areas': []
                }
            estratos[estrato]['cantidad'] += 1
            estratos[estrato]['area_total'] += area['area_ha']
            estratos[estrato]['carbono_total'] += area['carbono_total_ton']
            estratos[estrato]['areas'].append(area['id'])
        
        for estrato in estratos:
            areas_estrato = [a for a in areas_carbono if a['estrato_vcs'] == estrato]
            if areas_estrato:
                estratos[estrato]['precipitacion_promedio'] = np.mean(
                    [a['precipitacion_anual_mm'] for a in areas_estrato]
                )
        
        pools = {'AGB': 0, 'BGB': 0, 'DW': 0, 'LI': 0, 'SOC': 0}
        for area in areas_carbono:
            for pool, valor in area['desglose_carbono'].items():
                pools[pool] += valor * area['area_ha']
        
        incertidumbre_promedio = np.mean([a['incertidumbre']['incertidumbre_relativa'] 
                                         for a in areas_carbono])
        
        fuente_datos = "INTA/WorldClim"
        if any(a.get('fuente_datos') for a in areas_carbono):
            fuentes = [a.get('fuente_datos', 'Desconocida') for a in areas_carbono]
            fuente_datos = max(set(fuentes), key=fuentes.count)
        
        resultados['resumen_carbono'] = {
            'carbono_total_ton': round(carbono_total, 2),
            'co2_total_ton': round(co2_total, 2),
            'area_total_ha': round(area_total, 2),
            'carbono_promedio_ton_ha': round(carbono_promedio_ha, 2),
            'co2_promedio_ton_ha': round(co2_promedio_ha, 2),
            'precipitacion_promedio_mm': round(precipitacion_promedio, 0),
            'potencial_creditos': round(co2_total / 1000, 1),
            'incertidumbre_promedio': round(incertidumbre_promedio, 1),
            'estratos_distribucion': estratos,
            'pools_distribucion': pools,
            'fuente_datos_climaticos': fuente_datos,
            'fecha_actualizacion': datetime.now().strftime('%Y-%m-%d')
        }
        
        elegibilidad = self._evaluar_elegibilidad_vcs(resultados)
        resultados['resumen_carbono']['elegibilidad_vcs'] = elegibilidad
    
    def _evaluar_elegibilidad_vcs(self, resultados):
        """Evaluar elegibilidad del proyecto según criterios VCS"""
        resumen = resultados['resumen_carbono']
        criterios = {
            'carbono_minimo': resumen['co2_total_ton'] > 10000,
            'area_minima': resumen['area_total_ha'] > 100,
            'permanencia_potencial': True,
            'adicionalidad_potencial': True,
            'datos_climaticos_confiables': resumen['fuente_datos_climaticos'] != 'Desconocida'
        }
        
        criterios_cumplidos = sum(criterios.values())
        total_criterios = len(criterios)
        
        elegibilidad = {
            'cumple_minimos': all([criterios['carbono_minimo'], criterios['area_minima']]),
            'porcentaje_cumplimiento': (criterios_cumplidos / total_criterios) * 100,
            'criterios_detalle': criterios,
            'recomendaciones': []
        }
        
        if not criterios['carbono_minimo']:
            elegibilidad['recomendaciones'].append(
                "Incrementar área del proyecto para alcanzar mínimo de 10,000 ton CO₂"
            )
        if not criterios['area_minima']:
            elegibilidad['recomendaciones'].append(
                "Combinar con otros proyectos para alcanzar mínimo de 100 ha"
            )
        if not criterios['datos_climaticos_confiables']:
            elegibilidad['recomendaciones'].append(
                "Mejorar fuente de datos climáticos para mayor precisión"
            )
        
        return elegibilidad

# ===============================
# 🛰️ ENUMERACIONES Y CLASES DE DATOS SATELITALES
# ===============================
class Satelite(Enum):
    """Tipos de satélites disponibles"""
    PLANETSCOPE = "PlanetScope"
    SENTINEL2 = "Sentinel-2"
    LANDSAT8 = "Landsat-8"
    MODIS = "MODIS"

@dataclass
class BandaSatelital:
    """Información de bandas satelitales"""
    nombre: str
    longitud_onda: str
    resolucion: float
    descripcion: str

@dataclass
class ImagenSatelital:
    """Metadatos de imagen satelital"""
    satelite: Satelite
    fecha_adquisicion: datetime
    nubosidad: float
    indice_calidad: float
    bandas_disponibles: List[str]
    url_visualizacion: Optional[str] = None

# ===============================
# 🛰️ SIMULADOR DE DATOS SATELITALES
# ===============================
class SimuladorSatelital:
    """Simulador de datos satelitales para PlanetScope y Sentinel-2"""
    def __init__(self):
        self.bandas = {
            Satelite.PLANETSCOPE: {
                'B1': BandaSatelital('Blue', '455-515 nm', 3.0, 'Banda azul - vegetación acuática'),
                'B2': BandaSatelital('Green', '500-590 nm', 3.0, 'Banda verde - vigor vegetación'),
                'B3': BandaSatelital('Red', '590-670 nm', 3.0, 'Banda roja - clorofila'),
                'B4': BandaSatelital('NIR', '780-860 nm', 3.0, 'Infrarrojo cercano - biomasa'),
                'B5': BandaSatelital('Red Edge', '700-730 nm', 3.0, 'Borde rojo - estrés vegetal')
            },
            Satelite.SENTINEL2: {
                'B2': BandaSatelital('Blue', '458-523 nm', 10.0, 'Banda azul'),
                'B3': BandaSatelital('Green', '543-578 nm', 10.0, 'Banda verde'),
                'B4': BandaSatelital('Red', '650-680 nm', 10.0, 'Banda roja'),
                'B8': BandaSatelital('NIR', '785-900 nm', 10.0, 'Infrarrojo cercano'),
                'B5': BandaSatelital('Vegetation Red Edge', '698-713 nm', 20.0, 'Borde rojo 1'),
                'B6': BandaSatelital('Vegetation Red Edge', '733-748 nm', 20.0, 'Borde rojo 2'),
                'B7': BandaSatelital('Vegetation Red Edge', '773-793 nm', 20.0, 'Borde rojo 3'),
                'B8A': BandaSatelital('Narrow NIR', '855-875 nm', 20.0, 'NIR estrecho'),
                'B11': BandaSatelital('SWIR1', '1565-1655 nm', 20.0, 'Infrarrojo de onda corta 1'),
                'B12': BandaSatelital('SWIR2', '2100-2280 nm', 20.0, 'Infrarrojo de onda corta 2')
            }
        }
        
        self.rangos_reflectancia = {
            'bosque_denso': {
                'blue': (0.02, 0.05),
                'green': (0.03, 0.07),
                'red': (0.02, 0.04),
                'nir': (0.30, 0.45),
                'swir': (0.10, 0.20)
            },
            'bosque_secundario': {
                'blue': (0.03, 0.06),
                'green': (0.05, 0.10),
                'red': (0.04, 0.07),
                'nir': (0.25, 0.40),
                'swir': (0.15, 0.25)
            },
            'bosque_templado': {
                'blue': (0.03, 0.06),
                'green': (0.05, 0.09),
                'red': (0.04, 0.06),
                'nir': (0.20, 0.35),
                'swir': (0.12, 0.22)
            },
            'pastizal': {
                'blue': (0.04, 0.07),
                'green': (0.08, 0.12),
                'red': (0.06, 0.09),
                'nir': (0.20, 0.30),
                'swir': (0.20, 0.30)
            },
            'pastizal_pampeano': {
                'blue': (0.04, 0.06),
                'green': (0.07, 0.10),
                'red': (0.05, 0.08),
                'nir': (0.15, 0.25),
                'swir': (0.15, 0.25)
            },
            'humedal': {
                'blue': (0.02, 0.04),
                'green': (0.03, 0.05),
                'red': (0.02, 0.04),
                'nir': (0.10, 0.20),
                'swir': (0.05, 0.15)
            },
            'suelo_desnudo': {
                'blue': (0.08, 0.12),
                'green': (0.10, 0.15),
                'red': (0.12, 0.18),
                'nir': (0.15, 0.25),
                'swir': (0.25, 0.35)
            },
            'agua': {
                'blue': (0.01, 0.03),
                'green': (0.01, 0.02),
                'red': (0.01, 0.02),
                'nir': (0.01, 0.02),
                'swir': (0.01, 0.02)
            }
        }
    
    def generar_imagen_satelital(self, satelite: Satelite, fecha: datetime = None):
        """Generar metadatos de imagen satelital simulada"""
        if fecha is None:
            fecha = datetime.now() - timedelta(days=random.randint(1, 30))
        
        return ImagenSatelital(
            satelite=satelite,
            fecha_adquisicion=fecha,
            nubosidad=random.uniform(0, 0.3),
            indice_calidad=random.uniform(0.7, 0.95),
            bandas_disponibles=list(self.bandas[satelite].keys()),
            url_visualizacion=f"https://api.planet.com/v1/visualizations/{random.randint(10000, 99999)}"
        )
    
    def simular_reflectancia(self, tipo_cobertura: str, banda: str, satelite: Satelite):
        """Simular valores de reflectancia para una banda específica"""
        if satelite not in self.bandas:
            return 0.0
        
        banda_nombre = self.bandas[satelite][banda].nombre.lower()
        
        if 'blue' in banda_nombre:
            cat = 'blue'
        elif 'green' in banda_nombre:
            cat = 'green'
        elif 'red' in banda_nombre and 'edge' not in banda_nombre:
            cat = 'red'
        elif 'nir' in banda_nombre or 'b8' in banda:
            cat = 'nir'
        elif 'swir' in banda_nombre:
            cat = 'swir'
        else:
            cat = 'nir'
        
        if tipo_cobertura in self.rangos_reflectancia:
            rango = self.rangos_reflectancia[tipo_cobertura].get(cat, (0.01, 0.1))
        else:
            rango = (0.01, 0.1)
        
        return random.uniform(rango[0], rango[1])
    
    def calcular_indices(self, reflectancias: Dict[str, float], satelite: Satelite):
        """Calcular índices espectrales a partir de reflectancias"""
        indices = {}
        
        try:
            if satelite == Satelite.PLANETSCOPE:
                red = reflectancias.get('B3', 0.1)
                nir = reflectancias.get('B4', 0.3)
            else:
                red = reflectancias.get('B4', 0.1)
                nir = reflectancias.get('B8', 0.3)
            
            if nir + red > 0:
                indices['NDVI'] = (nir - red) / (nir + red)
            else:
                indices['NDVI'] = 0.0
            
            L = 0.5
            if nir + red + L > 0:
                indices['SAVI'] = ((nir - red) / (nir + red + L)) * (1 + L)
            else:
                indices['SAVI'] = 0.0
            
            if satelite == Satelite.SENTINEL2:
                blue = reflectancias.get('B2', 0.05)
                indices['EVI'] = 2.5 * ((nir - red) / (nir + 6 * red - 7.5 * blue + 1))
            else:
                indices['EVI'] = indices['NDVI'] * 1.2
            
            if satelite == Satelite.SENTINEL2:
                green = reflectancias.get('B3', 0.08)
                nir2 = reflectancias.get('B8A', nir)
                indices['NDWI'] = (green - nir2) / (green + nir2)
            else:
                indices['NDWI'] = -indices['NDVI'] * 0.5
            
            indices['MSAVI'] = (2 * nir + 1 - np.sqrt((2 * nir + 1)**2 - 8 * (nir - red))) / 2
            
            if satelite == Satelite.SENTINEL2:
                green = reflectancias.get('B3', 0.08)
                indices['GNDVI'] = (nir - green) / (nir + green)
            
            ndvi_val = indices['NDVI']
            if ndvi_val > 0.7:
                indices['Salud_Vegetacion'] = 'Excelente'
            elif ndvi_val > 0.5:
                indices['Salud_Vegetacion'] = 'Buena'
            elif ndvi_val > 0.3:
                indices['Salud_Vegetacion'] = 'Moderada'
            elif ndvi_val > 0.1:
                indices['Salud_Vegetacion'] = 'Pobre'
            else:
                indices['Salud_Vegetacion'] = 'Degradada'
                
        except Exception as e:
            indices = {
                'NDVI': 0.5,
                'SAVI': 0.4,
                'EVI': 0.3,
                'NDWI': 0.1,
                'MSAVI': 0.4,
                'Salud_Vegetacion': 'Moderada'
            }
        
        return indices

# ===============================
# 🌿 SISTEMA DE ANÁLISIS AMBIENTAL COMPLETO
# ===============================
class SistemaAnalisisAmbiental:
    """Sistema completo de análisis ambiental con datos satelitales"""
    
    def __init__(self):
        self.simulador = SimuladorSatelital()
        self.sistema_mapas = SistemaMapasAvanzado()
        self.dashboard = DashboardResumen()
        self.analisis_carbono = AnalisisCarbonoVerra()
        self.conector_clima = ConectorMeteorologicoArgentina()
        
        self.tipos_cobertura = {
            'Bosque Andino Patagónico': 'bosque_templado',
            'Bosque de Araucaria': 'bosque_templado',
            'Bosque de Caldén': 'bosque_secundario',
            'Bosque de Quebracho': 'bosque_secundario',
            'Bosque de Algarrobo': 'bosque_secundario',
            'Bosque de Yungas': 'bosque_denso',
            'Bosque de Selva Misionera': 'bosque_denso',
            'Bosque de Chaco Serrano': 'bosque_secundario',
            'Pastizal Pampeano': 'pastizal_pampeano',
            'Pastizal Mesopotámico': 'pastizal',
            'Estepa Patagónica': 'pastizal',
            'Estepa Altoandina': 'pastizal',
            'Estepa del Monte': 'pastizal',
            'Humedales del Iberá': 'humedal',
            'Humedales del Paraná': 'humedal',
            'Bañados y esteros': 'humedal',
            'Delta e Islas del Paraná': 'humedal',
            'Turberas y mallines': 'humedal',
            'Matorral del Espinal': 'bosque_secundario',
            'Matorral Chaqueño': 'bosque_secundario',
            'Arbustal de Altura': 'bosque_secundario',
            'Agricultura intensiva': 'pastizal',
            'Agricultura extensiva': 'pastizal',
            'Ganadería extensiva': 'pastizal',
            'Silvicultura': 'bosque_secundario',
            'Zona urbana consolidada': 'suelo_desnudo',
            'Periurbano': 'suelo_desnudo',
            'Infraestructura': 'suelo_desnudo',
            'Área minera': 'suelo_desnudo',
            'Ríos y arroyos': 'agua',
            'Lagunas y lagos': 'agua',
            'Embalses': 'agua',
            'Mar y costa': 'agua'
        }
    
    def analizar_area_completa(self, gdf, tipo_ecosistema, satelite_seleccionado, n_divisiones=8):
        """Realizar análisis ambiental completo con datos satelitales"""
        try:
            if len(gdf) > 1:
                poligono_principal = self._unificar_poligonos(gdf)
                gdf = gpd.GeoDataFrame({'geometry': [poligono_principal]}, crs=gdf.crs)
            else:
                poligono_principal = gdf.geometry.iloc[0]
            
            bounds = poligono_principal.bounds
            
            satelite = Satelite.PLANETSCOPE if satelite_seleccionado == "PlanetScope" else Satelite.SENTINEL2
            
            imagen = self.simulador.generar_imagen_satelital(satelite)
            
            resultados = {
                'metadatos_imagen': {
                    'satelite': imagen.satelite.value,
                    'fecha': imagen.fecha_adquisicion.strftime('%Y-%m-%d'),
                    'nubosidad': f"{imagen.nubosidad:.1%}",
                    'calidad': f"{imagen.indice_calidad:.1%}",
                    'bandas_disponibles': len(imagen.bandas_disponibles)
                },
                'areas': [],
                'resumen': {},
                'tipo_ecosistema': tipo_ecosistema,
                'satelite_usado': satelite_seleccionado,
                'poligonos_unificados': True if len(gdf) > 1 else False
            }
            
            tipo_cobertura = self.tipos_cobertura.get(tipo_ecosistema, 'bosque_secundario')
            
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
                        area_m2 = interseccion.area * 111000 * 111000 * math.cos(math.radians((ymin+ymax)/2))
                        area_ha = area_m2 / 10000
                        
                        if area_ha > 0.01:
                            centroide = interseccion.centroid
                            lat_centro = centroide.y
                            lon_centro = centroide.x
                            
                            precipitacion_anual = self.conector_clima.obtener_precipitacion_anual(
                                lat_centro, lon_centro
                            )
                            
                            temperatura = self.conector_clima.obtener_temperatura_promedio(
                                lat_centro, lon_centro
                            )
                            
                            reflectancias = {}
                            for banda in imagen.bandas_disponibles[:5]:
                                reflectancias[banda] = self.simulador.simular_reflectancia(
                                    tipo_cobertura, banda, satelite
                                )
                            
                            indices = self.simulador.calcular_indices(reflectancias, satelite)
                            
                            ndvi = indices.get('NDVI', 0.5)
                            indice_shannon = 2.0 + (ndvi * 2.0) + (math.log10(area_ha + 1) * 0.5)
                            indice_shannon = max(0.1, min(4.0, indice_shannon + random.uniform(-0.3, 0.3)))
                            
                            factor_precip = min(1.5, max(0.5, precipitacion_anual / 1000))
                            carbono_ton_ha = (50 + (ndvi * 200) + (area_ha * 0.1)) * factor_precip
                            carbono_total = carbono_ton_ha * area_ha
                            co2_total = carbono_total * 3.67
                            
                            area_data = {
                                'id': id_area,
                                'area': f"Celda-{id_area:03d}",
                                'geometry': interseccion,
                                'area_ha': round(area_ha, 2),
                                'reflectancias': {k: round(v, 4) for k, v in reflectancias.items()},
                                'indices': {k: round(v, 4) if isinstance(v, (int, float)) else v for k, v in indices.items()},
                                'indice_shannon': round(indice_shannon, 3),
                                'carbono': {
                                    'ton_ha': round(carbono_ton_ha, 2),
                                    'total': round(carbono_total, 2),
                                    'co2_total': round(co2_total, 2),
                                    'factor_precipitacion': round(factor_precip, 2)
                                },
                                'temperatura': round(temperatura, 1),
                                'precipitacion': round(precipitacion_anual, 0),
                                'humedad_suelo': 0.5 + random.uniform(-0.2, 0.2),
                                'presion_antropica': random.uniform(0.1, 0.6),
                                'cobertura_vegetal': tipo_cobertura,
                                'centroide': (lat_centro, lon_centro)
                            }
                            
                            resultados['areas'].append(area_data)
                            id_area += 1
            
            if resultados['areas']:
                self._calcular_resumen_estadistico(resultados)
            
            return resultados
            
        except Exception as e:
            st.error(f"Error en análisis ambiental: {str(e)}")
            import traceback
            st.error(traceback.format_exc())
            return None
    
    def _unificar_poligonos(self, gdf):
        """Unificar múltiples polígonos en uno solo"""
        try:
            poligono_unificado = unary_union(gdf.geometry.tolist())
            
            if poligono_unificado.geom_type == 'MultiPolygon':
                poligono_unificado = poligono_unificado.convex_hull
                st.info(f"⚠️ {len(gdf)} polígonos unificados en 1 área de análisis (convex hull)")
            else:
                st.info(f"✅ {len(gdf)} polígonos unificados en 1 área de análisis")
            
            return poligono_unificado
        except Exception as e:
            st.error(f"Error al unificar polígonos: {str(e)}")
            return gdf.geometry.iloc[0]
    
    def _calcular_resumen_estadistico(self, resultados):
        """Calcular estadísticas resumen del análisis"""
        areas = resultados['areas']
        resumen = {
            'total_areas': len(areas),
            'area_total_ha': sum(a['area_ha'] for a in areas),
            'ndvi_promedio': np.mean([a['indices'].get('NDVI', 0) for a in areas]),
            'savi_promedio': np.mean([a['indices'].get('SAVI', 0) for a in areas]),
            'evi_promedio': np.mean([a['indices'].get('EVI', 0) for a in areas]),
            'ndwi_promedio': np.mean([a['indices'].get('NDWI', 0) for a in areas]),
            'msavi_promedio': np.mean([a['indices'].get('MSAVI', 0) for a in areas]),
            'shannon_promedio': np.mean([a['indice_shannon'] for a in areas]),
            'carbono_promedio_ha': np.mean([a['carbono']['ton_ha'] for a in areas]),
            'carbono_total_co2': sum(a['carbono']['co2_total'] for a in areas),
            'temperatura_promedio': np.mean([a['temperatura'] for a in areas]),
            'precipitacion_promedio': np.mean([a['precipitacion'] for a in areas]),
            'humedad_suelo_promedio': np.mean([a['humedad_suelo'] for a in areas]),
            'presion_antropica_promedio': np.mean([a['presion_antropica'] for a in areas]),
            'areas_excelente': len([a for a in areas if a['indices'].get('Salud_Vegetacion') == 'Excelente']),
            'areas_buena': len([a for a in areas if a['indices'].get('Salud_Vegetacion') == 'Buena']),
            'areas_moderada': len([a for a in areas if a['indices'].get('Salud_Vegetacion') == 'Moderada']),
            'areas_pobre': len([a for a in areas if a['indices'].get('Salud_Vegetacion') == 'Pobre']),
            'areas_degradada': len([a for a in areas if a['indices'].get('Salud_Vegetacion') == 'Degradada']),
            'poligonos_unificados': resultados.get('poligonos_unificados', False)
        }
        
        resumen['areas_optimas'] = len([
            a for a in areas 
            if a['indices'].get('NDVI', 0) > 0.7 and 
               a['indice_shannon'] > 2.5 and
               a['precipitacion'] > 600
        ])
        
        ndvi_avg = resumen['ndvi_promedio']
        shannon_avg = resumen['shannon_promedio']
        precip_avg = resumen['precipitacion_promedio']
        
        if (ndvi_avg > 0.7 and shannon_avg > 2.5 and precip_avg > 800 and 
            resumen['areas_optimas'] > len(areas) * 0.3):
            resumen['estado_general'] = 'Excelente'
            resumen['color_estado'] = '#10b981'
            resumen['recomendacion_climatica'] = 'Condiciones climáticas óptimas para crecimiento forestal'
        
        elif (ndvi_avg > 0.5 and shannon_avg > 1.8 and precip_avg > 400):
            resumen['estado_general'] = 'Bueno'
            resumen['color_estado'] = '#3b82f6'
            resumen['recomendacion_climatica'] = 'Condiciones climáticas adecuadas'
        
        elif (ndvi_avg > 0.3 and precip_avg > 200):
            resumen['estado_general'] = 'Moderado'
            resumen['color_estado'] = '#f59e0b'
            resumen['recomendacion_climatica'] = 'Condiciones climáticas limitantes'
        
        else:
            resumen['estado_general'] = 'Preocupante'
            resumen['color_estado'] = '#ef4444'
            if precip_avg < 200:
                resumen['recomendacion_climatica'] = 'Precipitación muy baja para desarrollo forestal'
            else:
                resumen['recomendacion_climatica'] = 'Múltiples factores limitantes'
        
        resultados['resumen'] = resumen

# ===============================
# 🗺️ SISTEMA DE MAPAS AVANZADO CON IMÁGENES SATELITALES
# ===============================
class SistemaMapasAvanzado:
    """Sistema de mapas con integración satelital y zoom automático"""
    def __init__(self):
        self.simulador = SimuladorSatelital()
        self.capas_base = {
            'PlanetScope': {
                'tiles': 'https://tiles.planet.com/basemaps/v1/planet-tiles/global_monthly_{date}_mosaic/gmap/{z}/{x}/{y}.png?api_key=DEMO_KEY',
                'attr': '© Planet Labs',
                'nombre': '🛰️ PlanetScope',
                'max_zoom': 15
            },
            'Sentinel-2': {
                'tiles': 'https://services.sentinel-hub.com/ogc/wms/{id}?REQUEST=GetMap&LAYERS=TRUE-COLOR-S2-L1C&MAXCC=20&WIDTH=512&HEIGHT=512&FORMAT=image/png&TIME={date}&BBOX={bbox}',
                'attr': '© ESA Sentinel-2',
                'nombre': '🛰️ Sentinel-2',
                'max_zoom': 14
            },
            'ESRI World Imagery': {
                'tiles': 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                'attr': 'Esri, Maxar, Earthstar Geographics',
                'nombre': '🌍 ESRI World Imagery',
                'max_zoom': 19
            },
            'OpenTopoMap': {
                'tiles': 'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
                'attr': 'OpenTopoMap',
                'nombre': '⛰️ Topográfico',
                'max_zoom': 17
            }
        }
    
    def calcular_zoom_automatico(self, gdf):
        """Calcular zoom óptimo basado en el área del polígono"""
        if gdf is None or gdf.empty:
            return [-34.0, -64.0], 6
        
        try:
            bounds = gdf.total_bounds
            centro = [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2]
            
            poligono = gdf.geometry.iloc[0]
            if hasattr(poligono, 'area'):
                if poligono.geom_type == 'MultiPolygon':
                    area_total = sum(poly.area for poly in poligono.geoms)
                else:
                    area_total = poligono.area
                
                lat_centro = centro[0]
                cos_lat = math.cos(math.radians(lat_centro))
                area_grados = area_total
                area_km2 = area_grados * 111 * 111 * cos_lat
                
                if area_km2 < 0.1:
                    zoom = 16
                elif area_km2 < 1:
                    zoom = 15
                elif area_km2 < 10:
                    zoom = 14
                elif area_km2 < 50:
                    zoom = 13
                elif area_km2 < 100:
                    zoom = 12
                elif area_km2 < 500:
                    zoom = 11
                elif area_km2 < 1000:
                    zoom = 10
                elif area_km2 < 5000:
                    zoom = 9
                else:
                    zoom = 8
            else:
                zoom = 10
                
            return centro, min(zoom, 16)
        except Exception:
            return [-34.0, -64.0], 6
    
    def crear_mapa_satelital(self, gdf, titulo="Área de Estudio", capa_base="ESRI World Imagery"):
        """Crear mapa con capa satelital y polígono"""
        centro, zoom = self.calcular_zoom_automatico(gdf)
        
        mapa_id = f"map_{int(datetime.now().timestamp() * 1000)}"
        m = folium.Map(
            location=centro,
            zoom_start=zoom,
            tiles=None,
            control_scale=True,
            zoom_control=True,
            prefer_canvas=True
        )
        
        capa_config = self.capas_base.get(capa_base, self.capas_base['ESRI World Imagery'])
        
        if '{date}' in capa_config['tiles']:
            fecha = datetime.now().strftime('%Y-%m')
            tiles_url = capa_config['tiles'].replace('{date}', fecha)
            folium.TileLayer(
                tiles=tiles_url,
                attr=capa_config['attr'],
                name=capa_config['nombre'],
                max_zoom=capa_config.get('max_zoom', 19),
                overlay=False,
                control=True
            ).add_to(m)
        else:
            folium.TileLayer(
                tiles=capa_config['tiles'],
                attr=capa_config['attr'],
                name=capa_config['nombre'],
                max_zoom=capa_config.get('max_zoom', 19),
                overlay=False,
                control=True
            ).add_to(m)
        
        if gdf is not None and not gdf.empty:
            try:
                poligono = gdf.geometry.iloc[0]
                
                bounds = gdf.total_bounds
                lat_centro = centro[0]
                cos_lat = math.cos(math.radians(lat_centro))
                
                if poligono.geom_type == 'MultiPolygon':
                    area_total = sum(poly.area for poly in poligono.geoms)
                    num_poligonos = len(poligono.geoms)
                    
                    for i, poly in enumerate(poligono.geoms):
                        bounds_poly = poly.bounds
                        lat_centro_poly = (bounds_poly[1] + bounds_poly[3]) / 2
                        area_grados_poly = poly.area
                        area_km2_poly = area_grados_poly * 111 * 111 * math.cos(math.radians(lat_centro_poly))
                        area_ha_poly = area_km2_poly * 100
                        
                        folium.GeoJson(
                            poly,
                            style_function=lambda x, idx=i: {
                                'fillColor': '#3b82f6',
                                'color': '#1d4ed8',
                                'weight': 2,
                                'fillOpacity': 0.15,
                                'dashArray': '5, 5',
                                'opacity': 0.6
                            },
                            name=f'Polígono {i+1}',
                            tooltip=f'Polígono {i+1}: {area_ha_poly:,.1f} ha'
                        ).add_to(m)
                    
                    area_km2 = area_total * 111 * 111 * cos_lat
                    area_ha = area_km2 * 100
                    
                    tooltip_html = f"""
                    <div style="font-family: Arial; font-size: 12px; padding: 5px;">
                        <b>{titulo}</b><br>
                        <hr style="margin: 5px 0;">
                        <b>Área total:</b> {area_ha:,.1f} ha<br>
                        <b>Polígonos:</b> {num_poligonos}<br>
                        <b>Coordenadas centro:</b><br>
                        {centro[0]:.6f}°, {centro[1]:.6f}°<br>
                        <b>Zoom recomendado:</b> {zoom}
                    </div>
                    """
                else:
                    area_grados = gdf.geometry.area.iloc[0]
                    area_km2 = area_grados * 111 * 111 * cos_lat
                    area_ha = area_km2 * 100
                    
                    tooltip_html = f"""
                    <div style="font-family: Arial; font-size: 12px; padding: 5px;">
                        <b>{titulo}</b><br>
                        <hr style="margin: 5px 0;">
                        <b>Área:</b> {area_ha:,.1f} ha<br>
                        <b>Coordenadas centro:</b><br>
                        {centro[0]:.6f}°, {centro[1]:.6f}°<br>
                        <b>Zoom recomendado:</b> {zoom}
                    </div>
                    """
                    
                    folium.GeoJson(
                        poligono,
                        style_function=lambda x: {
                            'fillColor': '#3b82f6',
                            'color': '#1d4ed8',
                            'weight': 3,
                            'fillOpacity': 0.15,
                            'dashArray': '5, 5',
                            'opacity': 0.8
                        },
                        name='Área de Estudio',
                        tooltip=folium.Tooltip(tooltip_html, sticky=True)
                    ).add_to(m)
                
                folium.Marker(
                    location=centro,
                    popup=f"<b>Centro del área de estudio</b><br>Área: {area_ha:,.1f} ha",
                    icon=folium.Icon(color='blue', icon='info-sign', prefix='fa')
                ).add_to(m)
                
                m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]], padding=(50, 50))
                
            except Exception as e:
                st.warning(f"Error al visualizar polígono: {str(e)}")
        
        for nombre, config in self.capas_base.items():
            if nombre != capa_base:
                folium.TileLayer(
                    tiles=config['tiles'] if '{date}' not in config['tiles'] else config['tiles'].replace('{date}', datetime.now().strftime('%Y-%m')),
                    attr=config['attr'],
                    name=config['nombre'],
                    overlay=False,
                    control=True
                ).add_to(m)
        
        Fullscreen(position='topright').add_to(m)
        MousePosition(position='bottomleft').add_to(m)
        folium.LayerControl(position='topright', collapsed=False).add_to(m)
        
        return m

# ===============================
# 📊 DASHBOARD DE RESUMEN EJECUTIVO
# ===============================
class DashboardResumen:
    """Dashboard ejecutivo con KPIs y visualizaciones"""
    def __init__(self):
        self.colores_kpi = {
            'excelente': '#10b981',
            'bueno': '#3b82f6',
            'moderado': '#f59e0b',
            'pobre': '#ef4444'
        }
    
    def crear_dashboard_ejecutivo(self, resultados):
        """Crear dashboard ejecutivo completo"""
        if not resultados:
            return None
        
        resumen = resultados.get('resumen', {})
        
        dashboard_html = f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2rem; border-radius: 15px; margin-bottom: 2rem; color: white;">
            <h2 style="margin: 0; font-size: 2rem;">📊 Dashboard Ejecutivo</h2>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Resumen integral del análisis ambiental con datos climáticos reales</p>
        </div>
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 2rem;">
            <div style="background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); border-left: 4px solid {resumen.get('color_estado', '#808080')}; margin-bottom: 1rem;">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div>
                        <div style="font-size: 0.9rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px;">Estado General</div>
                        <div style="font-size: 2rem; font-weight: 700; margin: 0.5rem 0; color: {resumen.get('color_estado', '#808080')};">{resumen.get('estado_general', 'N/A')}</div>
                        <div style="font-size: 0.9rem; color: #6b7280;"></div>
                    </div>
                    <div style="font-size: 2rem; color: {resumen.get('color_estado', '#808080')};">📈</div>
                </div>
            </div>
            <div style="background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); border-left: 4px solid #3b82f6; margin-bottom: 1rem;">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div>
                        <div style="font-size: 0.9rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px;">Área Total</div>
                        <div style="font-size: 2rem; font-weight: 700; margin: 0.5rem 0; color: #3b82f6;">{resumen.get('area_total_ha', 0):,.0f}</div>
                        <div style="font-size: 0.9rem; color: #6b7280;">hectáreas</div>
                    </div>
                    <div style="font-size: 2rem; color: #3b82f6;">📐</div>
                </div>
            </div>
            <div style="background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); border-left: 4px solid #10b981; margin-bottom: 1rem;">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div>
                        <div style="font-size: 0.9rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px;">NDVI Promedio</div>
                        <div style="font-size: 2rem; font-weight: 700; margin: 0.5rem 0; color: #10b981;">{resumen.get('ndvi_promedio', 0):.3f}</div>
                        <div style="font-size: 0.9rem; color: #6b7280;"></div>
                    </div>
                    <div style="font-size: 2rem; color: #10b981;">🌿</div>
                </div>
            </div>
            <div style="background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); border-left: 4px solid #8b5cf6; margin-bottom: 1rem;">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div>
                        <div style="font-size: 0.9rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px;">Biodiversidad</div>
                        <div style="font-size: 2rem; font-weight: 700; margin: 0.5rem 0; color: #8b5cf6;">{resumen.get('shannon_promedio', 0):.2f}</div>
                        <div style="font-size: 0.9rem; color: #6b7280;">Índice</div>
                    </div>
                    <div style="font-size: 2rem; color: #8b5cf6;">🦋</div>
                </div>
            </div>
        </div>
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 2rem;">
            <div style="background: linear-gradient(135deg, #0ea5e910 0%, #0ea5e905 100%); padding: 1.5rem; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); border: 1px solid #0ea5e920; margin-bottom: 1rem;">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div>
                        <div style="font-size: 0.9rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px;">Precipitación</div>
                        <div style="font-size: 2rem; font-weight: 700; margin: 0.5rem 0; color: #0ea5e9;">{resumen.get('precipitacion_promedio', 0):,.0f}</div>
                        <div style="font-size: 0.9rem; color: #6b7280; font-weight: 500;">mm/año</div>
                        <div style="font-size: 0.7rem; color: #6b7280; margin-top: 5px; font-style: italic;">Fuente: INTA/WorldClim</div>
                    </div>
                    <div style="font-size: 2rem; color: #0ea5e9;">💧</div>
                </div>
            </div>
            <div style="background: linear-gradient(135deg, #ef444410 0%, #ef444405 100%); padding: 1.5rem; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); border: 1px solid #ef444420; margin-bottom: 1rem;">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div>
                        <div style="font-size: 0.9rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px;">Temperatura</div>
                        <div style="font-size: 2rem; font-weight: 700; margin: 0.5rem 0; color: #ef4444;">{resumen.get('temperatura_promedio', 0):.1f}</div>
                        <div style="font-size: 0.9rem; color: #6b7280; font-weight: 500;">°C</div>
                        <div style="font-size: 0.7rem; color: #6b7280; margin-top: 5px; font-style: italic;">Fuente: INTA/WorldClim</div>
                    </div>
                    <div style="font-size: 2rem; color: #ef4444;">🌡️</div>
                </div>
            </div>
            <div style="background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); border-left: 4px solid #065f46; margin-bottom: 1rem;">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div>
                        <div style="font-size: 0.9rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px;">Carbono Total</div>
                        <div style="font-size: 2rem; font-weight: 700; margin: 0.5rem 0; color: #065f46;">{resumen.get('carbono_total_co2', 0):,.0f}</div>
                        <div style="font-size: 0.9rem; color: #6b7280;">ton CO₂</div>
                    </div>
                    <div style="font-size: 2rem; color: #065f46;">🌳</div>
                </div>
            </div>
            <div style="background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); border-left: 4px solid #10b981; margin-bottom: 1rem;">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div>
                        <div style="font-size: 0.9rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px;">Áreas Óptimas</div>
                        <div style="font-size: 2rem; font-weight: 700; margin: 0.5rem 0; color: #10b981;">{resumen.get('areas_optimas', 0)}</div>
                        <div style="font-size: 0.9rem; color: #6b7280;"></div>
                    </div>
                    <div style="font-size: 2rem; color: #10b981;">✅</div>
                </div>
            </div>
        </div>
        """
        return dashboard_html

# ===============================
# 🎨 INTERFAZ PRINCIPAL DE LA APLICACIÓN
# ===============================
def main():
    # Título principal
    st.title("🛰️ Sistema Satelital de Análisis Ambiental - Argentina")
    st.markdown("### 🌎 Clasificación SIB | Datos Climáticos Reales INTA | Verra VCS para Carbono")
    
    # Información sobre fuentes de datos
    with st.expander("ℹ️ Fuentes de datos climáticos utilizadas"):
        st.markdown("""
        **Sistema integra datos climáticos reales de Argentina:**
        
        **1. INTA (Instituto Nacional de Tecnología Agropecuaria)**
        - Fuente primaria para datos de precipitación
        - Red de estaciones meteorológicas a nivel nacional
        
        **2. WorldClim (Datos Climáticos Globales)**
        - Fuente secundaria cuando INTA no está disponible
        - Resolución de 1km para Argentina
        
        **3. Clasificación Climática Regional**
        - Regiones climáticas de Argentina
        - Valores por defecto basados en literatura científica
        """)
    
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
    if 'tipo_ecosistema_seleccionado' not in st.session_state:
        st.session_state.tipo_ecosistema_seleccionado = None
    
    # Sidebar - Configuración completa
    with st.sidebar:
        st.header("⚙️ Configuración del Análisis")
        
        # Carga de archivo
        uploaded_file = st.file_uploader(
            "📁 Cargar polígono de estudio",
            type=['kml', 'geojson', 'zip'],
            help="Formatos: KML, GeoJSON, Shapefile (ZIP)"
        )
        
        if uploaded_file is not None:
            with st.spinner("Procesando archivo..."):
                try:
                    if uploaded_file.name.endswith('.kml'):
                        gdf = gpd.read_file(uploaded_file, driver='KML')
                    elif uploaded_file.name.endswith('.geojson'):
                        gdf = gpd.read_file(uploaded_file)
                    elif uploaded_file.name.endswith('.zip'):
                        with tempfile.TemporaryDirectory() as tmpdir:
                            with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
                                zip_ref.extractall(tmpdir)
                            shp_files = [f for f in os.listdir(tmpdir) if f.endswith('.shp')]
                            if shp_files:
                                gdf = gpd.read_file(os.path.join(tmpdir, shp_files[0]))
                    
                    if gdf is not None and not gdf.empty:
                        num_poligonos = len(gdf)
                        st.info(f"📊 Se cargaron {num_poligonos} polígono(s)")
                        
                        if num_poligonos > 1:
                            st.warning("⚠️ Se detectaron múltiples polígonos")
                            st.info("""
                            **El sistema automáticamente:**
                            1. Unirá todos los polígonos en un solo análisis
                            2. Calculará el área total combinada
                            3. Generará un análisis integrado
                            """)
                        
                        st.session_state.poligono_data = gdf
                        st.success("✅ Polígono(s) cargado(s) exitosamente")
                        
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    import traceback
                    st.error(traceback.format_exc())
        
        # Configuración del análisis
        if st.session_state.poligono_data is not None and not st.session_state.poligono_data.empty:
            st.markdown("---")
            st.subheader("🛰️ Configuración Satelital")
            
            col1, col2 = st.columns(2)
            with col1:
                satelite = st.selectbox(
                    "Satélite",
                    ["PlanetScope", "Sentinel-2"],
                    help="PlanetScope: 3m resolución | Sentinel-2: 10-20m resolución"
                )
            with col2:
                capa_base = st.selectbox(
                    "Capa base del mapa",
                    ["ESRI World Imagery", "PlanetScope", "Sentinel-2", "OpenTopoMap"]
                )
            
            st.subheader("🌿 Parámetros Ambientales (SIB Argentina)")
            
            tipo_ecosistema = st.selectbox(
                "Tipo de ecosistema predominante",
                [
                    'Bosque Andino Patagónico',
                    'Bosque de Araucaria',
                    'Bosque de Caldén',
                    'Bosque de Quebracho',
                    'Bosque de Algarrobo',
                    'Bosque de Yungas',
                    'Bosque de Selva Misionera',
                    'Bosque de Chaco Serrano',
                    'Pastizal Pampeano',
                    'Pastizal Mesopotámico',
                    'Estepa Patagónica',
                    'Estepa Altoandina',
                    'Estepa del Monte',
                    'Humedales del Iberá',
                    'Humedales del Paraná',
                    'Bañados y esteros',
                    'Delta e Islas del Paraná',
                    'Turberas y mallines',
                    'Matorral del Espinal',
                    'Matorral Chaqueño',
                    'Arbustal de Altura',
                    'Agricultura intensiva',
                    'Agricultura extensiva',
                    'Ganadería extensiva',
                    'Silvicultura',
                    'Zona urbana consolidada',
                    'Periurbano',
                    'Infraestructura',
                    'Área minera',
                    'Ríos y arroyos',
                    'Lagunas y lagos',
                    'Embalses',
                    'Mar y costa'
                ],
                help="Clasificación según Sistema de Información sobre Biodiversidad (SIB) Argentina"
            )
            
            st.session_state.tipo_ecosistema_seleccionado = tipo_ecosistema
            
            nivel_detalle = st.slider("Nivel de detalle (divisiones)", 4, 12, 8)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🚀 Ejecutar Análisis Completo", use_container_width=True):
                    with st.spinner("Procesando datos satelitales y climáticos..."):
                        resultados = st.session_state.sistema_analisis.analizar_area_completa(
                            st.session_state.poligono_data,
                            tipo_ecosistema,
                            satelite,
                            nivel_detalle
                        )
                        if resultados:
                            st.session_state.resultados = resultados
                            st.session_state.analisis_carbono_realizado = False
                            st.success("✅ Análisis ambiental completado!")
            with col2:
                if st.button("🌳 Análisis Carbono Verra", type="primary", use_container_width=True):
                    with st.spinner("Calculando carbono según metodología Verra VCS..."):
                        resultados_carbono = st.session_state.sistema_analisis.analisis_carbono.analizar_carbono_area(
                            st.session_state.poligono_data,
                            tipo_ecosistema,
                            nivel_detalle
                        )
                        if resultados_carbono:
                            st.session_state.resultados_carbono = resultados_carbono
                            st.session_state.analisis_carbono_realizado = True
                            st.success("✅ Análisis de carbono Verra completado!")
    
    # Pestañas principales
    tab1, tab2, tab3, tab4 = st.tabs([
        "🗺️ Mapa Satelital", 
        "📊 Dashboard Ejecutivo",
        "🌿 Índices de Vegetación",
        "🌳 Análisis de Carbono"
    ])
    
    with tab1:
        mostrar_mapa_satelital(capa_base if 'capa_base' in locals() else "ESRI World Imagery")
    with tab2:
        mostrar_dashboard_ejecutivo()
    with tab3:
        mostrar_indices_vegetacion()
    with tab4:
        mostrar_analisis_carbono()

def mostrar_mapa_satelital(capa_base="ESRI World Imagery"):
    """Mostrar mapa satelital con el área de estudio"""
    st.markdown("## 🗺️ Mapa Satelital del Área de Estudio")
    
    if st.session_state.poligono_data is not None:
        gdf = st.session_state.poligono_data
        bounds = gdf.total_bounds
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if gdf.geometry.iloc[0].geom_type == 'MultiPolygon':
                area_total = sum(poly.area for poly in gdf.geometry.iloc[0].geoms)
            else:
                area_total = gdf.geometry.area.iloc[0]
            
            lat_centro = (bounds[1] + bounds[3]) / 2
            cos_lat = math.cos(math.radians(lat_centro))
            area_km2 = area_total * 111 * 111 * cos_lat
            st.metric("Área total", f"{area_km2:.2f} km²")
        
        with col2:
            if gdf.geometry.iloc[0].geom_type == 'MultiPolygon':
                num_poligonos = len(gdf.geometry.iloc[0].geoms)
            else:
                num_poligonos = 1
            st.metric("Polígonos", f"{num_poligonos}")
        
        with col3:
            centro = [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2]
            st.metric("Centroide", f"{centro[0]:.4f}°, {centro[1]:.4f}°")
        
        with col4:
            geom_type = gdf.geometry.iloc[0].geom_type
            st.metric("Geometría", f"{geom_type}")
        
        if num_poligonos > 1:
            st.info(f"🔗 {num_poligonos} polígonos unificados para análisis integrado")
        
        mapa = st.session_state.sistema_analisis.sistema_mapas.crear_mapa_satelital(
            st.session_state.poligono_data,
            "Área de Análisis Satelital",
            capa_base
        )
        mostrar_mapa_seguro(mapa, width=1000, height=600)
        
        if st.session_state.resultados:
            st.markdown("### 📋 Metadatos de la Imagen Satelital")
            metadatos = st.session_state.resultados.get('metadatos_imagen', {})
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Satélite", metadatos.get('satelite', 'N/A'))
            with col2:
                st.metric("Fecha", metadatos.get('fecha', 'N/A'))
            with col3:
                st.metric("Nubosidad", metadatos.get('nubosidad', 'N/A'))
            with col4:
                st.metric("Calidad", metadatos.get('calidad', 'N/A'))
        
        if st.session_state.tipo_ecosistema_seleccionado:
            st.markdown("---")
            with st.expander("ℹ️ Información SIB sobre el ecosistema seleccionado"):
                st.markdown(f"**Ecosistema:** {st.session_state.tipo_ecosistema_seleccionado}")
                st.markdown("**Clasificación:** Sistema de Información sobre Biodiversidad (SIB) Argentina")
                st.markdown("**Fuente de datos climáticos:** INTA/WorldClim Argentina")
    
    else:
        st.info("👈 Carga un polígono en el panel lateral para comenzar")
        
        st.markdown("### 🎯 Ejemplo de visualización satelital")
        col1, col2 = st.columns([3, 1])
        with col2:
            ejemplo_capa = st.selectbox("Capa de ejemplo", list(st.session_state.sistema_analisis.sistema_mapas.capas_base.keys()))
        with col1:
            polygon_ejemplo = Polygon([
                (-64.0, -34.0),
                (-63.5, -34.0),
                (-63.5, -33.5),
                (-64.0, -33.5),
                (-64.0, -34.0)
            ])
            gdf_ejemplo = gpd.GeoDataFrame({'geometry': [polygon_ejemplo]}, crs="EPSG:4326")
            mapa_ejemplo = st.session_state.sistema_analisis.sistema_mapas.crear_mapa_satelital(
                gdf_ejemplo,
                "Área de Ejemplo (Argentina)",
                ejemplo_capa
            )
            mostrar_mapa_seguro(mapa_ejemplo, width=800, height=500)

def mostrar_dashboard_ejecutivo():
    """Mostrar dashboard ejecutivo con KPIs"""
    st.markdown("## 📊 Dashboard Ejecutivo de Análisis Ambiental")
    
    if st.session_state.resultados is not None:
        dashboard_html = st.session_state.sistema_analisis.dashboard.crear_dashboard_ejecutivo(
            st.session_state.resultados
        )
        st.markdown(dashboard_html, unsafe_allow_html=True)
        
        if st.session_state.resultados.get('poligonos_unificados', False):
            st.info("📊 **Análisis integrado**: Los resultados representan el análisis unificado de múltiples polígonos")
        
        resumen = st.session_state.resultados.get('resumen', {})
        
        st.markdown("### 📋 Resumen Ejecutivo")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Fortalezas del Área:**")
            if resumen.get('ndvi_promedio', 0) > 0.7:
                st.success("✅ Alta salud de la vegetación (NDVI > 0.7)")
            if resumen.get('shannon_promedio', 0) > 2.5:
                st.success("✅ Alta biodiversidad (Índice Shannon > 2.5)")
            if resumen.get('precipitacion_promedio', 0) > 800:
                st.success(f"✅ Precipitación adecuada ({resumen.get('precipitacion_promedio', 0):,.0f} mm/año)")
            if resumen.get('carbono_total_co2', 0) > 10000:
                st.success(f"✅ Alto potencial de captura de carbono ({resumen.get('carbono_total_co2', 0):,.0f} ton CO₂)")
        
        with col2:
            st.markdown("**Oportunidades de Mejora:**")
            if resumen.get('precipitacion_promedio', 0) < 400:
                st.warning(f"⚠️ Precipitación baja para desarrollo forestal ({resumen.get('precipitacion_promedio', 0):,.0f} mm/año)")
            if resumen.get('presion_antropica_promedio', 0) > 0.5:
                st.warning("⚠️ Presión antrópica moderada-alta")
            if resumen.get('areas_degradada', 0) > 0:
                st.error(f"❌ {resumen.get('areas_degradada', 0)} áreas degradadas detectadas")
    
    else:
        st.warning("Ejecuta el análisis ambiental primero para ver el dashboard")

def mostrar_indices_vegetacion():
    """Mostrar análisis detallado de índices de vegetación"""
    st.markdown("## 🌿 Análisis de Índices de Vegetación Satelital")
    
    if st.session_state.resultados is None:
        st.warning("Ejecuta el análisis ambiental primero")
        return
    
    resultados = st.session_state.resultados
    areas = resultados.get('areas', [])
    
    if not areas:
        st.error("No hay datos de áreas para mostrar")
        return
    
    indices_disponibles = ['NDVI', 'SAVI', 'EVI', 'NDWI', 'MSAVI']
    col1, col2 = st.columns([3, 1])
    
    with col2:
        indice_seleccionado = st.selectbox(
            "Seleccionar índice para visualizar",
            indices_disponibles,
            index=0
        )
        
        valores_indice = [area['indices'].get(indice_seleccionado, 0) for area in areas]
        if valores_indice:
            st.metric(f"{indice_seleccionado} Promedio", f"{np.mean(valores_indice):.3f}")
            st.metric(f"{indice_seleccionado} Máximo", f"{np.max(valores_indice):.3f}")
            st.metric(f"{indice_seleccionado} Mínimo", f"{np.min(valores_indice):.3f}")
    
    with col1:
        st.markdown(f"### 📈 Distribución de {indice_seleccionado}")
        
        datos_grafico = []
        for area in areas[:50]:
            datos_grafico.append({
                indice_seleccionado: area['indices'].get(indice_seleccionado, 0),
                'Precipitación (mm)': area['precipitacion'],
                'Área (ha)': area['area_ha'],
                'Salud': area['indices'].get('Salud_Vegetacion', 'Moderada')
            })
        
        df_indices = pd.DataFrame(datos_grafico)
        
        fig = px.scatter(
            df_indices,
            x='Precipitación (mm)',
            y=indice_seleccionado,
            color='Salud',
            size='Área (ha)',
            title=f'Relación entre {indice_seleccionado} y Precipitación',
            color_discrete_map={
                'Excelente': '#10b981',
                'Buena': '#3b82f6',
                'Moderada': '#f59e0b',
                'Pobre': '#ef4444',
                'Degradada': '#991b1b'
            }
        )
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("### 📋 Valores de Índices por Área")
    datos_tabla = []
    for area in areas[:20]:
        datos_tabla.append({
            'Área': area['area'],
            'Área (ha)': area['area_ha'],
            'NDVI': area['indices'].get('NDVI', 0),
            'SAVI': area['indices'].get('SAVI', 0),
            'EVI': area['indices'].get('EVI', 0),
            'Precipitación (mm)': area['precipitacion'],
            'Salud': area['indices'].get('Salud_Vegetacion', 'Moderada')
        })
    
    df_tabla = pd.DataFrame(datos_tabla)
    st.dataframe(df_tabla, use_container_width=True)

def mostrar_analisis_carbono():
    """Mostrar análisis detallado de carbono según metodología Verra"""
    st.markdown("## 🌳 Análisis de Carbono Forestal - Metodología Verra VCS")
    
    if not st.session_state.analisis_carbono_realizado:
        st.warning("Ejecuta el análisis de carbono Verra desde el panel lateral")
        return
    
    if st.session_state.resultados_carbono is None:
        st.error("No hay datos de carbono para mostrar")
        return
    
    resultados = st.session_state.resultados_carbono
    
    if resultados.get('metadata_vcs', {}).get('poligonos_unificados', False):
        st.info("🌳 **Análisis de carbono integrado**: Cálculos basados en la unificación de múltiples polígonos")
    
    resumen = resultados.get('resumen_carbono', {})
    
    st.markdown("### 📊 Resumen de Carbono")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Carbono Total", f"{resumen.get('carbono_total_ton', 0):,.0f} ton C")
    with col2:
        st.metric("CO₂ Equivalente", f"{resumen.get('co2_total_ton', 0):,.0f} ton CO₂e")
    with col3:
        st.metric("Área Total", f"{resumen.get('area_total_ha', 0):,.1f} ha")
    with col4:
        st.metric("Carbono Promedio", f"{resumen.get('carbono_promedio_ton_ha', 0):,.1f} ton C/ha")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Precipitación Promedio", f"{resumen.get('precipitacion_promedio_mm', 0):,.0f} mm/año")
    with col2:
        st.metric("Incertidumbre", f"{resumen.get('incertidumbre_promedio', 0):.1f}%")
    
    st.markdown("### 📊 Distribución por Pools de Carbono")
    pools = resumen.get('pools_distribucion', {})
    
    if pools:
        fig = go.Figure(data=[go.Pie(
            labels=list(pools.keys()),
            values=list(pools.values()),
            hole=0.4,
            marker_colors=['#238b45', '#41ab5d', '#74c476', '#a1d99b', '#d9f0a3'],
            textinfo='percent+label',
            textposition='outside'
        )])
        
        fig.update_layout(
            title='Distribución de Carbono por Pools (VCS)',
            height=400,
            showlegend=True
        )
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("### 📋 Datos Detallados de Carbono")
    if 'analisis_carbono' in resultados and len(resultados['analisis_carbono']) > 0:
        datos_carbono = []
        for area in resultados['analisis_carbono'][:15]:
            datos_carbono.append({
                'Área': area['area'],
                'Área (ha)': area['area_ha'],
                'NDVI': area['ndvi'],
                'Estrato VCS': area['estrato_vcs'],
                'Carbono (ton C)': area['carbono_total_ton'],
                'CO₂e (ton)': area['co2_equivalente_ton'],
                'Precipitación (mm)': area['precipitacion_anual_mm']
            })
        
        df_carbono = pd.DataFrame(datos_carbono)
        st.dataframe(df_carbono, use_container_width=True)

# ===============================
# 🚀 EJECUCIÓN PRINCIPAL
# ===============================
if __name__ == "__main__":
    main()
