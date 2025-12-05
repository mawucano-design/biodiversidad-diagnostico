# ✅ ABSOLUTAMENTE PRIMERO: Importar streamlit
import streamlit as st

# ✅ LUEGO: Configurar la página
st.set_page_config(
    page_title="Sistema Integral de Análisis Ambiental",
    page_icon="🌿",
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
from streamlit_folium import st_folium, folium_static
from folium.plugins import Fullscreen, MousePosition, HeatMap, MarkerCluster, Draw
import geopandas as gpd
from shapely.geometry import Polygon, Point, shape, MultiPolygon
import pyproj
from branca.colormap import LinearColormap
import matplotlib.cm as cm

# ===============================
# 🌿 BASE DE DATOS DE ESPECIES UICN MEJORADA
# ===============================

class BaseDatosEspeciesUICN:
    """Base de datos de especies en lista roja y amarilla con sus nichos ecológicos"""
    
    def __init__(self):
        # Datos reales aproximados de especies emblemáticas de Sudamérica
        self.especies_lista_roja = {
            'Jaguar': {
                'nombre_cientifico': 'Panthera onca',
                'categoria_uicn': 'Casi Amenazada',
                'tipo': 'Mamífero',
                'nicho': {
                    'temperatura_min': 20,  # °C
                    'temperatura_max': 35,
                    'precipitacion_min': 1000,  # mm/año
                    'precipitacion_max': 3000,
                    'elevacion_min': 0,  # msnm
                    'elevacion_max': 2000,
                    'cobertura_bosque_min': 0.7,  # % de cobertura
                    'humedad_suelo_min': 0.5,
                    'vegetacion_densa': True,
                    'cuerpos_agua': True,
                    'presion_antropica_max': 0.3
                },
                'requerimientos_habitat': [
                    'Bosques tropicales húmedos',
                    'Bosques secos',
                    'Sabanas arboladas',
                    'Proximidad a fuentes de agua'
                ],
                'area_home_range': 50,  # km² por individuo
                'densidad_poblacional': 0.5,  # ind/100km²
                'prioridad_conservacion': 0.9
            },
            'Oso de Anteojos': {
                'nombre_cientifico': 'Tremarctos ornatus',
                'categoria_uicn': 'Vulnerable',
                'tipo': 'Mamífero',
                'nicho': {
                    'temperatura_min': 10,
                    'temperatura_max': 25,
                    'precipitacion_min': 800,
                    'precipitacion_max': 2500,
                    'elevacion_min': 500,
                    'elevacion_max': 3800,
                    'cobertura_bosque_min': 0.6,
                    'humedad_suelo_min': 0.6,
                    'vegetacion_densa': True,
                    'cuerpos_agua': True,
                    'presion_antropica_max': 0.4
                },
                'requerimientos_habitat': [
                    'Bosques montanos',
                    'Páramos',
                    'Bosques nublados',
                    'Áreas remotas'
                ],
                'area_home_range': 30,
                'densidad_poblacional': 1.0,
                'prioridad_conservacion': 0.85
            },
            'Guacamayo Rojo': {
                'nombre_cientifico': 'Ara macao',
                'categoria_uicn': 'En Peligro',
                'tipo': 'Ave',
                'nicho': {
                    'temperatura_min': 22,
                    'temperatura_max': 32,
                    'precipitacion_min': 1500,
                    'precipitacion_max': 3500,
                    'elevacion_min': 0,
                    'elevacion_max': 800,
                    'cobertura_bosque_min': 0.8,
                    'humedad_suelo_min': 0.7,
                    'vegetacion_densa': True,
                    'arboles_altos': True,
                    'presion_antropica_max': 0.2
                },
                'requerimientos_habitat': [
                    'Bosques tropicales maduros',
                    'Árboles emergentes para anidación',
                    'Palmeras para alimentación',
                    'Claros naturales'
                ],
                'area_home_range': 15,
                'densidad_poblacional': 2.0,
                'prioridad_conservacion': 0.95
            },
            'Tapir Amazónico': {
                'nombre_cientifico': 'Tapirus terrestris',
                'categoria_uicn': 'Vulnerable',
                'tipo': 'Mamífero',
                'nicho': {
                    'temperatura_min': 22,
                    'temperatura_max': 30,
                    'precipitacion_min': 1800,
                    'precipitacion_max': 4000,
                    'elevacion_min': 0,
                    'elevacion_max': 1500,
                    'cobertura_bosque_min': 0.7,
                    'humedad_suelo_min': 0.8,
                    'vegetacion_densa': True,
                    'cuerpos_agua': True,
                    'presion_antropica_max': 0.3
                },
                'requerimientos_habitat': [
                    'Bosques húmedos tropicales',
                    'Bosques de galería',
                    'Pantanos y humedales',
                    'Áreas con suelo blando'
                ],
                'area_home_range': 5,
                'densidad_poblacional': 3.0,
                'prioridad_conservacion': 0.8
            },
            'Caimán Negro': {
                'nombre_cientifico': 'Melanosuchus niger',
                'categoria_uicn': 'En Peligro',
                'tipo': 'Reptil',
                'nicho': {
                    'temperatura_min': 25,
                    'temperatura_max': 35,
                    'precipitacion_min': 2000,
                    'precipitacion_max': 4500,
                    'elevacion_min': 0,
                    'elevacion_max': 300,
                    'cobertura_bosque_min': 0.5,
                    'humedad_suelo_min': 0.9,
                    'cuerpos_agua': True,
                    'vegetacion_riparia': True,
                    'presion_antropica_max': 0.2
                },
                'requerimientos_habitat': [
                    'Ríos y lagos grandes',
                    'Bosques inundables',
                    'Madera muerta en agua',
                    'Playas arenosas para anidar'
                ],
                'area_home_range': 10,
                'densidad_poblacional': 0.8,
                'prioridad_conservacion': 0.9
            }
        }
        
        self.especies_lista_amarilla = {
            'Mono Araña': {
                'nombre_cientifico': 'Ateles geoffroyi',
                'categoria_uicn': 'Preocupación Menor',
                'tipo': 'Mamífero',
                'nicho': {
                    'temperatura_min': 20,
                    'temperatura_max': 30,
                    'precipitacion_min': 1200,
                    'precipitacion_max': 3000,
                    'elevacion_min': 0,
                    'elevacion_max': 1800,
                    'cobertura_bosque_min': 0.6,
                    'humedad_suelo_min': 0.6,
                    'vegetacion_densa': True,
                    'arboles_altos': True,
                    'presion_antropica_max': 0.5
                },
                'requerimientos_habitat': [
                    'Bosques tropicales',
                    'Estratos altos del bosque',
                    'Árboles frutales',
                    'Corredores arbóreos'
                ],
                'area_home_range': 3,
                'densidad_poblacional': 5.0,
                'prioridad_conservacion': 0.6
            },
            'Tucán Pico Iris': {
                'nombre_cientifico': 'Ramphastos sulfuratus',
                'categoria_uicn': 'Casi Amenazada',
                'tipo': 'Ave',
                'nicho': {
                    'temperatura_min': 18,
                    'temperatura_max': 28,
                    'precipitacion_min': 1000,
                    'precipitacion_max': 2800,
                    'elevacion_min': 0,
                    'elevacion_max': 1500,
                    'cobertura_bosque_min': 0.5,
                    'humedad_suelo_min': 0.5,
                    'vegetacion_densa': False,
                    'arboles_huecos': True,
                    'presion_antropica_max': 0.6
                },
                'requerimientos_habitat': [
                    'Bosques húmedos',
                    'Bosques secundarios',
                    'Árboles con frutos',
                    'Claros boscosos'
                ],
                'area_home_range': 2,
                'densidad_poblacional': 8.0,
                'prioridad_conservacion': 0.5
            },
            'Pecarí de Labios Blancos': {
                'nombre_cientifico': 'Tayassu pecari',
                'categoria_uicn': 'Vulnerable',
                'tipo': 'Mamífero',
                'nicho': {
                    'temperatura_min': 20,
                    'temperatura_max': 32,
                    'precipitacion_min': 1000,
                    'precipitacion_max': 3500,
                    'elevacion_min': 0,
                    'elevacion_max': 2000,
                    'cobertura_bosque_min': 0.4,
                    'humedad_suelo_min': 0.5,
                    'vegetacion_densa': False,
                    'cuerpos_agua': True,
                    'presion_antropica_max': 0.4
                },
                'requerimientos_habitat': [
                    'Bosques húmedos',
                    'Sabanas arboladas',
                    'Áreas abiertas dentro del bosque',
                    'Caminos naturales'
                ],
                'area_home_range': 20,
                'densidad_poblacional': 4.0,
                'prioridad_conservacion': 0.7
            },
            'Iguana Verde': {
                'nombre_cientifico': 'Iguana iguana',
                'categoria_uicn': 'Preocupación Menor',
                'tipo': 'Reptil',
                'nicho': {
                    'temperatura_min': 24,
                    'temperatura_max': 38,
                    'precipitacion_min': 800,
                    'precipitacion_max': 2500,
                    'elevacion_min': 0,
                    'elevacion_max': 1000,
                    'cobertura_bosque_min': 0.3,
                    'humedad_suelo_min': 0.4,
                    'vegetacion_densa': False,
                    'arboles_soleados': True,
                    'presion_antropica_max': 0.7
                },
                'requerimientos_habitat': [
                    'Bosques ribereños',
                    'Árboles aislados',
                    'Zonas de sol y sombra',
                    'Troncos sobre el agua'
                ],
                'area_home_range': 0.5,
                'densidad_poblacional': 15.0,
                'prioridad_conservacion': 0.4
            },
            'Venado Cola Blanca': {
                'nombre_cientifico': 'Odocoileus virginianus',
                'categoria_uicn': 'Preocupación Menor',
                'tipo': 'Mamífero',
                'nicho': {
                    'temperatura_min': 10,
                    'temperatura_max': 30,
                    'precipitacion_min': 500,
                    'precipitacion_max': 2000,
                    'elevacion_min': 0,
                    'elevacion_max': 3000,
                    'cobertura_bosque_min': 0.2,
                    'humedad_suelo_min': 0.3,
                    'vegetacion_densa': False,
                    'matorrales': True,
                    'presion_antropica_max': 0.6
                },
                'requerimientos_habitat': [
                    'Bosques abiertos',
                    'Matorrales',
                    'Límites bosque-pastizal',
                    'Áreas con agua disponible'
                ],
                'area_home_range': 2,
                'densidad_poblacional': 10.0,
                'prioridad_conservacion': 0.3
            }
        }
    
    def obtener_todas_especies(self):
        """Retorna todas las especies combinadas"""
        return {**self.especies_lista_roja, **self.especies_lista_amarilla}
    
    def calcular_idoneidad_habitat(self, caracteristicas_area, especie_nombre):
        """Calcula la idoneidad del hábitat para una especie específica"""
        especies = self.obtener_todas_especies()
        if especie_nombre not in especies:
            return 0
        
        especie = especies[especie_nombre]
        nicho = especie['nicho']
        
        factores = []
        
        # 1. Temperatura
        if 'temperatura_promedio' in caracteristicas_area:
            temp = caracteristicas_area['temperatura_promedio']
            if nicho['temperatura_min'] <= temp <= nicho['temperatura_max']:
                factores.append(1.0)
            else:
                distancia = min(abs(temp - nicho['temperatura_min']), 
                              abs(temp - nicho['temperatura_max']))
                penalizacion = max(0, 1 - distancia / 10)
                factores.append(penalizacion)
        
        # 2. Precipitación
        if 'precipitacion_anual' in caracteristicas_area:
            precip = caracteristicas_area['precipitacion_anual']
            if nicho['precipitacion_min'] <= precip <= nicho['precipitacion_max']:
                factores.append(1.0)
            else:
                distancia = min(abs(precip - nicho['precipitacion_min']),
                              abs(precip - nicho['precipitacion_max']))
                penalizacion = max(0, 1 - distancia / 1000)
                factores.append(penalizacion)
        
        # 3. NDVI como proxy de cobertura bosque
        if 'ndvi' in caracteristicas_area:
            ndvi = caracteristicas_area['ndvi']
            cobertura_min = nicho.get('cobertura_bosque_min', 0)
            if ndvi >= cobertura_min:
                factores.append(1.0)
            else:
                factores.append(ndvi / cobertura_min if cobertura_min > 0 else 0)
        
        # 4. Presión antrópica
        if 'presion_antropica' in caracteristicas_area:
            presion = caracteristicas_area['presion_antropica']
            presion_max = nicho.get('presion_antropica_max', 1.0)
            if presion <= presion_max:
                factores.append(1.0)
            else:
                factores.append(max(0, 1 - (presion - presion_max) / (1 - presion_max)))
        
        # 5. Humedad del suelo
        if 'humedad_suelo' in caracteristicas_area:
            humedad = caracteristicas_area['humedad_suelo']
            humedad_min = nicho.get('humedad_suelo_min', 0)
            if humedad >= humedad_min:
                factores.append(1.0)
            else:
                factores.append(humedad / humedad_min if humedad_min > 0 else 0)
        
        if factores:
            idoneidad = np.mean(factores)
            idoneidad *= especie['prioridad_conservacion']
            return round(idoneidad, 3)
        
        return 0

# ===============================
# 🗺️ SISTEMA DE MAPAS MEJORADO CON ZOOM AUTOMÁTICO
# ===============================

class SistemaMapas:
    """Sistema avanzado de mapas con zoom automático y múltiples capas"""
    
    def __init__(self):
        self.capas_base = {
            'Satélite': {
                'tiles': 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                'attr': 'Esri World Imagery',
                'nombre': '🌍 Satélite ESRI'
            },
            'Topográfico': {
                'tiles': 'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
                'attr': 'OpenTopoMap',
                'nombre': '⛰️ Topográfico'
            },
            'OSM': {
                'tiles': 'OpenStreetMap',
                'attr': 'OpenStreetMap',
                'nombre': '🗺️ OpenStreetMap'
            }
        }
    
    def calcular_centro_y_zoom(self, gdf):
        """Calcular centro y zoom automático basado en el polígono"""
        if gdf is None or gdf.empty:
            return [-14.0, -60.0], 4
        
        try:
            bounds = gdf.total_bounds
            centro = [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2]
            
            # Calcular área aproximada para determinar zoom
            poligono = gdf.geometry.iloc[0]
            if hasattr(poligono, 'area'):
                area_grados = poligono.area
                lat_centro = centro[0]
                cos_lat = math.cos(math.radians(lat_centro))
                area_km2 = area_grados * 111 * 111 * cos_lat
                
                # Determinar zoom basado en área
                if area_km2 < 1:
                    zoom = 16
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
                elif area_km2 < 10000:
                    zoom = 8
                else:
                    zoom = 7
            else:
                zoom = 10
            
            return centro, zoom
        
        except Exception as e:
            return [-14.0, -60.0], 4
    
    def crear_mapa_base(self, gdf, titulo="Área de Estudio", capa_seleccionada='Satélite'):
        """Crear mapa base con zoom automático y múltiples capas"""
        centro, zoom = self.calcular_centro_y_zoom(gdf)
        
        m = folium.Map(
            location=centro,
            zoom_start=zoom,
            tiles=None,
            control_scale=True,
            zoom_control=True
        )
        
        # Agregar todas las capas base
        for nombre, config in self.capas_base.items():
            if nombre == 'OSM':
                folium.TileLayer(
                    config['tiles'],
                    attr=config['attr'],
                    name=config['nombre'],
                    overlay=False,
                    control=True
                ).add_to(m)
            else:
                folium.TileLayer(
                    tiles=config['tiles'],
                    attr=config['attr'],
                    name=config['nombre'],
                    overlay=False,
                    control=True
                ).add_to(m)
        
        # Agregar polígono si existe
        if gdf is not None and not gdf.empty:
            try:
                poligono = gdf.geometry.iloc[0]
                
                # Calcular área para tooltip
                bounds = gdf.total_bounds
                area_km2 = gdf.geometry.area.iloc[0] * 111 * 111 * math.cos(math.radians(centro[0]))
                
                tooltip_text = f"""
                <div style='font-family: Arial; font-size: 12px;'>
                <b>{titulo}</b><br>
                Área: {area_km2:.2f} km²<br>
                Centro: {centro[0]:.4f}°, {centro[1]:.4f}°
                </div>
                """
                
                folium.GeoJson(
                    poligono,
                    style_function=lambda x: {
                        'fillColor': '#3b82f6',
                        'color': '#1d4ed8',
                        'weight': 3,
                        'fillOpacity': 0.2,
                        'dashArray': '5, 5'
                    },
                    name='Área de Estudio',
                    tooltip=folium.Tooltip(tooltip_text, sticky=True)
                ).add_to(m)
                
                # Ajustar vista al polígono
                m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])
                
            except Exception as e:
                pass
        
        # Agregar controles
        Fullscreen().add_to(m)
        MousePosition().add_to(m)
        folium.LayerControl().add_to(m)
        
        return m
    
    def crear_mapa_indicador(self, gdf, datos_indicador, config_indicador):
        """Crear mapa para un indicador específico"""
        centro, zoom = self.calcular_centro_y_zoom(gdf)
        
        m = folium.Map(
            location=centro,
            zoom_start=zoom,
            tiles=self.capas_base['Satélite']['tiles'],
            attr=self.capas_base['Satélite']['attr'],
            control_scale=True
        )
        
        # Agregar polígono base
        if gdf is not None and not gdf.empty:
            poligono = gdf.geometry.iloc[0]
            folium.GeoJson(
                poligono,
                style_function=lambda x: {
                    'fillColor': '#ffffff',
                    'color': '#0066cc',
                    'weight': 1,
                    'fillOpacity': 0.05
                }
            ).add_to(m)
        
        # Agregar datos del indicador
        if datos_indicador and len(datos_indicador) > 0:
            for area_data in datos_indicador:
                try:
                    valor = area_data.get(config_indicador['columna'], 0)
                    geometry = area_data.get('geometry')
                    area_id = area_data.get('area', 'Desconocida')
                    
                    if geometry and hasattr(geometry, 'centroid'):
                        centroid = geometry.centroid
                        lat, lon = centroid.y, centroid.x
                        
                        # Determinar color basado en valor
                        color = '#808080'
                        for rango, color_rango in config_indicador['colores'].items():
                            if rango[0] <= valor <= rango[1]:
                                color = color_rango
                                break
                        
                        # Crear marcador
                        folium.CircleMarker(
                            location=[lat, lon],
                            radius=8,
                            popup=f"<b>{area_id}</b><br>{config_indicador['titulo']}: {valor:.3f}",
                            color=color,
                            fill=True,
                            fillColor=color,
                            fillOpacity=0.7,
                            tooltip=f"{area_id}: {valor:.3f}"
                        ).add_to(m)
                        
                except Exception as e:
                    continue
        
        return m

# ===============================
# 📊 SISTEMA DE ANÁLISIS AMBIENTAL COMPLETO
# ===============================

class AnalizadorAmbientalCompleto:
    """Analizador ambiental completo con todos los indicadores"""
    
    def __init__(self):
        self.base_especies = BaseDatosEspeciesUICN()
        self.sistema_mapas = SistemaMapas()
        
        # Parámetros base por tipo de ecosistema
        self.parametros_ecosistemas = {
            'Bosque Tropical Húmedo': {
                'ndvi_base': 0.85,
                'savi_base': 0.70,
                'mndvi_base': 0.80,
                'evi_base': 0.65,
                'ndwi_base': 0.45,
                'carbono_ton_ha': 250,
                'shannon_base': 2.8,
                'temperatura': 26,
                'precipitacion': 2500,
                'humedad_suelo': 0.8
            },
            'Bosque Seco Tropical': {
                'ndvi_base': 0.65,
                'savi_base': 0.50,
                'mndvi_base': 0.60,
                'evi_base': 0.45,
                'ndwi_base': 0.25,
                'carbono_ton_ha': 120,
                'shannon_base': 2.0,
                'temperatura': 28,
                'precipitacion': 800,
                'humedad_suelo': 0.4
            },
            'Bosque Montano': {
                'ndvi_base': 0.75,
                'savi_base': 0.60,
                'mndvi_base': 0.70,
                'evi_base': 0.55,
                'ndwi_base': 0.35,
                'carbono_ton_ha': 180,
                'shannon_base': 2.5,
                'temperatura': 18,
                'precipitacion': 1500,
                'humedad_suelo': 0.7
            },
            'Sabana Arborizada': {
                'ndvi_base': 0.55,
                'savi_base': 0.40,
                'mndvi_base': 0.50,
                'evi_base': 0.35,
                'ndwi_base': 0.20,
                'carbono_ton_ha': 80,
                'shannon_base': 1.8,
                'temperatura': 25,
                'precipitacion': 1200,
                'humedad_suelo': 0.5
            },
            'Humeral': {
                'ndvi_base': 0.70,
                'savi_base': 0.55,
                'mndvi_base': 0.65,
                'evi_base': 0.50,
                'ndwi_base': 0.60,
                'carbono_ton_ha': 150,
                'shannon_base': 2.2,
                'temperatura': 22,
                'precipitacion': 3000,
                'humedad_suelo': 0.9
            }
        }
    
    def calcular_indices_vegetacion(self, params_base, area_ha):
        """Calcular todos los índices de vegetación"""
        # Simular variación basada en área y parámetros aleatorios
        variacion = np.random.uniform(-0.15, 0.15)
        
        resultados = {
            'ndvi': max(0.1, min(1.0, params_base['ndvi_base'] + variacion)),
            'savi': max(0.1, min(1.0, params_base['savi_base'] + np.random.uniform(-0.1, 0.1))),
            'mndvi': max(0.1, min(1.0, params_base['mndvi_base'] + np.random.uniform(-0.1, 0.1))),
            'evi': max(0.1, min(1.0, params_base['evi_base'] + np.random.uniform(-0.1, 0.1))),
            'ndwi': max(0.1, min(1.0, params_base['ndwi_base'] + np.random.uniform(-0.1, 0.1))),
        }
        
        # Ajustar por área (áreas más grandes tienden a tener mejor vegetación)
        factor_area = min(1.5, 1 + (area_ha / 1000))
        for key in resultados:
            resultados[key] = min(1.0, resultados[key] * factor_area)
        
        return resultados
    
    def calcular_indice_shannon(self, params_base, indices_vegetacion, area_ha):
        """Calcular índice de Shannon de biodiversidad"""
        # Base del índice
        shannon = params_base['shannon_base']
        
        # Ajustar por NDVI (mejor vegetación = más biodiversidad)
        shannon *= (0.5 + 0.5 * indices_vegetacion['ndvi'])
        
        # Ajustar por área (efecto de área-especie)
        factor_area = min(2.0, 1 + math.log10(area_ha + 1) / 2)
        shannon *= factor_area
        
        # Añadir variación aleatoria
        shannon += np.random.uniform(-0.3, 0.3)
        
        return max(0.1, min(4.0, shannon))
    
    def calcular_carbono(self, params_base, area_ha, indices_vegetacion):
        """Calcular captura de carbono"""
        # Carbono base por hectárea
        carbono_ton_ha = params_base['carbono_ton_ha']
        
        # Ajustar por NDVI (mejor vegetación = más carbono)
        carbono_ton_ha *= (0.7 + 0.3 * indices_vegetacion['ndvi'])
        
        # Añadir variación
        carbono_ton_ha += np.random.uniform(-20, 20)
        
        # Calcular totales
        carbono_total = carbono_ton_ha * area_ha
        co2_total = carbono_total * 3.67  # Conversión a CO2
        
        return {
            'carbono_ton_ha': max(0, round(carbono_ton_ha, 2)),
            'carbono_total': max(0, round(carbono_total, 2)),
            'co2_total': max(0, round(co2_total, 2))
        }
    
    def analizar_area(self, gdf, tipo_ecosistema, n_divisiones=6):
        """Analizar toda el área dividida en celdas"""
        try:
            poligono_principal = gdf.geometry.iloc[0]
            bounds = poligono_principal.bounds
            
            params_base = self.parametros_ecosistemas.get(
                tipo_ecosistema, 
                self.parametros_ecosistemas['Bosque Tropical Húmedo']
            )
            
            resultados = {
                'areas': [],
                'resumen': {},
                'tipo_ecosistema': tipo_ecosistema
            }
            
            id_area = 1
            
            # Dividir en grilla
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
                        
                        if area_ha > 0.01:  # Ignorar áreas muy pequeñas
                            # Calcular todos los indicadores
                            indices_vegetacion = self.calcular_indices_vegetacion(params_base, area_ha)
                            indice_shannon = self.calcular_indice_shannon(params_base, indices_vegetacion, area_ha)
                            carbono = self.calcular_carbono(params_base, area_ha, indices_vegetacion)
                            
                            area_data = {
                                'id': id_area,
                                'area': f"Celda-{id_area:03d}",
                                'geometry': interseccion,
                                'area_ha': round(area_ha, 2),
                                'indices_vegetacion': indices_vegetacion,
                                'indice_shannon': round(indice_shannon, 3),
                                'carbono': carbono,
                                'temperatura': params_base['temperatura'] + np.random.uniform(-2, 2),
                                'precipitacion': params_base['precipitacion'] + np.random.uniform(-100, 100),
                                'humedad_suelo': params_base['humedad_suelo'] + np.random.uniform(-0.1, 0.1),
                                'presion_antropica': np.random.uniform(0.1, 0.6),
                                'conectividad': np.random.uniform(0.4, 0.9)
                            }
                            
                            resultados['areas'].append(area_data)
                            id_area += 1
            
            # Calcular resumen general
            if resultados['areas']:
                self._calcular_resumen(resultados)
            
            return resultados
            
        except Exception as e:
            st.error(f"Error en análisis ambiental: {str(e)}")
            return None
    
    def _calcular_resumen(self, resultados):
        """Calcular estadísticas resumen"""
        areas = resultados['areas']
        
        resumen = {
            'total_areas': len(areas),
            'area_total_ha': sum(a['area_ha'] for a in areas),
            'ndvi_promedio': np.mean([a['indices_vegetacion']['ndvi'] for a in areas]),
            'savi_promedio': np.mean([a['indices_vegetacion']['savi'] for a in areas]),
            'evi_promedio': np.mean([a['indices_vegetacion']['evi'] for a in areas]),
            'shannon_promedio': np.mean([a['indice_shannon'] for a in areas]),
            'carbono_total_co2': sum(a['carbono']['co2_total'] for a in areas),
            'carbono_promedio_ha': np.mean([a['carbono']['carbono_ton_ha'] for a in areas]),
            'temperatura_promedio': np.mean([a['temperatura'] for a in areas]),
            'precipitacion_promedio': np.mean([a['precipitacion'] for a in areas])
        }
        
        # Clasificar estado general
        ndvi_avg = resumen['ndvi_promedio']
        shannon_avg = resumen['shannon_promedio']
        
        if ndvi_avg > 0.7 and shannon_avg > 2.5:
            resumen['estado_general'] = 'Excelente'
            resumen['color_estado'] = '#10b981'
        elif ndvi_avg > 0.5 and shannon_avg > 1.8:
            resumen['estado_general'] = 'Bueno'
            resumen['color_estado'] = '#3b82f6'
        elif ndvi_avg > 0.3:
            resumen['estado_general'] = 'Moderado'
            resumen['color_estado'] = '#f59e0b'
        else:
            resumen['estado_general'] = 'Degradado'
            resumen['color_estado'] = '#ef4444'
        
        resultados['resumen'] = resumen

# ===============================
# 🎨 INTERFAZ DE USUARIO COMPLETA
# ===============================

def main():
    st.title("🌿 Sistema Integral de Análisis Ambiental")
    st.markdown("### Análisis de Biodiversidad, Vegetación, Carbono y Conservación de Especies")
    
    # Inicializar sistemas
    if 'analizador' not in st.session_state:
        st.session_state.analizador = AnalizadorAmbientalCompleto()
    if 'resultados_ambientales' not in st.session_state:
        st.session_state.resultados_ambientales = None
    if 'poligono_data' not in st.session_state:
        st.session_state.poligono_data = None
    
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
            try:
                if uploaded_file.name.endswith('.kml'):
                    gdf = gpd.read_file(uploaded_file, driver='KML')
                elif uploaded_file.name.endswith('.geojson'):
                    gdf = gpd.read_file(uploaded_file)
                elif uploaded_file.name.endswith('.zip'):
                    with tempfile.TemporaryDirectory() as tmpdir:
                        with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
                            zip_ref.extractall(tmpdir)
                        for file in os.listdir(tmpdir):
                            if file.endswith('.shp'):
                                gdf = gpd.read_file(os.path.join(tmpdir, file))
                                break
                
                if gdf is not None and not gdf.empty:
                    st.session_state.poligono_data = gdf
                    st.success("✅ Polígono cargado exitosamente")
            except Exception as e:
                st.error(f"Error cargando archivo: {str(e)}")
        
        # Parámetros de análisis
        if st.session_state.poligono_data is not None:
            st.markdown("---")
            st.subheader("📊 Parámetros del Análisis")
            
            tipo_ecosistema = st.selectbox(
                "Tipo de ecosistema predominante",
                ['Bosque Tropical Húmedo', 'Bosque Seco Tropical', 'Bosque Montano', 
                 'Sabana Arborizada', 'Humeral']
            )
            
            nivel_detalle = st.slider("Nivel de detalle (divisiones)", 3, 10, 6)
            
            if st.button("🚀 Ejecutar Análisis Ambiental Completo", type="primary"):
                with st.spinner("Realizando análisis integral..."):
                    resultados = st.session_state.analizador.analizar_area(
                        st.session_state.poligono_data,
                        tipo_ecosistema,
                        nivel_detalle
                    )
                    
                    if resultados:
                        st.session_state.resultados_ambientales = resultados
                        st.success("✅ Análisis completado exitosamente!")
    
    # Pestañas principales
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🗺️ Mapa del Área", 
        "📊 Indicadores Ambientales",
        "🌿 Análisis de Vegetación",
        "🦋 Biodiversidad y Carbono",
        "🎯 Conservación de Especies"
    ])
    
    with tab1:
        mostrar_mapa_area()
    
    with tab2:
        mostrar_indicadores_ambientales()
    
    with tab3:
        mostrar_analisis_vegetacion()
    
    with tab4:
        mostrar_biodiversidad_carbono()
    
    with tab5:
        mostrar_conservacion_especies()

def mostrar_mapa_area():
    """Mostrar mapa del área con zoom automático"""
    st.markdown("## 🗺️ Visualización del Área de Estudio")
    
    if st.session_state.poligono_data is not None:
        # Selector de capa base
        col1, col2 = st.columns([3, 1])
        
        with col2:
            capa_base = st.selectbox(
                "Capa base del mapa",
                ["Satélite", "Topográfico", "OSM"],
                index=0
            )
        
        with col1:
            # Crear y mostrar mapa
            mapa = st.session_state.analizador.sistema_mapas.crear_mapa_base(
                st.session_state.poligono_data,
                "Área de Análisis Ambiental",
                capa_base
            )
            folium_static(mapa, width=800, height=600)
        
        # Información del área
        if st.session_state.resultados_ambientales:
            resumen = st.session_state.resultados_ambientales['resumen']
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Área total", f"{resumen['area_total_ha']:,.1f} ha")
            with col2:
                st.metric("Celdas analizadas", resumen['total_areas'])
            with col3:
                st.metric("Estado general", resumen['estado_general'])
            with col4:
                st.metric("Tipo de ecosistema", 
                         st.session_state.resultados_ambientales['tipo_ecosistema'])
    else:
        st.info("👈 Carga un polígono en el panel lateral para comenzar")

def mostrar_indicadores_ambientales():
    """Mostrar todos los indicadores ambientales"""
    st.markdown("## 📊 Indicadores Ambientales por Celda")
    
    if st.session_state.resultados_ambientales is None:
        st.warning("Ejecuta el análisis ambiental primero")
        return
    
    resultados = st.session_state.resultados_ambientales
    
    # KPIs principales
    resumen = resultados['resumen']
    
    st.markdown("### 📈 Resumen General")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("NDVI Promedio", f"{resumen['ndvi_promedio']:.3f}")
    with col2:
        st.metric("Índice Shannon", f"{resumen['shannon_promedio']:.3f}")
    with col3:
        st.metric("Carbono Total CO₂", f"{resumen['carbono_total_co2']:,.0f} ton")
    with col4:
        st.metric("Estado General", resumen['estado_general'])
    
    # Tabla de datos
    st.markdown("### 📋 Datos por Celda")
    
    # Preparar datos para tabla
    datos_tabla = []
    for area in resultados['areas']:
        datos_tabla.append({
            'Celda': area['area'],
            'Área (ha)': area['area_ha'],
            'NDVI': area['indices_vegetacion']['ndvi'],
            'SAVI': area['indices_vegetacion']['savi'],
            'EVI': area['indices_vegetacion']['evi'],
            'Shannon': area['indice_shannon'],
            'Carbono (ton/ha)': area['carbono']['carbono_ton_ha'],
            'CO₂ Total': area['carbono']['co2_total'],
            'Temp. (°C)': area['temperatura'],
            'Precip. (mm)': area['precipitacion']
        })
    
    df = pd.DataFrame(datos_tabla)
    st.dataframe(df, use_container_width=True)
    
    # Descarga de datos
    st.markdown("### 📥 Exportar Datos")
    
    if st.button("⬇️ Descargar Datos Completos como CSV"):
        csv = df.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="datos_ambientales.csv">Descargar CSV</a>'
        st.markdown(href, unsafe_allow_html=True)

def mostrar_analisis_vegetacion():
    """Mostrar análisis detallado de vegetación"""
    st.markdown("## 🌿 Análisis Detallado de Vegetación")
    
    if st.session_state.resultados_ambientales is None:
        st.warning("Ejecuta el análisis ambiental primero")
        return
    
    resultados = st.session_state.resultados_ambientales
    
    # Selector de índice de vegetación
    indices_opciones = {
        'NDVI': 'ndvi',
        'SAVI': 'savi', 
        'MNDVI': 'mndvi',
        'EVI': 'evi',
        'NDWI': 'ndwi'
    }
    
    col1, col2 = st.columns([2, 1])
    
    with col2:
        indice_seleccionado = st.selectbox(
            "Seleccionar índice para visualizar",
            list(indices_opciones.keys())
        )
        
        # Configuración para el mapa
        config_mapa = {
            'titulo': f'Índice {indice_seleccionado}',
            'columna': indices_opciones[indice_seleccionado],
            'colores': {
                (0, 0.2): '#8B0000',
                (0.2, 0.4): '#FF4500',
                (0.4, 0.6): '#FFD700',
                (0.6, 0.8): '#32CD32',
                (0.8, 1.0): '#006400'
            }
        }
    
    with col1:
        # Preparar datos para el mapa
        datos_mapa = []
        for area in resultados['areas']:
            datos_mapa.append({
                'area': area['area'],
                'geometry': area['geometry'],
                indices_opciones[indice_seleccionado]: area['indices_vegetacion'][indices_opciones[indice_seleccionado]]
            })
        
        # Crear y mostrar mapa
        mapa = st.session_state.analizador.sistema_mapas.crear_mapa_indicador(
            st.session_state.poligono_data,
            datos_mapa,
            config_mapa
        )
        folium_static(mapa, width=800, height=500)
    
    # Gráficos de distribución
    st.markdown("### 📈 Distribución de Índices de Vegetación")
    
    # Preparar datos para gráficos
    indices_data = []
    for area in resultados['areas']:
        for idx_nombre, idx_valor in area['indices_vegetacion'].items():
            indices_data.append({
                'Índice': idx_nombre.upper(),
                'Valor': idx_valor,
                'Celda': area['area']
            })
    
    df_indices = pd.DataFrame(indices_data)
    
    # Box plot
    fig = px.box(
        df_indices, 
        x='Índice', 
        y='Valor',
        title='Distribución de Índices de Vegetación',
        color='Índice',
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)
    
    # Correlación entre índices
    st.markdown("### 🔗 Correlación entre Índices")
    
    # Crear matriz de correlación
    correlacion_data = []
    for area in resultados['areas']:
        correlacion_data.append(area['indices_vegetacion'])
    
    df_corr = pd.DataFrame(correlacion_data)
    corr_matrix = df_corr.corr()
    
    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix.values,
        x=corr_matrix.columns,
        y=corr_matrix.columns,
        colorscale='RdBu',
        zmin=-1, zmax=1,
        text=np.round(corr_matrix.values, 2),
        texttemplate='%{text}',
        textfont={"size": 10}
    ))
    
    fig.update_layout(
        title='Matriz de Correlación entre Índices',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

def mostrar_biodiversidad_carbono():
    """Mostrar análisis de biodiversidad y carbono"""
    st.markdown("## 🦋 Análisis de Biodiversidad y Captura de Carbono")
    
    if st.session_state.resultados_ambientales is None:
        st.warning("Ejecuta el análisis ambiental primero")
        return
    
    resultados = st.session_state.resultados_ambientales
    
    # Dos columnas para métricas
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🌿 Índice de Shannon (Biodiversidad)")
        
        # Preparar datos para mapa de biodiversidad
        datos_shannon = []
        for area in resultados['areas']:
            datos_shannon.append({
                'area': area['area'],
                'geometry': area['geometry'],
                'shannon': area['indice_shannon']
            })
        
        # Configuración del mapa
        config_shannon = {
            'titulo': 'Índice de Shannon (Biodiversidad)',
            'columna': 'shannon',
            'colores': {
                (0, 1.0): '#8B0000',
                (1.0, 2.0): '#FF4500',
                (2.0, 2.5): '#FFD700',
                (2.5, 3.0): '#32CD32',
                (3.0, 4.0): '#006400'
            }
        }
        
        # Crear y mostrar mapa
        mapa_shannon = st.session_state.analizador.sistema_mapas.crear_mapa_indicador(
            st.session_state.poligono_data,
            datos_shannon,
            config_shannon
        )
        folium_static(mapa_shannon, width=400, height=400)
        
        # Estadísticas de biodiversidad
        shannon_values = [area['indice_shannon'] for area in resultados['areas']]
        
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("Promedio", f"{np.mean(shannon_values):.2f}")
        with col_b:
            st.metric("Máximo", f"{np.max(shannon_values):.2f}")
        with col_c:
            st.metric("Mínimo", f"{np.min(shannon_values):.2f}")
    
    with col2:
        st.markdown("### 🌳 Captura de Carbono")
        
        # Preparar datos para mapa de carbono
        datos_carbono = []
        for area in resultados['areas']:
            datos_carbono.append({
                'area': area['area'],
                'geometry': area['geometry'],
                'carbono_ha': area['carbono']['carbono_ton_ha']
            })
        
        # Configuración del mapa
        config_carbono = {
            'titulo': 'Carbono Almacenado (ton/ha)',
            'columna': 'carbono_ha',
            'colores': {
                (0, 50): '#FFFACD',
                (50, 100): '#C2E699',
                (100, 150): '#78C679',
                (150, 200): '#238443',
                (200, 300): '#00441B'
            }
        }
        
        # Crear y mostrar mapa
        mapa_carbono = st.session_state.analizador.sistema_mapas.crear_mapa_indicador(
            st.session_state.poligono_data,
            datos_carbono,
            config_carbono
        )
        folium_static(mapa_carbono, width=400, height=400)
        
        # Estadísticas de carbono
        carbono_total = sum(area['carbono']['co2_total'] for area in resultados['areas'])
        carbono_promedio = np.mean([area['carbono']['carbono_ton_ha'] for area in resultados['areas']])
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("CO₂ Total", f"{carbono_total:,.0f} ton")
        with col_b:
            st.metric("Promedio/ha", f"{carbono_promedio:.1f} ton")
    
    # Relación entre biodiversidad y carbono
    st.markdown("### 🔄 Relación Biodiversidad-Carbono")
    
    # Preparar datos para gráfico de dispersión
    dispersion_data = []
    for area in resultados['areas']:
        dispersion_data.append({
            'Carbono (ton/ha)': area['carbono']['carbono_ton_ha'],
            'Biodiversidad (Shannon)': area['indice_shannon'],
            'NDVI': area['indices_vegetacion']['ndvi'],
            'Área (ha)': area['area_ha'],
            'Celda': area['area']
        })
    
    df_dispersion = pd.DataFrame(dispersion_data)
    
    # Gráfico de dispersión
    fig = px.scatter(
        df_dispersion,
        x='Carbono (ton/ha)',
        y='Biodiversidad (Shannon)',
        size='Área (ha)',
        color='NDVI',
        hover_name='Celda',
        title='Relación entre Carbono y Biodiversidad',
        color_continuous_scale='viridis'
    )
    
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)
    
    # Análisis de potencial
    st.markdown("### 📊 Potencial de Conservación")
    
    # Calcular potencial combinado
    potencial_data = []
    for area in resultados['areas']:
        # Normalizar valores (0-1)
        ndvi_norm = area['indices_vegetacion']['ndvi']
        shannon_norm = area['indice_shannon'] / 4.0  # Máximo teórico 4.0
        carbono_norm = min(1.0, area['carbono']['carbono_ton_ha'] / 300)  # Máximo 300 ton/ha
        
        # Potencial combinado (promedio ponderado)
        potencial = (ndvi_norm * 0.3 + shannon_norm * 0.4 + carbono_norm * 0.3)
        
        potencial_data.append({
            'Celda': area['area'],
            'Potencial': round(potencial, 3),
            'Categoría': 'Alto' if potencial > 0.7 else 'Medio' if potencial > 0.4 else 'Bajo',
            'NDVI': ndvi_norm,
            'Shannon': shannon_norm,
            'Carbono': carbono_norm
        })
    
    df_potencial = pd.DataFrame(potencial_data)
    df_potencial = df_potencial.sort_values('Potencial', ascending=False)
    
    # Mostrar ranking
    st.markdown("#### 🏆 Ranking de Celdas por Potencial de Conservación")
    st.dataframe(df_potencial.head(10), use_container_width=True)

def mostrar_conservacion_especies():
    """Mostrar análisis de conservación de especies UICN"""
    st.markdown("## 🎯 Análisis de Conservación de Especies UICN")
    
    if st.session_state.resultados_ambientales is None:
        st.warning("Ejecuta el análisis ambiental primero")
        return
    
    resultados = st.session_state.resultados_ambientales
    base_especies = BaseDatosEspeciesUICN()
    todas_especies = base_especies.obtener_todas_especies()
    
    # Selección de especies
    st.markdown("### 🦋 Selección de Especies para Análisis")
    
    especies_lista = list(todas_especies.keys())
    especies_seleccionadas = st.multiselect(
        "Selecciona las especies a analizar",
        especies_lista,
        default=especies_lista[:3]
    )
    
    if not especies_seleccionadas:
        st.info("Selecciona al menos una especie para analizar")
        return
    
    # Calcular idoneidad para cada especie
    st.markdown("### 📊 Idoneidad de Hábitat por Especie")
    
    resultados_idoneidad = {}
    
    for especie in especies_seleccionadas:
        idoneidades = []
        
        for area in resultados['areas']:
            # Preparar características del área
            caracteristicas = {
                'temperatura_promedio': area['temperatura'],
                'precipitacion_anual': area['precipitacion'],
                'ndvi': area['indices_vegetacion']['ndvi'],
                'presion_antropica': area['presion_antropica'],
                'humedad_suelo': area['humedad_suelo']
            }
            
            idoneidad = base_especies.calcular_idoneidad_habitat(caracteristicas, especie)
            idoneidades.append(idoneidad)
        
        resultados_idoneidad[especie] = {
            'idoneidad_promedio': np.mean(idoneidades) if idoneidades else 0,
            'idoneidad_max': np.max(idoneidades) if idoneidades else 0,
            'idoneidad_min': np.min(idoneidades) if idoneidades else 0,
            'areas_optimas': len([i for i in idoneidades if i > 0.7]),
            'areas_moderadas': len([i for i in idoneidades if 0.4 <= i <= 0.7]),
            'areas_pobres': len([i for i in idoneidades if i < 0.4])
        }
    
    # Mostrar resultados
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📈 Resumen por Especie")
        
        for especie, datos in resultados_idoneidad.items():
            with st.expander(f"{especie} - {datos['idoneidad_promedio']:.2%}"):
                st.write(f"**Categoría UICN:** {todas_especies[especie]['categoria_uicn']}")
                st.write(f"**Idoneidad promedio:** {datos['idoneidad_promedio']:.2%}")
                st.write(f"**Áreas óptimas:** {datos['areas_optimas']}")
                st.write(f"**Áreas moderadas:** {datos['areas_moderadas']}")
                st.write(f"**Áreas pobres:** {datos['areas_pobres']}")
                
                # Recomendación basada en idoneidad
                if datos['idoneidad_promedio'] > 0.7:
                    st.success("✅ Hábitat óptimo - Ideal para conservación in-situ")
                elif datos['idoneidad_promedio'] > 0.4:
                    st.warning("⚠️ Hábitat moderado - Considerar restauración")
                else:
                    st.error("❌ Hábitat pobre - Evaluar translocación")
    
    with col2:
        st.markdown("#### 📊 Comparativa de Idoneidad")
        
        # Preparar datos para gráfico
        comparacion_data = []
        for especie, datos in resultados_idoneidad.items():
            comparacion_data.append({
                'Especie': especie,
                'Idoneidad': datos['idoneidad_promedio'],
                'Categoría': todas_especies[especie]['categoria_uicn'],
                'Áreas Óptimas': datos['areas_optimas']
            })
        
        df_comparacion = pd.DataFrame(comparacion_data)
        
        # Gráfico de barras
        fig = px.bar(
            df_comparacion,
            x='Especie',
            y='Idoneidad',
            color='Categoría',
            title='Idoneidad de Hábitat por Especie',
            text='Idoneidad',
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        
        fig.update_traces(texttemplate='%{text:.2%}', textposition='outside')
        fig.update_layout(height=400)
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Áreas prioritarias para conservación
    st.markdown("### 🎯 Áreas Prioritarias para Conservación")
    
    # Calcular prioridad por celda basada en múltiples especies
    prioridad_celdas = {}
    
    for i, area in enumerate(resultados['areas']):
        prioridad_total = 0
        especies_presentes = 0
        
        for especie in especies_seleccionadas:
            # Obtener idoneidad para esta especie en esta celda
            caracteristicas = {
                'temperatura_promedio': area['temperatura'],
                'precipitacion_anual': area['precipitacion'],
                'ndvi': area['indices_vegetacion']['ndvi'],
                'presion_antropica': area['presion_antropica'],
                'humedad_suelo': area['humedad_suelo']
            }
            
            idoneidad = base_especies.calcular_idoneidad_habitat(caracteristicas, especie)
            prioridad_especie = todas_especies[especie]['prioridad_conservacion']
            
            prioridad_total += idoneidad * prioridad_especie
            especies_presentes += 1
        
        if especies_presentes > 0:
            prioridad_promedio = prioridad_total / especies_presentes
            prioridad_celdas[area['area']] = {
                'prioridad': prioridad_promedio,
                'especies': especies_presentes,
                'categoria': 'Alta' if prioridad_promedio > 0.7 else 'Media' if prioridad_promedio > 0.4 else 'Baja'
            }
    
    # Mostrar ranking de áreas prioritarias
    if prioridad_celdas:
        df_prioridad = pd.DataFrame.from_dict(prioridad_celdas, orient='index')
        df_prioridad = df_prioridad.sort_values('prioridad', ascending=False)
        df_prioridad['Prioridad %'] = df_prioridad['prioridad'].apply(lambda x: f"{x:.2%}")
        
        st.markdown("#### 🏆 Top 10 Áreas Prioritarias")
        st.dataframe(
            df_prioridad[['Prioridad %', 'categoria', 'especies']].head(10),
            use_container_width=True
        )
        
        # Mapa de prioridades
        st.markdown("#### 🗺️ Mapa de Prioridades de Conservación")
        
        # Preparar datos para mapa
        datos_prioridad = []
        for area in resultados['areas']:
            if area['area'] in prioridad_celdas:
                datos_prioridad.append({
                    'area': area['area'],
                    'geometry': area['geometry'],
                    'prioridad': prioridad_celdas[area['area']]['prioridad']
                })
        
        config_prioridad = {
            'titulo': 'Prioridad de Conservación',
            'columna': 'prioridad',
            'colores': {
                (0, 0.4): '#FF0000',
                (0.4, 0.7): '#FFA500',
                (0.7, 1.0): '#00FF00'
            }
        }
        
        mapa_prioridad = st.session_state.analizador.sistema_mapas.crear_mapa_indicador(
            st.session_state.poligono_data,
            datos_prioridad,
            config_prioridad
        )
        
        folium_static(mapa_prioridad, width=800, height=500)
    
    # Recomendaciones finales
    st.markdown("### 💡 Recomendaciones de Conservación")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Acciones Inmediatas:**")
        st.markdown("""
        1. 🛡️ Establecer vigilancia en áreas de alta prioridad
        2. 📊 Monitorear especies clave regularmente
        3. 🌿 Proteger corredores entre áreas óptimas
        4. 🤝 Involucrar a comunidades locales
        5. 📚 Educación ambiental en áreas adyacentes
        """)
    
    with col2:
        st.markdown("**Acciones a Largo Plazo:**")
        st.markdown("""
        1. 🏞️ Crear reservas naturales formales
        2. 🌳 Programas de restauración ecológica
        3. 🔬 Investigación científica continua
        4. 💰 Buscar financiamiento internacional
        5. 📈 Sistema de monitoreo permanente
        """)

# ===============================
# 🚀 EJECUCIÓN PRINCIPAL
# ===============================

if __name__ == "__main__":
    main()
