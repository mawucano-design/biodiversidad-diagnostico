class FileHandler {
    constructor() {
        this.currentData = null;
        this.map = null;
    }

    initializeMap() {
        this.map = L.map('map').setView([40.4168, -3.7038], 6); // Centro en España
        
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(this.map);
    }

    // Manejar archivo KML
    async handleKMLFile(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            
            reader.onload = (e) => {
                try {
                    const kmlContent = e.target.result;
                    // En una implementación real, usaríamos una librería KML
                    // Por ahora simulamos datos geoespaciales
                    const geoData = this.parseKMLContent(kmlContent);
                    this.displayOnMap(geoData);
                    resolve(geoData);
                } catch (error) {
                    reject(error);
                }
            };
            
            reader.onerror = () => reject(new Error('Error reading KML file'));
            reader.readAsText(file);
        });
    }

    // Manejar archivo Shapefile (ZIP)
    async handleSHPFile(file) {
        return new Promise((resolve, reject) => {
            shp(file).then(geoData => {
                this.displayOnMap(geoData);
                resolve(geoData);
            }).catch(error => {
                reject(new Error('Error processing Shapefile: ' + error.message));
            });
        });
    }

    // Mostrar datos en el mapa
    displayOnMap(geoData) {
        // Limpiar capas anteriores
        if (this.map) {
            this.map.eachLayer(layer => {
                if (layer instanceof L.GeoJSON) {
                    this.map.removeLayer(layer);
                }
            });

            // Añadir nueva capa
            L.geoJSON(geoData, {
                style: {
                    color: '#4CAF50',
                    weight: 2,
                    fillColor: '#8BC34A',
                    fillOpacity: 0.3
                }
            }).addTo(this.map);

            // Ajustar vista al área de interés
            if (geoData.features && geoData.features.length > 0) {
                this.map.fitBounds(L.geoJSON(geoData).getBounds());
            }
        }
    }

    // Parsear contenido KML (simplificado)
    parseKMLContent(kmlContent) {
        // En una implementación real, usaríamos una librería como tokml o similar
        // Por ahora retornamos datos geoespaciales de ejemplo
        return {
            type: "FeatureCollection",
            features: [
                {
                    type: "Feature",
                    properties: {},
                    geometry: {
                        type: "Polygon",
                        coordinates: [[
                            [-3.711, 40.417], [-3.695, 40.417],
                            [-3.695, 40.427], [-3.711, 40.427],
                            [-3.711, 40.417]
                        ]]
                    }
                }
            ]
        };
    }
}
