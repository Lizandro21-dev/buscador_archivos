"""
GestorHistorial - Módulo para gestionar el historial de búsquedas del usuario
Mantiene un registro persistente de las búsquedas realizadas, ordenado alfabéticamente
y limitado a un máximo de búsquedas para evitar saturación.
"""

import json
import os
from typing import List, Optional


class GestorHistorial:
    """
    Administrador del historial de búsquedas del usuario.
    
    Características:
    - Almacenamiento persistente en archivo JSON
    - Ordenamiento alfabético automático (case-insensitive)
    - Sin duplicados
    - Límite configurable de búsquedas
    - Búsqueda por coincidencias parciales
    """
    
    # Constantes de configuración
    MAX_BUSQUEDAS = 100
    ARCHIVO_DEFAULT = 'historial_busquedas.json'
    
    def __init__(self, archivo: str = ARCHIVO_DEFAULT):
        """
        Inicializa el gestor de historial.
        
        Args:
            archivo: Ruta del archivo JSON donde se persiste el historial
        """
        self.archivo = archivo
        self.historial: List[str] = self._cargar_historial()
    
    def _cargar_historial(self) -> List[str]:
        """
        Carga el historial desde el archivo JSON.
        
        Returns:
            Lista de términos de búsqueda ordenados alfabéticamente.
            Lista vacía si el archivo no existe o hay error de lectura.
        """
        if not os.path.exists(self.archivo):
            return []
        
        try:
            with open(self.archivo, 'r', encoding='utf-8') as f:
                historial_cargado = json.load(f)
                # Asegurar que el historial esté ordenado alfabéticamente
                return self._ordenar_lista(historial_cargado)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error al cargar historial: {e}")
            return []
    
    def _guardar_historial(self) -> bool:
        """
        Persiste el historial en el archivo JSON.
        
        Returns:
            True si se guardó exitosamente, False en caso contrario
        """
        try:
            # Ordenar antes de guardar para mantener consistencia
            self.historial = self._ordenar_lista(self.historial)
            
            with open(self.archivo, 'w', encoding='utf-8') as f:
                json.dump(self.historial, f, ensure_ascii=False, indent=2)
            return True
        except IOError as e:
            print(f"Error al guardar historial: {e}")
            return False
    
    @staticmethod
    def _ordenar_lista(lista: List[str]) -> List[str]:
        """
        Ordena una lista de strings alfabéticamente (case-insensitive).
        
        Args:
            lista: Lista de strings a ordenar
            
        Returns:
            Lista ordenada alfabéticamente
        """
        return sorted(lista, key=lambda x: x.lower())
    
    def agregar(self, termino: str) -> bool:
        """
        Agrega un término al historial.
        
        - Elimina espacios en blanco al inicio/final
        - Evita duplicados (si existe, lo remueve para agregarlo al final)
        - Mantiene un límite máximo de búsquedas
        - Ordena alfabéticamente
        - Guarda automáticamente
        
        Args:
            termino: Término de búsqueda a agregar
            
        Returns:
            True si se agregó exitosamente, False si el término está vacío
        """
        termino = termino.strip()
        if not termino:
            return False
        
        # Eliminar si ya existe para evitar duplicados
        if termino in self.historial:
            self.historial.remove(termino)
        
        # Agregar el nuevo término
        self.historial.append(termino)
        
        # Aplicar límite de búsquedas (mantener las más recientes)
        if len(self.historial) > self.MAX_BUSQUEDAS:
            self.historial = self.historial[-self.MAX_BUSQUEDAS:]
        
        # Ordenar alfabéticamente
        self.historial = self._ordenar_lista(self.historial)
        
        # Persistir cambios
        return self._guardar_historial()
    
    def buscar_coincidencias(self, texto: str) -> List[str]:
        """
        Busca términos que contengan el texto proporcionado.
        
        La búsqueda es case-insensitive y busca coincidencias parciales.
        Si no hay texto, retorna todo el historial.
        
        Args:
            texto: Texto a buscar dentro de los términos del historial
            
        Returns:
            Lista de términos que contienen el texto, ordenados alfabéticamente
        """
        if not texto:
            # Retornar todo el historial ordenado si no hay criterio de búsqueda
            return self._ordenar_lista(self.historial)
        
        texto_lower = texto.lower()
        # Filtrar coincidencias usando búsqueda case-insensitive
        coincidencias = [
            termino for termino in self.historial 
            if texto_lower in termino.lower()
        ]
        
        return self._ordenar_lista(coincidencias)
    
    def limpiar(self) -> bool:
        """
        Elimina todos los términos del historial.
        
        Returns:
            True si se limpió exitosamente
        """
        self.historial = []
        return self._guardar_historial()
    
    def obtener_todos(self) -> List[str]:
        """
        Obtiene todo el historial ordenado alfabéticamente.
        
        Returns:
            Lista completa del historial ordenado
        """
        return self._ordenar_lista(self.historial)
    
    def total_busquedas(self) -> int:
        """
        Obtiene la cantidad total de búsquedas en el historial.
        
        Returns:
            Número de términos en el historial
        """
        return len(self.historial)
    
    def eliminar_termino(self, termino: str) -> bool:
        """
        Elimina un término específico del historial.
        
        Args:
            termino: Término a eliminar
            
        Returns:
            True si se eliminó exitosamente, False si no se encontró
        """
        if termino in self.historial:
            self.historial.remove(termino)
            return self._guardar_historial()
        return False