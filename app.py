# ✅ ABSOLUTAMENTE PRIMERO: Importar streamlit
import streamlit as st

# ✅ LUEGO: Configurar la página
st.set_page_config(
    page_title="Sistema de Conservación de Especies UICN",
    page_icon="🦋",
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
from shapely.geometry import Polygon, Point, shape
import pyproj
from branca.colormap import LinearColormap
import matplotlib.cm as cm

# ===============================
# 🌿 BASE DE DATOS DE ESPECIES UICN CON NICHO ECOLÓGICO
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
        
        # Variables ambientales disponibles para el análisis
        self.variables_ambientales = [
            'temperatura_promedio',
            'precipitacion_anual',
            'elevacion',
            'cobertura_bosque',
            'humedad_suelo',
            'ndvi',
            'conectividad',
            'presion_antropica',
            'disponibilidad_agua',
            'densidad_vegetacion'
        ]
    
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
        
        # Factores de idoneidad (0-1)
        factores = []
        
        # 1. Temperatura
        if 'temperatura_promedio' in caracteristicas_area:
            temp = caracteristicas_area['temperatura_promedio']
            if nicho['temperatura_min'] <= temp <= nicho['temperatura_max']:
                factores.append(1.0)
            else:
                # Penalización por fuera del rango
                distancia = min(abs(temp - nicho['temperatura_min']), 
                              abs(temp - nicho['temperatura_max']))
                penalizacion = max(0, 1 - distancia / 10)  # 10°C de tolerancia
                factores.append(penalizacion)
        
        # 2. Precipitación
        if 'precipitacion_anual' in caracteristicas_area:
            precip = caracteristicas_area['precipitacion_anual']
            if nicho['precipitacion_min'] <= precip <= nicho['precipitacion_max']:
                factores.append(1.0)
            else:
                distancia = min(abs(precip - nicho['precipitacion_min']),
                              abs(precip - nicho['precipitacion_max']))
                penalizacion = max(0, 1 - distancia / 1000)  # 1000 mm de tolerancia
                factores.append(penalizacion)
        
        # 3. Cobertura de bosque (simulado por NDVI)
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
        
        # 6. Disponibilidad de agua
        if 'disponibilidad_agua' in caracteristicas_area:
            agua = caracteristicas_area['disponibilidad_agua']
            if nicho.get('cuerpos_agua', False):
                # Especies que requieren agua cercana
                factores.append(agua)
            else:
                # No es crítico
                factores.append(0.8)  # Valor base
        
        # 7. Densidad de vegetación
        if 'densidad_vegetacion' in caracteristicas_area:
            densidad = caracteristicas_area['densidad_vegetacion']
            if nicho.get('vegetacion_densa', False):
                # Prefiere vegetación densa
                factores.append(densidad)
            else:
                # Tolera vegetación menos densa
                factores.append(0.7)
        
        # Calcular idoneidad total (promedio ponderado)
        if factores:
            # Peso mayor para variables críticas
            pesos = [2.0 if i < 4 else 1.0 for i in range(len(factores))]
            idoneidad = np.average(factores, weights=pesos)
            
            # Ajustar por prioridad de conservación
            idoneidad *= especie['prioridad_conservacion']
            
            return round(idoneidad, 3)
        
        return 0
    
    def generar_recomendaciones_conservacion(self, resultados_idoneidad):
        """Genera recomendaciones basadas en los resultados de idoneidad"""
        recomendaciones = []
        
        # Análisis por especie
        for especie, datos in resultados_idoneidad.items():
            idoneidad_promedio = datos['idoneidad_promedio']
            areas_optimas = datos['areas_optimas']
            
            if idoneidad_promedio > 0.7:
                recomendaciones.append(f"✅ **{especie}**: Hábitat óptimo detectado. Recomendado para conservación in-situ.")
            elif idoneidad_promedio > 0.4:
                recomendaciones.append(f"⚠️ **{especie}**: Hábitat moderadamente adecuado. Considerar restauración ecológica.")
            else:
                recomendaciones.append(f"❌ **{especie}**: Hábitat poco adecuado. Evaluar translocación o cría en cautiverio.")
        
        # Recomendaciones generales
        if any(r['idoneidad_promedio'] > 0.7 for r in resultados_idoneidad.values()):
            recomendaciones.append("🎯 **Prioridad Alta**: Establecer corredores biológicos entre áreas óptimas.")
            recomendaciones.append("🛡️ **Protección**: Implementar medidas contra caza furtiva y tala ilegal.")
        
        if len([r for r in resultados_idoneidad.values() if r['idoneidad_promedio'] > 0.5]) >= 3:
            recomendaciones.append("🌿 **Biodiversidad**: El área puede albergar múltiples especies. Crear reserva natural.")
        
        return recomendaciones

# ===============================
# 🗺️ FUNCIONES DE MAPAS MEJORADAS
# ===============================

def crear_mapa_base_simple(gdf, titulo="Área de Estudio"):
    """Crear mapa base simple y funcional"""
    try:
        # Centro por defecto en Sudamérica
        m = folium.Map(location=[-14.0, -60.0], zoom_start=4, control_scale=True)
        
        # Capas base
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri World Imagery',
            name='Satélite',
            overlay=False,
            control=True
        ).add_to(m)
        
        folium.TileLayer('OpenStreetMap', name='OpenStreetMap').add_to(m)
        
        # Agregar polígono si existe
        if gdf is not None and not gdf.empty:
            try:
                poligono = gdf.geometry.iloc[0]
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
                    tooltip=titulo
                ).add_to(m)
                
                # Centrar mapa
                bounds = gdf.total_bounds
                if len(bounds) == 4:
                    m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])
                    
            except Exception as e:
                st.warning(f"Error al agregar polígono: {str(e)}")
        
        folium.LayerControl().add_to(m)
        Fullscreen().add_to(m)
        
        return m
        
    except Exception as e:
        st.error(f"Error creando mapa: {str(e)}")
        return folium.Map(location=[-14.0, -60.0], zoom_start=4)

def crear_mapa_idoneidad_especies(gdf, resultados_idoneidad, especie_seleccionada):
    """Crear mapa de idoneidad para especies"""
    try:
        m = crear_mapa_base_simple(gdf, f"Idoneidad: {especie_seleccionada}")
        
        if especie_seleccionada not in resultados_idoneidad:
            return m
        
        datos_especie = resultados_idoneidad[especie_seleccionada]
        
        # Agregar marcadores para áreas analizadas
        for area_data in datos_especie.get('datos_detallados', []):
            try:
                idoneidad = area_data.get('idoneidad', 0)
                geometry = area_data.get('geometry')
                area_id = area_data.get('area', 'Desconocida')
                
                if geometry and hasattr(geometry, 'centroid'):
                    centroid = geometry.centroid
                    lat, lon = centroid.y, centroid.x
                    
                    # Color basado en idoneidad
                    if idoneidad > 0.7:
                        color = '#00FF00'  # Verde - óptimo
                    elif idoneidad > 0.4:
                        color = '#FFFF00'  # Amarillo - moderado
                    else:
                        color = '#FF0000'  # Rojo - pobre
                    
                    # Popup informativo
                    popup_text = f"""
                    <div style='font-family: Arial;'>
                    <b>{especie_seleccionada}</b><br>
                    <b>Área:</b> {area_id}<br>
                    <b>Idoneidad:</b> {idoneidad:.2%}<br>
                    <b>Lat:</b> {lat:.4f}<br>
                    <b>Lon:</b> {lon:.4f}<br>
                    <br>
                    <small>💚 >70%: Óptimo<br>
                    💛 40-70%: Moderado<br>
                    ❤️ <40%: Pobre</small>
                    </div>
                    """
                    
                    # Agregar marcador
                    folium.CircleMarker(
                        location=[lat, lon],
                        radius=10,
                        popup=popup_text,
                        color=color,
                        fill=True,
                        fillColor=color,
                        fillOpacity=0.7,
                        tooltip=f"{area_id}: {idoneidad:.2%}"
                    ).add_to(m)
                    
            except Exception as e:
                continue
        
        return m
        
    except Exception as e:
        st.error(f"Error mapa idoneidad: {str(e)}")
        return crear_mapa_base_simple(gdf)

# ===============================
# 📊 FUNCIONES DE ANÁLISIS Y VISUALIZACIÓN
# ===============================

class AnalizadorConservacion:
    """Analizador de hábitat para especies UICN"""
    
    def __init__(self):
        self.base_datos = BaseDatosEspeciesUICN()
        self.parametros_ambientales = {
            'Bosque Tropical Húmedo': {
                'temperatura_promedio': 26,
                'precipitacion_anual': 2500,
                'elevacion': 200,
                'humedad_suelo': 0.8,
                'densidad_vegetacion': 0.9
            },
            'Bosque Seco': {
                'temperatura_promedio': 28,
                'precipitacion_anual': 800,
                'elevacion': 500,
                'humedad_suelo': 0.4,
                'densidad_vegetacion': 0.6
            },
            'Bosque Montano': {
                'temperatura_promedio': 18,
                'precipitacion_anual': 1500,
                'elevacion': 2000,
                'humedad_suelo': 0.7,
                'densidad_vegetacion': 0.8
            },
            'Sabana': {
                'temperatura_promedio': 25,
                'precipitacion_anual': 1200,
                'elevacion': 300,
                'humedad_suelo': 0.5,
                'densidad_vegetacion': 0.4
            },
            'Humeral': {
                'temperatura_promedio': 22,
                'precipitacion_anual': 3000,
                'elevacion': 100,
                'humedad_suelo': 0.9,
                'densidad_vegetacion': 0.7
            }
        }
    
    def generar_caracteristicas_areas(self, gdf, tipo_ecosistema, n_divisiones=5):
        """Generar características ambientales para cada área"""
        try:
            poligono_principal = gdf.geometry.iloc[0]
            bounds = poligono_principal.bounds
            
            areas = []
            id_area = 1
            
            # Parámetros base según ecosistema
            params_base = self.parametros_ambientales.get(tipo_ecosistema, 
                                                        self.parametros_ambientales['Bosque Tropical Húmedo'])
            
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
                        # Calcular características con variación
                        caracteristicas = {
                            'area': f"Área-{id_area}",
                            'geometry': interseccion,
                            'temperatura_promedio': params_base['temperatura_promedio'] + np.random.uniform(-3, 3),
                            'precipitacion_anual': params_base['precipitacion_anual'] + np.random.uniform(-200, 200),
                            'elevacion': params_base['elevacion'] + np.random.uniform(-100, 100),
                            'humedad_suelo': max(0.1, min(1.0, params_base['humedad_suelo'] + np.random.uniform(-0.2, 0.2))),
                            'densidad_vegetacion': max(0.1, min(1.0, params_base['densidad_vegetacion'] + np.random.uniform(-0.2, 0.2))),
                            'ndvi': params_base['densidad_vegetacion'] + np.random.uniform(-0.1, 0.1),
                            'conectividad': np.random.uniform(0.3, 0.9),
                            'presion_antropica': np.random.uniform(0.1, 0.7),
                            'disponibilidad_agua': np.random.uniform(0.3, 0.9)
                        }
                        
                        areas.append(caracteristicas)
                        id_area += 1
            
            return areas
            
        except Exception as e:
            st.error(f"Error generando características: {str(e)}")
            return []
    
    def analizar_idoneidad_especies(self, areas_caracteristicas, especies_seleccionadas):
        """Analizar idoneidad para especies seleccionadas"""
        resultados = {}
        
        for especie_nombre in especies_seleccionadas:
            idoneidades = []
            datos_detallados = []
            
            for area in areas_caracteristicas:
                idoneidad = self.base_datos.calcular_idoneidad_habitat(area, especie_nombre)
                idoneidades.append(idoneidad)
                
                # Guardar datos detallados
                datos_detallados.append({
                    'area': area['area'],
                    'idoneidad': idoneidad,
                    'geometry': area['geometry'],
                    'temperatura': area['temperatura_promedio'],
                    'precipitacion': area['precipitacion_anual'],
                    'elevacion': area['elevacion']
                })
            
            # Estadísticas
            if idoneidades:
                resultados[especie_nombre] = {
                    'idoneidad_promedio': np.mean(idoneidades),
                    'idoneidad_max': np.max(idoneidades),
                    'idoneidad_min': np.min(idoneidades),
                    'areas_optimas': len([i for i in idoneidades if i > 0.7]),
                    'areas_moderadas': len([i for i in idoneidades if 0.4 <= i <= 0.7]),
                    'areas_pobres': len([i for i in idoneidades if i < 0.4]),
                    'datos_detallados': datos_detallados,
                    'especie_info': self.base_datos.obtener_todas_especies()[especie_nombre]
                }
        
        return resultados
    
    def identificar_areas_prioritarias(self, resultados_idoneidad):
        """Identificar áreas prioritarias para conservación"""
        areas_prioritarias = {}
        
        # Para cada área, calcular prioridad basada en múltiples especies
        especies = list(resultados_idoneidad.keys())
        
        if not especies:
            return areas_prioritarias
        
        # Obtener todas las áreas únicas
        todas_areas = []
        for especie, datos in resultados_idoneidad.items():
            for area_data in datos['datos_detallados']:
                if area_data['area'] not in todas_areas:
                    todas_areas.append(area_data['area'])
        
        # Calcular prioridad por área
        for area_nombre in todas_areas:
            prioridad_total = 0
            especies_presentes = 0
            
            for especie, datos in resultados_idoneidad.items():
                for area_data in datos['datos_detallados']:
                    if area_data['area'] == area_nombre:
                        idoneidad = area_data['idoneidad']
                        prioridad_especie = datos['especie_info']['prioridad_conservacion']
                        
                        # Ponderar por prioridad de la especie
                        prioridad_total += idoneidad * prioridad_especie
                        especies_presentes += 1
            
            if especies_presentes > 0:
                prioridad_promedio = prioridad_total / especies_presentes
                areas_prioritarias[area_nombre] = {
                    'prioridad': prioridad_promedio,
                    'especies_presentes': especies_presentes,
                    'categoria': self._clasificar_prioridad(prioridad_promedio)
                }
        
        return areas_prioritarias
    
    def _clasificar_prioridad(self, prioridad):
        """Clasificar nivel de prioridad"""
        if prioridad > 0.7:
            return "Alta Prioridad"
        elif prioridad > 0.4:
            return "Prioridad Media"
        else:
            return "Baja Prioridad"

# ===============================
# 🎨 INTERFAZ DE USUARIO
# ===============================

def mostrar_panel_especies_uicn():
    """Mostrar panel de información de especies UICN"""
    st.markdown("## 📋 Base de Datos de Especies UICN")
    
    base_datos = BaseDatosEspeciesUICN()
    todas_especies = base_datos.obtener_todas_especies()
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    with col1:
        filtrar_lista = st.selectbox("Filtrar por lista", ["Todas", "Lista Roja", "Lista Amarilla"])
    with col2:
        filtrar_tipo = st.selectbox("Filtrar por tipo", ["Todos", "Mamífero", "Ave", "Reptil"])
    with col3:
        filtrar_categoria = st.selectbox("Filtrar por categoría", ["Todas", "En Peligro", "Vulnerable", "Casi Amenazada", "Preocupación Menor"])
    
    # Filtrar especies
    especies_filtradas = {}
    for nombre, datos in todas_especies.items():
        cumple_lista = True
        cumple_tipo = True
        cumple_categoria = True
        
        if filtrar_lista != "Todas":
            if filtrar_lista == "Lista Roja":
                cumple_lista = nombre in base_datos.especies_lista_roja
            else:
                cumple_lista = nombre in base_datos.especies_lista_amarilla
        
        if filtrar_tipo != "Todos":
            cumple_tipo = datos['tipo'] == filtrar_tipo
        
        if filtrar_categoria != "Todas":
            cumple_categoria = datos['categoria_uicn'] == filtrar_categoria
        
        if cumple_lista and cumple_tipo and cumple_categoria:
            especies_filtradas[nombre] = datos
    
    # Mostrar tarjetas de especies
    for nombre, datos in especies_filtradas.items():
        with st.expander(f"🦋 {nombre} ({datos['nombre_cientifico']}) - {datos['categoria_uicn']}"):
            col_info, col_nicho = st.columns(2)
            
            with col_info:
                st.markdown(f"**Tipo:** {datos['tipo']}")
                st.markdown(f"**Prioridad:** {datos['prioridad_conservacion']:.2%}")
                st.markdown(f"**Área home range:** {datos['area_home_range']} km²")
                st.markdown(f"**Densidad:** {datos['densidad_poblacional']} ind/100km²")
                
                st.markdown("**Requerimientos de hábitat:**")
                for req in datos['requerimientos_habitat']:
                    st.markdown(f"• {req}")
            
            with col_nicho:
                st.markdown("**Parámetros de nicho:**")
                nicho = datos['nicho']
                
                if 'temperatura_min' in nicho:
                    st.markdown(f"• Temperatura: {nicho['temperatura_min']}-{nicho['temperatura_max']}°C")
                if 'precipitacion_min' in nicho:
                    st.markdown(f"• Precipitación: {nicho['precipitacion_min']}-{nicho['precipitacion_max']} mm/año")
                if 'elevacion_min' in nicho:
                    st.markdown(f"• Elevación: {nicho['elevacion_min']}-{nicho['elevacion_max']} msnm")
                if 'cobertura_bosque_min' in nicho:
                    st.markdown(f"• Cobertura bosque: >{nicho['cobertura_bosque_min']*100:.0f}%")
                if 'presion_antropica_max' in nicho:
                    st.markdown(f"• Presión antrópica: <{nicho['presion_antropica_max']*100:.0f}%")

def mostrar_analisis_idoneidad(gdf, resultados_idoneidad, areas_prioritarias):
    """Mostrar análisis de idoneidad"""
    st.markdown("## 📊 Resultados de Idoneidad de Hábitat")
    
    if not resultados_idoneidad:
        st.warning("No hay resultados de idoneidad para mostrar.")
        return
    
    # Seleccionar especie para visualización detallada
    especies_disponibles = list(resultados_idoneidad.keys())
    especie_seleccionada = st.selectbox("Seleccionar especie para análisis detallado", especies_disponibles)
    
    if especie_seleccionada:
        datos_especie = resultados_idoneidad[especie_seleccionada]
        
        # KPIs para la especie
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Idoneidad Promedio", f"{datos_especie['idoneidad_promedio']:.2%}")
        with col2:
            st.metric("Áreas Óptimas", datos_especie['areas_optimas'])
        with col3:
            st.metric("Áreas Moderadas", datos_especie['areas_moderadas'])
        with col4:
            st.metric("Áreas Pobres", datos_especie['areas_pobres'])
        
        # Mapa de idoneidad
        st.markdown("### 🗺️ Mapa de Idoneidad")
        mapa_idoneidad = crear_mapa_idoneidad_especies(gdf, resultados_idoneidad, especie_seleccionada)
        folium_static(mapa_idoneidad, width=800, height=500)
        
        # Gráfico de distribución de idoneidad
        st.markdown("### 📈 Distribución de Idoneidad")
        
        # Preparar datos para el gráfico
        idoneidades = [d['idoneidad'] for d in datos_especie['datos_detallados']]
        
        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=idoneidades,
            nbinsx=20,
            name='Frecuencia',
            marker_color='#3b82f6'
        ))
        
        fig.update_layout(
            title=f'Distribución de Idoneidad para {especie_seleccionada}',
            xaxis_title='Idoneidad',
            yaxis_title='Número de Áreas',
            bargap=0.1,
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Tabla de áreas por idoneidad
        st.markdown("### 📋 Ranking de Áreas por Idoneidad")
        
        df_areas = pd.DataFrame(datos_especie['datos_detallados'])
        df_areas = df_areas.sort_values('idoneidad', ascending=False)
        df_areas['idoneidad_%'] = df_areas['idoneidad'].apply(lambda x: f"{x:.2%}")
        df_areas['categoria'] = df_areas['idoneidad'].apply(
            lambda x: 'Óptima' if x > 0.7 else 'Moderada' if x > 0.4 else 'Pobre'
        )
        
        st.dataframe(
            df_areas[['area', 'idoneidad_%', 'categoria', 'temperatura', 'precipitacion', 'elevacion']].head(10),
            use_container_width=True
        )
    
    # Áreas prioritarias
    st.markdown("## 🎯 Áreas Prioritarias para Conservación")
    
    if areas_prioritarias:
        # Convertir a DataFrame
        df_prioritarias = pd.DataFrame.from_dict(areas_prioritarias, orient='index')
        df_prioritarias = df_prioritarias.sort_values('prioridad', ascending=False)
        df_prioritarias['prioridad_%'] = df_prioritarias['prioridad'].apply(lambda x: f"{x:.2%}")
        
        # Mostrar tabla
        st.dataframe(
            df_prioritarias[['prioridad_%', 'categoria', 'especies_presentes']],
            use_container_width=True
        )
        
        # Gráfico de prioridades
        fig = go.Figure(data=[
            go.Bar(
                x=df_prioritarias.index[:10],
                y=df_prioritarias['prioridad'][:10],
                marker_color=['#FF0000' if p > 0.7 else '#FFA500' if p > 0.4 else '#00FF00' 
                            for p in df_prioritarias['prioridad'][:10]]
            )
        ])
        
        fig.update_layout(
            title='Top 10 Áreas Prioritarias',
            xaxis_title='Área',
            yaxis_title='Prioridad',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)

def mostrar_recomendaciones_conservacion(resultados_idoneidad):
    """Mostrar recomendaciones de conservación"""
    st.markdown("## 💡 Recomendaciones para Conservación")
    
    base_datos = BaseDatosEspeciesUICN()
    recomendaciones = base_datos.generar_recomendaciones_conservacion(resultados_idoneidad)
    
    for rec in recomendaciones:
        st.markdown(f"• {rec}")
    
    # Plan de acción sugerido
    st.markdown("### 📝 Plan de Acción Sugerido")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Acciones Inmediatas (0-6 meses):**")
        st.markdown("""
        1. 📋 Realizar inventario biológico detallado
        2. 🛡️ Establecer vigilancia contra actividades ilegales
        3. 📊 Monitorear poblaciones de especies clave
        4. 🌿 Identificar corredores biológicos naturales
        5. 🤝 Establecer alianzas con comunidades locales
        """)
    
    with col2:
        st.markdown("**Acciones a Mediano Plazo (6-24 meses):**")
        st.markdown("""
        1. 🌳 Implementar programas de restauración
        2. 🏞️ Diseñar áreas protegidas formales
        3. 📚 Desarrollar programas de educación ambiental
        4. 💰 Buscar financiamiento para conservación
        5. 🔬 Establecer estaciones de investigación
        """)
    
    # Especies para programas específicos
    st.markdown("### 🦋 Programas Específicos por Especie")
    
    especies_prioritarias = sorted(
        [(nombre, datos['idoneidad_promedio']) for nombre, datos in resultados_idoneidad.items()],
        key=lambda x: x[1],
        reverse=True
    )[:3]
    
    for especie, idoneidad in especies_prioritarias:
        if idoneidad > 0.7:
            st.success(f"**{especie}**: Ideal para programa de conservación in-situ")
        elif idoneidad > 0.4:
            st.warning(f"**{especie}**: Requiere restauración de hábitat antes de programas de conservación")
        else:
            st.error(f"**{especie}**: Considerar programas ex-situ o translocación")

# ===============================
# 🚀 APLICACIÓN PRINCIPAL
# ===============================

def main():
    st.title("🌿 Sistema de Conservación de Especies UICN")
    st.markdown("### Análisis de Nichos Ecológicos y Hábitats Prioritarios")
    
    # Inicializar estado de sesión
    if 'poligono_data' not in st.session_state:
        st.session_state.poligono_data = None
    if 'resultados_idoneidad' not in st.session_state:
        st.session_state.resultados_idoneidad = None
    if 'areas_prioritarias' not in st.session_state:
        st.session_state.areas_prioritarias = None
    if 'analizador' not in st.session_state:
        st.session_state.analizador = AnalizadorConservacion()
    
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
                        # Buscar shapefile
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
                ['Bosque Tropical Húmedo', 'Bosque Seco', 'Bosque Montano', 'Sabana', 'Humeral']
            )
            
            nivel_detalle = st.slider("Nivel de detalle del análisis", 3, 10, 5)
            
            # Selección de especies
            base_datos = BaseDatosEspeciesUICN()
            todas_especies = list(base_datos.obtener_todas_especies().keys())
            
            especies_seleccionadas = st.multiselect(
                "Seleccionar especies para análisis",
                todas_especies,
                default=todas_especies[:3]  # Por defecto, primeras 3 especies
            )
            
            if st.button("🚀 Ejecutar Análisis de Conservación", type="primary"):
                with st.spinner("Analizando idoneidad de hábitat..."):
                    # Generar características ambientales
                    areas_caracteristicas = st.session_state.analizador.generar_caracteristicas_areas(
                        st.session_state.poligono_data,
                        tipo_ecosistema,
                        nivel_detalle
                    )
                    
                    # Analizar idoneidad
                    resultados = st.session_state.analizador.analizar_idoneidad_especies(
                        areas_caracteristicas,
                        especies_seleccionadas
                    )
                    
                    # Identificar áreas prioritarias
                    areas_prioritarias = st.session_state.analizador.identificar_areas_prioritarias(resultados)
                    
                    st.session_state.resultados_idoneidad = resultados
                    st.session_state.areas_prioritarias = areas_prioritarias
                    
                    st.success("✅ Análisis completado exitosamente!")
    
    # Pestañas principales
    tab1, tab2, tab3, tab4 = st.tabs([
        "🗺️ Mapa del Área",
        "📋 Base de Especies UICN", 
        "📊 Análisis de Idoneidad",
        "💡 Recomendaciones"
    ])
    
    with tab1:
        if st.session_state.poligono_data is not None:
            st.markdown("## 🗺️ Área de Estudio")
            mapa = crear_mapa_base_simple(st.session_state.poligono_data, "Área de Análisis de Conservación")
            folium_static(mapa, width=800, height=600)
            
            # Información del área
            gdf = st.session_state.poligono_data
            area_km2 = gdf.geometry.area.iloc[0] * 111 * 111 * math.cos(math.radians(gdf.geometry.centroid.y.iloc[0]))
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Área aproximada", f"{area_km2:.2f} km²")
            with col2:
                st.metric("Tipo de geometría", gdf.geometry.iloc[0].geom_type)
            with col3:
                bounds = gdf.total_bounds
                st.metric("Centroide", f"{bounds[1]:.4f}°, {bounds[0]:.4f}°")
        else:
            st.info("👈 Carga un polígono en el panel lateral para comenzar")
    
    with tab2:
        mostrar_panel_especies_uicn()
    
    with tab3:
        if st.session_state.resultados_idoneidad:
            mostrar_analisis_idoneidad(
                st.session_state.poligono_data,
                st.session_state.resultados_idoneidad,
                st.session_state.areas_prioritarias
            )
        else:
            st.warning("Ejecuta el análisis de conservación primero")
    
    with tab4:
        if st.session_state.resultados_idoneidad:
            mostrar_recomendaciones_conservacion(st.session_state.resultados_idoneidad)
        else:
            st.warning("Ejecuta el análisis de conservación primero")
    
    # Información adicional
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    ### 📚 Acerca de este sistema
    
    Este sistema utiliza:
    
    • **Listas UICN**: Categorías de amenaza
    • **Nichos ecológicos**: Requerimientos específicos por especie
    • **Análisis espacial**: Evaluación de idoneidad de hábitat
    • **Priorización**: Identificación de áreas críticas
    
    Desarrollado para la conservación de biodiversidad en América del Sur.
    """)

if __name__ == "__main__":
    main()
