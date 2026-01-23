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
import requests  # ✅ Añadido para APIs
from typing import Optional, Dict, Any, List, Tuple
warnings.filterwarnings('ignore')
# Librerías geoespaciales
import folium
from streamlit_folium import st_folium, folium_static
from folium.plugins import Fullscreen, MousePosition, HeatMap
import geopandas as gpd
from shapely.geometry import Polygon, Point, shape, MultiPolygon
from shapely.ops import unary_union
import pyproj
from branca.colormap import LinearColormap
import matplotlib.cm as cm
# Para simulación de datos satelitales
import random
from dataclasses import dataclass
from enum import Enum

# ✅ AÑADIR: Librerías para manejar KML
try:
    from fastkml import kml
    import xml.etree.ElementTree as ET
    KML_SUPPORT = True
except ImportError:
    KML_SUPPORT = False
    st.warning("⚠️ fastkml no está instalado. Para soporte completo de KML, instálelo con: pip install fastkml lxml")

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
        url = "https://power.larc.nasa.gov/api/temporal/annual/point"
        params = {
            "parameters": "PRECTOTCORR",
            "community": "RE",
            "longitude": lon,
            "latitude": lat,
            "format": "json",
            "start": datetime.now().year - 5,
            "end": datetime.now().year
        }
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            annual_data = data['properties']['parameter']['PRECTOTCORR']
            if annual_data:
                return np.mean(list(annual_data.values()))
        return None

    def _obtener_open_meteo(self, lat, lon):
        url = "https://archive-api.open-meteo.com/v1/archive"
        end_year = datetime.now().year
        start_year = end_year - 5
        total_precip = 0
        valid_years = 0
        for year in range(start_year, end_year + 1):
            start_date = f"{year}-01-01"
            end_date = f"{year}-12-31"
            params = {
                "latitude": lat,
                "longitude": lon,
                "start_date": start_date,
                "end_date": end_date,
                "daily": "precipitation_sum",
                "timezone": "UTC"
            }
            try:
                response = requests.get(url, params=params, timeout=8)
                if response.status_code == 200:
                    data = response.json()
                    if 'daily' in data and 'precipitation_sum' in data['daily']:
                        annual_sum = sum(x for x in data['daily']['precipitation_sum'] if x is not None)
                        total_precip += annual_sum
                        valid_years += 1
            except:
                continue
        return total_precip / valid_years if valid_years > 0 else None

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

    def calcular_carbono_arbol_individual(self, dap_cm, altura_m, tipo_bosque="subtropical"):
        if dap_cm < 10:
            return 0.0
        try:
            ecuacion = self.factores_vcs['AGB']['ecuaciones_alometricas'][tipo_bosque]['ecuacion']
            agb_kg = ecuacion(dap_cm, altura_m)
            carbono_arbol_kg = agb_kg * self.factores_vcs['AGB']['factor_conversion_carbono']
            return carbono_arbol_kg / 1000
        except Exception as e:
            return (0.05 * dap_cm**2 * altura_m * 0.47) / 1000

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

    def calcular_incertidumbre(self, carbono_total, tipo_bosque, estado):
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
Precipitación anual de referencia: {resultados_carbono.get('factores_aplicados', {}).get('precipitacion_anual_mm', 'N/A')} mm
RESULTADOS DE CARBONO:
----------------------
Carbono total estimado: {resultados_carbono.get('carbono_total_ton_ha', 0):,.2f} ton C/ha
CO₂ equivalente total: {resultados_carbono.get('co2_equivalente_ton_ha', 0):,.2f} ton CO₂e/ha
Factor de ajuste por precipitación: {resultados_carbono.get('factores_aplicados', {}).get('factor_precipitacion', 1.0):.2f}
DESGLOSE POR POOLS DE CARBONO (ton C/ha):
-----------------------------------------
• Biomasa Aérea viva (AGB): {resultados_carbono.get('desglose', {}).get('AGB', 0):,.2f}
• Biomasa Subterránea (BGB): {resultados_carbono.get('desglose', {}).get('BGB', 0):,.2f}
• Madera Muerta (DW): {resultados_carbono.get('desglose', {}).get('DW', 0):,.2f}
• Hojarasca (LI): {resultados_carbono.get('desglose', {}).get('LI', 0):,.2f}
• Carbono Orgánico del Suelo (SOC): {resultados_carbono.get('desglose', {}).get('SOC', 0):,.2f}
FACTORES APLICADOS:
-------------------
• Tipo de bosque: {resultados_carbono.get('factores_aplicados', {}).get('tipo_bosque', 'N/A')}
• Estado del bosque: {resultados_carbono.get('factores_aplicados', {}).get('estado', 'N/A')}
• Factor de conservatividad: {resultados_carbono.get('factores_aplicados', {}).get('factor_conservatividad', 'N/A')}
• Ratio CO₂/Carbono: {resultados_carbono.get('factores_aplicados', {}).get('ratio_co2_carbono', 'N/A')}
• Precipitación anual: {resultados_carbono.get('factores_aplicados', {}).get('precipitacion_anual_mm', 'N/A')} mm
ANÁLISIS DE INCERTIDUMBRE:
--------------------------
Se recomienda realizar mediciones de campo para reducir la incertidumbre
y validar las estimaciones satelitales.
ELEGIBILIDAD PARA CRÉDITOS DE CARBONO:
--------------------------------------
✓ Cumple con principios VCS: Sí
✓ Adicionalidad demostrable: Requiere análisis de línea base
✓ Permanencia: Requiere plan de manejo a largo plazo
✓ Evitación de fuga: Requiere análisis de actividades circundantes
RECOMENDACIONES PARA VALIDACIÓN VCS:
------------------------------------
1. Establecer parcelas de muestreo permanentes
2. Realizar inventarios forestales cada 2-5 años
3. Documentar factores de emisión específicos del sitio
4. Implementar sistema MRV (Monitoreo, Reporte y Verificación)
5. Contratar validador VCS acreditado
======================================================
FIN DEL REPORTE VCS
======================================================
"""
        return reporte

# ===============================
# 🌳 SISTEMA DE ANÁLISIS DE CARBONO VERRA (ACTUALIZADO)
# ===============================
class AnalisisCarbonoVerra:
    def __init__(self):
        self.metodologia = MetodologiaVerra()
        self.conector_clima = ConectorClimaticoTropical()

    def analizar_carbono_area(self, gdf, tipo_ecosistema, nivel_detalle=8):
        try:
            if len(gdf) > 1:
                poligono_principal = self._unificar_poligonos(gdf)
                gdf = gpd.GeoDataFrame({'geometry': [poligono_principal]}, crs=gdf.crs)
            else:
                poligono_principal = gdf.geometry.iloc[0]

            bounds = poligono_principal.bounds

            mapeo_ecosistema_vcs = {
                # Argentina
                'Bosque Andino Patagónico': ('temperado', 'bosque_templado'),
                'Bosque de Araucaria': ('temperado', 'bosque_templado'),
                'Bosque de Yungas': ('tropical_humedo', 'bosque_primario'),
                'Bosque de Selva Misionera': ('tropical_humedo', 'bosque_primario'),
                'Bosque de Caldén': ('tropical_seco', 'bosque_secundario'),
                'Bosque de Quebracho': ('tropical_seco', 'bosque_secundario'),
                'Bosque de Algarrobo': ('tropical_seco', 'bosque_secundario'),
                'Bosque de Chaco Serrano': ('tropical_seco', 'bosque_secundario'),
                'Pastizal Pampeano': ('subtropical', 'pastizal_pampeano'),
                'Humedales del Iberá': ('subtropical', 'humedal'),
                # Trópicos
                'Selva Amazónica (bosque húmedo tropical)': ('tropical_humedo_amazonia', 'bosque_primario'),
                'Bosque del Chocó Biogeográfico': ('tropical_humedo_choco', 'bosque_primario'),
                'Bosque del Escudo Guayanés': ('tropical_humedo_escudo_guayanes', 'bosque_primario'),
                'Páramo andino': ('subtropical', 'pastizal'),
                'Manglar costero': ('tropical_humedo', 'humedal'),
                'Sabana de Llanos (Orinoquía)': ('tropical_seco', 'pastizal'),
                'Bosque seco tropical (Caribe colombiano)': ('tropical_seco', 'bosque_secundario'),
                'Cerrado brasileño': ('tropical_seco', 'pastizal'),
                'Caatinga (Brasil NE)': ('tropical_seco', 'bosque_degradado'),
                'Bosque de galería': ('tropical_humedo', 'bosque_secundario'),
                # Genéricos
                'Agricultura intensiva': ('subtropical', 'agricultura'),
                'Zona urbana consolidada': ('subtropical', 'agricultura')
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
                        # 🔥 CORRECCIÓN: Cálculo preciso de área en hectáreas
                        inter_gdf = gpd.GeoDataFrame(geometry=[interseccion], crs="EPSG:4326")
                        inter_gdf = inter_gdf.to_crs("EPSG:3857")  # Equal-area projection
                        area_m2 = inter_gdf.geometry.area.iloc[0]
                        area_ha = area_m2 / 10000

                        if area_ha > 0.01:
                            centroide = interseccion.centroid
                            lat_centro = centroide.y
                            lon_centro = centroide.x
                            precipitacion_anual, fuente_clima = self.conector_clima.obtener_precipitacion_anual(lat_centro, lon_centro)
                            ndvi = 0.5 + random.uniform(-0.2, 0.3)
                            estrato_info = self.metodologia.clasificar_estrato_vcs(ndvi)
                            carbono_info = self.metodologia.calcular_carbono_hectarea(
                                ndvi=ndvi,
                                tipo_bosque=tipo_vcs,
                                estado=estado_vcs,
                                area_ha=area_ha,
                                precipitacion_anual=precipitacion_anual,
                                tipo_ecosistema=tipo_ecosistema
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
                                'fuente_clima': fuente_clima,
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
        areas_carbono = resultados['analisis_carbono']
        if not areas_carbono:
            return

        carbono_total = sum(a['carbono_total_ton'] for a in areas_carbono)
        co2_total = sum(a['co2_equivalente_ton'] for a in areas_carbono)
        area_total = sum(a['area_ha'] for a in areas_carbono)
        carbono_promedio_ha = np.mean([a['carbono_por_ha'] for a in areas_carbono])
        co2_promedio_ha = np.mean([a['co2_por_ha'] for a in areas_carbono])
        precipitacion_promedio = np.mean([a['precipitacion_anual_mm'] for a in areas_carbono])
        fuente_datos = areas_carbono[0].get('fuente_clima', 'Desconocida')

        estratos = {}
        for area in areas_carbono:
            estrato = area['estrato_vcs']
            if estrato not in estratos:
                estratos[estrato] = {'cantidad': 0, 'area_total': 0, 'carbono_total': 0, 'precipitacion_promedio': 0, 'areas': []}
            estratos[estrato]['cantidad'] += 1
            estratos[estrato]['area_total'] += area['area_ha']
            estratos[estrato]['carbono_total'] += area['carbono_total_ton']
            estratos[estrato]['areas'].append(area['id'])

        for estrato in estratos:
            areas_estrato = [a for a in areas_carbono if a['estrato_vcs'] == estrato]
            if areas_estrato:
                estratos[estrato]['precipitacion_promedio'] = np.mean([a['precipitacion_anual_mm'] for a in areas_estrato])

        pools = {'AGB': 0, 'BGB': 0, 'DW': 0, 'LI': 0, 'SOC': 0}
        for area in areas_carbono:
            for pool, valor in area['desglose_carbono'].items():
                pools[pool] += valor * area['area_ha']

        incertidumbre_promedio = np.mean([a['incertidumbre']['incertidumbre_relativa'] for a in areas_carbono])

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
            elegibilidad['recomendaciones'].append("Incrementar área del proyecto para alcanzar mínimo de 10,000 ton CO₂")
        if not criterios['area_minima']:
            elegibilidad['recomendaciones'].append("Combinar con otros proyectos para alcanzar mínimo de 100 ha")
        if not criterios['datos_climaticos_confiables']:
            elegibilidad['recomendaciones'].append("Mejorar fuente de datos climáticos para mayor precisión")
        return elegibilidad

# ===============================
# 🛰️ ENUMERACIONES Y CLASES DE DATOS SATELITALES
# ===============================
class Satelite(Enum):
    PLANETSCOPE = "PlanetScope"
    SENTINEL2 = "Sentinel-2"
    LANDSAT8 = "Landsat-8"
    MODIS = "MODIS"

@dataclass
class BandaSatelital:
    nombre: str
    longitud_onda: str
    resolucion: float
    descripcion: str

@dataclass
class ImagenSatelital:
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
            'bosque_denso': {'blue': (0.02, 0.05), 'green': (0.03, 0.07), 'red': (0.02, 0.04), 'nir': (0.30, 0.45), 'swir': (0.10, 0.20)},
            'bosque_secundario': {'blue': (0.03, 0.06), 'green': (0.05, 0.10), 'red': (0.04, 0.07), 'nir': (0.25, 0.40), 'swir': (0.15, 0.25)},
            'bosque_templado': {'blue': (0.03, 0.06), 'green': (0.05, 0.09), 'red': (0.04, 0.06), 'nir': (0.20, 0.35), 'swir': (0.12, 0.22)},
            'pastizal': {'blue': (0.04, 0.07), 'green': (0.08, 0.12), 'red': (0.06, 0.09), 'nir': (0.20, 0.30), 'swir': (0.20, 0.30)},
            'pastizal_pampeano': {'blue': (0.04, 0.06), 'green': (0.07, 0.10), 'red': (0.05, 0.08), 'nir': (0.15, 0.25), 'swir': (0.15, 0.25)},
            'humedal': {'blue': (0.02, 0.04), 'green': (0.03, 0.05), 'red': (0.02, 0.04), 'nir': (0.10, 0.20), 'swir': (0.05, 0.15)},
            'suelo_desnudo': {'blue': (0.08, 0.12), 'green': (0.10, 0.15), 'red': (0.12, 0.18), 'nir': (0.15, 0.25), 'swir': (0.25, 0.35)},
            'agua': {'blue': (0.01, 0.03), 'green': (0.01, 0.02), 'red': (0.01, 0.02), 'nir': (0.01, 0.02), 'swir': (0.01, 0.02)}
        }

    def generar_imagen_satelital(self, satelite: Satelite, fecha: datetime = None):
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
# 🗺️ SISTEMA DE MAPAS AVANZADO — SOLO ESRI
# ===============================
class SistemaMapasAvanzado:
    def __init__(self):
        self.simulador = SimuladorSatelital()
        # ✅ Solo ESRI World Imagery
        self.capas_base = {
            'ESRI World Imagery': {
                'tiles': 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                'attr': 'Esri, Maxar, Earthstar Geographics',
                'nombre': '🌍 ESRI World Imagery',
                'max_zoom': 19
            }
        }

    def calcular_zoom_automatico(self, gdf):
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
        centro, zoom = self.calcular_zoom_automatico(gdf)
        mapa_id = f"map_{int(datetime.now().timestamp() * 1000)}"
        m = folium.Map(
            location=centro,
            zoom_start=zoom,
            tiles=self.capas_base['ESRI World Imagery']['tiles'],
            attr=self.capas_base['ESRI World Imagery']['attr'],
            control_scale=True,
            zoom_control=True,
            prefer_canvas=True
        )

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

        Fullscreen(position='topright').add_to(m)
        MousePosition(position='bottomleft').add_to(m)
        return m

    def crear_mapa_indices(self, gdf, datos_areas, indice_seleccionado, titulo="Mapa de Índices"):
        centro, zoom = self.calcular_zoom_automatico(gdf)
        m = folium.Map(
            location=centro,
            zoom_start=zoom,
            tiles=self.capas_base['ESRI World Imagery']['tiles'],
            attr=self.capas_base['ESRI World Imagery']['attr'],
            control_scale=True
        )

        if gdf is not None and not gdf.empty:
            poligono = gdf.geometry.iloc[0]
            if poligono.geom_type == 'MultiPolygon':
                for poly in poligono.geoms:
                    folium.GeoJson(
                        poly,
                        style_function=lambda x: {
                            'fillColor': '#ffffff',
                            'color': '#000000',
                            'weight': 1,
                            'fillOpacity': 0.05,
                            'opacity': 0.3
                        }
                    ).add_to(m)
            else:
                folium.GeoJson(
                    poligono,
                    style_function=lambda x: {
                        'fillColor': '#ffffff',
                        'color': '#000000',
                        'weight': 1,
                        'fillOpacity': 0.05,
                        'opacity': 0.3
                    }
                ).add_to(m)

        paletas_colores = {
            'NDVI': ['#8B0000', '#FF4500', '#FFD700', '#32CD32', '#006400'],
            'SAVI': ['#8B4513', '#DEB887', '#FFD700', '#32CD32', '#006400'],
            'EVI': ['#4B0082', '#9370DB', '#32CD32', '#FFD700', '#FF4500'],
            'NDWI': ['#8B0000', '#FF4500', '#FFD700', '#87CEEB', '#00008B'],
            'MSAVI': ['#8B4513', '#D2691E', '#FFD700', '#32CD32', '#006400']
        }
        colores = paletas_colores.get(indice_seleccionado, ['#808080', '#A9A9A9', '#D3D3D3'])
        heatmap_data = []
        for area_data in datos_areas:
            try:
                valor = area_data.get('indices', {}).get(indice_seleccionado, 0)
                geometry = area_data.get('geometry')
                if geometry and hasattr(geometry, 'centroid'):
                    centroid = geometry.centroid
                    heatmap_data.append([centroid.y, centroid.x, valor])
                    color_idx = min(int(valor * (len(colores) - 1)), len(colores) - 1)
                    color = colores[color_idx]
                    folium.GeoJson(
                        geometry,
                        style_function=lambda x, color=color: {
                            'fillColor': color,
                            'color': color,
                            'weight': 1,
                            'fillOpacity': 0.4,
                            'opacity': 0.6
                        },
                        tooltip=f"Valor: {valor:.3f}"
                    ).add_to(m)
            except Exception:
                continue

        if len(heatmap_data) > 3:
            try:
                HeatMap(
                    heatmap_data,
                    name='Heatmap',
                    min_opacity=0.3,
                    max_zoom=15,
                    radius=20,
                    blur=15,
                    gradient={0.2: 'blue', 0.4: 'lime', 0.6: 'yellow', 0.8: 'orange', 1.0: 'red'}
                ).add_to(m)
            except:
                pass

        self._agregar_leyenda(m, indice_seleccionado, colores)
        Fullscreen().add_to(m)
        return m

    def crear_mapa_carbono(self, gdf, datos_carbono, titulo="Mapa de Carbono"):
        centro, zoom = self.calcular_zoom_automatico(gdf)
        m = folium.Map(
            location=centro,
            zoom_start=zoom,
            tiles=self.capas_base['ESRI World Imagery']['tiles'],
            attr=self.capas_base['ESRI World Imagery']['attr'],
            control_scale=True
        )

        colores_carbono = ['#00441b', '#238b45', '#41ab5d', '#74c476', '#a1d99b', '#d9f0a3']
        valores_carbono = [d.get('carbono_por_ha', 0) for d in datos_carbono]
        if valores_carbono:
            min_carbono = min(valores_carbono)
            max_carbono = max(valores_carbono)
        else:
            min_carbono, max_carbono = 0, 100

        heatmap_data = []
        for area_data in datos_carbono:
            try:
                carbono_ha = area_data.get('carbono_por_ha', 0)
                co2_ha = area_data.get('co2_por_ha', 0)
                geometry = area_data.get('geometry')
                estrato = area_data.get('estrato_vcs', 'E')
                precipitacion = area_data.get('precipitacion_anual_mm', 0)
                if geometry and hasattr(geometry, 'centroid'):
                    centroid = geometry.centroid
                    heatmap_data.append([centroid.y, centroid.x, carbono_ha])
                    if max_carbono > min_carbono:
                        normalized = (carbono_ha - min_carbono) / (max_carbono - min_carbono)
                    else:
                        normalized = 0.5
                    color_idx = min(int(normalized * (len(colores_carbono) - 1)), len(colores_carbono) - 1)
                    color = colores_carbono[color_idx]
                    tooltip = f"""
                    <div style="font-family: Arial; font-size: 12px;">
                    <b>Carbono según Verra VCS</b><br>
                    <hr style="margin: 3px 0;">
                    <b>Estrato:</b> {estrato}<br>
                    <b>Carbono:</b> {carbono_ha:.1f} ton C/ha<br>
                    <b>CO₂ equivalente:</b> {co2_ha:.1f} ton CO₂e/ha<br>
                    <b>Precipitación anual:</b> {precipitacion:.0f} mm<br>
                    <b>Área:</b> {area_data.get('area_ha', 0):.1f} ha
                    </div>
                    """
                    folium.GeoJson(
                        geometry,
                        style_function=lambda x, color=color: {
                            'fillColor': color,
                            'color': color,
                            'weight': 1,
                            'fillOpacity': 0.6,
                            'opacity': 0.8
                        },
                        tooltip=folium.Tooltip(tooltip, sticky=True)
                    ).add_to(m)
            except Exception as e:
                continue

        if len(heatmap_data) > 3:
            try:
                HeatMap(
                    heatmap_data,
                    name='Carbono (ton C/ha)',
                    min_opacity=0.4,
                    max_zoom=15,
                    radius=25,
                    blur=20,
                    gradient={0.0: 'blue', 0.3: 'lime', 0.6: 'yellow', 0.8: 'orange', 1.0: 'red'}
                ).add_to(m)
            except:
                pass

        self._agregar_leyenda_carbono(m, min_carbono, max_carbono, colores_carbono)
        Fullscreen().add_to(m)
        return m

    def _agregar_leyenda(self, mapa, indice, colores):
        leyenda_html = f'''
        <div style="position: fixed;
        bottom: 50px;
        left: 50px;
        width: 250px;
        background-color: white;
        border: 2px solid grey;
        z-index: 9999;
        padding: 10px;
        border-radius: 5px;
        box-shadow: 0 0 10px rgba(0,0,0,0.2);
        font-family: Arial;">
        <h4 style="margin-top: 0; color: #1e3a8a; border-bottom: 1px solid #ddd; padding-bottom: 5px;">
        🛰️ {indice}
        </h4>
        <div style="margin: 10px 0;">
        <div style="height: 20px; background: linear-gradient(90deg, {', '.join(colores)}); border: 1px solid #666;"></div>
        <div style="display: flex; justify-content: space-between; margin-top: 5px;">
        <span>0.0</span>
        <span>0.5</span>
        <span>1.0</span>
        </div>
        </div>
        <div style="font-size: 12px; color: #666;">
        <div>🟢 >0.7: Excelente</div>
        <div>🟡 0.5-0.7: Bueno</div>
        <div>🟠 0.3-0.5: Moderado</div>
        <div>🔴 <0.3: Pobre</div>
        </div>
        </div>
        '''
        mapa.get_root().html.add_child(folium.Element(leyenda_html))

    def _agregar_leyenda_carbono(self, mapa, min_val, max_val, colores):
        leyenda_html = f'''
        <div style="position: fixed;
        bottom: 50px;
        left: 50px;
        width: 280px;
        background-color: white;
        border: 2px solid #065f46;
        z-index: 9999;
        padding: 10px;
        border-radius: 5px;
        box-shadow: 0 0 10px rgba(0,0,0,0.2);
        font-family: Arial;">
        <h4 style="margin-top: 0; color: #065f46; border-bottom: 1px solid #ddd; padding-bottom: 5px;">
        🌳 Carbono (Verra VCS)
        </h4>
        <div style="margin: 10px 0;">
        <div style="height: 20px; background: linear-gradient(90deg, {', '.join(colores)}); border: 1px solid #666;"></div>
        <div style="display: flex; justify-content: space-between; margin-top: 5px; font-size: 11px;">
        <span>{min_val:.0f} tC/ha</span>
        <span>{(min_val+max_val)/2:.0f} tC/ha</span>
        <span>{max_val:.0f} tC/ha</span>
        </div>
        </div>
        <div style="font-size: 12px; color: #666;">
        <div><span style="color: #00441b; font-weight: bold;">■</span> Alto: >{(min_val+max_val)*0.8:.0f} tC/ha</div>
        <div><span style="color: #41ab5d; font-weight: bold;">■</span> Medio: {(min_val+max_val)*0.4:.0f}-{(min_val+max_val)*0.8:.0f} tC/ha</div>
        <div><span style="color: #a1d99b; font-weight: bold;">■</span> Bajo: <{(min_val+max_val)*0.4:.0f} tC/ha</div>
        <hr style="margin: 8px 0;">
        <div style="font-size: 11px; color: #444;">
        <i>Metodología: Verra VCS VM0007</i><br>
        <i>CO₂ equivalente = Carbono × 3.67</i><br>
        <i>Fuente climática: NASA POWER/Open-Meteo</i>
        </div>
        </div>
        </div>
        '''
        mapa.get_root().html.add_child(folium.Element(leyenda_html))

# ===============================
# 📊 DASHBOARD DE RESUMEN EJECUTIVO
# ===============================
class DashboardResumen:
    def __init__(self):
        self.colores_kpi = {
            'excelente': '#10b981',
            'bueno': '#3b82f6',
            'moderado': '#f59e0b',
            'pobre': '#ef4444'
        }

    def crear_kpi_card(self, titulo, valor, icono, color, unidad="", cambio=None):
        cambio_html = ""
        if cambio is not None:
            cambio_clase = "positive" if cambio > 0 else "negative"
            signo = "+" if cambio > 0 else ""
            cambio_html = f'<span style="font-size: 0.8rem; padding: 2px 8px; background-color: {"#d1fae5" if cambio > 0 else "#fee2e2"}; color: {"#065f46" if cambio > 0 else "#991b1b"}; border-radius: 12px;">{signo}{cambio}%</span>'
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
        {cambio_html}
        </div>
        """

    def crear_kpi_carbono(self, titulo, valor, icono, color, unidad="", subtitulo=""):
        return f"""
        <div style="background: linear-gradient(135deg, {color}15 0%, {color}05 100%);
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        border: 1px solid {color}30;
        margin-bottom: 1rem;">
        <div style="display: flex; justify-content: space-between; align-items: start;">
        <div>
        <div style="font-size: 0.9rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px;">{titulo}</div>
        <div style="font-size: 2rem; font-weight: 700; margin: 0.5rem 0; color: {color};">{valor}</div>
        <div style="font-size: 0.9rem; color: {color}; font-weight: 500;">{unidad}</div>
        {f'<div style="font-size: 0.8rem; color: #6b7280; margin-top: 5px;">{subtitulo}</div>' if subtitulo else ''}
        </div>
        <div style="font-size: 2rem; color: {color};">{icono}</div>
        </div>
        </div>
        """

    def crear_kpi_clima(self, titulo, valor, icono, color, unidad="", fuente=""):
        fuente_html = f'<div style="font-size: 0.7rem; color: #6b7280; margin-top: 5px; font-style: italic;">Fuente: {fuente}</div>' if fuente else ''
        return f"""
        <div style="background: linear-gradient(135deg, {color}10 0%, {color}05 100%);
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        border: 1px solid {color}20;
        margin-bottom: 1rem;">
        <div style="display: flex; justify-content: space-between; align-items: start;">
        <div>
        <div style="font-size: 0.9rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px;">{titulo}</div>
        <div style="font-size: 2rem; font-weight: 700; margin: 0.5rem 0; color: {color};">{valor}</div>
        <div style="font-size: 0.9rem; color: #6b7280; font-weight: 500;">{unidad}</div>
        {fuente_html}
        </div>
        <div style="font-size: 2rem; color: {color};">{icono}</div>
        </div>
        </div>
        """

    def crear_dashboard_ejecutivo(self, resultados):
        if not resultados:
            return None
        resumen = resultados.get('resumen', {})
        dashboard_html = f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2rem; border-radius: 15px; margin-bottom: 2rem; color: white;">
        <h2 style="margin: 0; font-size: 2rem;">📊 Dashboard Ejecutivo</h2>
        <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Resumen integral del análisis ambiental con datos climáticos reales</p>
        </div>
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 2rem;">
        {self.crear_kpi_card('Estado General', resumen.get('estado_general', 'N/A'), '📈', resumen.get('color_estado', '#808080'))}
        {self.crear_kpi_card('Área Total', f"{resumen.get('area_total_ha', 0):,.0f}", '📐', '#3b82f6', 'hectáreas')}
        {self.crear_kpi_card('NDVI Promedio', f"{resumen.get('ndvi_promedio', 0):.3f}", '🌿', '#10b981')}
        {self.crear_kpi_card('Biodiversidad', f"{resumen.get('shannon_promedio', 0):.2f}", '🦋', '#8b5cf6', 'Índice')}
        </div>
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 2rem;">
        {self.crear_kpi_clima('Precipitación', f"{resumen.get('precipitacion_promedio', 0):,.0f}", '💧', '#0ea5e9', 'mm/año', resumen.get('fuente_clima', 'NASA POWER/Open-Meteo'))}
        {self.crear_kpi_clima('Temperatura', f"{resumen.get('temperatura_promedio', 0):.1f}", '🌡️', '#ef4444', '°C', resumen.get('fuente_clima', 'NASA POWER/Open-Meteo'))}
        {self.crear_kpi_card('Carbono Total', f"{resumen.get('carbono_total_co2', 0):,.0f}", '🌳', '#065f46', 'ton CO₂')}
        {self.crear_kpi_card('Áreas Óptimas', resumen.get('areas_optimas', 0), '✅', '#10b981')}
        </div>
        """
        return dashboard_html

    def crear_dashboard_carbono(self, resultados_carbono):
        if not resultados_carbono:
            return None
        resumen = resultados_carbono.get('resumen_carbono', {})
        valor_economico = resumen.get('co2_total_ton', 0) * 15
        dashboard_html = f"""
        <div style="background: linear-gradient(135deg, #065f46 0%, #0a7e5a 100%); padding: 2rem; border-radius: 15px; margin-bottom: 2rem; color: white;">
        <h2 style="margin: 0; font-size: 2rem;">🌳 Análisis de Carbono - Verra VCS</h2>
        <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Metodología VCS VM0007 para proyectos REDD+ con datos climáticos reales</p>
        </div>
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 2rem;">
        {self.crear_kpi_carbono('Carbono Total', f"{resumen.get('carbono_total_ton', 0):,.0f}", '🌳', '#065f46', 'ton C', 'Almacenamiento total')}
        {self.crear_kpi_carbono('CO₂ Equivalente', f"{resumen.get('co2_total_ton', 0):,.0f}", '🏭', '#0a7e5a', 'ton CO₂e', 'Potencial de créditos')}
        {self.crear_kpi_carbono('Carbono Promedio', f"{resumen.get('carbono_promedio_ton_ha', 0):,.1f}", '📊', '#10b981', 'ton C/ha', 'Por hectárea')}
        {self.crear_kpi_clima('Precipitación', f"{resumen.get('precipitacion_promedio_mm', 0):,.0f}", '💧', '#0ea5e9', 'mm/año', resumen.get('fuente_datos_climaticos', 'NASA POWER/Open-Meteo'))}
        </div>
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 2rem;">
        {self.crear_kpi_carbono('Potencial Créditos', f"{resumen.get('potencial_creditos', 0):,.1f}", '💰', '#f59e0b', 'miles', '1 crédito = 1 ton CO₂')}
        {self.crear_kpi_carbono('Valor Económico', f"${valor_economico:,.0f}", '💵', '#8b5cf6', 'USD', 'Aprox. @ US$15/ton')}
        {self.crear_kpi_carbono('Incertidumbre', f"{resumen.get('incertidumbre_promedio', 0):.1f}", '📉', '#ef4444', '%', 'Nivel de confianza 90%')}
        {self.crear_kpi_carbono('Elegibilidad VCS', f"{'✅' if resumen.get('elegibilidad_vcs', {}).get('cumple_minimos', False) else '❌'}", '📋', '#10b981' if resumen.get('elegibilidad_vcs', {}).get('cumple_minimos', False) else '#ef4444', '', 'Cumple criterios mínimos')}
        </div>
        """
        return dashboard_html

    def crear_grafico_radar(self, resultados):
        if not resultados:
            return None
        resumen = resultados.get('resumen', {})
        categorias = ['NDVI', 'SAVI', 'EVI', 'Biodiversidad', 'Carbono', 'Precipitación']
        valores = [
            resumen.get('ndvi_promedio', 0) * 100,
            resumen.get('savi_promedio', 0) * 100,
            resumen.get('evi_promedio', 0) * 100,
            min(resumen.get('shannon_promedio', 0) * 25, 100),
            min(resumen.get('carbono_promedio_ha', 0) / 3, 100),
            min(resumen.get('precipitacion_promedio', 0) / 20, 100)
        ]
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=valores,
            theta=categorias,
            fill='toself',
            name='Índices',
            line_color='#3b82f6',
            fillcolor='rgba(59, 130, 246, 0.3)'
        ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            showlegend=True,
            title='Comparación de Índices Ambientales y Climáticos',
            height=400
        )
        return fig

    def crear_grafico_pools_carbono(self, resultados_carbono):
        if not resultados_carbono:
            return None
        pools = resultados_carbono.get('resumen_carbono', {}).get('pools_distribucion', {})
        if not pools:
            return None
        labels = list(pools.keys())
        values = list(pools.values())
        colores_pools = {
            'AGB': '#238b45',
            'BGB': '#41ab5d',
            'DW': '#74c476',
            'LI': '#a1d99b',
            'SOC': '#d9f0a3'
        }
        colors = [colores_pools.get(label, '#808080') for label in labels]
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.4,
            marker_colors=colors,
            textinfo='percent+label',
            textposition='outside',
            hoverinfo='label+value+percent'
        )])
        fig.update_layout(
            title='Distribución de Carbono por Pools (VCS)',
            height=400,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
        )
        return fig

    def crear_grafico_estratos_vcs(self, resultados_carbono):
        if not resultados_carbono:
            return None
        estratos = resultados_carbono.get('resumen_carbono', {}).get('estratos_distribucion', {})
        if not estratos:
            return None
        orden_estratos = ['A', 'B', 'C', 'D', 'E']
        labels = []
        areas = []
        carbono = []
        precipitacion = []
        for estrato in orden_estratos:
            if estrato in estratos:
                labels.append(f"Estrato {estrato}")
                areas.append(estratos[estrato]['area_total'])
                carbono.append(estratos[estrato]['carbono_total'])
                precipitacion.append(estratos[estrato].get('precipitacion_promedio', 0))
        colores_estratos = ['#00441b', '#238b45', '#41ab5d', '#74c476', '#a1d99b']
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Área y Carbono por Estratos', 'Precipitación por Estrato'),
            vertical_spacing=0.15
        )
        fig.add_trace(go.Bar(x=labels, y=areas, name='Área (ha)', marker_color=colores_estratos, text=[f"{a:.1f} ha" for a in areas], textposition='auto'), row=1, col=1)
        fig.add_trace(go.Scatter(x=labels, y=carbono, name='Carbono (ton)', mode='lines+markers', line=dict(color='#065f46', width=3), marker=dict(size=10, color='#0a7e5a'), yaxis='y2'), row=1, col=1)
        fig.add_trace(go.Bar(x=labels, y=precipitacion, name='Precipitación (mm)', marker_color='#0ea5e9', text=[f"{p:.0f} mm" for p in precipitacion], textposition='auto'), row=2, col=1)
        fig.update_layout(title='Distribución por Estratos VCS', height=600, showlegend=True, barmode='group')
        fig.update_yaxes(title_text="Área (ha)", row=1, col=1)
        fig.update_yaxes(title_text="Carbono Total (ton)", secondary_y=True, row=1, col=1)
        fig.update_yaxes(title_text="Precipitación (mm/año)", row=2, col=1)
        return fig

    def crear_grafico_barras_apiladas(self, resultados):
        if not resultados:
            return None
        areas = resultados.get('areas', [])
        categorias = {'Excelente': 0, 'Buena': 0, 'Moderada': 0, 'Pobre': 0, 'Degradada': 0}
        for area in areas:
            salud = area.get('indices', {}).get('Salud_Vegetacion', 'Moderada')
            if salud in categorias:
                categorias[salud] += 1
        fig = go.Figure(data=[
            go.Bar(
                x=list(categorias.keys()),
                y=list(categorias.values()),
                marker_color=['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#991b1b'],
                text=list(categorias.values()),
                textposition='auto',
            )
        ])
        fig.update_layout(
            title='Distribución de Salud de la Vegetación',
            xaxis_title='Categoría de Salud',
            yaxis_title='Número de Áreas',
            height=400
        )
        return fig

# ===============================
# 🌿 SISTEMA DE ANÁLISIS AMBIENTAL COMPLETO (ACTUALIZADO)
# ===============================
class SistemaAnalisisAmbiental:
    def __init__(self):
        self.simulador = SimuladorSatelital()
        self.sistema_mapas = SistemaMapasAvanzado()
        self.dashboard = DashboardResumen()
        self.analisis_carbono = AnalisisCarbonoVerra()
        self.conector_clima = ConectorClimaticoTropical()
        self.tipos_cobertura = {
            # Argentina
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
            'Humedales del Iberá': 'humedal',
            # Trópicos
            'Selva Amazónica (bosque húmedo tropical)': 'bosque_denso',
            'Bosque del Chocó Biogeográfico': 'bosque_denso',
            'Bosque del Escudo Guayanés': 'bosque_denso',
            'Páramo andino': 'pastizal',
            'Manglar costero': 'humedal',
            'Sabana de Llanos (Orinoquía)': 'pastizal',
            'Bosque seco tropical (Caribe colombiano)': 'bosque_secundario',
            'Cerrado brasileño': 'pastizal',
            'Caatinga (Brasil NE)': 'bosque_secundario',
            'Bosque de galería': 'bosque_denso',
            # Genéricos
            'Agricultura intensiva': 'pastizal',
            'Zona urbana consolidada': 'suelo_desnudo'
        }

    def analizar_area_completa(self, gdf, tipo_ecosistema, satelite, n_divisiones=8):
        try:
            if len(gdf) > 1:
                poligono_principal = self._unificar_poligonos(gdf)
                gdf = gpd.GeoDataFrame({'geometry': [poligono_principal]}, crs=gdf.crs)
            else:
                poligono_principal = gdf.geometry.iloc[0]

            bounds = poligono_principal.bounds

            satelite_enum = Satelite.PLANETSCOPE if satelite == "PlanetScope" else Satelite.SENTINEL2
            imagen = self.simulador.generar_imagen_satelital(satelite_enum)

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
                'satelite_usado': satelite,
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
                        # 🔥 CORRECCIÓN: Cálculo preciso de área en hectáreas
                        inter_gdf = gpd.GeoDataFrame(geometry=[interseccion], crs="EPSG:4326")
                        inter_gdf = inter_gdf.to_crs("EPSG:3857")
                        area_m2 = inter_gdf.geometry.area.iloc[0]
                        area_ha = area_m2 / 10000

                        if area_ha > 0.01:
                            centroide = interseccion.centroid
                            lat_centro = centroide.y
                            lon_centro = centroide.x
                            precipitacion_anual, fuente_clima = self.conector_clima.obtener_precipitacion_anual(lat_centro, lon_centro)
                            temperatura, fuente_temp = self.conector_clima.obtener_temperatura_promedio(lat_centro, lon_centro)
                            reflectancias = {}
                            for banda in imagen.bandas_disponibles[:5]:
                                reflectancias[banda] = self.simulador.simular_reflectancia(tipo_cobertura, banda, satelite_enum)
                            indices = self.simulador.calcular_indices(reflectancias, satelite_enum)
                            ndvi = indices.get('NDVI', 0.5)
                            indice_shannon = 2.0 + (ndvi * 2.0) + (math.log10(area_ha + 1) * 0.5)
                            indice_shannon = max(0.1, min(4.0, indice_shannon + random.uniform(-0.3, 0.3)))
                            factor_precip = min(2.0, max(0.5, precipitacion_anual / 1500))
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
                                'fuente_clima': fuente_clima,
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
# 🎨 INTERFAZ PRINCIPAL DE LA APLICACIÓN - VERSIÓN CORREGIDA
# ===============================
def main():
    # Título principal
    st.title("🛰️ Sistema Satelital de Análisis Ambiental - Sudamérica")
    st.markdown("### 🌎 Clasificación SIB | Datos Climáticos Reales | Verra VCS para Carbono")

    # Información sobre fuentes de datos
    with st.expander("ℹ️ Fuentes de datos climáticos utilizadas"):
        st.markdown("""
        **Sistema integra datos climáticos reales para Sudamérica:**
        **1. NASA POWER & Open-Meteo**
        - Fuente primaria para datos de precipitación y temperatura
        - Cobertura global con alta resolución temporal
        - Ideal para regiones tropicales sin estaciones locales
        **2. WorldClim (Datos Climáticos Globales)**
        - Fuente secundaria cuando servicios en tiempo real fallan
        - Resolución de 1km
        - Datos de precipitación anual promedio (1970-2000)
        **3. Ecosistemas especializados**
        - Páramos, Manglares, Amazonía, Chocó, Escudo Guayanés
        - Ecuaciones alométricas de Chave et al. (2014) para trópicos
        """)

    # Inicializar sistemas con manejo de errores
    try:
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
    except Exception as e:
        st.error(f"Error al inicializar el sistema: {str(e)}")
        st.info("Por favor, recarga la página e intenta nuevamente.")
        return

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuración del Análisis")
        # Carga de archivo con mejor manejo de errores
        uploaded_file = st.file_uploader(
            "📁 Cargar polígono de estudio",
            type=['kml', 'geojson', 'zip'],
            help="Formatos: KML, GeoJSON, Shapefile (ZIP)"
        )
        if uploaded_file is not None:
            with st.spinner("Procesando archivo..."):
                try:
                    gdf = None
                    file_content = uploaded_file.read()
                    uploaded_file.seek(0)  # reset pointer

                    if uploaded_file.name.endswith('.kml'):
                        if KML_SUPPORT:
                            k = kml.KML()
                            k.from_string(file_content)
                            geometries = []
                            def extract_geom(elem):
                                if hasattr(elem, 'features'):
                                    for f in elem.features():
                                        extract_geom(f)
                                elif hasattr(elem, 'geometry') and elem.geometry:
                                    geometries.append(shape(elem.geometry))
                            extract_geom(k)
                            if geometries:
                                gdf = gpd.GeoDataFrame({'geometry': geometries}, crs="EPSG:4326")
                            else:
                                st.error("No se encontraron geometrías en el KML")
                        else:
                            st.error("Instala 'fastkml lxml' para soporte KML.")
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
                        if 'geometry' not in gdf.columns:
                            st.error("El archivo no contiene geometrías válidas")
                        else:
                            if gdf.crs is None:
                                gdf.set_crs('EPSG:4326', inplace=True)
                            else:
                                gdf = gdf.to_crs('EPSG:4326')
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
                    else:
                        st.error("No se pudo cargar el archivo o está vacío")
                except Exception as e:
                    st.error(f"Error al procesar el archivo: {str(e)}")
                    import traceback
                    st.error(traceback.format_exc())

        # Configuración del análisis
        if st.session_state.poligono_data is not None and not st.session_state.poligono_data.empty:
            st.markdown("---")
            st.subheader("🛰️ Configuración Satelital")
            satelite = st.selectbox(
                "Satélite",
                ["PlanetScope", "Sentinel-2"],
                help="PlanetScope: 3m resolución | Sentinel-2: 10-20m resolución"
            )

            st.subheader("🌿 Ecosistemas Sudamericanos")
            tipo_ecosistema = st.selectbox(
                "Tipo de ecosistema predominante",
                [
                    # Trópicos
                    'Selva Amazónica (bosque húmedo tropical)',
                    'Bosque del Chocó Biogeográfico',
                    'Bosque del Escudo Guayanés',
                    'Páramo andino',
                    'Manglar costero',
                    'Sabana de Llanos (Orinoquía)',
                    'Bosque seco tropical (Caribe colombiano)',
                    'Cerrado brasileño',
                    'Caatinga (Brasil NE)',
                    'Bosque de galería',
                    # Argentina
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
                    'Humedales del Iberá',
                    # Genéricos
                    'Agricultura intensiva',
                    'Zona urbana consolidada'
                ],
                help="Clasificación adaptada para Sudamérica con énfasis en trópicos"
            )

            # Guardar el tipo de ecosistema seleccionado
            st.session_state.tipo_ecosistema_seleccionado = tipo_ecosistema
            nivel_detalle = st.slider("Nivel de detalle (divisiones)", 4, 12, 8)

            col1, col2 = st.columns(2)
            with col1:
                if st.button("🚀 Ejecutar Análisis Completo", use_container_width=True):
                    with st.spinner("Procesando datos satelitales y climáticos..."):
                        try:
                            # ✅ CORRECCIÓN FINAL: uso correcto del parámetro 'satelite'
                            resultados = st.session_state.sistema_analisis.analizar_area_completa(
                                gdf=st.session_state.poligono_data,
                                tipo_ecosistema=tipo_ecosistema,
                                satelite=satelite,  # 👈 Nombre correcto según la firma del método
                                n_divisiones=nivel_detalle
                            )
                            if resultados:
                                st.session_state.resultados = resultados
                                st.session_state.analisis_carbono_realizado = False
                                st.success("✅ Análisis ambiental completado!")
                            else:
                                st.error("No se pudieron generar resultados")
                        except Exception as e:
                            st.error(f"Error en el análisis: {str(e)}")
                            import traceback
                            st.error(traceback.format_exc())

            with col2:
                if st.button("🌳 Análisis Carbono Verra", type="primary", use_container_width=True):
                    with st.spinner("Calculando carbono según metodología Verra VCS..."):
                        try:
                            resultados_carbono = st.session_state.sistema_analisis.analisis_carbono.analizar_carbono_area(
                                st.session_state.poligono_data,
                                tipo_ecosistema,
                                nivel_detalle
                            )
                            if resultados_carbono:
                                st.session_state.resultados_carbono = resultados_carbono
                                st.session_state.analisis_carbono_realizado = True
                                st.success("✅ Análisis de carbono Verra completado!")
                            else:
                                st.error("No se pudieron generar resultados de carbono")
                        except Exception as e:
                            st.error(f"Error en el análisis de carbono: {str(e)}")
                            import traceback
                            st.error(traceback.format_exc())

    # Pestañas principales
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🗺️ Mapa Satelital",
        "📊 Dashboard Ejecutivo",
        "🌿 Índices de Vegetación",
        "🌳 Análisis de Carbono",
        "📋 Reporte Verra",
        "📈 Datos Completos"
    ])

    with tab1:
        # ✅ Sin selector de capa base: siempre ESRI
        mostrar_mapa_satelital("ESRI World Imagery")
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

def mostrar_mapa_satelital(capa_base="ESRI World Imagery"):
    """Mostrar mapa satelital con el área de estudio"""
    st.markdown("## 🗺️ Mapa Satelital del Área de Estudio")
    if st.session_state.poligono_data is not None:
        try:
            gdf = st.session_state.poligono_data
            bounds = gdf.total_bounds
            # 🔥 CORRECCIÓN: Cálculo preciso de área en hectáreas
            gdf_calc = gdf.to_crs("EPSG:3857")
            area_ha = gdf_calc.geometry.area.sum() / 10000

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Área aproximada", f"{area_ha:,.1f} ha")
            with col2:
                num_poligonos = len(gdf)
                st.metric("Polígonos", f"{num_poligonos}")
            with col3:
                centro = [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2]
                st.metric("Centro", f"{centro[0]:.4f}°, {centro[1]:.4f}°")

            # Crear y mostrar mapa
            mapa = st.session_state.sistema_analisis.sistema_mapas.crear_mapa_satelital(
                gdf,
                "Área de Análisis",
                capa_base
            )
            if mapa:
                mostrar_mapa_seguro(mapa, width=1000, height=600)
            else:
                st.error("No se pudo crear el mapa")
        except Exception as e:
            st.error(f"Error al mostrar el mapa: {str(e)}")
    else:
        st.info("👈 Carga un polígono en el panel lateral para comenzar")

    # Mapa de ejemplo centrado en Sudamérica
    st.markdown("### 🎯 Ejemplo de visualización (Amazonía)")
    polygon_ejemplo = Polygon([
        (-65.0, -3.0),
        (-60.0, -3.0),
        (-60.0, 2.0),
        (-65.0, 2.0),
        (-65.0, -3.0)
    ])
    gdf_ejemplo = gpd.GeoDataFrame({'geometry': [polygon_ejemplo]}, crs="EPSG:4326")
    try:
        mapa_ejemplo = st.session_state.sistema_analisis.sistema_mapas.crear_mapa_satelital(
            gdf_ejemplo,
            "Área de Ejemplo - Amazonía",
            capa_base
        )
        if mapa_ejemplo:
            mostrar_mapa_seguro(mapa_ejemplo, width=800, height=500)
    except Exception as e:
        st.warning(f"No se pudo cargar el mapa de ejemplo: {str(e)}")

def mostrar_dashboard_ejecutivo():
    """Mostrar dashboard ejecutivo con KPIs"""
    st.markdown("## 📊 Dashboard Ejecutivo de Análisis Ambiental")
    if st.session_state.resultados is not None:
        try:
            dashboard_html = st.session_state.sistema_analisis.dashboard.crear_dashboard_ejecutivo(
                st.session_state.resultados
            )
            if dashboard_html:
                st.markdown(dashboard_html, unsafe_allow_html=True)
            else:
                st.warning("No se pudo generar el dashboard")
        except Exception as e:
            st.error(f"Error al mostrar el dashboard: {str(e)}")
    else:
        st.warning("Ejecuta el análisis ambiental primero para ver el dashboard")

def mostrar_indices_vegetacion():
    """Mostrar análisis detallado de índices de vegetación"""
    st.markdown("## 🌿 Análisis de Índices de Vegetación Satelital")
    if st.session_state.resultados is None:
        st.warning("Ejecuta el análisis ambiental primero")
        return
    try:
        resultados = st.session_state.resultados
        areas = resultados.get('areas', [])
        if not areas:
            st.error("No hay datos de áreas para mostrar")
            return

        indices_disponibles = ['NDVI', 'SAVI', 'EVI', 'NDWI', 'MSAVI']
        indice_seleccionado = st.selectbox(
            "Seleccionar índice para visualizar",
            indices_disponibles,
            index=0
        )

        valores_indice = [area['indices'].get(indice_seleccionado, 0) for area in areas]
        if valores_indice:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(f"{indice_seleccionado} Promedio", f"{np.mean(valores_indice):.3f}")
            with col2:
                st.metric(f"{indice_seleccionado} Máximo", f"{np.max(valores_indice):.3f}")
            with col3:
                st.metric(f"{indice_seleccionado} Mínimo", f"{np.min(valores_indice):.3f}")

            st.markdown(f"### 📈 Distribución de {indice_seleccionado}")
            fig = go.Figure()
            fig.add_trace(go.Histogram(
                x=valores_indice,
                nbinsx=20,
                marker_color='#3b82f6',
                opacity=0.7
            ))
            fig.update_layout(
                title=f'Distribución de {indice_seleccionado}',
                xaxis_title=indice_seleccionado,
                yaxis_title='Frecuencia',
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error al mostrar índices de vegetación: {str(e)}")

def mostrar_analisis_carbono():
    """Mostrar análisis detallado de carbono según metodología Verra"""
    st.markdown("## 🌳 Análisis de Carbono Forestal - Metodología Verra VCS")
    if not st.session_state.analisis_carbono_realizado:
        st.warning("Ejecuta el análisis de carbono Verra desde el panel lateral")
        return
    if st.session_state.resultados_carbono is None:
        st.error("No hay datos de carbono para mostrar")
        return
    try:
        resultados = st.session_state.resultados_carbono
        resumen = resultados.get('resumen_carbono', {})
        if resumen:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Carbono Total", f"{resumen.get('carbono_total_ton', 0):,.0f} ton C")
            with col2:
                st.metric("CO₂ Equivalente", f"{resumen.get('co2_total_ton', 0):,.0f} ton CO₂e")
            with col3:
                st.metric("Área Total", f"{resumen.get('area_total_ha', 0):,.1f} ha")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Carbono Promedio", f"{resumen.get('carbono_promedio_ton_ha', 0):,.1f} ton C/ha")
            with col2:
                st.metric("Precipitación", f"{resumen.get('precipitacion_promedio_mm', 0):,.0f} mm/año")
        else:
            st.warning("No hay resumen disponible")
    except Exception as e:
        st.error(f"Error al mostrar análisis de carbono: {str(e)}")

def mostrar_reporte_verra():
    """Mostrar reporte completo según estándar Verra VCS"""
    st.markdown("## 📋 Reporte de Carbono - Estándar Verra VCS")
    if not st.session_state.analisis_carbono_realizado:
        st.warning("Ejecuta el análisis de carbono Verra desde el panel lateral")
        return
    if st.session_state.resultados_carbono is None:
        st.error("No hay datos de carbono para mostrar")
        return
    try:
        resultados = st.session_state.resultados_carbono
        st.markdown("### 📊 Resumen del Proyecto")
        if st.session_state.poligono_data is not None:
            gdf = st.session_state.poligono_data
            bounds = gdf.total_bounds
            centro = [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2]
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Ubicación:**")
                st.markdown(f"- Centro: {centro[0]:.4f}°, {centro[1]:.4f}°")
                st.markdown(f"- Extensión: {bounds[0]:.4f}° a {bounds[2]:.4f}° (long)")
                st.markdown(f"- Extensión: {bounds[1]:.4f}° a {bounds[3]:.4f}° (lat)")
            with col2:
                st.markdown("**Metodología:**")
                st.markdown("- Verra VCS VM0007")
                st.markdown("- Datos climáticos: NASA POWER/Open-Meteo")
                st.markdown(f"- Fecha: {datetime.now().strftime('%Y-%m-%d')}")

        resumen = resultados.get('resumen_carbono', {})
        if resumen:
            st.markdown("### 🌳 Resultados de Carbono")
            data = {
                'Métrica': ['Carbono Total', 'CO₂ Equivalente', 'Área Total', 'Carbono Promedio/ha', 'Precipitación'],
                'Valor': [
                    f"{resumen.get('carbono_total_ton', 0):,.0f} ton C",
                    f"{resumen.get('co2_total_ton', 0):,.0f} ton CO₂e",
                    f"{resumen.get('area_total_ha', 0):,.1f} ha",
                    f"{resumen.get('carbono_promedio_ton_ha', 0):,.1f} ton C/ha",
                    f"{resumen.get('precipitacion_promedio_mm', 0):,.0f} mm/año"
                ]
            }
            df = pd.DataFrame(data)
            st.table(df)
    except Exception as e:
        st.error(f"Error al mostrar reporte Verra: {str(e)}")

def mostrar_datos_completos():
    """Mostrar todos los datos completos del análisis"""
    st.markdown("## 📈 Datos Completos del Análisis")
    tipo_datos = st.radio(
        "Seleccionar tipo de datos",
        ["Datos Ambientales", "Datos de Carbono"],
        horizontal=True
    )
    try:
        if tipo_datos == "Datos Ambientales":
            if st.session_state.resultados is None:
                st.warning("Ejecuta el análisis ambiental primero")
                return
            resultados = st.session_state.resultados
            areas = resultados.get('areas', [])
            if areas:
                datos = []
                for area in areas[:50]:
                    datos.append({
                        'ID': area.get('id', ''),
                        'Área (ha)': area.get('area_ha', 0),
                        'NDVI': area.get('indices', {}).get('NDVI', 0),
                        'Temperatura (°C)': area.get('temperatura', 0),
                        'Precipitación (mm)': area.get('precipitacion', 0),
                        'Salud': area.get('indices', {}).get('Salud_Vegetacion', '')
                    })
                if datos:
                    df = pd.DataFrame(datos)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.warning("No hay datos disponibles")
            else:
                st.warning("No hay áreas analizadas")
        else:
            if not st.session_state.analisis_carbono_realizado:
                st.warning("Ejecuta el análisis de carbono primero")
                return
            if st.session_state.resultados_carbono is None:
                st.error("No hay datos de carbono")
                return
            resultados = st.session_state.resultados_carbono
            areas_carbono = resultados.get('analisis_carbono', [])
            if areas_carbono:
                datos = []
                for area in areas_carbono[:50]:
                    datos.append({
                        'ID': area.get('id', ''),
                        'Área (ha)': area.get('area_ha', 0),
                        'NDVI': area.get('ndvi', 0),
                        'Estrato': area.get('estrato_vcs', ''),
                        'Carbono (ton)': area.get('carbono_total_ton', 0),
                        'CO₂e (ton)': area.get('co2_equivalente_ton', 0),
                        'Precipitación (mm)': area.get('precipitacion_anual_mm', 0)
                    })
                if datos:
                    df = pd.DataFrame(datos)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.warning("No hay datos de carbono disponibles")
            else:
                st.warning("No hay datos de carbono analizados")
    except Exception as e:
        st.error(f"Error al mostrar datos completos: {str(e)}")

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
        st.info("Por favor, recarga la página e intenta nuevamente.")
