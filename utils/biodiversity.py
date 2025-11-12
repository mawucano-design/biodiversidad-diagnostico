import numpy as np
import pandas as pd
from scipy import stats
import math

class BiodiversityAnalyzer:
    """Analizador de métricas de biodiversidad"""
    
    def __init__(self):
        self.species_pool = [
            'Quercus robur', 'Fagus sylvatica', 'Pinus sylvestris', 
            'Acer pseudoplatanus', 'Betula pendula', 'Alnus glutinosa',
            'Pinus pinaster', 'Quercus ilex', 'Quercus suber',
            'Juniperus communis', 'Castanea sativa', 'Populus nigra',
            'Fraxinus excelsior', 'Ulmus minor', 'Salix alba',
            'Corylus avellana', 'Crataegus monogyna', 'Rubus fruticosus',
            'Hedera helix', 'Rosa canina', 'Prunus spinosa'
        ]
    
    def shannon_index(self, abundances):
        """Calcula el índice de Shannon-Wiener"""
        total = sum(abundances)
        if total == 0:
            return 0.0
        
        proportions = [abundance / total for abundance in abundances if abundance > 0]
        return -sum(p * math.log(p) for p in proportions)
    
    def simpson_index(self, abundances):
        """Calcula el índice de Simpson"""
        total = sum(abundances)
        if total == 0:
            return 0.0
        
        return sum((abundance / total) ** 2 for abundance in abundances)
    
    def species_richness(self, abundances):
        """Calcula la riqueza de especies"""
        return sum(1 for abundance in abundances if abundance > 0)
    
    def evenness(self, shannon_index, species_richness):
        """Calcula la equitatividad de Pielou"""
        if species_richness <= 1:
            return 1.0
        return shannon_index / math.log(species_richness)
    
    def simulate_species_data(self, geo_data, method="Basado en área", max_species=15):
        """Simula datos de especies basados en datos geográficos"""
        species_data = []
        
        # Seleccionar especies del pool
        selected_species = np.random.choice(
            self.species_pool, 
            size=min(max_species, len(self.species_pool)), 
            replace=False
        )
        
        for _, feature in geo_data.iterrows():
            # Calcular área (simplificado)
            area_factor = self._calculate_area_factor(feature.geometry)
            
            for species in selected_species:
                # Calcular abundancia basada en el método seleccionado
                if method == "Basado en área":
                    abundance = self._area_based_abundance(species, area_factor)
                elif method == "Basado en tipo de vegetación":
                    abundance = self._vegetation_based_abundance(species, feature)
                else:  # Aleatorio
                    abundance = self._random_abundance(species)
                
                species_data.append({
                    'species': species,
                    'abundance': int(abundance),
                    'frequency': round(np.random.uniform(0.1, 1.0), 3),
                    'area': f"Área {_}" if 'name' not in feature else feature['name']
                })
        
        return species_data
    
    def _calculate_area_factor(self, geometry):
        """Calcula factor de área (simplificado)"""
        try:
            area = geometry.area
            return min(area * 1000, 1.0)  # Normalizar
        except:
            return 0.5
    
    def _area_based_abundance(self, species, area_factor):
        """Abundancia basada en área"""
        base_abundance = {
            'Quercus robur': 50, 'Fagus sylvatica': 40, 'Pinus sylvestris': 60,
            'Acer pseudoplatanus': 30, 'Betula pendula': 35, 'Alnus glutinosa': 25
        }
        base = base_abundance.get(species, 20)
        return max(1, int(base * area_factor * np.random.lognormal(0, 0.5)))
    
    def _vegetation_based_abundance(self, species, feature):
        """Abundancia basada en tipo de vegetación (simulado)"""
        return max(1, int(np.random.lognormal(3, 1)))
    
    def _random_abundance(self, species):
        """Abundancia aleatoria"""
        return np.random.poisson(25) + 1
    
    def analyze_biodiversity(self, species_data):
        """Analiza biodiversidad a partir de datos de especies"""
        df = pd.DataFrame(species_data)
        
        if df.empty:
            return {
                'shannon_index': 0,
                'species_richness': 0,
                'total_abundance': 0,
                'evenness': 0,
                'simpson_index': 0
            }
        
        # Agrupar por especie y sumar abundancias
        species_abundances = df.groupby('species')['abundance'].sum().values
        
        # Calcular métricas
        shannon = self.shannon_index(species_abundances)
        richness = self.species_richness(species_abundances)
        total_abundance = sum(species_abundances)
        evenness_val = self.evenness(shannon, richness)
        simpson = self.simpson_index(species_abundances)
        
        return {
            'shannon_index': shannon,
            'species_richness': richness,
            'total_abundance': total_abundance,
            'evenness': evenness_val,
            'simpson_index': simpson
        }
