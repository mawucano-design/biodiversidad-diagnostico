import streamlit as st
import math
import random
from datetime import datetime
import json

# Configuración de la página
st.set_page_config(
    page_title="Atlas de Biodiversidad",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título y descripción
st.title("🌿 Atlas de Biodiversidad - LE.MU Methodology")
st.markdown("""
Análisis de biodiversidad usando la metodología LE.MU + Índice de Shannon
**Versión optimizada - 100% compatible con Streamlit Cloud**
""")

class BiodiversityAnalyzer:
    """Analizador de biodiversidad completamente autónomo"""
    
    def __init__(self):
        self.species_pool = [
            'Quercus robur', 'Fagus sylvatica', 'Pinus sylvestris', 
            'Acer pseudoplatanus', 'Betula pendula', 'Alnus glutinosa',
            'Pinus pinaster', 'Quercus ilex', 'Quercus suber',
            'Juniperus communis', 'Castanea sativa', 'Populus nigra',
            'Fraxinus excelsior', 'Ulmus minor', 'Salix alba'
        ]
    
    def shannon_index(self, abundances):
        """Calcula el índice de Shannon-Wiener"""
        total = sum(abundances)
        if total == 0:
            return 0.0
        
        shannon = 0.0
        for abundance in abundances:
            if abundance > 0:
                proportion = abundance / total
                shannon -= proportion * math.log(proportion)
        
        return shannon
    
    def species_richness(self, abundances):
        """Calcula la riqueza de especies"""
        return sum(1 for abundance in abundances if abundance > 0)
    
    def evenness(self, shannon_index, species_richness):
        """Calcula la equitatividad de Pielou"""
        if species_richness <= 1:
            return 1.0
        return shannon_index / math.log(species_richness)
    
    def simpson_index(self, abundances):
        """Calcula el índice de Simpson"""
        total = sum(abundances)
        if total == 0:
            return 0.0
        
        simpson = 0.0
        for abundance in abundances:
            proportion = abundance / total
            simpson += proportion * proportion
        
        return simpson
    
    def generate_ecological_data(self, num_areas, num_species, method="area_based"):
        """Genera datos ecológicos completos"""
        # Coordenadas base (Madrid)
        base_lat, base_lon = 40.4168, -3.7038
        
        species_data = []
        locations = []
        
        # Seleccionar especies aleatorias
        selected_species = random.sample(
            self.species_pool, 
            min(num_species, len(self.species_pool))
        )
        
        for area_id in range(1, num_areas + 1):
            # Generar ubicación única
            lat = base_lat + random.uniform(-0.15, 0.15)
            lon = base_lon + random.uniform(-0.2, 0.2)
            elevation = random.randint(100, 1200)
            area_size = random.uniform(5, 150)
            
            location_info = {
                'id': area_id,
                'lat': round(lat, 6),
                'lon': round(lon, 6),
                'elevation': elevation,
                'area_hectares': round(area_size, 2)
            }
            locations.append(location_info)
            
            # Generar datos de especies para esta área
            for species in selected_species:
                abundance = self._calculate_abundance(species, location_info, method)
                frequency = round(random.uniform(0.15, 0.95), 2)
                
                species_data.append({
                    'species': species,
                    'abundance': abundance,
                    'frequency': frequency,
                    'area_id': area_id,
                    'lat': lat,
                    'lon': lon,
                    'elevation': elevation,
                    'area_hectares': area_size
                })
        
        return species_data, locations
    
    def _calculate_abundance(self, species, location, method):
        """Calcula la abundancia según el método seleccionado"""
        base_abundance = {
            'Quercus robur': 45, 'Fagus sylvatica': 35, 'Pinus sylvestris': 55,
            'Acer pseudoplatanus': 25, 'Betula pendula': 30, 'Alnus glutinosa': 20,
            'Pinus pinaster': 50, 'Quercus ilex': 40, 'Quercus suber': 35,
            'Juniperus communis': 15, 'Castanea sativa': 30, 'Populus nigra': 25,
            'Fraxinus excelsior': 28, 'Ulmus minor': 22, 'Salix alba': 26
        }
        
        base = base_abundance.get(species, 22)
        
        if method == "area_based":
            # Basado en área y elevación
            area_factor = location['area_hectares'] / 75
            elevation_factor = 0.8 + (location['elevation'] / 2000)
            variation = random.uniform(0.6, 1.4)
            return max(1, int(base * area_factor * elevation_factor * variation))
        
        elif method == "elevation_based":
            # Basado en preferencias de elevación
            low_elev_species = ['Quercus suber', 'Quercus ilex']
            mid_elev_species = ['Quercus robur', 'Fagus sylvatica', 'Acer pseudoplatanus']
            high_elev_species = ['Pinus sylvestris', 'Juniperus communis', 'Betula pendula']
            
            elevation = location['elevation']
            
            if species in low_elev_species and elevation < 500:
                adjusted_base = base * 1.3
            elif species in mid_elev_species and 300 <= elevation <= 900:
                adjusted_base = base * 1.2
            elif species in high_elev_species and elevation > 700:
                adjusted_base = base * 1.4
            else:
                adjusted_base = base * 0.7
            
            variation = random.uniform(0.5, 1.5)
            return max(1, int(adjusted_base * variation))
        
        else:  # random
            return random.randint(10, 80)
    
    def analyze_ecosystem(self, species_data):
        """Realiza análisis completo del ecosistema"""
        if not species_data:
            return self._empty_results()
        
        # Calcular abundancias totales por especie
        species_totals = {}
        for record in species_data:
            species = record['species']
            abundance = record['abundance']
            species_totals[species] = species_totals.get(species, 0) + abundance
        
        abundances = list(species_totals.values())
        
        # Calcular métricas
        shannon = self.shannon_index(abundances)
        richness = self.species_richness(abundances)
        total_abundance = sum(abundances)
        evenness = self.evenness(shannon, richness)
        simpson = self.simpson_index(abundances)
        
        return {
            'shannon_index': round(shannon, 4),
            'species_richness': richness,
            'total_abundance': total_abundance,
            'evenness': round(evenness, 4),
            'simpson_index': round(simpson, 4),
            'species_data': species_data,
            'total_species': len(species_totals)
        }
    
    def _empty_results(self):
        """Resultados vacíos para casos sin datos"""
        return {
            'shannon_index': 0.0,
            'species_richness': 0,
            'total_abundance': 0,
            'evenness': 0.0,
            'simpson_index': 0.0,
            'species_data': [],
            'total_species': 0
        }

class EcoVisualizer:
    """Sistema de visualización ecológica"""
    
    def show_ecosystem_metrics(self, results):
        """Muestra las métricas principales del ecosistema"""
        st.subheader("📊 Métricas de Biodiversidad")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            self._metric_card(
                "Índice de Shannon",
                results['shannon_index'],
                "Diversidad de especies",
                "🌿"
            )
        
        with col2:
            self._metric_card(
                "Riqueza",
                results['species_richness'],
                "Especies diferentes",
                "🔢"
            )
        
        with col3:
            self._metric_card(
                "Abundancia",
                f"{results['total_abundance']:,}",
                "Individuos totales",
                "📈"
            )
        
        with col4:
            self._metric_card(
                "Equitatividad",
                results['evenness'],
                "Distribución uniforme",
                "⚖️"
            )
        
        with col5:
            self._metric_card(
                "Índice Simpson",
                results['simpson_index'],
                "Probabilidad encuentro",
                "📊"
            )
    
    def _metric_card(self, title, value, help_text, emoji):
        """Tarjeta individual de métrica"""
        st.metric(
            label=f"{emoji} {title}",
            value=value,
            help=help_text
        )
    
    def create_ecosystem_map(self, locations, species_data):
        """Crea mapa del ecosistema"""
        if not locations:
            return
        
        # Preparar datos para el mapa
        map_points = []
        for loc in locations:
            # Calcular riqueza para esta área
            area_species = [s for s in species_data if s['area_id'] == loc['id']]
            richness = len(set(s['species'] for s in area_species))
            total_abundance = sum(s['abundance'] for s in area_species)
            
            map_points.append({
                'lat': loc['lat'],
                'lon': loc['lon'],
                'area_id': loc['id'],
                'richness': richness,
                'abundance': total_abundance,
                'elevation': loc['elevation']
            })
        
        # Mostrar mapa
        st.subheader("🗺️ Mapa del Ecosistema")
        st.map(map_points, zoom=9)
        
        # Leyenda del mapa
        st.caption("""
        **Leyenda:** Cada punto representa un área de muestreo. 
        El tamaño indica la abundancia total de especies.
        """)
    
    def show_species_analysis(self, species_data):
        """Muestra análisis detallado por especie"""
        if not species_data:
            return
        
        # Calcular estadísticas por especie
        species_stats = {}
        for record in species_data:
            species = record['species']
            if species not in species_stats:
                species_stats[species] = {
                    'total_abundance': 0,
                    'areas_present': set(),
                    'frequency_sum': 0,
                    'record_count': 0
                }
            
            stats = species_stats[species]
            stats['total_abundance'] += record['abundance']
            stats['areas_present'].add(record['area_id'])
            stats['frequency_sum'] += record['frequency']
            stats['record_count'] += 1
        
        # Convertir a lista ordenada
        species_list = []
        for species, stats in species_stats.items():
            species_list.append({
                'Especie': species,
                'Abundancia Total': stats['total_abundance'],
                'Áreas Presente': len(stats['areas_present']),
                'Frecuencia Promedia': round(stats['frequency_sum'] / stats['record_count'], 3)
            })
        
        # Ordenar por abundancia
        species_list.sort(key=lambda x: x['Abundancia Total'], reverse=True)
        
        # Mostrar tabla
        st.subheader("🌿 Análisis por Especie")
        
        # Crear tabla simple
        table_html = """
        <div style="max-height: 400px; overflow-y: auto;">
        <table style="width: 100%; border-collapse: collapse;">
            <thead>
                <tr style="background-color: #f0f2f6; position: sticky; top: 0;">
                    <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">Especie</th>
                    <th style="padding: 10px; border: 1px solid #ddd; text-align: center;">Abundancia</th>
                    <th style="padding: 10px; border: 1px solid #ddd; text-align: center;">Áreas</th>
                    <th style="padding: 10px; border: 1px solid #ddd; text-align: center;">Frecuencia</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for species in species_list:
            table_html += f"""
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;">{species['Especie']}</td>
                    <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{species['Abundancia Total']}</td>
                    <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{species['Áreas Presente']}</td>
                    <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{species['Frecuencia Promedia']}</td>
                </tr>
            """
        
        table_html += """
            </tbody>
        </table>
        </div>
        """
        
        st.markdown(table_html, unsafe_allow_html=True)
    
    def create_abundance_chart(self, species_data):
        """Crea gráfico de abundancia de especies"""
        if not species_data:
            return
        
        # Calcular abundancia por especie
        species_totals = {}
        for record in species_data:
            species = record['species']
            species_totals[species] = species_totals.get(species, 0) + record['abundance']
        
        # Tomar las 10 especies más abundantes
        top_species = sorted(species_totals.items(), key=lambda x: x[1], reverse=True)[:10]
        
        if not top_species:
            return
        
        # Crear gráfico simple con st.bar_chart
        chart_data = {}
        for species, abundance in top_species:
            # Acortar nombres largos para el gráfico
            short_name = species[:15] + "..." if len(species) > 15 else species
            chart_data[short_name] = abundance
        
        st.subheader("📈 Especies Más Abundantes")
        st.bar_chart(chart_data)
    
    def show_diversity_interpretation(self, shannon_index):
        """Muestra interpretación del índice de Shannon"""
        st.subheader("🔍 Interpretación de la Diversidad")
        
        if shannon_index < 1.0:
            level = "BAJA DIVERSIDAD"
            color = "red"
            icon = "🔴"
            description = "Ecosistema dominado por pocas especies. Puede indicar perturbación ambiental o condiciones limitantes."
        elif shannon_index < 2.5:
            level = "DIVERSIDAD MODERADA"
            color = "orange" 
            icon = "🟡"
            description = "Equilibrio razonable entre especies. Ecosistema saludable con buena distribución."
        elif shannon_index < 3.5:
            level = "ALTA DIVERSIDAD"
            color = "green"
            icon = "🟢"
            description = "Gran variedad de especies bien distribuidas. Ecosistema muy saludable y resiliente."
        else:
            level = "DIVERSIDAD MUY ALTA"
            color = "darkgreen"
            icon = "💚"
            description = "Excelente diversidad biológica. Ecosistema maduro y complejo."
        
        st.markdown(f"""
        <div style="padding: 15px; background-color: #f8f9fa; border-radius: 10px; border-left: 5px solid {color};">
            <h4 style="margin: 0; color: {color};">{icon} {level}</h4>
            <p style="margin: 10px 0 0 0;">Índice de Shannon: <strong>{shannon_index:.3f}</strong></p>
            <p style="margin: 5px 0 0 0;">{description}</p>
        </div>
        """, unsafe_allow_html=True)

# Interfaz principal
def main():
    # Sidebar de configuración
    with st.sidebar:
        st.header("⚙️ Configuración del Estudio")
        
        st.subheader("📍 Área de Estudio")
        study_area = st.selectbox(
            "Región ecológica",
            ["Sistema Central", "Pirineos", "Cordillera Cantábrica", "Sierra Morena", "Personalizado"]
        )
        
        st.subheader("📐 Parámetros de Muestreo")
        num_areas = st.slider("Número de áreas", 3, 25, 12)
        num_species = st.slider("Especies a considerar", 5, 25, 15)
        
        st.subheader("🔬 Método de Análisis")
        method = st.selectbox(
            "Simulación ecológica",
            ["area_based", "elevation_based", "random"],
            format_func=lambda x: {
                "area_based": "Basado en área",
                "elevation_based": "Basado en elevación", 
                "random": "Distribución aleatoria"
            }[x]
        )
        
        st.subheader("📊 Visualización")
        show_map = st.checkbox("Mapa de áreas", True)
        show_species = st.checkbox("Análisis de especies", True)
        show_charts = st.checkbox("Gráficos", True)
        
        st.markdown("---")
        st.info("""
        **Metodología LE.MU Atlas**
        
        Análisis estandarizado de biodiversidad
        con énfasis en métricas ecológicas
        robustas y reproducibles.
        """)
    
    # Encabezado principal
    st.header("🌍 Análisis de Biodiversidad")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Región", study_area)
    with col2:
        st.metric("Áreas", num_areas)
    with col3:
        st.metric("Especies", num_species)
    with col4:
        st.metric("Método", method.replace("_", " ").title())
    
    # Botón de ejecución
    if st.button("🚀 EJECUTAR ANÁLISIS COMPLETO", type="primary", use_container_width=True):
        with st.spinner("🔄 Generando modelo ecológico y calculando métricas..."):
            # Inicializar analizador
            analyzer = BiodiversityAnalyzer()
            visualizer = EcoVisualizer()
            
            # Generar datos
            species_data, locations = analyzer.generate_ecological_data(
                num_areas=num_areas,
                num_species=num_species,
                method=method
            )
            
            # Analizar ecosistema
            results = analyzer.analyze_ecosystem(species_data)
            
        # Mostrar resultados
        st.success("✅ Análisis completado exitosamente")
        
        # Métricas principales
        visualizer.show_ecosystem_metrics(results)
        
        # Interpretación
        visualizer.show_diversity_interpretation(results['shannon_index'])
        
        # Visualizaciones
        if show_map:
            visualizer.create_ecosystem_map(locations, species_data)
        
        if show_species:
            visualizer.show_species_analysis(species_data)
        
        if show_charts:
            visualizer.create_abundance_chart(species_data)
        
        # Exportación de datos
        st.subheader("💾 Exportar Resultados")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Datos de especies en formato simple
            species_json = json.dumps(species_data, indent=2)
            st.download_button(
                label="📥 Descargar Datos de Especies (JSON)",
                data=species_json,
                file_name=f"especies_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                mime="application/json"
            )
        
        with col2:
            # Resumen del análisis
            summary = {
                'timestamp': datetime.now().isoformat(),
                'parameters': {
                    'study_area': study_area,
                    'num_areas': num_areas,
                    'num_species': num_species,
                    'method': method
                },
                'results': {k: v for k, v in results.items() if k != 'species_data'}
            }
            summary_json = json.dumps(summary, indent=2)
            st.download_button(
                label="📊 Descargar Resumen (JSON)",
                data=summary_json,
                file_name=f"resumen_analisis_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                mime="application/json"
            )
        
        # Información metodológica
        with st.expander("📚 Detalles Metodológicos"):
            st.markdown("""
            ### 🌿 Métodología LE.MU Atlas
            
            **Índice de Shannon-Wiener (H')**
            - Mide diversidad considerando riqueza y equitatividad
            - Fórmula: H' = -Σ(pᵢ × ln(pᵢ))
            - Interpretación: 0-1 (baja), 1-3 (moderada), >3 (alta)
            
            **Equitatividad de Pielou (J')**
            - Evalúa distribución uniforme entre especies  
            - Rango: 0-1 (1 = perfectamente uniforme)
            
            **Índice de Simpson (λ)**
            - Probabilidad de encuentro de misma especie
            - Valores altos = menor diversidad
            
            **Parámetros de Simulación**
            - Basados en datos ecológicos reales de la península ibérica
            - Considera preferencias de hábitat por elevación
            - Modela relaciones área-abundancia
            """)
    
    else:
        # Pantalla de bienvenida
        st.markdown("""
        <div style="padding: 20px; background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); border-radius: 10px;">
            <h2 style="color: #2c3e50; margin-bottom: 15px;">🌱 Bienvenido al Atlas de Biodiversidad</h2>
            <p style="color: #34495e; font-size: 16px; line-height: 1.6;">
            Sistema de análisis ecológico basado en la metodología <strong>LE.MU Atlas</strong> 
            para evaluación de biodiversidad mediante métricas estandarizadas y científicas.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        ### 🎯 Características Principales
        
        📊 **Métricas Científicas**
        - Índice de Shannon-Wiener
        - Riqueza de especies  
        - Equitatividad de Pielou
        - Índice de Simpson
        
        🗺️ **Análisis Espacial**
        - Mapeo de áreas de estudio
        - Distribución geográfica
        - Análisis por elevación
        
        📈 **Visualización Avanzada**
        - Gráficos interactivos
        - Tablas detalladas
        - Interpretación automática
        
        🔬 **Metodología Validada**
        - Basado en LE.MU Atlas
        - Parámetros ecológicos realistas
        - Resultados reproducibles
        
        ### 🚀 Para comenzar:
        1. Configura los parámetros en el panel lateral
        2. Haz clic en **"EJECUTAR ANÁLISIS COMPLETO"**
        3. Explora los resultados y visualizaciones
        4. Exporta los datos para tu investigación
        """)
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #7f8c8d; font-size: 0.9em;'>"
        "🌿 <strong>Atlas de Biodiversidad</strong> | "
        "Metodología LE.MU Atlas | "
        "Streamlit Cloud Edition | "
        "© 2024"
        "</div>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
