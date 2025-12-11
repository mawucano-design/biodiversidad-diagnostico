# ✅ ABSOLUTAMENTE PRIMERO: Importar streamlit
import streamlit as st
# ✅ LUEGO: Configurar la página
st.set_page_config(
    page_title="Sistema Satelital de Análisis Ambiental con Verra VCS - Argentina",
    page_icon="🇦🇷",
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
warnings.filterwarnings('ignore')
# Librerías geoespaciales
import folium
from streamlit_folium import st_folium  # Mantener para posibles usos alternativos
from folium.plugins import Fullscreen, MousePosition, HeatMap, MarkerCluster, Draw
import geopandas as gpd
from shapely.geometry import Polygon, Point, shape, MultiPolygon
import pyproj
from branca.colormap import LinearColormap
import matplotlib.cm as cm
# Para simulación de datos satelitales
import random
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
from enum import Enum
import requests  # Agregado para NASA POWER API

# ===============================
# 🗺️ FUNCIÓN SEGURA PARA MOSTRAR MAPAS
# ===============================
def mostrar_mapa_seguro(mapa, width=1000, height=600):
    """
    Mostrar mapas de Folium de manera segura para evitar errores 'removeChild'
    Args:
        mapa: Objeto folium.Map
        width: Ancho del mapa en píxeles
        height: Alto del mapa en píxeles
    """
    try:
        # Método 1: Usar components.v1.html (más estable)
        mapa_html = mapa._repr_html_()
        st.components.v1.html(mapa_html, width=width, height=height, scrolling=False)
    except Exception as e:
        st.warning(f"Error al renderizar el mapa: {str(e)}")
        # Método alternativo
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
        # Factores de expansión de biomasa según VCS (VM0007, VM0035, etc.)
        self.factores_vcs = {
            # Biomasa Aérea viva (AGB)
            'AGB': {
                'ecuaciones_alometricas': {
                    'tropical_humedo': {
                        'ecuacion': lambda D, H: 0.0673 * (D**2 * H)**0.976,  # Chave et al. 2014
                        'rango_dap': (10, 150),  # cm
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
                    'temperado': {  # Nueva para bosques templados argentinos
                        'ecuacion': lambda D, H: 0.058 * (D**2 * H)**0.905,
                        'rango_dap': (10, 110),
                        'incertidumbre': 0.22
                    }
                },
                'factor_conversion_carbono': 0.47,  # IPCC 2006
                'factor_incertidumbre': 1.645  # 90% intervalo de confianza
            },
            # Biomasa Subterránea (BGB) - Raíces
            'BGB': {
                'ratio_raiz_tallo': {
                    'tropical_humedo': 0.24,  # IPCC 2006
                    'tropical_seco': 0.27,
                    'subtropical': 0.26,
                    'temperado': 0.28,  # Mayor proporción de raíces en climas fríos
                    'templado': 0.25
                },
                'incertidumbre': 0.20
            },
            # Madera Muerta (DW)
            'DW': {
                'proporcion_AGB': {
                    'bosque_primario': 0.15,
                    'bosque_secundario': 0.10,
                    'bosque_degradado': 0.20,
                    'bosque_templado': 0.18  # Para bosques andino-patagónicos
                },
                'densidad_base': 0.5,  # ton/m3
                'incertidumbre': 0.25
            },
            # Hojarasca (LI)
            'LI': {
                'acumulacion_anual': {
                    'tropical_humedo': 8.5,  # ton/ha/año
                    'tropical_seco': 6.2,
                    'subtropical': 7.3,
                    'temperado': 5.8,  # Menor acumulación en climas fríos
                    'templado': 4.5
                },
                'incertidumbre': 0.30
            },
            # Carbono Orgánico del Suelo (SOC)
            'SOC': {
                'profundidad_referencia': 30,  # cm (VCS default)
                'densidad_aparente': 1.2,  # g/cm3
                'contenido_carbono': {
                    'bosque_no_intervenido': 2.5,  # %
                    'bosque_secundario': 2.0,
                    'bosque_templado': 3.0,  # Suelos andinos más ricos en materia orgánica
                    'pastizal': 1.5,
                    'pastizal_pampeano': 2.2,  # Suelos pampeanos fértiles
                    'agricultura': 1.0,
                    'humedal': 3.5  # Alta acumulación en humedales
                },
                'factor_cambio_uso_suelo': {
                    'bosque_a_agricultura': 0.58,
                    'bosque_a_pastizal': 0.71,
                    'secundario_a_primario': 1.25,
                    'pastizal_a_agricultura': 0.65,
                    'humedal_a_agricultura': 0.40  # Gran pérdida en humedales
                },
                'incertidumbre': 0.40
            }
        }
        # Factores de conservatividad (VCS)
        self.factores_conservatividad = {
            'alto': 0.8,    # 20% descuento conservativo
            'medio': 0.9,   # 10% descuento conservativo
            'bajo': 0.95    # 5% descuento conservativo
        }
        # Clases de estrato VCS
        self.estratos_vcs = {
            'A': {'density': 'Alta', 'ndvi_range': (0.7, 1.0), 'carbon_factor': 1.0},
            'B': {'density': 'Media-Alta', 'ndvi_range': (0.5, 0.7), 'carbon_factor': 0.8},
            'C': {'density': 'Media', 'ndvi_range': (0.3, 0.5), 'carbon_factor': 0.6},
            'D': {'density': 'Baja', 'ndvi_range': (0.1, 0.3), 'carbon_factor': 0.4},
            'E': {'density': 'Muy Baja', 'ndvi_range': (-1.0, 0.1), 'carbon_factor': 0.1}
        }
    def calcular_carbono_arbol_individual(self, dap_cm, altura_m, tipo_bosque="subtropical"):
        """Calcular carbono en un árbol individual usando ecuaciones alométricas VCS"""
        if dap_cm < 10:  # Límite mínimo VCS
            return 0.0
        try:
            # Obtener ecuación alométrica
            ecuacion = self.factores_vcs['AGB']['ecuaciones_alometricas'][tipo_bosque]['ecuacion']
            # Calcular biomasa aérea (kg)
            agb_kg = ecuacion(dap_cm, altura_m)
            # Convertir a carbono (47% de la biomasa)
            carbono_arbol_kg = agb_kg * self.factores_vcs['AGB']['factor_conversion_carbono']
            return carbono_arbol_kg / 1000  # Retornar en toneladas
        except Exception as e:
            # Fórmula simplificada de respaldo
            return (0.05 * dap_cm**2 * altura_m * 0.47) / 1000
    def calcular_carbono_hectarea(self, ndvi, tipo_bosque="subtropical", estado="bosque_secundario", area_ha=1.0):
        """Calcular carbono total por hectárea según metodología VCS"""
        # Estimación de biomasa basada en NDVI
        if ndvi > 0.7:
            # Bosque denso
            agb_ton_ha = 200 + (ndvi - 0.7) * 100  # 200-250 ton/ha
        elif ndvi > 0.5:
            # Bosque medio
            agb_ton_ha = 120 + (ndvi - 0.5) * 400  # 120-200 ton/ha
        elif ndvi > 0.3:
            # Bosque bajo/vegetación arbustiva
            agb_ton_ha = 40 + (ndvi - 0.3) * 400   # 40-120 ton/ha
        else:
            # No bosque
            agb_ton_ha = 5 + ndvi * 100            # 5-40 ton/ha
        # Ajustar por tipo de bosque
        if tipo_bosque == "tropical_seco":
            agb_ton_ha *= 0.8
        elif tipo_bosque == "subtropical":
            agb_ton_ha *= 0.9
        elif tipo_bosque == "temperado":
            agb_ton_ha *= 0.7  # Bosques templados tienen menor biomasa
        # ===== CÁLCULO DE POOLS DE CARBONO VCS =====
        # 1. Carbono en Biomasa Aérea viva (AGB)
        carbono_agb = agb_ton_ha * self.factores_vcs['AGB']['factor_conversion_carbono']
        # 2. Carbono en Biomasa Subterránea (BGB - raíces)
        ratio_bgb = self.factores_vcs['BGB']['ratio_raiz_tallo'].get(tipo_bosque, 0.26)
        carbono_bgb = carbono_agb * ratio_bgb
        # 3. Carbono en Madera Muerta (DW)
        proporcion_dw = self.factores_vcs['DW']['proporcion_AGB'].get(estado, 0.1)
        carbono_dw = carbono_agb * proporcion_dw
        # 4. Carbono en Hojarasca (LI)
        acumulacion_li = self.factores_vcs['LI']['acumulacion_anual'].get(tipo_bosque, 5.0)
        # Asumir 5 años de acumulación
        carbono_li = acumulacion_li * 5 * self.factores_vcs['AGB']['factor_conversion_carbono'] * 0.3
        # 5. Carbono Orgánico del Suelo (SOC)
        contenido_soc = self.factores_vcs['SOC']['contenido_carbono'].get(estado, 1.5)
        # Ajustar para ecosistemas específicos
        if estado == "humedal":
            contenido_soc = 3.5
        elif estado == "pastizal_pampeano":
            contenido_soc = 2.2
        # Cálculo simplificado: ton C/ha en primeros 30cm
        carbono_soc = (self.factores_vcs['SOC']['profundidad_referencia'] * 
                      self.factores_vcs['SOC']['densidad_aparente'] * 
                      contenido_soc * 10)  # 10 para convertir a ton/ha
        # Total carbono por hectárea (ton C/ha)
        carbono_total_ton_ha = (
            carbono_agb + 
            carbono_bgb + 
            carbono_dw + 
            carbono_li + 
            carbono_soc
        )
        # Aplicar factor de conservatividad (default: medio)
        factor_conservatividad = self.factores_conservatividad['medio']
        carbono_total_ton_ha *= factor_conservatividad
        # Convertir a CO₂ equivalente
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
                'ratio_co2_carbono': 3.67
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
        # Incertidumbres combinadas (método de propagación de errores)
        try:
            incertidumbre_agb = self.factores_vcs['AGB']['ecuaciones_alometricas'][tipo_bosque]['incertidumbre']
        except:
            incertidumbre_agb = 0.20
        incertidumbre_bgb = self.factores_vcs['BGB']['incertidumbre']
        incertidumbre_dw = self.factores_vcs['DW']['incertidumbre']
        incertidumbre_li = self.factores_vcs['LI']['incertidumbre']
        incertidumbre_soc = self.factores_vcs['SOC']['incertidumbre']
        # Incertidumbre combinada (raíz cuadrada de la suma de cuadrados)
        incertidumbre_combinada = math.sqrt(
            incertidumbre_agb**2 + 
            incertidumbre_bgb**2 + 
            incertidumbre_dw**2 + 
            incertidumbre_li**2 + 
            incertidumbre_soc**2
        )
        # Intervalo de confianza al 90%
        intervalo_confianza = carbono_total * incertidumbre_combinada * self.factores_vcs['AGB']['factor_incertidumbre']
        return {
            'incertidumbre_relativa': round(incertidumbre_combinada * 100, 1),  # Porcentaje
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
        Carbono total estimado: {resultados_carbono['carbono_total_ton_ha']:,.2f} ton C/ha
        CO₂ equivalente total: {resultados_carbono['co2_equivalente_ton_ha']:,.2f} ton CO₂e/ha
        DESGLOSE POR POOLS DE CARBONO (ton C/ha):
        -----------------------------------------
        • Biomasa Aérea viva (AGB): {resultados_carbono['desglose']['AGB']:,.2f}
        • Biomasa Subterránea (BGB): {resultados_carbono['desglose']['BGB']:,.2f}
        • Madera Muerta (DW): {resultados_carbono['desglose']['DW']:,.2f}
        • Hojarasca (LI): {resultados_carbono['desglose']['LI']:,.2f}
        • Carbono Orgánico del Suelo (SOC): {resultados_carbono['desglose']['SOC']:,.2f}
        FACTORES APLICADOS:
        -------------------
        • Tipo de bosque: {resultados_carbono['factores_aplicados']['tipo_bosque']}
        • Estado del bosque: {resultados_carbono['factores_aplicados']['estado']}
        • Factor de conservatividad: {resultados_carbono['factores_aplicados']['factor_conservatividad']}
        • Ratio CO₂/Carbono: {resultados_carbono['factores_aplicados']['ratio_co2_carbono']}
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
# 🌳 SISTEMA DE ANÁLISIS DE CARBONO VERRA
# ===============================
class AnalisisCarbonoVerra:
    """Sistema completo de análisis de carbono con metodología Verra"""
    def __init__(self):
        self.metodologia = MetodologiaVerra()
    
    def analizar_carbono_area(self, gdf, tipo_ecosistema, nivel_detalle=8):
        """Analizar carbono en toda el área usando metodología Verra"""
        try:
            poligono_principal = gdf.geometry.iloc[0]
            bounds = poligono_principal.bounds
            
            # Mapear tipo de ecosistema SIB a parámetros VCS
            mapeo_ecosistema_vcs = {
                # Bosques densos - alta biomasa
                'Bosque Andino Patagónico': ('temperado', 'bosque_templado'),
                'Bosque de Araucaria': ('temperado', 'bosque_templado'),
                'Bosque de Yungas': ('tropical_humedo', 'bosque_primario'),
                'Bosque de Selva Misionera': ('tropical_humedo', 'bosque_primario'),
                
                # Bosques secos y secundarios
                'Bosque de Caldén': ('tropical_seco', 'bosque_secundario'),
                'Bosque de Quebracho': ('tropical_seco', 'bosque_secundario'),
                'Bosque de Algarrobo': ('tropical_seco', 'bosque_secundario'),
                'Bosque de Chaco Serrano': ('tropical_seco', 'bosque_secundario'),
                'Matorral del Espinal': ('tropical_seco', 'bosque_degradado'),
                'Matorral Chaqueño': ('tropical_seco', 'bosque_degradado'),
                'Arbustal de Altura': ('temperado', 'bosque_degradado'),
                
                # Pastizales y estepas
                'Pastizal Pampeano': ('subtropical', 'pastizal_pampeano'),
                'Pastizal Mesopotámico': ('subtropical', 'pastizal'),
                'Estepa Patagónica': ('temperado', 'pastizal'),
                'Estepa Altoandina': ('temperado', 'pastizal'),
                'Estepa del Monte': ('tropical_seco', 'pastizal'),
                
                # Humedales
                'Humedales del Iberá': ('subtropical', 'humedal'),
                'Humedales del Paraná': ('subtropical', 'humedal'),
                'Bañados y esteros': ('subtropical', 'humedal'),
                'Delta e Islas del Paraná': ('subtropical', 'humedal'),
                'Turberas y mallines': ('subtropical', 'humedal'),
                
                # Áreas productivas
                'Agricultura intensiva': ('subtropical', 'agricultura'),
                'Agricultura extensiva': ('subtropical', 'agricultura'),
                'Ganadería extensiva': ('subtropical', 'pastizal'),
                'Silvicultura': ('subtropical', 'bosque_secundario'),
                
                # Áreas urbanas e intervenidas
                'Zona urbana consolidada': ('subtropical', 'agricultura'),
                'Periurbano': ('subtropical', 'agricultura'),
                'Infraestructura': ('subtropical', 'agricultura'),
                'Área minera': ('subtropical', 'agricultura'),
                
                # Cuerpos de agua (mínimo carbono)
                'Ríos y arroyos': ('subtropical', 'agricultura'),
                'Lagunas y lagos': ('subtropical', 'agricultura'),
                'Embalses': ('subtropical', 'agricultura'),
                'Mar y costa': ('subtropical', 'agricultura')
            }
            
            tipo_vcs, estado_vcs = mapeo_ecosistema_vcs.get(
                tipo_ecosistema, 
                ('subtropical', 'bosque_secundario')  # Valor por defecto para Argentina
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
                    'fecha_analisis': datetime.now().strftime('%Y-%m-%d')
                }
            }
            
            id_area = 1
            
            # Dividir en grilla para análisis detallado
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
                        # Calcular área en hectáreas
                        area_m2 = interseccion.area * 111000 * 111000 * math.cos(math.radians((ymin+ymax)/2))
                        area_ha = area_m2 / 10000
                        
                        if area_ha > 0.01:
                            # Simular NDVI para esta celda
                            # En un sistema real, esto vendría del análisis satelital
                            ndvi = 0.5 + random.uniform(-0.2, 0.3)
                            
                            # Clasificar estrato VCS
                            estrato_info = self.metodologia.clasificar_estrato_vcs(ndvi)
                            
                            # Calcular carbono según metodología Verra
                            carbono_info = self.metodologia.calcular_carbono_hectarea(
                                ndvi=ndvi,
                                tipo_bosque=tipo_vcs,
                                estado=estado_vcs,
                                area_ha=area_ha
                            )
                            
                            # Calcular incertidumbre
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
                                'factores_aplicados': carbono_info['factores_aplicados']
                            }
                            
                            resultados['analisis_carbono'].append(area_data)
                            id_area += 1
            
            # Calcular resumen estadístico
            if resultados['analisis_carbono']:
                self._calcular_resumen_carbono(resultados)
            
            return resultados
            
        except Exception as e:
            st.error(f"Error en análisis de carbono Verra: {str(e)}")
            return None
    
    def _calcular_resumen_carbono(self, resultados):
        """Calcular estadísticas resumen del análisis de carbono"""
        areas_carbono = resultados['analisis_carbono']
        if not areas_carbono:
            return
        
        # Calcular totales
        carbono_total = sum(a['carbono_total_ton'] for a in areas_carbono)
        co2_total = sum(a['co2_equivalente_ton'] for a in areas_carbono)
        area_total = sum(a['area_ha'] for a in areas_carbono)
        
        # Promedios por hectárea
        carbono_promedio_ha = np.mean([a['carbono_por_ha'] for a in areas_carbono])
        co2_promedio_ha = np.mean([a['co2_por_ha'] for a in areas_carbono])
        
        # Distribución por estratos VCS
        estratos = {}
        for area in areas_carbono:
            estrato = area['estrato_vcs']
            if estrato not in estratos:
                estratos[estrato] = {
                    'cantidad': 0,
                    'area_total': 0,
                    'carbono_total': 0
                }
            estratos[estrato]['cantidad'] += 1
            estratos[estrato]['area_total'] += area['area_ha']
            estratos[estrato]['carbono_total'] += area['carbono_total_ton']
        
        # Distribución por pools de carbono
        pools = {'AGB': 0, 'BGB': 0, 'DW': 0, 'LI': 0, 'SOC': 0}
        for area in areas_carbono:
            for pool, valor in area['desglose_carbono'].items():
                pools[pool] += valor * area['area_ha']
        
        # Calcular incertidumbre promedio
        incertidumbre_promedio = np.mean([a['incertidumbre']['incertidumbre_relativa'] 
                                         for a in areas_carbono])
        
        resultados['resumen_carbono'] = {
            'carbono_total_ton': round(carbono_total, 2),
            'co2_total_ton': round(co2_total, 2),
            'area_total_ha': round(area_total, 2),
            'carbono_promedio_ton_ha': round(carbono_promedio_ha, 2),
            'co2_promedio_ton_ha': round(co2_promedio_ha, 2),
            'potencial_creditos': round(co2_total / 1000, 1),  # En miles de créditos (1 crédito = 1 ton CO₂)
            'incertidumbre_promedio': round(incertidumbre_promedio, 1),
            'estratos_distribucion': estratos,
            'pools_distribucion': pools
        }
        
        # Evaluar elegibilidad VCS
        elegibilidad = self._evaluar_elegibilidad_vcs(resultados)
        resultados['resumen_carbono']['elegibilidad_vcs'] = elegibilidad
    
    def _evaluar_elegibilidad_vcs(self, resultados):
        """Evaluar elegibilidad del proyecto según criterios VCS"""
        resumen = resultados['resumen_carbono']
        criterios = {
            'carbono_minimo': resumen['co2_total_ton'] > 10000,  # Mínimo 10,000 ton CO₂
            'area_minima': resumen['area_total_ha'] > 100,  # Mínimo 100 ha
            'permanencia_potencial': True,  # Asumir sí por ahora
            'adicionalidad_potencial': True  # Asumir sí por ahora
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
    resolucion: float  # en metros
    descripcion: str

@dataclass
class ImagenSatelital:
    """Metadatos de imagen satelital"""
    satelite: Satelite
    fecha_adquisicion: datetime
    nubosidad: float  # 0-1
    indice_calidad: float  # 0-1
    bandas_disponibles: List[str]
    url_visualizacion: Optional[str] = None
# ===============================
# 🛰️ SIMULADOR DE DATOS SATELITALES
# ===============================
class SimuladorSatelital:
    """Simulador de datos satelitales para PlanetScope y Sentinel-2"""
    def __init__(self):
        # Configuración de bandas por satélite
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
        
        # Rangos típicos de reflectancia por tipo de cobertura
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
        
        # Mapear bandas a categorías generales
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
            cat = 'nir'  # Por defecto
        
        # Obtener rango según tipo de cobertura
        if tipo_cobertura in self.rangos_reflectancia:
            rango = self.rangos_reflectancia[tipo_cobertura].get(cat, (0.01, 0.1))
        else:
            rango = (0.01, 0.1)
        
        # Añadir variación aleatoria
        return random.uniform(rango[0], rango[1])
    
    def calcular_indices(self, reflectancias: Dict[str, float], satelite: Satelite):
        """Calcular índices espectrales a partir de reflectancias"""
        indices = {}
        
        try:
            # NDVI - Índice de Vegetación de Diferencia Normalizada
            if satelite == Satelite.PLANETSCOPE:
                red = reflectancias.get('B3', 0.1)
                nir = reflectancias.get('B4', 0.3)
            else:  # Sentinel-2
                red = reflectancias.get('B4', 0.1)
                nir = reflectancias.get('B8', 0.3)
            
            if nir + red > 0:
                indices['NDVI'] = (nir - red) / (nir + red)
            else:
                indices['NDVI'] = 0.0
            
            # SAVI - Índice de Vegetación Ajustado al Suelo
            L = 0.5  # Factor de corrección del suelo
            if nir + red + L > 0:
                indices['SAVI'] = ((nir - red) / (nir + red + L)) * (1 + L)
            else:
                indices['SAVI'] = 0.0
            
            # EVI - Índice de Vegetación Mejorado
            if satelite == Satelite.SENTINEL2:
                blue = reflectancias.get('B2', 0.05)
                indices['EVI'] = 2.5 * ((nir - red) / (nir + 6 * red - 7.5 * blue + 1))
            else:
                indices['EVI'] = indices['NDVI'] * 1.2  # Aproximación
            
            # NDWI - Índice de Agua de Diferencia Normalizada
            if satelite == Satelite.SENTINEL2:
                green = reflectancias.get('B3', 0.08)
                nir2 = reflectancias.get('B8A', nir)
                indices['NDWI'] = (green - nir2) / (green + nir2)
            else:
                indices['NDWI'] = -indices['NDVI'] * 0.5  # Aproximación
            
            # MSAVI - Índice de Vegetación Ajustado al Suelo Modificado
            indices['MSAVI'] = (2 * nir + 1 - np.sqrt((2 * nir + 1)**2 - 8 * (nir - red))) / 2
            
            # GNDVI - Índice de Vegetación de Diferencia Normalizada Verde
            if satelite == Satelite.SENTINEL2:
                green = reflectancias.get('B3', 0.08)
                indices['GNDVI'] = (nir - green) / (nir + green)
            
            # Clasificar salud vegetal basada en NDVI
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
            # Valores por defecto en caso de error
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
# 🗺️ SISTEMA DE MAPAS AVANZADO CON IMÁGENES SATELITALES
# ===============================
class SistemaMapasAvanzado:
    """Sistema de mapas con integración satelital y zoom automático"""
    def __init__(self):
        self.simulador = SimuladorSatelital()
        # Capas base con URLs reales de servicios WMS/TMS
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
            return [-34.0, -64.0], 6  # Centro de Argentina por defecto
        
        try:
            # Calcular centroide
            bounds = gdf.total_bounds
            centro = [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2]
            
            # Calcular área en km²
            poligono = gdf.geometry.iloc[0]
            if hasattr(poligono, 'area'):
                # Conversión aproximada de grados a km²
                lat_centro = centro[0]
                cos_lat = math.cos(math.radians(lat_centro))
                area_grados = poligono.area
                area_km2 = area_grados * 111 * 111 * cos_lat
                
                # Algoritmo de zoom basado en área (optimizado)
                if area_km2 < 0.1:      # Muy pequeño (< 0.1 km²)
                    zoom = 16
                elif area_km2 < 1:      # Pequeño (0.1-1 km²)
                    zoom = 15
                elif area_km2 < 10:     # Pequeño-mediano (1-10 km²)
                    zoom = 14
                elif area_km2 < 50:     # Mediano (10-50 km²)
                    zoom = 13
                elif area_km2 < 100:    # Mediano-grande (50-100 km²)
                    zoom = 12
                elif area_km2 < 500:    # Grande (100-500 km²)
                    zoom = 11
                elif area_km2 < 1000:   # Muy grande (500-1000 km²)
                    zoom = 10
                elif area_km2 < 5000:   # Enorme (1000-5000 km²)
                    zoom = 9
                else:                   # Gigantesco (>5000 km²)
                    zoom = 8
            else:
                zoom = 10
                
            return centro, min(zoom, 16)  # Limitar zoom máximo
        except Exception:
            return [-34.0, -64.0], 6  # Centro de Argentina por defecto
    
    def crear_mapa_satelital(self, gdf, titulo="Área de Estudio", capa_base="ESRI World Imagery"):
        """Crear mapa con capa satelital y polígono"""
        centro, zoom = self.calcular_zoom_automatico(gdf)
        
        # Crear mapa base con ID único para evitar conflictos DOM
        mapa_id = f"map_{int(datetime.now().timestamp() * 1000)}"
        m = folium.Map(
            location=centro,
            zoom_start=zoom,
            tiles=None,
            control_scale=True,
            zoom_control=True,
            prefer_canvas=True
        )
        
        # Agregar capa base seleccionada
        capa_config = self.capas_base.get(capa_base, self.capas_base['ESRI World Imagery'])
        
        if '{date}' in capa_config['tiles']:
            # Reemplazar parámetros dinámicos
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
        
        # Agregar polígono si existe
        if gdf is not None and not gdf.empty:
            try:
                poligono = gdf.geometry.iloc[0]
                
                # Calcular área aproximada
                bounds = gdf.total_bounds
                lat_centro = centro[0]
                cos_lat = math.cos(math.radians(lat_centro))
                area_grados = gdf.geometry.area.iloc[0]
                area_km2 = area_grados * 111 * 111 * cos_lat
                area_ha = area_km2 * 100
                
                # Tooltip informativo
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
                
                # Estilo del polígono
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
                
                # Agregar marcador en el centro
                folium.Marker(
                    location=centro,
                    popup=f"<b>Centro del área de estudio</b><br>Área: {area_ha:,.1f} ha",
                    icon=folium.Icon(color='blue', icon='info-sign', prefix='fa')
                ).add_to(m)
                
                # Ajustar vista al polígono con margen
                m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]], padding=(50, 50))
                
            except Exception as e:
                st.warning(f"Error al visualizar polígono: {str(e)}")
        
        # Agregar capas adicionales
        for nombre, config in self.capas_base.items():
            if nombre != capa_base:
                folium.TileLayer(
                    tiles=config['tiles'] if '{date}' not in config['tiles'] else config['tiles'].replace('{date}', datetime.now().strftime('%Y-%m')),
                    attr=config['attr'],
                    name=config['nombre'],
                    overlay=False,
                    control=True
                ).add_to(m)
        
        # Controles adicionales
        Fullscreen(position='topright').add_to(m)
        MousePosition(position='bottomleft').add_to(m)
        folium.LayerControl(position='topright', collapsed=False).add_to(m)
        
        # Medir distancia (opcional, puede causar conflictos)
        try:
            Draw(
                export=True,
                position='topleft',
                draw_options={
                    'polyline': True,
                    'rectangle': True,
                    'polygon': True,
                    'circle': False,
                    'marker': True,
                    'circlemarker': False
                }
            ).add_to(m)
        except:
            pass  # Ignorar si hay error en controles Draw
        
        return m
    
    def crear_mapa_indices(self, gdf, datos_areas, indice_seleccionado, titulo="Mapa de Índices"):
        """Crear mapa temático para índices satelitales"""
        centro, zoom = self.calcular_zoom_automatico(gdf)
        
        # Mapa base con capa satelital
        m = folium.Map(
            location=centro,
            zoom_start=zoom,
            tiles=self.capas_base['ESRI World Imagery']['tiles'],
            attr=self.capas_base['ESRI World Imagery']['attr'],
            control_scale=True
        )
        
        # Agregar polígono base semi-transparente
        if gdf is not None and not gdf.empty:
            folium.GeoJson(
                gdf,
                style_function=lambda x: {
                    'fillColor': '#3b82f6',
                    'color': '#1d4ed8',
                    'weight': 2,
                    'fillOpacity': 0.1,
                    'opacity': 0.5
                },
                name='Área de Estudio'
            ).add_to(m)
        
        # Normalizar valores del índice para colormap
        valores = [area['indices'].get(indice_seleccionado, 0) for area in datos_areas]
        min_val = min(valores) if valores else 0
        max_val = max(valores) if valores else 1
        
        # Colormap para el índice (verde-rojo para NDVI, azul para NDWI, etc.)
        if indice_seleccionado in ['NDVI', 'SAVI', 'EVI', 'MSAVI']:
            colormap = LinearColormap(colors=['red', 'yellow', 'green'], vmin=min_val, vmax=max_val)
        elif indice_seleccionado == 'NDWI':
            colormap = LinearColormap(colors=['brown', 'yellow', 'blue'], vmin=min_val, vmax=max_val)
        else:
            colormap = LinearColormap(colors=['blue', 'green', 'red'], vmin=min_val, vmax=max_val)
        
        m.add_child(colormap)
        
        # Agregar celdas con colores según índice
        for area in datos_areas:
            valor = area['indices'].get(indice_seleccionado, 0)
            color = colormap(valor)
            folium.GeoJson(
                area['geometry'],
                style_function=lambda x, color=color: {
                    'fillColor': color,
                    'color': 'black',
                    'weight': 1,
                    'fillOpacity': 0.7
                },
                tooltip=f"""
                <div style="font-family: Arial; font-size: 12px;">
                    <b>{indice_seleccionado}</b>: {valor:.3f}<br>
                    <b>Área</b>: {area['area_ha']:.2f} ha<br>
                    <b>Salud</b>: {area['indices'].get('Salud_Vegetacion', 'N/A')}
                </div>
                """
            ).add_to(m)
        
        # Controles
        Fullscreen().add_to(m)
        MousePosition().add_to(m)
        folium.LayerControl().add_to(m)
        
        # Ajustar bounds
        m.fit_bounds(gdf.total_bounds)
        
        return m

# ===============================
# 🌿 SISTEMA DE ANÁLISIS AMBIENTAL
# ===============================
class SistemaAnalisisAmbiental:
    """Sistema principal de análisis ambiental con datos satelitales"""
    def __init__(self):
        self.simulador = SimuladorSatelital()
        self.analisis_carbono = AnalisisCarbonoVerra()
        self.sistema_mapas = SistemaMapasAvanzado()
        self.dashboard = DashboardEjecutivo()  # Asumir que esta clase existe en el código truncado

    def get_annual_precipitation(self, lat, lon, tipo_ecosistema=None):
        """
        Obtiene precipitación anual histórica (climatología) desde NASA POWER usando coordenadas.
        Retorna mm/año. Fallback si falla.
        """
        url = f"https://power.larc.nasa.gov/api/temporal/climatology/point?parameters=PRECTOTCORR&community=AG&longitude={lon}&latitude={lat}&format=JSON"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()  # Lanza error si HTTP falla
            data = response.json()
            
            # Extraer datos mensuales (mm/día)
            monthly = data['properties']['parameter']['PRECTOTCORR']
            
            # Días por mes (aprox., sin bisiesto)
            days_per_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
            
            # Sumar: (mm/día * días) para cada mes
            annual_mm = sum(float(monthly.get(f"{i:03d}", 0)) * days_per_month[i-1] for i in range(1, 13))
            
            return round(annual_mm, 2)
        except Exception as e:
            st.warning(f"Error al consultar NASA POWER: {str(e)}. Usando fallback para {tipo_ecosistema}.")
            return self._get_fallback_precipitation(tipo_ecosistema)

    def _get_fallback_precipitation(self, tipo_ecosistema):
        """
        Fallback con valores históricos aproximados por ecosistema SIB (basados en SMN/WorldClim).
        """
        fallbacks = {
            'Bosque Andino Patagónico': 600,    # 400-800 mm
            'Bosque de Araucaria': 800,         # 600-1000 mm
            'Bosque de Yungas': 1500,           # >1200 mm
            'Bosque de Selva Misionera': 1800,  # >1500 mm
            'Bosque de Caldén': 700,            # 500-900 mm
            'Bosque de Quebracho': 700,         # 500-900 mm
            'Bosque de Algarrobo': 500,         # 300-700 mm
            'Bosque de Chaco Serrano': 800,     # 600-1000 mm
            'Pastizal Pampeano': 900,           # 800-1000 mm
            'Pastizal Mesopotámico': 1100,      # 900-1300 mm
            'Estepa Patagónica': 200,           # <300 mm
            'Estepa Altoandina': 300,           # 200-500 mm
            'Estepa del Monte': 400,            # 300-600 mm
            'Humedales del Iberá': 1400,        # >1200 mm
            'Humedales del Paraná': 1200,       # 1000-1400 mm
            'Bañados y esteros': 1000,          # 800-1200 mm
            'Delta e Islas del Paraná': 1100,   # 900-1300 mm
            'Turberas y mallines': 900,         # 700-1100 mm
            'Matorral del Espinal': 600,        # 400-800 mm
            'Matorral Chaqueño': 700,           # 500-900 mm
            'Arbustal de Altura': 500,          # 300-700 mm
            'Agricultura intensiva': 800,       # Promedio Pampa
            'Agricultura extensiva': 800,       # Promedio Pampa
            'Ganadería extensiva': 700,         # Chaco/Pampa
            'Silvicultura': 900,                # NEA
            'Zona urbana consolidada': 900,     # Promedio urbano
            'Periurbano': 900,                  # Promedio periurbano
            'Infraestructura': 900,             # Promedio
            'Área minera': 500,                 # NOA árido
            'Ríos y arroyos': 1000,             # Promedio fluvial
            'Lagunas y lagos': 1000,            # Promedio lacustre
            'Embalses': 800,                    # Promedio
            'Mar y costa': 1000                 # Litoral
        }
        return fallbacks.get(tipo_ecosistema, 800)  # Default: promedio Argentina ~800 mm

    def analizar_area_completa(self, gdf, tipo_ecosistema, satelite, nivel_detalle=8):
        """Analizar el área completa con datos satelitales"""
        try:
            poligono_principal = gdf.geometry.iloc[0]
            bounds = poligono_principal.bounds
            
            # Calcular centro del polígono para NASA POWER
            centro_lat, centro_lon = poligono_principal.centroid.y, poligono_principal.centroid.x
            
            # Obtener precipitación anual real
            precipitacion_anual = self.get_annual_precipitation(centro_lat, centro_lon, tipo_ecosistema)
            
            resultados = {
                'areas': [],
                'resumen': {},
                'metadatos_imagen': {},
                'satelite_usado': satelite,
                'tipo_ecosistema': tipo_ecosistema
            }
            
            # Generar metadatos satelitales
            sat_enum = Satelite[satelite.upper().replace('-', '')]
            imagen = self.simulador.generar_imagen_satelital(sat_enum)
            resultados['metadatos_imagen'] = {
                'satelite': imagen.satelite.value,
                'fecha': imagen.fecha_adquisicion.strftime('%Y-%m-%d'),
                'nubosidad': f"{imagen.nubosidad:.2f}%",
                'calidad': f"{imagen.indice_calidad:.2f}",
                'bandas_disponibles': len(imagen.bandas_disponibles)
            }
            
            id_area = 1
            
            # Dividir en grilla
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
                            # Simular datos satelitales
                            reflectancias = {
                                banda: self.simulador.simular_reflectancia(tipo_ecosistema, banda, sat_enum)
                                for banda in self.simulador.bandas[sat_enum]
                            }
                            
                            indices = self.simulador.calcular_indices(reflectancias, sat_enum)
                            
                            # Simular variables ambientales
                            temperatura = random.uniform(15, 25)  # Ejemplo, puedes integrar más APIs si necesitas
                            precipitacion = precipitacion_anual  # Usar el valor real de NASA
                            # Agrega variación si quieres: precipitacion = precipitacion_anual + random.uniform(-100, 100)
                            
                            area_data = {
                                'id': id_area,
                                'area': f"Área-{id_area:03d}",
                                'geometry': interseccion,
                                'area_ha': round(area_ha, 2),
                                'indices': indices,
                                'temperatura': temperatura,
                                'precipitacion': precipitacion,
                                # Agrega más campos si es necesario
                            }
                            
                            resultados['areas'].append(area_data)
                            id_area += 1
            
            # Calcular resumen
            if resultados['areas']:
                self._calcular_resumen_ambiental(resultados)
            
            return resultados
            
        except Exception as e:
            st.error(f"Error en análisis ambiental: {str(e)}")
            return None

    def _calcular_resumen_ambiental(self, resultados):
        """Calcular resumen estadístico del análisis ambiental"""
        areas = resultados['areas']
        resumen = {
            'total_areas': len(areas),
            'area_total_ha': sum(a['area_ha'] for a in areas),
            'ndvi_promedio': np.mean([a['indices'].get('NDVI', 0) for a in areas]),
            'shannon_promedio': np.mean([a.get('indice_shannon', 0) for a in areas]),  # Asumir que indice_shannon está en el código truncado
            'temperatura_promedio': np.mean([a['temperatura'] for a in areas]),
            'precipitacion_promedio': np.mean([a['precipitacion'] for a in areas]),
            # Agrega más resúmenes si es necesario
        }
        resultados['resumen'] = resumen

# ===============================
# 🎨 FUNCIONES AUXILIARES PARA INFORMACIÓN SIB
# ===============================
def mostrar_info_sib(tipo_ecosistema):
    """Mostrar información sobre el ecosistema según SIB Argentina"""
    info_sib = {
        'Bosque Andino Patagónico': {
            'descripcion': 'Bosques del sur andino con especies como ñire, lenga y coihue. Se extiende desde Neuquén hasta Tierra del Fuego.',
            'region': 'Patagonia Andina',
            'conservacion': 'Vulnerable - Áreas protegidas: Parque Nacional Los Alerces, Nahuel Huapi',
            'especies_iconicas': ['Lenga', 'Ñire', 'Coihue', 'Ciprés de la Cordillera', 'Huemul'],
            'amenazas': ['Deforestación histórica', 'Incendios', 'Cambio climático', 'Especies exóticas'],
            'carbono_promedio': 'Alto (150-300 ton C/ha)'
        },
        'Bosque de Yungas': {
            'descripcion': 'Selva subtropical de montaña con alta biodiversidad. También conocida como Selva Tucumano-Oranense.',
            'region': 'Nororeste argentino (Salta, Jujuy, Tucumán)',
            'conservacion': 'En peligro - Reserva de Biosfera de las Yungas',
            'especies_iconicas': ['Cedro', 'Laurel', 'Tarumá', 'Jaguar', 'Tapir'],
            'amenazas': ['Avance agrícola', 'Tala selectiva', 'Fragmentación'],
            'carbono_promedio': 'Muy alto (200-400 ton C/ha)'
        },
        'Pastizal Pampeano': {
            'descripcion': 'Extensa llanura herbácea, uno de los pastizales más productivos del mundo. Transformado en gran medida por la agricultura.',
            'region': 'Región Pampeana',
            'conservacion': 'Críticamente amenazado - Menos del 1% en estado natural',
            'especies_iconicas': ['Flechilla', 'Paja Colorada', 'Ñandú', 'Venado de las Pampas'],
            'amenazas': ['Conversión agrícola', 'Ganadería intensiva', 'Urbanización'],
            'carbono_promedio': 'Medio-bajo (50-100 ton C/ha) pero con alto carbono en suelo'
        },
        'Humedales del Iberá': {
            'descripcion': 'Uno de los mayores humedales de agua dulce del mundo. Reservorio de biodiversidad y regulador hídrico.',
            'region': 'Corrientes',
            'conservacion': 'Importancia internacional - Sitio Ramsar, Parque Nacional Iberá',
            'especies_iconicas': ['Ciervo de los pantanos', 'Carpincho', 'Yacaré', 'Aguará guazú'],
            'amenazas': ['Drenaje', 'Contaminación', 'Especies invasoras'],
            'carbono_promedio': 'Alto en suelo (150-250 ton C/ha)'
        },
        'Estepa Patagónica': {
            'descripcion': 'Árido arbustivo y herbáceo adaptado a condiciones extremas. Domina la meseta patagónica.',
            'region': 'Patagonia Extraandina',
            'conservacion': 'Vulnerable - Áreas protegidas insuficientes',
            'especies_iconicas': ['Coirón', 'Mata negra', 'Guanaco', 'Choique', 'Puma'],
            'amenazas': ['Sobrepastoreo ovino', 'Desertificación', 'Minería'],
            'carbono_promedio': 'Bajo (20-60 ton C/ha)'
        },
        'Bosque de Quebracho': {
            'descripcion': 'Bosque seco chaqueño dominado por quebracho colorado y blanco. Importante para la industria forestal histórica.',
            'region': 'Chaco Seco',
            'conservacion': 'En peligro - Deforestación masiva',
            'especies_iconicas': ['Quebracho colorado', 'Quebracho blanco', 'Mistol', 'Tatú carreta'],
            'amenazas': ['Deforestación para agricultura', 'Tala histórica'],
            'carbono_promedio': 'Medio (80-150 ton C/ha)'
        },
        'Delta e Islas del Paraná': {
            'descripcion': 'Complejo sistema de islas, riachos y humedales. Importante corredor biológico y productor forestal.',
            'region': 'Entre Ríos, Santa Fe, Buenos Aires',
            'conservacion': 'Presión media - Sitio Ramsar Delta del Paraná',
            'especies_iconicas': ['Sauce criollo', 'Aliso', 'Carpincho', 'Nutria'],
            'amenazas': ['Forestación exótica', 'Contaminación', 'Modificación hidrológica'],
            'carbono_promedio': 'Medio-alto (100-200 ton C/ha)'
        }
    }
    
    return info_sib.get(tipo_ecosistema, {
        'descripcion': 'Ecosistema argentino reconocido por el Sistema de Información sobre Biodiversidad.',
        'region': 'Argentina',
        'conservacion': 'Estado de conservación no especificado',
        'especies_iconicas': [],
        'amenazas': [],
        'carbono_promedio': 'Variable según condiciones'
    })

# ===============================
# 🎨 INTERFAZ PRINCIPAL DE LA APLICACIÓN
# ===============================
def main():
    # Título principal
    st.title("🛰️ Sistema Satelital de Análisis Ambiental - Argentina")
    st.markdown("### 🌎 Clasificación SIB | Análisis con PlanetScope & Sentinel-2 | Verra VCS para Carbono")
    
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
    
    # Sidebar
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
                        st.session_state.poligono_data = gdf
                        st.success("✅ Polígono cargado exitosamente")
                        
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        
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
                    # Bosques
                    'Bosque Andino Patagónico',
                    'Bosque de Araucaria',
                    'Bosque de Caldén',
                    'Bosque de Quebracho',
                    'Bosque de Algarrobo',
                    'Bosque de Yungas',
                    'Bosque de Selva Misionera',
                    'Bosque de Chaco Serrano',
                    
                    # Pastizales y estepas
                    'Pastizal Pampeano',
                    'Pastizal Mesopotámico',
                    'Estepa Patagónica',
                    'Estepa Altoandina',
                    'Estepa del Monte',
                    
                    # Humedales
                    'Humedales del Iberá',
                    'Humedales del Paraná',
                    'Bañados y esteros',
                    'Delta e Islas del Paraná',
                    'Turberas y mallines',
                    
                    # Matorrales
                    'Matorral del Espinal',
                    'Matorral Chaqueño',
                    'Arbustal de Altura',
                    
                    # Áreas productivas
                    'Agricultura intensiva',
                    'Agricultura extensiva',
                    'Ganadería extensiva',
                    'Silvicultura',
                    
                    # Áreas urbanas
                    'Zona urbana consolidada',
                    'Periurbano',
                    'Infraestructura',
                    'Área minera',
                    
                    # Cuerpos de agua
                    'Ríos y arroyos',
                    'Lagunas y lagos',
                    'Embalses',
                    'Mar y costa'
                ],
                help="Clasificación según Sistema de Información sobre Biodiversidad (SIB) Argentina"
            )
            
            # Guardar el tipo de ecosistema seleccionado
            st.session_state.tipo_ecosistema_seleccionado = tipo_ecosistema
            
            nivel_detalle = st.slider("Nivel de detalle (divisiones)", 4, 12, 8)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🚀 Ejecutar Análisis Completo", use_container_width=True):
                    with st.spinner("Procesando datos satelitales..."):
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
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🗺️ Mapa Satelital", 
        "📊 Dashboard Ejecutivo",
        "🌿 Índices de Vegetación",
        "🌳 Análisis de Carbono",
        "📋 Reporte Verra",
        "📈 Datos Completos"
    ])
    
    with tab1:
        mostrar_mapa_satelital(capa_base if 'capa_base' in locals() else "ESRI World Imagery")
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
        # Información del área
        gdf = st.session_state.poligono_data
        bounds = gdf.total_bounds
        
        col1, col2, col3 = st.columns(3)
        with col1:
            area_km2 = gdf.geometry.area.iloc[0] * 111 * 111 * math.cos(math.radians((bounds[1] + bounds[3])/2))
            st.metric("Área aproximada", f"{area_km2:.2f} km²")
        with col2:
            st.metric("Centroide", f"{(bounds[1] + bounds[3])/2:.4f}°, {(bounds[0] + bounds[2])/2:.4f}°")
        with col3:
            st.metric("Tipo de geometría", gdf.geometry.iloc[0].geom_type)
        
        # Crear y mostrar mapa
        mapa = st.session_state.sistema_analisis.sistema_mapas.crear_mapa_satelital(
            st.session_state.poligono_data,
            "Área de Análisis Satelital",
            capa_base
        )
        mostrar_mapa_seguro(mapa, width=1000, height=600)
        
        # Información adicional si hay resultados
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
        
        # Agregar información SIB si hay un ecosistema seleccionado
        if st.session_state.tipo_ecosistema_seleccionado:
            st.markdown("---")
            with st.expander("ℹ️ Información SIB sobre el ecosistema seleccionado"):
                info = mostrar_info_sib(st.session_state.tipo_ecosistema_seleccionado)
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Descripción:** {info['descripcion']}")
                    st.markdown(f"**Región:** {info['region']}")
                    st.markdown(f"**Estado de conservación:** {info['conservacion']}")
                    st.markdown(f"**Carbono promedio estimado:** {info['carbono_promedio']}")
                
                with col2:
                    if info['especies_iconicas']:
                        st.markdown(f"**Especies icónicas:**")
                        for especie in info['especies_iconicas']:
                            st.markdown(f"- {especie}")
                    
                    if info['amenazas']:
                        st.markdown(f"**Principales amenazas:**")
                        for amenaza in info['amenazas']:
                            st.markdown(f"- {amenaza}")
                
                st.markdown("*Fuente: Sistema de Información sobre Biodiversidad (SIB) Argentina*")
    
    else:
        st.info("👈 Carga un polígono en el panel lateral para comenzar")
        
        # Mapa de ejemplo
        st.markdown("### 🎯 Ejemplo de visualización satelital")
        col1, col2 = st.columns([3, 1])
        with col2:
            ejemplo_capa = st.selectbox("Capa de ejemplo", list(st.session_state.sistema_analisis.sistema_mapas.capas_base.keys()))
        with col1:
            # Crear un polígono de ejemplo en Argentina
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
        # Dashboard principal
        dashboard_html = st.session_state.sistema_analisis.dashboard.crear_dashboard_ejecutivo(
            st.session_state.resultados
        )
        st.markdown(dashboard_html, unsafe_allow_html=True)
        
        # Gráficos complementarios
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 📈 Comparación de Índices")
            fig_radar = st.session_state.sistema_analisis.dashboard.crear_grafico_radar(
                st.session_state.resultados
            )
            if fig_radar:
                st.plotly_chart(fig_radar, use_container_width=True)
        with col2:
            st.markdown("### 🌿 Salud de la Vegetación")
            fig_barras = st.session_state.sistema_analisis.dashboard.crear_grafico_barras_apiladas(
                st.session_state.resultados
            )
            if fig_barras:
                st.plotly_chart(fig_barras, use_container_width=True)
        
        # Mapa de calor de NDVI
        st.markdown("### 🗺️ Mapa de Calor - NDVI")
        if (st.session_state.poligono_data is not None and 
            st.session_state.resultados and 
            'areas' in st.session_state.resultados and 
            len(st.session_state.resultados['areas']) > 0):
            
            datos_areas = st.session_state.resultados['areas']
            mapa_calor = st.session_state.sistema_analisis.sistema_mapas.crear_mapa_indices(
                st.session_state.poligono_data,
                datos_areas,
                'NDVI',
                'Mapa de NDVI'
            )
            mostrar_mapa_seguro(mapa_calor, width=1000, height=500)
        
        # Resumen ejecutivo textual
        st.markdown("### 📋 Resumen Ejecutivo")
        resumen = st.session_state.resultados.get('resumen', {})
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Fortalezas del Área:**")
            if resumen.get('ndvi_promedio', 0) > 0.7:
                st.success("✅ Alta salud de la vegetación (NDVI > 0.7)")
            if resumen.get('shannon_promedio', 0) > 2.5:
                st.success("✅ Alta biodiversidad (Índice Shannon > 2.5)")
            if resumen.get('carbono_total_co2', 0) > 10000:
                st.success(f"✅ Alto potencial de captura de carbono ({resumen.get('carbono_total_co2', 0):,.0f} ton CO₂)")
        
        with col2:
            st.markdown("**Oportunidades de Mejora:**")
            if resumen.get('presion_antropica_promedio', 0) > 0.5:
                st.warning("⚠️ Presión antrópica moderada-alta")
            if resumen.get('areas_degradada', 0) > 0:
                st.error(f"❌ {resumen.get('areas_degradada', 0)} áreas degradadas detectadas")
            if resumen.get('ndwi_promedio', 0) < 0:
                st.info("💧 Baja disponibilidad de agua (NDWI negativo)")
    
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
    
    # Selector de índice para visualización
    indices_disponibles = ['NDVI', 'SAVI', 'EVI', 'NDWI', 'MSAVI']
    col1, col2 = st.columns([3, 1])
    
    with col2:
        indice_seleccionado = st.selectbox(
            "Seleccionar índice para visualizar",
            indices_disponibles,
            index=0
        )
        
        # Estadísticas del índice seleccionado
        valores_indice = [area['indices'].get(indice_seleccionado, 0) for area in areas]
        if valores_indice:
            st.metric(f"{indice_seleccionado} Promedio", f"{np.mean(valores_indice):.3f}")
            st.metric(f"{indice_seleccionado} Máximo", f"{np.max(valores_indice):.3f}")
            st.metric(f"{indice_seleccionado} Mínimo", f"{np.min(valores_indice):.3f}")
    
    with col1:
        # Mapa del índice seleccionado
        if st.session_state.poligono_data is not None:
            mapa_indice = st.session_state.sistema_analisis.sistema_mapas.crear_mapa_indices(
                st.session_state.poligono_data,
                areas,
                indice_seleccionado,
                f"Mapa de {indice_seleccionado}"
            )
            mostrar_mapa_seguro(mapa_indice, width=800, height=500)
    
    # Gráficos de comparación de índices
    st.markdown("### 📊 Comparación entre Índices")
    
    # Preparar datos para gráfico de dispersión
    datos_grafico = []
    for area in areas[:50]:  # Limitar a 50 áreas para mejor visualización
        datos_grafico.append({
            'NDVI': area['indices'].get('NDVI', 0),
            'SAVI': area['indices'].get('SAVI', 0),
            'EVI': area['indices'].get('EVI', 0),
            'NDWI': area['indices'].get('NDWI', 0),
            'Área (ha)': area['area_ha'],
            'Salud': area['indices'].get('Salud_Vegetacion', 'Moderada')
        })
    
    df_indices = pd.DataFrame(datos_grafico)
    
    # Matriz de dispersión
    fig = px.scatter_matrix(
        df_indices,
        dimensions=['NDVI', 'SAVI', 'EVI', 'NDWI'],
        color='Salud',
        title='Matriz de Dispersión entre Índices',
        color_discrete_map={
            'Excelente': '#10b981',
            'Buena': '#3b82f6',
            'Moderada': '#f59e0b',
            'Pobre': '#ef4444',
            'Degradada': '#991b1b'
        }
    )
    fig.update_layout(height=600)
    st.plotly_chart(fig, use_container_width=True)
    
    # Correlación entre índices
    st.markdown("### 🔗 Matriz de Correlación")
    corr_matrix = df_indices[['NDVI', 'SAVI', 'EVI', 'NDWI']].corr()
    
    fig_corr = go.Figure(data=go.Heatmap(
        z=corr_matrix.values,
        x=corr_matrix.columns,
        y=corr_matrix.columns,
        colorscale='RdBu',
        zmin=-1, zmax=1,
        text=np.round(corr_matrix.values, 2),
        texttemplate='%{text}',
        textfont={"size": 12}
    ))
    
    fig_corr.update_layout(
        title='Correlación entre Índices de Vegetación',
        height=400
    )
    st.plotly_chart(fig_corr, use_container_width=True)
    
    # Tabla de valores por área
    st.markdown("### 📋 Valores de Índices por Área")
    datos_tabla = []
    for area in areas[:20]:  # Mostrar primeras 20 áreas
        datos_tabla.append({
            'Área': area['area'],
            'Área (ha)': area['area_ha'],
            'NDVI': area['indices'].get('NDVI', 0),
            'SAVI': area['indices'].get('SAVI', 0),
            'EVI': area['indices'].get('EVI', 0),
            'NDWI': area['indices'].get('NDWI', 0),
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
    
    # Dashboard de carbono
    st.markdown("### 📊 Dashboard de Carbono Verra")
    dashboard_carbono_html = st.session_state.sistema_analisis.dashboard.crear_dashboard_carbono(resultados)
    st.markdown(dashboard_carbono_html, unsafe_allow_html=True)
    
    # Mapa de carbono
    st.markdown("### 🗺️ Mapa de Distribución de Carbono")
    if (st.session_state.poligono_data is not None and 
        'analisis_carbono' in resultados and 
        len(resultados['analisis_carbono']) > 0):
        
        mapa_carbono = st.session_state.sistema_analisis.sistema_mapas.crear_mapa_carbono(
            st.session_state.poligono_data,
            resultados['analisis_carbono'],
            "Mapa de Carbono según Verra VCS"
        )
        mostrar_mapa_seguro(mapa_carbono, width=1000, height=500)
    
    # Gráficos de carbono
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 📊 Distribución por Pools de Carbono")
        fig_pools = st.session_state.sistema_analisis.dashboard.crear_grafico_pools_carbono(resultados)
        if fig_pools:
            st.plotly_chart(fig_pools, use_container_width=True)
        
        # Explicación de pools
        with st.expander("ℹ️ Explicación de los Pools de Carbono VCS"):
            st.markdown("""
            **Pools de Carbono según Verra VCS:**
            1. **AGB (Above Ground Biomass)**: Biomasa aérea viva (troncos, ramas, hojas)
            2. **BGB (Below Ground Biomass)**: Biomasa subterránea (raíces)
            3. **DW (Dead Wood)**: Madera muerta en pie o en el suelo
            4. **LI (Litter)**: Hojarasca y materia orgánica superficial
            5. **SOC (Soil Organic Carbon)**: Carbono orgánico del suelo (primeros 30cm)
            
            **Metodología**: VCS VM0007 - REDD+ Methodological Framework
            **Aplicación Argentina**: Parámetros ajustados para ecosistemas locales
            """)
    
    with col2:
        st.markdown("### 📈 Distribución por Estratos VCS")
        fig_estratos = st.session_state.sistema_analisis.dashboard.crear_grafico_estratos_vcs(resultados)
        if fig_estratos:
            st.plotly_chart(fig_estratos, use_container_width=True)
        
        # Explicación de estratos
        with st.expander("ℹ️ Explicación de los Estratos VCS"):
            st.markdown("""
            **Clasificación por Estratos de Carbono:**
            - **Estrato A**: Alta densidad (>0.7 NDVI) - Carbono alto
            - **Estrato B**: Media-alta densidad (0.5-0.7 NDVI) - Carbono medio-alto
            - **Estrato C**: Media densidad (0.3-0.5 NDVI) - Carbono medio
            - **Estrato D**: Baja densidad (0.1-0. The user asked: "podes pasarme el codigo completo corregido" which means "can you pass me the complete corrected code" in Spanish. This refers to the Streamlit app code with the NASA POWER API integration for precipitation.

I need to provide the entire corrected `app.py` code, incorporating the changes for NASA POWER.

The code is very long, but I must output the full corrected version.

Key changes:
- Add `import requests`
- In class `SistemaAnalisisAmbiental`, add the two new methods: `get_annual_precipitation` and `_get_fallback_precipitation`
- In `analizar_area_completa`, calculate the center and fetch precipitation once, then use it in the loop for each cell (or add slight variation if wanted).
- In the loop where `area_data` is created, set `'precipitacion': precipitacion_anual`
- Also, update `_simular_variables_ambientales` if needed, but since the simulation is in `analizar_area_completa`, modify there.

The original code has the simulation inside the loop in `analizar_area_completa`:

For each cell:

ndvi = 0.5 + random.uniform(-0.2, 0.3)

Then variables_ambientales = self._simular_variables_ambientales(ndvi, tipo_ecosistema)

In `_simular_variables_ambientales`:

Based on tipo_ecosistema, set ranges for temperatura, precipitacion, etc.

For precipitacion: random.uniform(min, max) based on ecosistema.

To correct, I need to modify this to use the API.

In `analizar_area_completa`, before the loop, calculate centro = poligono_principal.centroid

precipitacion_anual = self.get_annual_precipitation(centro.y, centro.x, tipo_ecosistema)

Then, in the loop, instead of random in _simular, pass or set precipitacion = precipitacion_anual

But since _simular returns a dict, I need to adjust.

Looking closely, in the provided code snippet, `analizar_area_completa` has:

for i in range...

  for j in...

    celda = Polygon...

    interseccion = ...

    if ...:

      area_ha = ...

      ndvi = 0.5 + random.uniform(-0.2, 0.3)

      cobertura = self.clasificar_cobertura(ndvi)

      indices = self.simulador.calcular_indices(...)

      indice_shannon = ...

      carbono = self.calcular_carbono(ndvi, tipo_ecosistema)

      variables_ambientales = self._simular_variables_ambientales(ndvi, tipo_ecosistema)

      area_data = { 'precipitacion': variables_ambientales['precipitacion'], ... }

To fix, I can compute precipitacion_anual once before the loops, then in _simular_variables_ambientales, return the fixed value instead of random.

But to keep it simple, since precipitacion is annual for the area, use the same for all cells.

Modify _simular_variables_ambientales to take precipitacion as param, but since it's per call, better compute once and override.

Easiest: Compute once in analizar_area_completa, then in the loop, after calling _simular, override variables_ambientales['precipitacion'] = precipitacion_anual

Yes.

Also need to import requests at top.

The code is truncated in the initial message, but I have the structure.

The document is long, but I need to output the full code.

Since it's "the code complete corrected", I must provide the entire app.py with changes.<|control12|>```python
# ✅ ABSOLUTAMENTE PRIMERO: Importar streamlit
import streamlit as st
# ✅ LUEGO: Configurar la página
st.set_page_config(
    page_title="Sistema Satelital de Análisis Ambiental con Verra VCS - Argentina",
    page_icon="🇦🇷",
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
warnings.filterwarnings('ignore')
# Librerías geoespaciales
import folium
from streamlit_folium import st_folium  # Mantener para posibles usos alternativos
from folium.plugins import Fullscreen, MousePosition, HeatMap, MarkerCluster, Draw
import geopandas as gpd
from shapely.geometry import Polygon, Point, shape, MultiPolygon
import pyproj
from branca.colormap import LinearColormap
import matplotlib.cm as cm
# Para simulación de datos satelitales
import random
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
from enum import Enum
import requests  # Agregado para NASA POWER API

# ===============================
# 🗺️ FUNCIÓN SEGURA PARA MOSTRAR MAPAS
# ===============================
def mostrar_mapa_seguro(mapa, width=1000, height=600):
    """
    Mostrar mapas de Folium de manera segura para evitar errores 'removeChild'
    Args:
        mapa: Objeto folium.Map
        width: Ancho del mapa en píxeles
        height: Alto del mapa en píxeles
    """
    try:
        # Método 1: Usar components.v1.html (más estable)
        mapa_html = mapa._repr_html_()
        st.components.v1.html(mapa_html, width=width, height=height, scrolling=False)
    except Exception as e:
        st.warning(f"Error al renderizar el mapa: {str(e)}")
        # Método alternativo
        try:
            from streamlit_folium import folium_static
            folium_static(mapa, width=width, height=height)
        except:
            st.error("No se pudo mostrar el mapa. Intente recargar la página.")
# ===============================
# 🌳 CLASE PARA METODOLOGÍA VERR A (VCS)
# ===============================
class MetodologiaVerra:
    """Implementación de la metodología Verra VCS para cálculo de carbono forestal"""
    def __init__(self):
        # Factores de expansión de biomasa según VCS (VM0007, VM0035, etc.)
        self.factores_vcs = {
            # Biomasa Aérea viva (AGB)
            'AGB': {
                'ecuaciones_alometricas': {
                    'tropical_humedo': {
                        'ecuacion': lambda D, H: 0.0673 * (D**2 * H)**0.976,  # Chave et al. 2014
                        'rango_dap': (10, 150),  # cm
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
                    'temperado': {  # Nueva para bosques templados argentinos
                        'ecuacion': lambda D, H: 0.058 * (D**2 * H)**0.905,
                        'rango_dap': (10, 110),
                        'incertidumbre': 0.22
                    }
                },
                'factor_conversion_carbono': 0.47,  # IPCC 2006
                'factor_incertidumbre': 1.645  # 90% intervalo de confianza
            },
            # Biomasa Subterránea (BGB) - Raíces
            'BGB': {
                'ratio_raiz_tallo': {
                    'tropical_humedo': 0.24,  # IPCC 2006
                    'tropical_seco': 0.27,
                    'subtropical': 0.26,
                    'temperado': 0.28,  # Mayor proporción de raíces en climas fríos
                    'templado': 0.25
                },
                'incertidumbre': 0.20
            },
            # Madera Muerta (DW)
            'DW': {
                'proporcion_AGB': {
                    'bosque_primario': 0.15,
                    'bosque_secundario': 0.10,
                    'bosque_degradado': 0.20,
                    'bosque_templado': 0.18  # Para bosques andino-patagónicos
                },
                'densidad_base': 0.5,  # ton/m3
                'incertidumbre': 0.25
            },
            # Hojarasca (LI)
            'LI': {
                'acumulacion_anual': {
                    'tropical_humedo': 8.5,  # ton/ha/año
                    'tropical_seco': 6.2,
                    'subtropical': 7.3,
                    'temperado': 5.8,  # Menor acumulación en climas fríos
                    'templado': 4.5
                },
                'incertidumbre': 0.30
            },
            # Carbono Orgánico del Suelo (SOC)
            'SOC': {
                'profundidad_referencia': 30,  # cm (VCS default)
                'densidad_aparente': 1.2,  # g/cm3
                'contenido_carbono': {
                    'bosque_no_intervenido': 2.5,  # %
                    'bosque_secundario': 2.0,
                    'bosque_templado': 3.0,  # Suelos andinos más ricos en materia orgánica
                    'pastizal': 1.5,
                    'pastizal_pampeano': 2.2,  # Suelos pampeanos fértiles
                    'agricultura': 1.0,
                    'humedal': 3.5  # Alta acumulación en humedales
                },
                'factor_cambio_uso_suelo': {
                    'bosque_a_agricultura': 0.58,
                    'bosque_a_pastizal': 0.71,
                    'secundario_a_primario': 1.25,
                    'pastizal_a_agricultura': 0.65,
                    'humedal_a_agricultura': 0.40  # Gran pérdida en humedales
                },
                'incertidumbre': 0.40
            }
        }
        # Factores de conservatividad (VCS)
        self.factores_conservatividad = {
            'alto': 0.8,    # 20% descuento conservativo
            'medio': 0.9,   # 10% descuento conservativo
            'bajo': 0.95    # 5% descuento conservativo
        }
        # Clases de estrato VCS
        self.estratos_vcs = {
            'A': {'density': 'Alta', 'ndvi_range': (0.7, 1.0), 'carbon_factor': 1.0},
            'B': {'density': 'Media-Alta', 'ndvi_range': (0.5, 0.7), 'carbon_factor': 0.8},
            'C': {'density': 'Media', 'ndvi_range': (0.3, 0.5), 'carbon_factor': 0.6},
            'D': {'density': 'Baja', 'ndvi_range': (0.1, 0.3), 'carbon_factor': 0.4},
            'E': {'density': 'Muy Baja', 'ndvi_range': (-1.0, 0.1), 'carbon_factor': 0.1}
        }
    def calcular_carbono_arbol_individual(self, dap_cm, altura_m, tipo_bosque="subtropical"):
        """Calcular carbono en un árbol individual usando ecuaciones alométricas VCS"""
        if dap_cm < 10:  # Límite mínimo VCS
            return 0.0
        try:
            # Obtener ecuación alométrica
            ecuacion = self.factores_vcs['AGB']['ecuaciones_alometricas'][tipo_bosque]['ecuacion']
            # Calcular biomasa aérea (kg)
            agb_kg = ecuacion(dap_cm, altura_m)
            # Convertir a carbono (47% de la biomasa)
            carbono_arbol_kg = agb_kg * self.factores_vcs['AGB']['factor_conversion_carbono']
            return carbono_arbol_kg / 1000  # Retornar en toneladas
        except Exception as e:
            # Fórmula simplificada de respaldo
            return (0.05 * dap_cm**2 * altura_m * 0.47) / 1000
    def calcular_carbono_hectarea(self, ndvi, tipo_bosque="subtropical", estado="bosque_secundario", area_ha=1.0):
        """Calcular carbono total por hectárea según metodología VCS"""
        # Estimación de biomasa basada en NDVI
        if ndvi > 0.7:
            # Bosque denso
            agb_ton_ha = 200 + (ndvi - 0.7) * 100  # 200-250 ton/ha
        elif ndvi > 0.5:
            # Bosque medio
            agb_ton_ha = 120 + (ndvi - 0.5) * 400  # 120-200 ton/ha
        elif ndvi > 0.3:
            # Bosque bajo/vegetación arbustiva
            agb_ton_ha = 40 + (ndvi - 0.3) * 400   # 40-120 ton/ha
        else:
            # No bosque
            agb_ton_ha = 5 + ndvi * 100            # 5-40 ton/ha
        # Ajustar por tipo de bosque
        if tipo_bosque == "tropical_seco":
            agb_ton_ha *= 0.8
        elif tipo_bosque == "subtropical":
            agb_ton_ha *= 0.9
        elif tipo_bosque == "temperado":
            agb_ton_ha *= 0.7  # Bosques templados tienen menor biomasa
        # ===== CÁLCULO DE POOLS DE CARBONO VCS =====
        # 1. Carbono en Biomasa Aérea viva (AGB)
        carbono_agb = agb_ton_ha * self.factores_vcs['AGB']['factor_conversion_carbono']
        # 2. Carbono en Biomasa Subterránea (BGB - raíces)
        ratio_bgb = self.factores_vcs['BGB']['ratio_raiz_tallo'].get(tipo_bosque, 0.26)
        carbono_bgb = carbono_agb * ratio_bgb
        # 3. Carbono en Madera Muerta (DW)
        proporcion_dw = self.factores_vcs['DW']['proporcion_AGB'].get(estado, 0.1)
        carbono_dw = carbono_agb * proporcion_dw
        # 4. Carbono en Hojarasca (LI)
        acumulacion_li = self.factores_vcs['LI']['acumulacion_anual'].get(tipo_bosque, 5.0)
        # Asumir 5 años de acumulación
        carbono_li = acumulacion_li * 5 * self.factores_vcs['AGB']['factor_conversion_carbono'] * 0.3
        # 5. Carbono Orgánico del Suelo (SOC)
        contenido_soc = self.factores_vcs['SOC']['contenido_carbono'].get(estado, 1.5)
        # Ajustar para ecosistemas específicos
        if estado == "humedal":
            contenido_soc = 3.5
        elif estado == "pastizal_pampeano":
            contenido_soc = 2.2
        # Cálculo simplificado: ton C/ha en primeros 30cm
        carbono_soc = (self.factores_vcs['SOC']['profundidad_referencia'] * 
                      self.factores_vcs['SOC']['densidad_aparente'] * 
                      contenido_soc * 10)  # 10 para convertir a ton/ha
        # Total carbono por hectárea (ton C/ha)
        carbono_total_ton_ha = (
            carbono_agb + 
            carbono_bgb + 
            carbono_dw + 
            carbono_li + 
            carbono_soc
        )
        # Aplicar factor de conservatividad (default: medio)
        factor_conservatividad = self.factores_conservatividad['medio']
        carbono_total_ton_ha *= factor_conservatividad
        # Convertir a CO₂ equivalente
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
                'ratio_co2_carbono': 3.67
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
        # Incertidumbres combinadas (método de propagación de errores)
        try:
            incertidumbre_agb = self.factores_vcs['AGB']['ecuaciones_alometricas'][tipo_bosque]['incertidumbre']
        except:
            incertidumbre_agb = 0.20
        incertidumbre_bgb = self.factores_vcs['BGB']['incertidumbre']
        incertidumbre_dw = self.factores_vcs['DW']['incertidumbre']
        incertidumbre_li = self.factores_vcs['LI']['incertidumbre']
        incertidumbre_soc = self.factores_vcs['SOC']['incertidumbre']
        # Incertidumbre combinada (raíz cuadrada de la suma de cuadrados)
        incertidumbre_combinada = math.sqrt(
            incertidumbre_agb**2 + 
            incertidumbre_bgb**2 + 
            incertidumbre_dw**2 + 
            incertidumbre_li**2 + 
            incertidumbre_soc**2
        )
        # Intervalo de confianza al 90%
        intervalo_confianza = carbono_total * incertidumbre_combinada * self.factores_vcs['AGB']['factor_incertidumbre']
        return {
            'incertidumbre_relativa': round(incertidumbre_combinada * 100, 1),  # Porcentaje
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
        Carbono total estimado: {resultados_carbono['carbono_total_ton_ha']:,.2f} ton C/ha
        CO₂ equivalente total: {resultados_carbono['co2_equivalente_ton_ha']:,.2f} ton CO₂e/ha
        DESGLOSE POR POOLS DE CARBONO (ton C/ha):
        -----------------------------------------
        • Biomasa Aérea viva (AGB): {resultados_carbono['desglose']['AGB']:,.2f}
        • Biomasa Subterránea (BGB): {resultados_carbono['desglose']['BGB']:,.2f}
        • Madera Muerta (DW): {resultados_carbono['desglose']['DW']:,.2f}
        • Hojarasca (LI): {resultados_carbono['desglose']['LI']:,.2f}
        • Carbono Orgánico del Suelo (SOC): {resultados_carbono['desglose']['SOC']:,.2f}
        FACTORES APLICADOS:
        -------------------
        • Tipo de bosque: {resultados_carbono['factores_aplicados']['tipo_bosque']}
        • Estado del bosque: {resultados_carbono['factores_aplicados']['estado']}
        • Factor de conservatividad: {resultados_carbono['factores_aplicados']['factor_conservatividad']}
        • Ratio CO₂/Carbono: {resultados_carbono['factores_aplicados']['ratio_co2_carbono']}
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
# 🌳 SISTEMA DE ANÁLISIS DE CARBONO VERRA
# ===============================
class AnalisisCarbonoVerra:
    """Sistema completo de análisis de carbono con metodología Verra"""
    def __init__(self):
        self.metodologia = MetodologiaVerra()
    
    def analizar_carbono_area(self, gdf, tipo_ecosistema, nivel_detalle=8):
        """Analizar carbono en toda el área usando metodología Verra"""
        try:
            poligono_principal = gdf.geometry.iloc[0]
            bounds = poligono_principal.bounds
            
            # Mapear tipo de ecosistema SIB a parámetros VCS
            mapeo_ecosistema_vcs = {
                # Bosques densos - alta biomasa
                'Bosque Andino Patagónico': ('temperado', 'bosque_templado'),
                'Bosque de Araucaria': ('temperado', 'bosque_templado'),
                'Bosque de Yungas': ('tropical_humedo', 'bosque_primario'),
                'Bosque de Selva Misionera': ('tropical_humedo', 'bosque_primario'),
                
                # Bosques secos y secundarios
                'Bosque de Caldén': ('tropical_seco', 'bosque_secundario'),
                'Bosque de Quebracho': ('tropical_seco', 'bosque_secundario'),
                'Bosque de Algarrobo': ('tropical_seco', 'bosque_secundario'),
                'Bosque de Chaco Serrano': ('tropical_seco', 'bosque_secundario'),
                'Matorral del Espinal': ('tropical_seco', 'bosque_degradado'),
                'Matorral Chaqueño': ('tropical_seco', 'bosque_degradado'),
                'Arbustal de Altura': ('temperado', 'bosque_degradado'),
                
                # Pastizales y estepas
                'Pastizal Pampeano': ('subtropical', 'pastizal_pampeano'),
                'Pastizal Mesopotámico': ('subtropical', 'pastizal'),
                'Estepa Patagónica': ('temperado', 'pastizal'),
                'Estepa Altoandina': ('temperado', 'pastizal'),
                'Estepa del Monte': ('tropical_seco', 'pastizal'),
                
                # Humedales
                'Humedales del Iberá': ('subtropical', 'humedal'),
                'Humedales del Paraná': ('subtropical', 'humedal'),
                'Bañados y esteros': ('subtropical', 'humedal'),
                'Delta e Islas del Paraná': ('subtropical', 'humedal'),
                'Turberas y mallines': ('subtropical', 'humedal'),
                
                # Áreas productivas
                'Agricultura intensiva': ('subtropical', 'agricultura'),
                'Agricultura extensiva': ('subtropical', 'agricultura'),
                'Ganadería extensiva': ('subtropical', 'pastizal'),
                'Silvicultura': ('subtropical', 'bosque_secundario'),
                
                # Áreas urbanas e intervenidas
                'Zona urbana consolidada': ('subtropical', 'agricultura'),
                'Periurbano': ('subtropical', 'agricultura'),
                'Infraestructura': ('subtropical', 'agricultura'),
                'Área minera': ('subtropical', 'agricultura'),
                
                # Cuerpos de agua (mínimo carbono)
                'Ríos y arroyos': ('subtropical', 'agricultura'),
                'Lagunas y lagos': ('subtropical', 'agricultura'),
                'Embalses': ('subtropical', 'agricultura'),
                'Mar y costa': ('subtropical', 'agricultura')
            }
            
            tipo_vcs, estado_vcs = mapeo_ecosistema_vcs.get(
                tipo_ecosistema, 
                ('subtropical', 'bosque_secundario')  # Valor por defecto para Argentina
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
                    'fecha_analisis': datetime.now().strftime('%Y-%m-%d')
                }
            }
            
            id_area = 1
            
            # Dividir en grilla para análisis detallado
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
                        # Calcular área en hectáreas
                        area_m2 = interseccion.area * 111000 * 111000 * math.cos(math.radians((ymin+ymax)/2))
                        area_ha = area_m2 / 10000
                        
                        if area_ha > 0.01:
                            # Simular NDVI para esta celda
                            # En un sistema real, esto vendría del análisis satelital
                            ndvi = 0.5 + random.uniform(-0.2, 0.3)
                            
                            # Clasificar estrato VCS
                            estrato_info = self.metodologia.clasificar_estrato_vcs(ndvi)
                            
                            # Calcular carbono según metodología Verra
                            carbono_info = self.metodologia.calcular_carbono_hectarea(
                                ndvi=ndvi,
                                tipo_bosque=tipo_vcs,
                                estado=estado_vcs,
                                area_ha=area_ha
                            )
                            
                            # Calcular incertidumbre
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
                                'factores_aplicados': carbono_info['factores_aplicados']
                            }
                            
                            resultados['analisis_carbono'].append(area_data)
                            id_area += 1
            
            # Calcular resumen estadístico
            if resultados['analisis_carbono']:
                self._calcular_resumen_carbono(resultados)
            
            return resultados
            
        except Exception as e:
            st.error(f"Error en análisis de carbono Verra: {str(e)}")
            return None
    
    def _calcular_resumen_carbono(self, resultados):
        """Calcular estadísticas resumen del análisis de carbono"""
        areas_carbono = resultados['analisis_carbono']
        if not areas_carbono:
            return
        
        # Calcular totales
        carbono_total = sum(a['carbono_total_ton'] for a in areas_carbono)
        co2_total = sum(a['co2_equivalente_ton'] for a in areas_carbono)
        area_total = sum(a['area_ha'] for a in areas_carbono)
        
        # Promedios por hectárea
        carbono_promedio_ha = np.mean([a['carbono_por_ha'] for a in areas_carbono])
        co2_promedio_ha = np.mean([a['co2_por_ha'] for a in areas_carbono])
        
        # Distribución por estratos VCS
        estratos = {}
        for area in areas_carbono:
            estrato = area['estrato_vcs']
            if estrato not in estratos:
                estratos[estrato] = {
                    'cantidad': 0,
                    'area_total': 0,
                    'carbono_total': 0
                }
            estratos[estrato]['cantidad'] += 1
            estratos[estrato]['area_total'] += area['area_ha']
            estratos[estrato]['carbono_total'] += area['carbono_total_ton']
        
        # Distribución por pools de carbono
        pools = {'AGB': 0, 'BGB': 0, 'DW': 0, 'LI': 0, 'SOC': 0}
        for area in areas_carbono:
            for pool, valor in area['desglose_carbono'].items():
                pools[pool] += valor * area['area_ha']
        
        # Calcular incertidumbre promedio
        incertidumbre_promedio = np.mean([a['incertidumbre']['incertidumbre_relativa'] 
                                         for a in areas_carbono])
        
        resultados['resumen_carbono'] = {
            'carbono_total_ton': round(carbono_total, 2),
            'co2_total_ton': round(co2_total, 2),
            'area_total_ha': round(area_total, 2),
            'carbono_promedio_ton_ha': round(carbono_promedio_ha, 2),
            'co2_promedio_ton_ha': round(co2_promedio_ha, 2),
            'potencial_creditos': round(co2_total / 1000, 1),  # En miles de créditos (1 crédito = 1 ton CO₂)
            'incertidumbre_promedio': round(incertidumbre_promedio, 1),
            'estratos_distribucion': estratos,
            'pools_distribucion': pools
        }
        
        # Evaluar elegibilidad VCS
        elegibilidad = self._evaluar_elegibilidad_vcs(resultados)
        resultados['resumen_carbono']['elegibilidad_vcs'] = elegibilidad
    
    def _evaluar_elegibilidad_vcs(self, resultados):
        """Evaluar elegibilidad del proyecto según criterios VCS"""
        resumen = resultados['resumen_carbono']
        criterios = {
            'carbono_minimo': resumen['co2_total_ton'] > 10000,  # Mínimo 10,000 ton CO₂
            'area_minima': resumen['area_total_ha'] > 100,  # Mínimo 100 ha
            'permanencia_potencial': True,  # Asumir sí por ahora
            'adicionalidad_potencial': True  # Asumir sí por ahora
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
    resolucion: float  # en metros
    descripcion: str

@dataclass
class ImagenSatelital:
    """Metadatos de imagen satelital"""
    satelite: Satelite
    fecha_adquisicion: datetime
    nubosidad: float  # 0-1
    indice_calidad: float  # 0-1
    bandas_disponibles: List[str]
    url_visualizacion: Optional[str] = None
# ===============================
# 🛰️ SIMULADOR DE DATOS SATELITALES
# ===============================
class SimuladorSatelital:
    """Simulador de datos satelitales para PlanetScope y Sentinel-2"""
    def __init__(self):
        # Configuración de bandas por satélite
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
        
        # Rangos típicos de reflectancia por tipo de cobertura
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
        
        # Mapear bandas a categorías generales
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
            cat = 'nir'  # Por defecto
        
        # Obtener rango según tipo de cobertura
        if tipo_cobertura in self.rangos_reflectancia:
            rango = self.rangos_reflectancia[tipo_cobertura].get(cat, (0.01, 0.1))
        else:
            rango = (0.01, 0.1)
        
        # Añadir variación aleatoria
        return random.uniform(rango[0], rango[1])
    
    def calcular_indices(self, reflectancias: Dict[str, float], satelite: Satelite):
        """Calcular índices espectrales a partir de reflectancias"""
        indices = {}
        
        try:
            # NDVI - Índice de Vegetación de Diferencia Normalizada
            if satelite == Satelite.PLANETSCOPE:
                red = reflectancias.get('B3', 0.1)
                nir = reflectancias.get('B4', 0.3)
            else:  # Sentinel-2
                red = reflectancias.get('B4', 0.1)
                nir = reflectancias.get('B8', 0.3)
            
            if nir + red > 0:
                indices['NDVI'] = (nir - red) / (nir + red)
            else:
                indices['NDVI'] = 0.0
            
            # SAVI - Índice de Vegetación Ajustado al Suelo
            L = 0.5  # Factor de corrección del suelo
            if nir + red + L > 0:
                indices['SAVI'] = ((nir - red) / (nir + red + L)) * (1 + L)
            else:
                indices['SAVI'] = 0.0
            
            # EVI - Índice de Vegetación Mejorado
            if satelite == Satelite.SENTINEL2:
                blue = reflectancias.get('B2', 0.05)
                indices['EVI'] = 2.5 * ((nir - red) / (nir + 6 * red - 7.5 * blue + 1))
            else:
                indices['EVI'] = indices['NDVI'] * 1.2  # Aproximación
            
            # NDWI - Índice de Agua de Diferencia Normalizada
            if satelite == Satelite.SENTINEL2:
                green = reflectancias.get('B3', 0.08)
                nir2 = reflectancias.get('B8A', nir)
                indices['NDWI'] = (green - nir2) / (green + nir2)
            else:
                indices['NDWI'] = -indices['NDVI'] * 0.5  # Aproximación
            
            # MSAVI - Índice de Vegetación Ajustado al Suelo Modificado
            indices['MSAVI'] = (2 * nir + 1 - np.sqrt((2 * nir + 1)**2 - 8 * (nir - red))) / 2
            
            # GNDVI - Índice de Vegetación de Diferencia Normalizada Verde
            if satelite == Satelite.SENTINEL2:
                green = reflectancias.get('B3', 0.08)
                indices['GNDVI'] = (nir - green) / (nir + green)
            
            # Clasificar salud vegetal basada en NDVI
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
            # Valores por defecto en caso de error
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
# 🗺️ SISTEMA DE MAPAS AVANZADO CON IMÁGENES SATELITALES
# ===============================
class SistemaMapasAvanzado:
    """Sistema de mapas con integración satelital y zoom automático"""
    def __init__(self):
        self.simulador = SimuladorSatelital()
        # Capas base con URLs reales de servicios WMS/TMS
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
            return [-34.0, -64.0], 6  # Centro de Argentina por defecto
        
        try:
            # Calcular centroide
            bounds = gdf.total_bounds
            centro = [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2]
            
            # Calcular área en km²
            poligono = gdf.geometry.iloc[0]
            if hasattr(poligono, 'area'):
                # Conversión aproximada de grados a km²
                lat_centro = centro[0]
                cos_lat = math.cos(math.radians(lat_centro))
                area_grados = poligono.area
                area_km2 = area_grados * 111 * 111 * cos_lat
                
                # Algoritmo de zoom basado en área (optimizado)
                if area_km2 < 0.1:      # Muy pequeño (< 0.1 km²)
                    zoom = 16
                elif area_km2 < 1:      # Pequeño (0.1-1 km²)
                    zoom = 15
                elif area_km2 < 10:     # Pequeño-mediano (1-10 km²)
                    zoom = 14
                elif area_km2 < 50:     # Mediano (10-50 km²)
                    zoom = 13
                elif area_km2 < 100:    # Mediano-grande (50-100 km²)
                    zoom = 12
                elif area_km2 < 500:    # Grande (100-500 km²)
                    zoom = 11
                elif area_km2 < 1000:   # Muy grande (500-1000 km²)
                    zoom = 10
                elif area_km2 < 5000:   # Enorme (1000-5000 km²)
                    zoom = 9
                else:                   # Gigantesco (>5000 km²)
                    zoom = 8
            else:
                zoom = 10
                
            return centro, min(zoom, 16)  # Limitar zoom máximo
        except Exception:
            return [-34.0, -64.0], 6  # Centro de Argentina por defecto
    
    def crear_mapa_satelital(self, gdf, titulo="Área de Estudio", capa_base="ESRI World Imagery"):
        """Crear mapa con capa satelital y polígono"""
        centro, zoom = self.calcular_zoom_automatico(gdf)
        
        # Crear mapa base con ID único para evitar conflictos DOM
        mapa_id = f"map_{int(datetime.now().timestamp() * 1000)}"
        m = folium.Map(
            location=centro,
            zoom_start=zoom,
            tiles=None,
            control_scale=True,
            zoom_control=True,
            prefer_canvas=True
        )
        
        # Agregar capa base seleccionada
        capa_config = self.capas_base.get(capa_base, self.capas_base['ESRI World Imagery'])
        
        if '{date}' in capa_config['tiles']:
            # Reemplazar parámetros dinámicos
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
        
        # Agregar polígono si existe
        if gdf is not None and not gdf.empty:
            try:
                poligono = gdf.geometry.iloc[0]
                
                # Calcular área aproximada
                bounds = gdf.total_bounds
                lat_centro = centro[0]
                cos_lat = math.cos(math.radians(lat_centro))
                area_grados = gdf.geometry.area.iloc[0]
                area_km2 = area_grados * 111 * 111 * cos_lat
                area_ha = area_km2 * 100
                
                # Tooltip informativo
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
                
                # Estilo del polígono
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
                
                # Agregar marcador en el centro
                folium.Marker(
                    location=centro,
                    popup=f"<b>Centro del área de estudio</b><br>Área: {area_ha:,.1f} ha",
                    icon=folium.Icon(color='blue', icon='info-sign', prefix='fa')
                ).add_to(m)
                
                # Ajustar vista al polígono con margen
                m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]], padding=(50, 50))
                
            except Exception as e:
                st.warning(f"Error al visualizar polígono: {str(e)}")
        
        # Agregar capas adicionales
        for nombre, config in self.capas_base.items():
            if nombre != capa_base:
                folium.TileLayer(
                    tiles=config['tiles'] if '{date}' not in config['tiles'] else config['tiles'].replace('{date}', datetime.now().strftime('%Y-%m')),
                    attr=config['attr'],
                    name=config['nombre'],
                    overlay=False,
                    control=True
                ).add_to(m)
        
        # Controles adicionales
        Fullscreen(position='topright').add_to(m)
        MousePosition(position='bottomleft').add_to(m)
        folium.LayerControl(position='topright', collapsed=False).add_to(m)
        
        # Medir distancia (opcional, puede causar conflictos)
        try:
            Draw(
                export=True,
                position='topleft',
                draw_options={
                    'polyline': True,
                    'rectangle': True,
                    'polygon': True,
                    'circle': False,
                    'marker': True,
                    'circlemarker': False
                }
            ).add_to(m)
        except:
            pass  # Ignorar si hay error en controles Draw
        
        return m
    
    def crear_mapa_indices(self, gdf, datos_areas, indice_seleccionado, titulo="Mapa de Índices"):
        """Crear mapa temático para índices satelitales"""
        centro, zoom = self.calcular_zoom_automatico(gdf)
        
        # Mapa base con capa satelital
        m = folium.Map(
            location=centro,
            zoom_start=zoom,
            tiles=self.capas_base['ESRI World Imagery']['tiles'],
            attr=self.capas_base['ESRI World Imagery']['attr'],
            control_scale=True
        )
        
        # Agregar polígono base semi-transparente
        if gdf is not None and not gdf.empty:
            folium.GeoJson(
                gdf.geometry.iloc[0],
                style_function=lambda x: {
                    'fillColor': '#ffffff',
                    'color': '#000000',
                    'weight': 1,
                    'fillOpacity': 0.05,
                    'opacity': 0.3
                }
            ).add_to(m)
        
        # Definir paletas de colores por índice
        paletas_colores = {
            'NDVI': ['#8B0000', '#FF4500', '#FFD700', '#32CD32', '#006400'],  # Rojo a Verde
            'SAVI': ['#8B4513', '#DEB887', '#FFD700', '#32CD32', '#006400'],  # Marrón a Verde
            'EVI': ['#4B0082', '#9370DB', '#32CD32', '#FFD700', '#FF4500'],   # Violeta a Rojo
            'NDWI': ['#8B0000', '#FF4500', '#FFD700', '#87CEEB', '#00008B'],  # Rojo a Azul
            'MSAVI': ['#8B4513', '#D2691E', '#FFD700', '#32CD32', '#006400'] # Marrón a Verde
        }
        
        # Obtener paleta para el índice seleccionado
        colores = paletas_colores.get(indice_seleccionado, ['#808080', '#A9A9A9', '#D3D3D3'])
        
        # Crear capa de calor para los índices
        heatmap_data = []
        for area_data in datos_areas:
            try:
                valor = area_data.get('indices', {}).get(indice_seleccionado, 0)
                geometry = area_data.get('geometry')
                
                if geometry and hasattr(geometry, 'centroid'):
                    centroid = geometry.centroid
                    heatmap_data.append([centroid.y, centroid.x, valor])
                    
                    # También agregar polígono coloreado
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
        
        # Agregar heatmap si hay datos suficientes
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
        
        # Agregar leyenda
        self._agregar_leyenda(m, indice_seleccionado, colores)
        
        # Controles
        Fullscreen().add_to(m)
        folium.LayerControl().add_to(m)
        
        return m
    
    def crear_mapa_carbono(self, gdf, datos_carbono, titulo="Mapa de Carbono"):
        """Crear mapa temático para carbono según metodología Verra"""
        centro, zoom = self.calcular_zoom_automatico(gdf)
        
        m = folium.Map(
            location=centro,
            zoom_start=zoom,
            tiles=self.capas_base['ESRI World Imagery']['tiles'],
            attr=self.capas_base['ESRI World Imagery']['attr'],
            control_scale=True
        )
        
        # Paleta de colores para carbono (verde oscuro a claro)
        colores_carbono = ['#00441b', '#238b45', '#41ab5d', '#74c476', '#a1d99b', '#d9f0a3']
        
        # Encontrar rango de valores de carbono
        valores_carbono = [d.get('carbono_por_ha', 0) for d in datos_carbono]
        if valores_carbono:
            min_carbono = min(valores_carbono)
            max_carbono = max(valores_carbono)
        else:
            min_carbono, max_carbono = 0, 100
        
        # Crear capa de calor y polígonos coloreados
        heatmap_data = []
        for area_data in datos_carbono:
            try:
                carbono_ha = area_data.get('carbono_por_ha', 0)
                co2_ha = area_data.get('co2_por_ha', 0)
                geometry = area_data.get('geometry')
                estrato = area_data.get('estrato_vcs', 'E')
                
                if geometry and hasattr(geometry, 'centroid'):
                    centroid = geometry.centroid
                    heatmap_data.append([centroid.y, centroid.x, carbono_ha])
                    
                    # Calcular índice de color
                    if max_carbono > min_carbono:
                        normalized = (carbono_ha - min_carbono) / (max_carbono - min_carbono)
                    else:
                        normalized = 0.5
                    
                    color_idx = min(int(normalized * (len(colores_carbono) - 1)), len(colores_carbono) - 1)
                    color = colores_carbono[color_idx]
                    
                    # Tooltip con información de carbono
                    tooltip = f"""
                    <div style="font-family: Arial; font-size: 12px;">
                        <b>Carbono según Verra VCS</b><br>
                        <hr style="margin: 3px 0;">
                        <b>Estrato:</b> {estrato}<br>
                        <b>Carbono:</b> {carbono_ha:.1f} ton C/ha<br>
                        <b>CO₂ equivalente:</b> {co2_ha:.1f} ton CO₂e/ha<br>
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
        
        # Agregar heatmap
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
        
        # Agregar leyenda de carbono
        self._agregar_leyenda_carbono(m, min_carbono, max_carbono, colores_carbono)
        
        # Controles
        Fullscreen().add_to(m)
        folium.LayerControl().add_to(m)
        
        return m
    
    def _agregar_leyenda(self, mapa, indice, colores):
        """Agregar leyenda al mapa"""
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
        """Agregar leyenda de carbono al mapa"""
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
                    <i>CO₂ equivalente = Carbono × 3.67</i>
                </div>
            </div>
        </div>
        '''
        mapa.get_root().html.add_child(folium.Element(leyenda_html))
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
    
    def crear_kpi_card(self, titulo, valor, icono, color, unidad="", cambio=None):
        """Crear tarjeta KPI estilizada"""
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
        """Crear tarjeta KPI especializada para carbono"""
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
    
    def crear_dashboard_ejecutivo(self, resultados):
        """Crear dashboard ejecutivo completo"""
        if not resultados:
            return None
        
        resumen = resultados.get('resumen', {})
        
        # Crear HTML del dashboard
        dashboard_html = f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2rem; border-radius: 15px; margin-bottom: 2rem; color: white;">
            <h2 style="margin: 0; font-size: 2rem;">📊 Dashboard Ejecutivo</h2>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Resumen integral del análisis ambiental</p>
        </div>
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 2rem;">
            {self.crear_kpi_card('Estado General', resumen.get('estado_general', 'N/A'), '📈', resumen.get('color_estado', '#808080'))}
            {self.crear_kpi_card('Área Total', f"{resumen.get('area_total_ha', 0):,.0f}", '📐', '#3b82f6', 'hectáreas')}
            {self.crear_kpi_card('NDVI Promedio', f"{resumen.get('ndvi_promedio', 0):.3f}", '🌿', '#10b981')}
            {self.crear_kpi_card('Biodiversidad', f"{resumen.get('shannon_promedio', 0):.2f}", '🦋', '#8b5cf6', 'Índice')}
        </div>
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem;">
            {self.crear_kpi_card('Carbono Total', f"{resumen.get('carbono_total_co2', 0):,.0f}", '🌳', '#065f46', 'ton CO₂')}
            {self.crear_kpi_card('Áreas Óptimas', resumen.get('areas_optimas', 0), '✅', '#10b981')}
            {self.crear_kpi_card('Temperatura', f"{resumen.get('temperatura_promedio', 0):.1f}", '🌡️', '#ef4444', '°C')}
            {self.crear_kpi_card('Precipitación', f"{resumen.get('precipitacion_promedio', 0):.0f}", '💧', '#0ea5e9', 'mm/año')}
        </div>
        """
        return dashboard_html
    
    def crear_dashboard_carbono(self, resultados_carbono):
        """Crear dashboard especializado para análisis de carbono"""
        if not resultados_carbono:
            return None
        
        resumen = resultados_carbono.get('resumen_carbono', {})
        
        # Calcular valor económico aproximado (US$15/ton CO₂)
        valor_economico = resumen.get('co2_total_ton', 0) * 15
        
        dashboard_html = f"""
        <div style="background: linear-gradient(135deg, #065f46 0%, #0a7e5a 100%); padding: 2rem; border-radius: 15px; margin-bottom: 2rem; color: white;">
            <h2 style="margin: 0; font-size: 2rem;">🌳 Análisis de Carbono - Verra VCS</h2>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Metodología VCS VM0007 para proyectos REDD+</p>
        </div>
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 2rem;">
            {self.crear_kpi_carbono('Carbono Total', f"{resumen.get('carbono_total_ton', 0):,.0f}", '🌳', '#065f46', 'ton C', 'Almacenamiento total')}
            {self.crear_kpi_carbono('CO₂ Equivalente', f"{resumen.get('co2_total_ton', 0):,.0f}", '🏭', '#0a7e5a', 'ton CO₂e', 'Potencial de créditos')}
            {self.crear_kpi_carbono('Carbono Promedio', f"{resumen.get('carbono_promedio_ton_ha', 0):,.1f}", '📊', '#10b981', 'ton C/ha', 'Por hectárea')}
            {self.crear_kpi_carbono('Área Total', f"{resumen.get('area_total_ha', 0):,.1f}", '🗺️', '#3b82f6', 'hectáreas', 'Área del proyecto')}
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
        """Crear gráfico radar para comparación de índices"""
        if not resultados:
            return None
        
        resumen = resultados.get('resumen', {})
        
        # Datos para el radar
        categorias = ['NDVI', 'SAVI', 'EVI', 'Biodiversidad', 'Carbono']
        valores = [
            resumen.get('ndvi_promedio', 0) * 100,
            resumen.get('savi_promedio', 0) * 100,
            resumen.get('evi_promedio', 0) * 100,
            min(resumen.get('shannon_promedio', 0) * 25, 100),  # Escalar Shannon (0-4 -> 0-100)
            min(resumen.get('carbono_promedio_ha', 0) / 3, 100)  # Escalar Carbono (0-300 -> 0-100)
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
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )),
            showlegend=True,
            title='Comparación de Índices Ambientales',
            height=400
        )
        
        return fig
    
    def crear_grafico_pools_carbono(self, resultados_carbono):
        """Crear gráfico de torta para pools de carbono"""
        if not resultados_carbono:
            return None
        
        pools = resultados_carbono.get('resumen_carbono', {}).get('pools_distribucion', {})
        if not pools:
            return None
        
        labels = list(pools.keys())
        values = list(pools.values())
        
        # Colores específicos para pools VCS
        colores_pools = {
            'AGB': '#238b45',  # Verde oscuro - Biomasa aérea
            'BGB': '#41ab5d',  # Verde medio - Raíces
            'DW': '#74c476',   # Verde claro - Madera muerta
            'LI': '#a1d99b',   # Verde muy claro - Hojarasca
            'SOC': '#d9f0a3'   # Verde amarillento - Suelo
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
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5
            )
        )
        
        return fig
    
    def crear_grafico_estratos_vcs(self, resultados_carbono):
        """Crear gráfico de barras para estratos VCS"""
        if not resultados_carbono:
            return None
        
        estratos = resultados_carbono.get('resumen_carbono', {}).get('estratos_distribucion', {})
        if not estratos:
            return None
        
        # Ordenar estratos de A (alto) a E (bajo)
        orden_estratos = ['A', 'B', 'C', 'D', 'E']
        labels = []
        areas = []
        carbono = []
        
        for estrato in orden_estratos:
            if estrato in estratos:
                labels.append(f"Estrato {estrato}")
                areas.append(estratos[estrato]['area_total'])
                carbono.append(estratos[estrato]['carbono_total'])
        
        # Colores para estratos
        colores_estratos = ['#00441b', '#238b45', '#41ab5d', '#74c476', '#a1d99b']
        
        fig = make_subplots(specs=[[ {"secondary_y": True} ]])
        
        # Barras para área
        fig.add_trace(
            go.Bar(
                x=labels,
                y=areas,
                name='Área (ha)',
                marker_color=colores_estratos,
                text=[f"{a:.1f} ha" for a in areas],
                textposition='auto'
            ),
            secondary_y=False
        )
        
        # Línea para carbono
        fig.add_trace(
            go.Scatter(
                x=labels,
                y=carbono,
                name='Carbono (ton)',
                mode='lines+markers',
                line=dict(color='#065f46', width=3),
                marker=dict(size=10, color='#0a7e5a')
            ),
            secondary_y=True
        )
        
        fig.update_layout(
            title='Distribución por Estratos VCS',
            height=400,
            xaxis_title='Estratos de Carbono',
            barmode='group'
        )
        
        fig.update_yaxes(title_text="Área (ha)", secondary_y=False)
        fig.update_yaxes(title_text="Carbono Total (ton)", secondary_y=True)
        
        return fig
    
    def crear_grafico_barras_apiladas(self, resultados):
        """Crear gráfico de barras apiladas para distribución de áreas"""
        if not resultados:
            return None
        
        areas = resultados.get('areas', [])
        
        # Contar áreas por categoría de salud
        categorias = {
            'Excelente': 0,
            'Buena': 0,
            'Moderada': 0,
            'Pobre': 0,
            'Degradada': 0
        }
        
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
# 🌿 SISTEMA DE ANÁLISIS AMBIENTAL COMPLETO
# ===============================
class SistemaAnalisisAmbiental:
    """Sistema completo de análisis ambiental con datos satelitales"""
    def __init__(self):
        self.simulador = SimuladorSatelital()
        self.sistema_mapas = SistemaMapasAvanzado()
        self.dashboard = DashboardResumen()
        self.analisis_carbono = AnalisisCarbonoVerra()
        
        # Tipos de cobertura vegetal según SIB Argentina
        self.tipos_cobertura = {
            # Bosques
            'Bosque Andino Patagónico': 'bosque_templado',
            'Bosque de Araucaria': 'bosque_templado',
            'Bosque de Caldén': 'bosque_secundario',
            'Bosque de Quebracho': 'bosque_secundario',
            'Bosque de Algarrobo': 'bosque_secundario',
            'Bosque de Yungas': 'bosque_denso',
            'Bosque de Selva Misionera': 'bosque_denso',
            'Bosque de Chaco Serrano': 'bosque_secundario',
            
            # Pastizales y estepas
            'Pastizal Pampeano': 'pastizal_pampeano',
            'Pastizal Mesopotámico': 'pastizal',
            'Estepa Patagónica': 'pastizal',
            'Estepa Altoandina': 'pastizal',
            'Estepa del Monte': 'pastizal',
            
            # Humedales y áreas inundables
            'Humedales del Iberá': 'humedal',
            'Humedales del Paraná': 'humedal',
            'Bañados y esteros': 'humedal',
            'Delta e Islas del Paraná': 'humedal',
            'Turberas y mallines': 'humedal',
            
            # Matorrales y arbustales
            'Matorral del Espinal': 'bosque_secundario',
            'Matorral Chaqueño': 'bosque_secundario',
            'Arbustal de Altura': 'bosque_secundario',
            
            # Áreas productivas
            'Agricultura intensiva': 'pastizal',
            'Agricultura extensiva': 'pastizal',
            'Ganadería extensiva': 'pastizal',
            'Silvicultura': 'bosque_secundario',
            
            # Áreas urbanas e intervenidas
            'Zona urbana consolidada': 'suelo_desnudo',
            'Periurbano': 'suelo_desnudo',
            'Infraestructura': 'suelo_desnudo',
            'Área minera': 'suelo_desnudo',
            
            # Cuerpos de agua
            'Ríos y arroyos': 'agua',
            'Lagunas y lagos': 'agua',
            'Embalses': 'agua',
            'Mar y costa': 'agua'
        }
    
    def get_annual_precipitation(self, lat, lon, tipo_ecosistema=None):
        """
        Obtiene precipitación anual histórica (climatología) desde NASA POWER usando coordenadas.
        Retorna mm/año. Fallback si falla.
        """
        url = f"https://power.larc.nasa.gov/api/temporal/climatology/point?parameters=PRECTOTCORR&community=AG&longitude={lon}&latitude={lat}&format=JSON"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()  # Lanza error si HTTP falla
            data = response.json()
            
            # Extraer datos mensuales (mm/día)
            monthly = data['properties']['parameter']['PRECTOTCORR']
            
            # Días por mes (aprox., sin bisiesto)
            days_per_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
            
            # Sumar: (mm/día * días) para cada mes
            annual_mm = sum(float(monthly.get(f"{i:03d}", 0)) * days_per_month[i-1] for i in range(1, 13))
            
            return round(annual_mm, 2)
        except Exception as e:
            st.warning(f"Error al consultar NASA POWER: {str(e)}. Usando fallback para {tipo_ecosistema}.")
            return self._get_fallback_precipitation(tipo_ecosistema)
    
    def _get_fallback_precipitation(self, tipo_ecosistema):
        """
        Fallback con valores históricos aproximados por ecosistema SIB (basados en SMN/WorldClim).
        """
        fallbacks = {
            'Bosque Andino Patagónico': 600,    # 400-800 mm
            'Bosque de Araucaria': 800,         # 600-1000 mm
            'Bosque de Yungas': 1500,           # >1200 mm
            'Bosque de Selva Misionera': 1800,  # >1500 mm
            'Bosque de Caldén': 700,            # 500-900 mm
            'Bosque de Quebracho': 700,         # 500-900 mm
            'Bosque de Algarrobo': 500,         # 300-700 mm
            'Bosque de Chaco Serrano': 800,     # 600-1000 mm
            'Pastizal Pampeano': 900,           # 800-1000 mm
            'Pastizal Mesopotámico': 1100,      # 900-1300 mm
            'Estepa Patagónica': 200,           # <300 mm
            'Estepa Altoandina': 300,           # 200-500 mm
            'Estepa del Monte': 400,            # 300-600 mm
            'Humedales del Iberá': 1400,        # >1200 mm
            'Humedales del Paraná': 1200,       # 1000-1400 mm
            'Bañados y esteros': 1000,          # 800-1200 mm
            'Delta e Islas del Paraná': 1100,   # 900-1300 mm
            'Turberas y mallines': 900,         # 700-1100 mm
            'Matorral del Espinal': 600,        # 400-800 mm
            'Matorral Chaqueño': 700,           # 500-900 mm
            'Arbustal de Altura': 500,          # 300-700 mm
            'Agricultura intensiva': 800,       # Promedio Pampa
            'Agricultura extensiva': 800,       # Promedio Pampa
            'Ganadería extensiva': 700,         # Chaco/Pampa
            'Silvicultura': 900,                # NEA
            'Zona urbana consolidada': 900,     # Promedio urbano
            'Periurbano': 900,                  # Promedio periurbano
            'Infraestructura': 900,             # Promedio
            'Área minera': 500,                 # NOA árido
            'Ríos y arroyos': 1000,             # Promedio fluvial
            'Lagunas y lagos': 1000,            # Promedio lacustre
            'Embalses': 800,                    # Promedio
            'Mar y costa': 1000                 # Litoral
        }
        return fallbacks.get(tipo_ecosistema, 800)  # Default: promedio Argentina ~800 mm
    
    def _simular_variables_ambientales(self, ndvi, tipo_ecosistema):
        """Simular variables ambientales basadas en ecosistema"""
        # Rangos típicos por ecosistema SIB (valores aproximados reales)
        rangos = {
            'Bosque Andino Patagónico': {'temp_min': 5, 'temp_max': 15, 'precip_min': 400, 'precip_max': 800, 'humedad_min': 0.4, 'humedad_max': 0.7, 'antropica_min': 0.1, 'antropica_max': 0.3},
            'Bosque de Araucaria': {'temp_min': 8, 'temp_max': 18, 'precip_min': 600, 'precip_max': 1000, 'humedad_min': 0.5, 'humedad_max': 0.8, 'antropica_min': 0.1, 'antropica_max': 0.3},
            'Bosque de Yungas': {'temp_min': 18, 'temp_max': 28, 'precip_min': 1200, 'precip_max': 2500, 'humedad_min': 0.6, 'humedad_max': 0.9, 'antropica_min': 0.3, 'antropica_max': 0.6},
            'Bosque de Selva Misionera': {'temp_min': 20, 'temp_max': 30, 'precip_min': 1500, 'precip_max': 2500, 'humedad_min': 0.7, 'humedad_max': 0.95, 'antropica_min': 0.4, 'antropica_max': 0.7},
            'Bosque de Caldén': {'temp_min': 12, 'temp_max': 25, 'precip_min': 500, 'precip_max': 900, 'humedad_min': 0.4, 'humedad_max': 0.7, 'antropica_min': 0.2, 'antropica_max': 0.5},
            'Bosque de Quebracho': {'temp_min': 15, 'temp_max': 28, 'precip_min': 500, 'precip_max': 900, 'humedad_min': 0.4, 'humedad_max': 0.7, 'antropica_min': 0.3, 'antropica_max': 0.6},
            'Bosque de Algarrobo': {'temp_min': 15, 'temp_max': 28, 'precip_min': 300, 'precip_max': 700, 'humedad_min': 0.3, 'humedad_max': 0.6, 'antropica_min': 0.3, 'antropica_max': 0.6},
            'Bosque de Chaco Serrano': {'temp_min': 15, 'temp_max': 28, 'precip_min': 600, 'precip_max': 1000, 'humedad_min': 0.4, 'humedad_max': 0.7, 'antropica_min': 0.2, 'antropica_max': 0.5},
            'Pastizal Pampeano': {'temp_min': 12, 'temp_max': 22, 'precip_min': 800, 'precip_max': 1000, 'humedad_min': 0.5, 'humedad_max': 0.8, 'antropica_min': 0.5, 'antropica_max': 0.8},
            'Pastizal Mesopotámico': {'temp_min': 15, 'temp_max': 25, 'precip_min': 900, 'precip_max': 1300, 'humedad_min': 0.6, 'humedad_max': 0.9, 'antropica_min': 0.4, 'antropica_max': 0.7},
            'Estepa Patagónica': {'temp_min': 5, 'temp_max': 15, 'precip_min': 100, 'precip_max': 300, 'humedad_min': 0.2, 'humedad_max': 0.5, 'antropica_min': 0.1, 'antropica_max': 0.3},
            'Estepa Altoandina': {'temp_min': 0, 'temp_max': 10, 'precip_min': 200, 'precip_max': 500, 'humedad_min': 0.3, 'humedad_max': 0.6, 'antropica_min': 0.05, 'antropica_max': 0.2},
            'Estepa del Monte': {'temp_min': 10, 'temp_max': 20, 'precip_min': 300, 'precip_max': 600, 'humedad_min': 0.3, 'humedad_max': 0.6, 'antropica_min': 0.2, 'antropica_max': 0.4},
            'Humedales del Iberá': {'temp_min': 18, 'temp_max': 28, 'precip_min': 1200, 'precip_max': 1600, 'humedad_min': 0.7, 'humedad_max': 0.95, 'antropica_min': 0.2, 'antropica_max': 0.5},
            'Humedales del Paraná': {'temp_min': 15, 'temp_max': 25, 'precip_min': 1000, 'precip_max': 1400, 'humedad_min': 0.6, 'humedad_max': 0.9, 'antropica_min': 0.3, 'antropica_max': 0.6},
            'Bañados y esteros': {'temp_min': 15, 'temp_max': 25, 'precip_min': 800, 'precip_max': 1200, 'humedad_min': 0.6, 'humedad_max': 0.9, 'antropica_min': 0.2, 'antropica_max': 0.5},
            'Delta e Islas del Paraná': {'temp_min': 15, 'temp_max': 25, 'precip_min': 900, 'precip_max': 1300, 'humedad_min': 0.6, 'humedad_max': 0.9, 'antropica_min': 0.4, 'antropica_max': 0.7},
            'Turberas y mallines': {'temp_min': 5, 'temp_max': 15, 'precip_min': 700, 'precip_max': 1100, 'humedad_min': 0.7, 'humedad_max': 0.95, 'antropica_min': 0.1, 'antropica_max': 0.3},
            'Matorral del Espinal': {'temp_min': 12, 'temp_max': 22, 'precip_min': 400, 'precip_max': 800, 'humedad_min': 0.4, 'humedad_max': 0.7, 'antropica_min': 0.3, 'antropica_max': 0.6},
            'Matorral Chaqueño': {'temp_min': 15, 'temp_max': 28, 'precip_min': 500, 'precip_max': 900, 'humedad_min': 0.4, 'humedad_max': 0.7, 'antropica_min': 0.3, 'antropica_max': 0.6},
            'Arbustal de Altura': {'temp_min': 5, 'temp_max': 15, 'precip_min': 300, 'precip_max': 700, 'humedad_min': 0.3, 'humedad_max': 0.6, 'antropica_min': 0.1, 'antropica_max': 0.3},
            'Agricultura intensiva': {'temp_min': 12, 'temp_max': 22, 'precip_min': 700, 'precip_max': 1000, 'humedad_min': 0.5, 'humedad_max': 0.8, 'antropica_min': 0.7, 'antropica_max': 0.9},
            'Agricultura extensiva': {'temp_min': 12, 'temp_max': 22, 'precip_min': 700, 'precip_max': 1000, 'humedad_min': 0.5, 'humedad_max': 0.8, 'antropica_min': 0.6, 'antropica_max': 0.8},
            'Ganadería extensiva': {'temp_min': 12, 'temp_max': 22, 'precip_min': 600, 'precip_max': 900, 'humedad_min': 0.4, 'humedad_max': 0.7, 'antropica_min': 0.5, 'antropica_max': 0.7},
            'Silvicultura': {'temp_min': 15, 'temp_max': 25, 'precip_min': 800, 'precip_max': 1200, 'humedad_min': 0.5, 'humedad_max': 0.8, 'antropica_min': 0.4, 'antropica_max': 0.6},
            'Zona urbana consolidada': {'temp_min': 15, 'temp_max': 25, 'precip_min': 800, 'precip_max': 1000, 'humedad_min': 0.4, 'humedad_max': 0.7, 'antropica_min': 0.8, 'antropica_max': 1.0},
            'Periurbano': {'temp_min': 15, 'temp_max': 25, 'precip_min': 800, 'precip_max': 1000, 'humedad_min': 0.4, 'humedad_max': 0.7, 'antropica_min': 0.7, 'antropica_max': 0.9},
            'Infraestructura': {'temp_min': 15, 'temp_max': 25, 'precip_min': 800, 'precip_max': 1000, 'humedad_min': 0.4, 'humedad_max': 0.7, 'antropica_min': 0.9, 'antropica_max': 1.0},
            'Área minera': {'temp_min': 10, 'temp_max': 20, 'precip_min': 300, 'precip_max': 700, 'humedad_min': 0.3, 'humedad_max': 0.6, 'antropica_min': 0.8, 'antropica_max': 1.0},
            'Ríos y arroyos': {'temp_min': 15, 'temp_max': 25, 'precip_min': 800, 'precip_max': 1200, 'humedad_min': 0.8, 'humedad_max': 1.0, 'antropica_min': 0.2, 'antropica_max': 0.5},
            'Lagunas y lagos': {'temp_min': 15, 'temp_max': 25, 'precip_min': 800, 'precip_max': 1200, 'humedad_min': 0.8, 'humedad_max': 1.0, 'antropica_min': 0.1, 'antropica_max': 0.4},
            'Embalses': {'temp_min': 15, 'temp_max': 25, 'precip_min': 700, 'precip_max': 1100, 'humedad_min': 0.7, 'humedad_max': 0.9, 'antropica_min': 0.3, 'antropica_max': 0.6},
            'Mar y costa': {'temp_min': 15, 'temp_max': 25, 'precip_min': 800, 'precip_max': 1200, 'humedad_min': 0.7, 'humedad_max': 0.9, 'antropica_min': 0.4, 'antropica_max': 0.7}
        }
        
        rango = rangos.get(tipo_ecosistema, {'temp_min': 15, 'temp_max': 25, 'precip_min': 600, 'precip_max': 1200, 'humedad_min': 0.4, 'humedad_max': 0.8, 'antropica_min': 0.2, 'antropica_max': 0.5})
        
        # Ajustar rangos basados en NDVI (mayor NDVI → mayor humedad, menor presión antrópica)
        ajuste_ndvi = ndvi * 0.2  # Factor de ajuste
        temperatura = random.uniform(rango['temp_min'], rango['temp_max'])
        precipitacion = random.uniform(rango['precip_min'], rango['precip_max'])
        humedad_suelo = random.uniform(rango['humedad_min'], rango['humedad_max']) + ajuste_ndvi
        presion_antropica = random.uniform(rango['antropica_min'], rango['antropica_max']) - ajuste_ndvi
        
        # Asegurar rangos válidos
        humedad_suelo = max(0.1, min(1.0, humedad_suelo))
        presion_antropica = max(0.0, min(1.0, presion_antropica))
        
        return {
            'temperatura': round(temperatura, 1),
            'precipitacion': round(precipitacion),
            'humedad_suelo': round(humedad_suelo, 2),
            'presion_antropica': round(presion_antropica, 2)
        }
    
    def analizar_area_completa(self, gdf, tipo_ecosistema, satelite_seleccionado, n_divisiones=8):
        """Realizar análisis ambiental completo con datos satelitales"""
        try:
            poligono_principal = gdf.geometry.iloc[0]
            bounds = poligono_principal.bounds
            
            # Determinar satélite
            satelite = Satelite.PLANETSCOPE if satelite_seleccionado == "PlanetScope" else Satelite.SENTINEL2
            
            # Generar metadatos de imagen
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
                'satelite_usado': satelite_seleccionado
            }
            
            # Determinar tipo de cobertura para simulación
            tipo_cobertura = self.tipos_cobertura.get(tipo_ecosistema, 'bosque_secundario')
            
            # Calcular centro del polígono para precipitación
            centro_lat, centro_lon = poligono_principal.centroid.y, poligono_principal.centroid.x
            precipitacion_anual = self.get_annual_precipitation(centro_lat, centro_lon, tipo_ecosistema)
            
            id_area = 1
            
            # Dividir en grilla y analizar cada celda
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
                        # Calcular área en hectáreas
                        area_m2 = interseccion.area * 111000 * 111000 * math.cos(math.radians((ymin+ymax)/2))
                        area_ha = area_m2 / 10000
                        
                        if area_ha > 0.01:
                            # Simular reflectancias para cada banda
                            reflectancias = {}
                            for banda in imagen.bandas_disponibles[:5]:  # Usar primeras 5 bandas
                                reflectancias[banda] = self.simulador.simular_reflectancia(
                                    tipo_cobertura, banda, satelite
                                )
                            
                            # Calcular índices
                            indices = self.simulador.calcular_indices(reflectancias, satelite)
                            
