import json
import os


class GestorHistorial:
    """Maneja el historial de búsquedas del usuario"""
    
    def __init__(self, archivo='historial_busquedas.json'):
        # Ruta del archivo JSON donde se guarda el historial
        self.archivo = archivo
        # Lista que contiene todas las búsquedas
        self.historial = self.cargar_historial()
    
    def cargar_historial(self):
        """Carga el historial desde archivo JSON"""
        try:
            if os.path.exists(self.archivo):
                with open(self.archivo, 'r', encoding='utf-8') as f:
                    historial_cargado = json.load(f)
                    # Ordenar alfabéticamente (insensible a mayúsculas)
                    return sorted(historial_cargado, key=lambda x: x.lower())
            return []
        except Exception:
            return []
    
    def guardar_historial(self):
        """Guarda el historial en archivo JSON ordenado alfabéticamente"""
        try:
            # Ordenar antes de guardar
            self.historial = sorted(self.historial, key=lambda x: x.lower())
            with open(self.archivo, 'w', encoding='utf-8') as f:
                json.dump(self.historial, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def agregar(self, termino):
        """Agrega un término al historial sin duplicados"""
        termino = termino.strip()
        if not termino:
            return
        
        # Eliminar si ya existe
        if termino in self.historial:
            self.historial.remove(termino)
        
        # Agregar
        self.historial.append(termino)
        
        # Limitar a 100 búsquedas
        self.historial = self.historial[:100]
        
        # Ordenar alfabéticamente
        self.historial = sorted(self.historial, key=lambda x: x.lower())
        
        self.guardar_historial()
    
    def buscar_coincidencias(self, texto):
        """Busca términos que coincidan con el texto"""
        if not texto:
            # Mostrar todo el historial ordenado alfabéticamente
            return sorted(self.historial, key=lambda x: x.lower())
        
        texto_lower = texto.lower()
        # Filtrar coincidencias y ordenar alfabéticamente
        coincidencias = [h for h in self.historial if texto_lower in h.lower()]
        return sorted(coincidencias, key=lambda x: x.lower())
    
    def limpiar(self):
        """Limpia todo el historial"""
        self.historial = []
        self.guardar_historial()
    
    def obtener_todos(self):
        """Retorna todo el historial ordenado"""
        return sorted(self.historial, key=lambda x: x.lower())
    
    def total_busquedas(self):
        """Retorna cantidad de búsquedas en historial"""
        return len(self.historial)