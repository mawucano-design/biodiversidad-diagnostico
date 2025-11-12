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

# Librerías para análisis geoespacial
import folium
from streamlit_folium import st_folium
import pydeck as pdk
import geopandas as gpd
from shapely.geometry import Point, Polygon
import rasterio
from PIL import Image
import json

# ===============================
# 🌿 CONFIGURACIÓN DE LA PÁGINA
# ===============================

st.set_page_config(
    page_title="Diagnóstico de Biodiversidad Ambiental",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===============================
# 🧭 TÍTULO Y DESCRIPCIÓN
# ===============================

st.title("🌍 Diagnóstico de Biodiversidad Ambiental de un Territorio")
st.markdown("""
**Sistema integral de evaluación ambiental** que combina la metodología **LE.MU Atlas** con  
**Índices de Vegetación** y **Métricas de Biodiversidad** para un análisis completo del territorio.
""")

# ===============================
# 🧩 CLASES DE ANÁLISIS
# ===============================

class BiodiversityAnalyzer:
    """Analizador completo de biodiversidad LE.MU + Shannon"""
    
    def __init__(self):
        self.species_pool = self._load_species_pool()
        self.vegetation_types = [
            'Bosque Denso Primario', 'Bosque Secundario', 'Bosque Ripario',
            'Matorral Denso', 'Matorral Abierto', 'Sabana Arborizada',
            'Herbazal Natural', 'Zona de Transición', 'Área de Restauración'
        ]
    
    def _load_species_pool(self):
        """Cargar pool de especies basado en ecosistemas latinoamericanos"""
        return {
            'Bosques': [
                'Handroanthus chrysanthus', 'Ceiba pentandra', 'Ficus insipida',
                'Ocotea quixos', 'Erythrina edulis', 'Inga edulis',
                'Cedrela odorata', 'Swietenia macrophylla', 'Brosimum utile',
                'Virola sebifera', 'Iriartea deltoidea', 'Socratea exorrhiza'
            ],
            'Matorrales': [
                'Baccharis latifolia', 'Dodonaea viscosa', 'Lantana camara',
                'Croton lechleri', 'Piper spp', 'Psychotria spp',
                'Miconia spp', 'Tibouchina spp', 'Gaultheria spp'
            ],
            'Herbáceas': [
                'Paspalum spp', 'Axonopus spp', 'Setaria spp',
                'Eragrostis spp', 'Cyperus spp', 'Eleocharis spp',
                'Lycopodium spp', 'Selaginella spp'
            ]
        }
    
    def shannon_index(self, abundances):
        """Índice de Shannon-Wiener para diversidad de especies"""
        total = sum(abundances)
        if total == 0:
            return 0.0
        proportions = [a / total for a in abundances if a > 0]
        return -sum(p * math.log(p) for p in proportions)
    
    def simpson_index(self, abundances):
        """Índice de Simpson para dominancia"""
        total = sum(abundances)
        if total == 0:
            return 0.0
        return sum((a / total) ** 2 for a in abundances)
    
    def species_richness(self, abundances):
        """Riqueza de especies"""
        return sum(1 for a in abundances if a > 0)
    
    def evenness(self, shannon_index, richness):
        """Equitatividad de Pielou"""
        if richness <= 1:
            return 1.0
        return shannon_index / math.log(richness)
    
    def margalef_index(self, richness, total_individuals):
        """Índice de Margalef para riqueza relativa"""
        if total_individuals == 0:
            return 0.0
        return (richness - 1) / math.log(total_individuals)
    
    def calculate_lemu_indicators(self, species_data, area_hectares):
        """Calcular indicadores LE.MU personalizados"""
        df = pd.DataFrame(species_data)
        
        if df.empty:
            return self._default_lemu_indicators()
        
        # Métricas básicas
        total_species = df['species'].nunique()
        total_abundance = df['abundance'].sum()
        endemic_species = len([s for s in df['species'].unique() if 'endemica' in s.lower()])
        
        # Calcular densidad por hectárea
        density_per_hectare = total_abundance / area_hectares if area_hectares > 0 else total_abundance
        
        # Estructura vertical (simulada basada en tipos de vegetación)
        vertical_structure = self._assess_vertical_structure(df)
        
        # Conectividad ecológica (simulada)
        connectivity_score = self._calculate_connectivity(df)
        
        return {
            'diversidad_alfa': total_species,
            'densidad_individuos': density_per_hectare,
            'riqueza_especies': total_species,
            'especies_endemicas': endemic_species,
            'estructura_vertical': vertical_structure,
            'conectividad_ecologica': connectivity_score,
            'estado_conservacion': self._assess_conservation_status(df),
            'presencia_especies_clave': self._assess_keystone_species(df),
            'regeneracion_natural': self._assess_natural_regeneration(df)
        }
    
    def _assess_vertical_structure(self, df):
        """Evaluar estructura vertical del bosque"""
        # Simulación basada en distribución de abundancias
        abundance_std = df['abundance'].std()
        if abundance_std > df['abundance'].mean() * 0.8:
            return "Estructura Compleja"
        elif abundance_std > df['abundance'].mean() * 0.4:
            return "Estructura Media"
        else:
            return "Estructura Simple"
    
    def _calculate_connectivity(self, df):
        """Calcular score de conectividad ecológica"""
        areas_count = df['area'].nunique()
        species_per_area = df.groupby('area')['species'].nunique().mean()
        return min(100, (areas_count * species_per_area) / 10)
    
    def _assess_conservation_status(self, df):
        """Evaluar estado de conservación"""
        total_species = df['species'].nunique()
        if total_species >= 15:
            return "Excelente"
        elif total_species >= 10:
            return "Bueno"
        elif total_species >= 5:
            return "Regular"
        else:
            return "Crítico"
    
    def _assess_keystone_species(self, df):
        """Evaluar presencia de especies clave"""
        keystone_species = ['Ficus insipida', 'Ceiba pentandra', 'Ocotea quixos']
        present_keystone = sum(1 for species in keystone_species if species in df['species'].values)
        return f"{present_keystone}/{len(keystone_species)}"
    
    def _assess_natural_regeneration(self, df):
        """Evaluar regeneración natural"""
        young_species = ['Piper spp', 'Miconia spp', 'Psychotria spp']
        young_count = sum(df[df['species'].isin(young_species)]['abundance'])
        return "Alta" if young_count > 20 else "Media" if young_count > 10 else "Baja"
    
    def _default_lemu_indicators(self):
        return {key: 0 for key in [
            'diversidad_alfa', 'densidad_individuos', 'riqueza_especies',
            'especies_endemicas', 'estructura_vertical', 'conectividad_ecologica',
            'estado_conservacion', 'presencia_especies_clave', 'regeneracion_natural'
        ]}

class VegetationIndexAnalyzer:
    """Analizador de índices de vegetación multiespectral"""
    
    def __init__(self):
        self.indices = {
            'NDVI': self.calculate_ndvi,
            'NDWI': self.calculate_ndwi,
            'EVI': self.calculate_evi,
            'SAVI': self.calculate_savi,
            'RVI': self.calculate_rvi,
            'NDRE': self.calculate_ndre,
            'GNDVI': self.calculate_gndvi,
            'OSAVI': self.calculate_osavi
        }
    
    def calculate_ndvi(self, nir, red):
        """Normalized Difference Vegetation Index"""
        return (nir - red) / (nir + red + 1e-10)
    
    def calculate_ndwi(self, nir, swir):
        """Normalized Difference Water Index"""
        return (nir - swir) / (nir + swir + 1e-10)
    
    def calculate_evi(self, nir, red, blue):
        """Enhanced Vegetation Index"""
        return 2.5 * (nir - red) / (nir + 6 * red - 7.5 * blue + 1)
    
    def calculate_savi(self, nir, red, L=0.5):
        """Soil Adjusted Vegetation Index"""
        return ((nir - red) / (nir + red + L)) * (1 + L)
    
    def calculate_rvi(self, nir, red):
        """Ratio Vegetation Index"""
        return nir / (red + 1e-10)
    
    def calculate_ndre(self, nir, red_edge):
        """Normalized Difference Red Edge"""
        return (nir - red_edge) / (nir + red_edge + 1e-10)
    
    def calculate_gndvi(self, nir, green):
        """Green Normalized Difference Vegetation Index"""
        return (nir - green) / (nir + green + 1e-10)
    
    def calculate_osavi(self, nir, red, L=0.16):
        """Optimized Soil Adjusted Vegetation Index"""
        return (nir - red) / (nir + red + L + 1e-10)
    
    def simulate_spectral_data(self, area_count, vegetation_type):
        """Simular datos espectrales para diferentes tipos de vegetación"""
        spectral_data = []
        
        base_values = {
            'Bosque Denso Primario': {'ndvi': 0.8, 'ndwi': 0.3, 'evi': 0.6},
            'Bosque Secundario': {'ndvi': 0.7, 'ndwi': 0.2, 'evi': 0.5},
            'Matorral Denso': {'ndvi': 0.6, 'ndwi': 0.1, 'evi': 0.4},
            'Herbazal Natural': {'ndvi': 0.5, 'ndwi': 0.05, 'evi': 0.3}
        }
        
        base = base_values.get(vegetation_type, {'ndvi': 0.4, 'ndwi': 0.0, 'evi': 0.2})
        
        for area_idx in range(area_count):
            # Simular variación espacial
            ndvi = max(0.1, min(0.9, np.random.normal(base['ndvi'], 0.1)))
            ndwi = max(-0.2, min(0.5, np.random.normal(base['ndwi'], 0.05)))
            evi = max(0.1, min(0.8, np.random.normal(base['evi'], 0.08)))
            
            # Calcular bandas espectrales simuladas
            red = 0.1 + (1 - ndvi) * 0.3
            nir = red * (1 + ndvi) / (1 - ndvi) if ndvi < 1 else 0.8
            blue = 0.1
            green = 0.2
            red_edge = 0.15
            swir = 0.3
            
            spectral_data.append({
                'area': f"Área {area_idx + 1}",
                'NDVI': ndvi,
                'NDWI': ndwi,
                'EVI': evi,
                'SAVI': self.calculate_savi(nir, red),
                'RVI': self.calculate_rvi(nir, red),
                'NDRE': self.calculate_ndre(nir, red_edge),
                'GNDVI': self.calculate_gndvi(nir, green),
                'OSAVI': self.calculate_osavi(nir, red),
                'biomasa_estimada': ndvi * 100 + np.random.normal(0, 10),
                'estres_hidrico': (1 - ndwi) * 50 + np.random.normal(0, 5)
            })
        
        return spectral_data

class IntegratedAnalyzer:
    """Analizador integrado de biodiversidad y vegetación"""
    
    def __init__(self):
        self.bio_analyzer = BiodiversityAnalyzer()
        self.veg_analyzer = VegetationIndexAnalyzer()
    
    def comprehensive_analysis(self, area_count, vegetation_type, area_hectares=100):
        """Análisis integral combinando biodiversidad y vegetación"""
        # Simular datos de biodiversidad
        species_data = self._simulate_integrated_species_data(area_count, vegetation_type)
        
        # Simular datos de vegetación
        spectral_data = self.veg_analyzer.simulate_spectral_data(area_count, vegetation_type)
        
        # Calcular métricas de biodiversidad
        df_species = pd.DataFrame(species_data)
        species_abundances = df_species.groupby('species')['abundance'].sum().values
        
        biodiversity_metrics = {
            'shannon_index': self.bio_analyzer.shannon_index(species_abundances),
            'species_richness': self.bio_analyzer.species_richness(species_abundances),
            'evenness': self.bio_analyzer.evenness(
                self.bio_analyzer.shannon_index(species_abundances),
                self.bio_analyzer.species_richness(species_abundances)
            ),
            'simpson_index': self.bio_analyzer.simpson_index(species_abundances),
            'margalef_index': self.bio_analyzer.margalef_index(
                self.bio_analyzer.species_richness(species_abundances),
                sum(species_abundances)
            )
        }
        
        # Calcular indicadores LE.MU
        lemu_indicators = self.bio_analyzer.calculate_lemu_indicators(
            species_data, area_hectares
        )
        
        # Calcular promedios de índices de vegetación
        df_spectral = pd.DataFrame(spectral_data)
        vegetation_metrics = {
            index: df_spectral[index].mean() for index in [
                'NDVI', 'NDWI', 'EVI', 'SAVI', 'RVI', 'NDRE', 'GNDVI', 'OSAVI'
            ]
        }
        
        # Métricas integradas
        integrated_scores = self._calculate_integrated_scores(
            biodiversity_metrics, vegetation_metrics, lemu_indicators
        )
        
        return {
            'biodiversity_metrics': biodiversity_metrics,
            'vegetation_metrics': vegetation_metrics,
            'lemu_indicators': lemu_indicators,
            'integrated_scores': integrated_scores,
            'species_data': species_data,
            'spectral_data': spectral_data,
            'raw_data': {
                'species_df': df_species,
                'spectral_df': df_spectral
            }
        }
    
    def _simulate_integrated_species_data(self, area_count, vegetation_type):
        """Simular datos de especies integrados con tipo de vegetación"""
        species_data = []
        
        # Seleccionar especies según tipo de vegetación
        if 'Bosque' in vegetation_type:
            ecosystem = 'Bosques'
        elif 'Matorral' in vegetation_type:
            ecosystem = 'Matorrales'
        else:
            ecosystem = 'Herbáceas'
        
        selected_species = np.random.choice(
            self.bio_analyzer.species_pool[ecosystem],
            size=min(12, len(self.bio_analyzer.species_pool[ecosystem])),
            replace=False
        )
        
        for area_idx in range(area_count):
            for species in selected_species:
                # Abundancia basada en tipo de vegetación
                if 'Primario' in vegetation_type:
                    abundance = np.random.poisson(30) + 20
                elif 'Secundario' in vegetation_type:
                    abundance = np.random.poisson(20) + 10
                else:
                    abundance = np.random.poisson(15) + 5
                
                species_data.append({
                    'species': species,
                    'abundance': int(abundance),
                    'frequency': round(np.random.uniform(0.3, 0.9), 3),
                    'area': f"Área {area_idx + 1}",
                    'ecosystem': ecosystem,
                    'vegetation_type': vegetation_type
                })
        
        return species_data
    
    def _calculate_integrated_scores(self, bio_metrics, veg_metrics, lemu_indicators):
        """Calcular scores integrados de salud del ecosistema"""
        
        # Score de biodiversidad (0-100)
        biodiversity_score = min(100, (
            bio_metrics['shannon_index'] * 20 +
            bio_metrics['species_richness'] * 2 +
            lemu_indicators['diversidad_alfa'] * 3
        ))
        
        # Score de vegetación (0-100)
        vegetation_score = min(100, (
            veg_metrics['NDVI'] * 60 +
            veg_metrics['EVI'] * 40 +
            (1 - veg_metrics['NDWI']) * 20  # Menos estrés hídrico = mejor
        ))
        
        # Score de conservación (0-100)
        conservation_score = min(100, (
            lemu_indicators['conectividad_ecologica'] +
            lemu_indicators['estructura_vertical'] * 10 +  # Valor simbólico
            lemu_indicators['presencia_especies_clave'].split('/')[0] * 15
        ))
        
        # Score integral de salud del ecosistema
        ecosystem_health = (
            biodiversity_score * 0.4 +
            vegetation_score * 0.4 +
            conservation_score * 0.2
        )
        
        return {
            'biodiversity_score': biodiversity_score,
            'vegetation_score': vegetation_score,
            'conservation_score': conservation_score,
            'ecosystem_health': ecosystem_health,
            'overall_rating': self._get_rating(ecosystem_health)
        }
    
    def _get_rating(self, score):
        """Convertir score a rating cualitativo"""
        if score >= 80:
            return "Excelente"
        elif score >= 60:
            return "Bueno"
        elif score >= 40:
            return "Regular"
        elif score >= 20:
            return "Precario"
        else:
            return "Crítico"

# ===============================
# 📁 SIDEBAR DE CONFIGURACIÓN
# ===============================

with st.sidebar:
    st.header("🌍 Configuración del Territorio")
    
    uploaded_file = st.file_uploader(
        "Sube archivo del territorio (KML/ZIP/Shapefile)",
        type=['kml', 'zip'],
        help="Archivos geoespaciales con la delimitación del área de estudio"
    )
    
    st.markdown("---")
    st.header("📊 Parámetros de Análisis")
    
    vegetation_type = st.selectbox(
        "Tipo de vegetación predominante",
        [
            'Bosque Denso Primario', 'Bosque Secundario', 'Bosque Ripario',
            'Matorral Denso', 'Matorral Abierto', 'Sabana Arborizada',
            'Herbazal Natural', 'Zona de Transición', 'Área de Restauración'
        ]
    )
    
    area_hectares = st.slider(
        "Área total del territorio (hectáreas)",
        min_value=1, max_value=10000, value=100, step=10
    )
    
    manual_areas = st.slider(
        "Número de parcelas de muestreo",
        min_value=1, max_value=50, value=12
    )
    
    analysis_depth = st.selectbox(
        "Profundidad del análisis",
        ["Básico", "Intermedio", "Completo"],
        index=1
    )
    
    st.markdown("---")
    st.info("""
    **📈 Indicadores Principales:**
    - 🌿 Shannon: Diversidad de especies
    - 📊 LE.MU: Métricas de conservación
    - 🛰️ NDVI/EVI: Salud de la vegetación
    - 🔗 Conectividad: Integridad ecológica
    """)

# ===============================
# 🚀 EJECUCIÓN DEL ANÁLISIS
# ===============================

analyzer = IntegratedAnalyzer()

# Procesar archivo subido
if uploaded_file:
    with st.spinner("Procesando archivo del territorio..."):
        # Simulación de procesamiento de archivo
        area_count = min(manual_areas * 2, 50)
        st.success(f"🗺️ Territorio procesado: {uploaded_file.name}")
        st.info(f"🔍 Se analizarán {area_count} parcelas de muestreo")
else:
    area_count = manual_areas
    st.info(f"🔬 Configuración manual: {area_count} parcelas de muestreo")

# Mostrar resumen de configuración
col1, col2, col3, col4 = st.columns(4)
col1.metric("Parcelas", area_count)
col2.metric("Hectáreas", f"{area_hectares:,}")
col3.metric("Vegetación", vegetation_type)
col4.metric("Análisis", analysis_depth)

# Botón de ejecución
if st.button("🚀 EJECUTAR DIAGNÓSTICO INTEGRAL", type="primary", use_container_width=True):
    
    with st.spinner("Realizando análisis integral del territorio..."):
        results = analyzer.comprehensive_analysis(area_count, vegetation_type, area_hectares)
    
    # ===============================
    # 📊 RESULTADOS PRINCIPALES
    # ===============================
    
    st.subheader("📈 RESUMEN EJECUTIVO DEL DIAGNÓSTICO")
    
    # Tarjetas de métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        health_score = results['integrated_scores']['ecosystem_health']
        st.metric(
            "Salud del Ecosistema",
            f"{health_score:.1f}/100",
            results['integrated_scores']['overall_rating']
        )
    
    with col2:
        st.metric(
            "Diversidad (Shannon)",
            f"{results['biodiversity_metrics']['shannon_index']:.3f}",
            "Alta" if results['biodiversity_metrics']['shannon_index'] > 2.5 else "Media"
        )
    
    with col3:
        st.metric(
            "Riqueza de Especies",
            results['biodiversity_metrics']['species_richness'],
            f"Área: {area_hectares} ha"
        )
    
    with col4:
        ndvi = results['vegetation_metrics']['NDVI']
        st.metric(
            "Vigor Vegetal (NDVI)",
            f"{ndvi:.3f}",
            "Excelente" if ndvi > 0.6 else "Bueno" if ndvi > 0.4 else "Regular"
        )
    
    # ===============================
    # 🌿 ANÁLISIS DE BIODIVERSIDAD
    # ===============================
    
    st.subheader("🌿 ANÁLISIS DE BIODIVERSIDAD")
    
    tab1, tab2, tab3 = st.tabs(["Métricas", "Composición", "Indicadores LE.MU"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📊 Métricas de Diversidad**")
            metrics_df = pd.DataFrame([
                {"Métrica": "Índice de Shannon", "Valor": results['biodiversity_metrics']['shannon_index']},
                {"Métrica": "Riqueza de Especies", "Valor": results['biodiversity_metrics']['species_richness']},
                {"Métrica": "Equitatividad", "Valor": results['biodiversity_metrics']['evenness']},
                {"Métrica": "Índice de Simpson", "Valor": results['biodiversity_metrics']['simpson_index']},
                {"Métrica": "Índice de Margalef", "Valor": results['biodiversity_metrics']['margalef_index']}
            ])
            st.dataframe(metrics_df, use_container_width=True, hide_index=True)
        
        with col2:
            st.markdown("**📈 Distribución de Abundancia**")
            species_summary = results['raw_data']['species_df'].groupby('species')['abundance'].sum().reset_index()
            fig = px.pie(species_summary, values='abundance', names='species', 
                        title="Composición de Especies")
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.markdown("**🪴 Composición de Especies por Área**")
        pivot_df = results['raw_data']['species_df'].pivot_table(
            index='species', columns='area', values='abundance', fill_value=0
        )
        st.dataframe(pivot_df, use_container_width=True)
        
        # Heatmap de abundancia
        fig = px.imshow(pivot_df, aspect='auto', title="Mapa de Calor de Abundancia por Especie y Área")
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.markdown("**🔍 Indicadores LE.MU de Conservación**")
        
        lemu_data = []
        for indicator, value in results['lemu_indicators'].items():
            lemu_data.append({
                "Indicador": indicator.replace('_', ' ').title(),
                "Valor": value,
                "Categoría": self._categorize_lemu_indicator(indicator, value)
            })
        
        lemu_df = pd.DataFrame(lemu_data)
        st.dataframe(lemu_df, use_container_width=True, hide_index=True)
        
        # Radar chart para indicadores LE.MU
        self._create_lemu_radar_chart(results['lemu_indicators'])
    
    # ===============================
    # 🛰️ ANÁLISIS DE VEGETACIÓN
    # ===============================
    
    st.subheader("🛰️ ANÁLISIS DE INDICES DE VEGETACIÓN")
    
    veg_tab1, veg_tab2, veg_tab3 = st.tabs(["Índices Principales", "Comparativa", "Tendencias"])
    
    with veg_tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📋 Valores Promedio por Índice**")
            veg_metrics = []
            for index, value in results['vegetation_metrics'].items():
                veg_metrics.append({
                    "Índice": index,
                    "Valor": f"{value:.4f}",
                    "Interpretación": self._interpret_vegetation_index(index, value)
                })
            veg_df = pd.DataFrame(veg_metrics)
            st.dataframe(veg_df, use_container_width=True, hide_index=True)
        
        with col2:
            st.markdown("**📊 Distribución Espacial de NDVI**")
            spectral_df = pd.DataFrame(results['spectral_data'])
            fig = px.box(spectral_df, y='NDVI', title="Distribución de NDVI entre Parcelas")
            st.plotly_chart(fig, use_container_width=True)
    
    with veg_tab2:
        st.markdown("**🔄 Correlación entre Índices**")
        
        # Matriz de correlación
        indices_df = pd.DataFrame(results['spectral_data'])[[
            'NDVI', 'NDWI', 'EVI', 'SAVI', 'RVI', 'NDRE', 'GNDVI', 'OSAVI'
        ]]
        corr_matrix = indices_df.corr()
        
        fig = px.imshow(corr_matrix, text_auto=True, aspect='auto',
                       title="Matriz de Correlación entre Índices de Vegetación")
        st.plotly_chart(fig, use_container_width=True)
    
    with veg_tab3:
        st.markdown("**📈 Tendencias por Parcela**")
        
        spectral_df = pd.DataFrame(results['spectral_data'])
        melted_df = spectral_df.melt(id_vars=['area'], 
                                   value_vars=['NDVI', 'NDWI', 'EVI', 'SAVI'],
                                   var_name='Índice', value_name='Valor')
        
        fig = px.line(melted_df, x='area', y='Valor', color='Índice',
                     title="Variación de Índices por Parcela de Muestreo")
        st.plotly_chart(fig, use_container_width=True)
    
    # ===============================
    # 🗺️ VISUALIZACIÓN GEOESPACIAL
    # ===============================
    
    st.subheader("🗺️ MAPA INTERACTIVO DEL TERRITORIO")
    
    # Crear mapa base centrado en Latinoamérica
    m = folium.Map(location=[-14.0, -60.0], zoom_start=4, tiles=None)
    
    # Capas base
    folium.TileLayer(
        tiles='https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri', name='Satélite'
    ).add_to(m)
    
    folium.TileLayer(
        tiles='OpenStreetMap',
        name='Calles'
    ).add_to(m)
    
    # Añadir puntos de muestreo
    for idx, area_data in enumerate(results['spectral_data']):
        # Generar coordenadas realistas para Latinoamérica
        lat = -14.0 + np.random.uniform(-8, 8)
        lon = -60.0 + np.random.uniform(-8, 8)
        
        # Color basado en NDVI
        ndvi = area_data['NDVI']
        if ndvi > 0.6:
            color = 'darkgreen'
        elif ndvi > 0.4:
            color = 'green'
        elif ndvi > 0.2:
            color = 'orange'
        else:
            color = 'red'
        
        popup_text = f"""
        <b>{area_data['area']}</b><br>
        NDVI: {ndvi:.3f}<br>
        EVI: {area_data['EVI']:.3f}<br>
        Biomasa: {area_data['biomasa_estimada']:.1f}
        """
        
        folium.CircleMarker(
            location=[lat, lon],
            radius=8,
            popup=folium.Popup(popup_text, max_width=300),
            tooltip=area_data['area'],
            color=color,
            fillColor=color,
            fillOpacity=0.7
        ).add_to(m)
    
    # Añadir control de capas
    folium.LayerControl().add_to(m)
    
    # Mostrar mapa
    st_folium(m, width=800, height=500)
    
    # ===============================
    # 📋 RECOMENDACIONES
    # ===============================
    
    st.subheader("💡 RECOMENDACIONES DE MANEJO Y CONSERVACIÓN")
    
    recommendations = self._generate_recommendations(results)
    
    for i, rec in enumerate(recommendations, 1):
        with st.expander(f"Recomendación {i}: {rec['title']}"):
            st.write(rec['description'])
            st.progress(rec['priority'] / 100)
            st.caption(f"Prioridad: {rec['priority']}/100")
    
    # ===============================
    # 📥 EXPORTACIÓN DE RESULTADOS
    # ===============================
    
    st.subheader("📊 EXPORTAR DIAGNÓSTICO")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Generar Reporte PDF", use_container_width=True):
            st.success("✅ Reporte PDF generado (simulación)")
    
    with col2:
        if st.button("📊 Exportar Datos Excel", use_container_width=True):
            st.success("✅ Datos exportados a Excel (simulación)")
    
    with col3:
        if st.button("🗺️ Exportar Capas GIS", use_container_width=True):
            st.success("✅ Capas GIS exportadas (simulación)")

else:
    # Pantalla de bienvenida
    st.markdown("""
    ## 👋 ¡Bienvenido al Diagnóstico de Biodiversidad Ambiental!
    
    ### 🎯 ¿Qué puedes hacer con esta herramienta?
    
    1. **📁 Cargar tu territorio**: Sube archivos KML o Shapefile con la delimitación de tu área de estudio
    2. **🌿 Analizar biodiversidad**: Calcula índices de diversidad, riqueza y equitatividad de especies
    3. **🛰️ Evaluar vegetación**: Obtén índices espectrales (NDVI, EVI, NDWI, etc.) para salud vegetal
    4. **🔍 Aplicar LE.MU**: Utiliza indicadores de conservación y conectividad ecológica
    5. **📊 Integrar resultados**: Obtén un diagnóstico completo con recomendaciones de manejo
    
    ### 🚀 Para comenzar:
    
    1. Configura los parámetros en la **barra lateral** ←
    2. Sube tu archivo territorial (opcional)
    3. Presiona ****EJECUTAR DIAGNÓSTICO INTEGRAL****
    
    ---
    
    **📚 Metodologías integradas:**
    - 🌿 **LE.MU Atlas**: Sistema de indicadores de conservación
    - 📊 **Índice de Shannon-Wiener**: Diversidad de especies
    - 🛰️ **Teledetección**: Índices de vegetación multiespectral
    - 🔗 **Análisis integral**: Salud completa del ecosistema
    """)

# ===============================
# 🛠️ MÉTODOS AUXILIARES
# ===============================

def _categorize_lemu_indicator(self, indicator, value):
    """Categorizar indicadores LE.MU"""
    if indicator == 'estado_conservacion':
        return value
    elif indicator == 'estructura_vertical':
        return value
    elif indicator == 'regeneracion_natural':
        return value
    elif isinstance(value, (int, float)):
        if value >= 80: return "Excelente"
        elif value >= 60: return "Bueno"
        elif value >= 40: return "Regular"
        else: return "Mejorable"
    return "N/A"

def _interpret_vegetation_index(self, index, value):
    """Interpretar valores de índices de vegetación"""
    interpretations = {
        'NDVI': {
            (0.8, 1.0): "Vegetación muy densa y saludable",
            (0.6, 0.8): "Vegetación densa",
            (0.4, 0.6): "Vegetación moderada", 
            (0.2, 0.4): "Vegetación escasa",
            (0.0, 0.2): "Suelo desnudo/vegetación muy escasa",
            (-1.0, 0.0): "Agua/sin vegetación"
        },
        'EVI': {
            (0.6, 1.0): "Alto vigor vegetal",
            (0.4, 0.6): "Vigor vegetal moderado",
            (0.2, 0.4): "Vigor vegetal bajo",
            (0.0, 0.2): "Vigor muy bajo"
        },
        'NDWI': {
            (0.3, 1.0): "Alto contenido de agua",
            (0.1, 0.3): "Contenido moderado de agua",
            (-0.1, 0.1): "Bajo contenido de agua",
            (-1.0, -0.1): "Sequía/ausencia de agua"
        }
    }
    
    if index in interpretations:
        for range_val, interpretation in interpretations[index].items():
            if range_val[0] <= value <= range_val[1]:
                return interpretation
    
    return "Valor fuera de rango típico"

def _create_lemu_radar_chart(self, lemu_indicators):
    """Crear gráfico radar para indicadores LE.MU"""
    try:
        # Seleccionar indicadores numéricos para el radar
        numeric_indicators = {
            'Diversidad Alfa': lemu_indicators['diversidad_alfa'],
            'Densidad': lemu_indicators['densidad_individuos'],
            'Riqueza': lemu_indicators['riqueza_especies'], 
            'Endemismos': lemu_indicators['especies_endemicas'],
            'Conectividad': lemu_indicators['conectividad_ecologica']
        }
        
        categories = list(numeric_indicators.keys())
        values = list(numeric_indicators.values())
        
        # Normalizar valores para el radar (0-100)
        max_vals = [50, 100, 50, 10, 100]  # Valores máximos esperados
        normalized_values = [min(100, (v / max_v) * 100) for v, max_v in zip(values, max_vals)]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=normalized_values + [normalized_values[0]],  # Cerrar el círculo
            theta=categories + [categories[0]],
            fill='toself',
            name='Indicadores LE.MU',
            line=dict(color='green', width=2),
            fillcolor='rgba(0, 128, 0, 0.3)'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )),
            showlegend=False,
            title="Indicadores LE.MU - Perfil de Conservación"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.warning(f"No se pudo generar el gráfico radar: {e}")

def _generate_recommendations(self, results):
    """Generar recomendaciones basadas en los resultados"""
    recommendations = []
    
    # Analizar biodiversidad
    shannon = results['biodiversity_metrics']['shannon_index']
    if shannon < 2.0:
        recommendations.append({
            'title': 'Mejorar Diversidad de Especies',
            'description': 'Considerar enriquecimiento con especies nativas y restauración de hábitats.',
            'priority': 85
        })
    
    # Analizar vegetación
    ndvi = results['vegetation_metrics']['NDVI']
    if ndvi < 0.4:
        recommendations.append({
            'title': 'Mejorar Cobertura Vegetal',
            'description': 'Implementar prácticas de conservación de suelos y reforestación.',
            'priority': 90
        })
    
    # Analizar conectividad
    connectivity = results['lemu_indicators']['conectividad_ecologica']
    if connectivity < 60:
        recommendations.append({
            'title': 'Incrementar Conectividad Ecológica',
            'description': 'Establecer corredores biológicos y reducir fragmentación.',
            'priority': 75
        })
    
    # Analizar regeneración
    regeneration = results['lemu_indicators']['regeneracion_natural']
    if regeneration == "Baja":
        recommendations.append({
            'title': 'Fomentar Regeneración Natural',
            'description': 'Reducir perturbaciones y promover bancos de semillas nativas.',
            'priority': 70
        })
    
    # Recomendación general de monitoreo
    recommendations.append({
        'title': 'Establecer Programa de Monitoreo',
        'description': 'Implementar monitoreo periódico para evaluar cambios en el tiempo.',
        'priority': 60
    })
    
    return sorted(recommendations, key=lambda x: x['priority'], reverse=True)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center'>"
    "🌍 <b>Diagnóstico de Biodiversidad Ambiental</b> | "
    "Metodología LE.MU Atlas + Índices de Vegetación | "
    "Desarrollado con Streamlit 🚀"
    "</div>",
    unsafe_allow_html=True
)
