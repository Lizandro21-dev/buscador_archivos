from PyQt5.QtCore import Qt, QTimer, QStringListModel
from PyQt5.QtWidgets import (QCompleter
)

# ========== AUTOCOMPLETADO Y HISTORIAL ==========

class autoHisto:
    
    def configurar_autocompletado(self):
        """
        Configura el sistema de autocompletado con el historial de búsquedas.
        
        Features:
        - Búsqueda case-insensitive
        - Coincidencias parciales
        - Máximo 20 sugerencias visibles
        - Popup estilizado
        """
        self.completer = QCompleter()
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchContains)
        self.completer.setMaxVisibleItems(20)
        
        # Configurar estilo del popup de sugerencias
        popup = self.completer.popup()
        popup.setMinimumWidth(600)
        popup.setMinimumHeight(400)
        popup.setStyleSheet("""
            QListView {
                background-color: #2B313F;
                color: white;
                border: 3px solid #E32D64;
                border-radius: 12px;
                padding: 10px;
                font-size: 16px;
                font-family: 'Segoe UI', Arial;
            }
            QListView::item {
                padding: 12px;
                border-radius: 8px;
                margin: 3px;
                min-height: 30px;
            }
            QListView::item:selected {
                background-color: #E32D64;
                color: white;
                font-weight: bold;
            }
            QListView::item:hover {
                background-color: #4a4a4c;
            }
        """)
        
        self.search_input.setCompleter(self.completer)
        self.actualizar_completer()
        self.configurar_eventos_seleccion()
    
    def actualizar_completer(self):
        """Actualiza el modelo del completer con el historial actual."""
        model = QStringListModel()
        model.setStringList(self.historial.obtener_todos())
        self.completer.setModel(model)
    
    def configurar_eventos_seleccion(self):
        """
        Configura eventos personalizados para el campo de búsqueda.
        Permite mostrar el historial al hacer clic o enfocar.
        """
        # Guardar eventos originales
        self.search_input_click_original = self.search_input.mousePressEvent
        self.search_input_focus_original = self.search_input.focusInEvent
        
        # Reemplazar con eventos personalizados
        self.search_input.mousePressEvent = self.on_search_input_click
        self.search_input.focusInEvent = self.on_search_input_focus
    
    def on_search_input_click(self, event):
        """
        Maneja el evento de clic en el campo de búsqueda.
        Muestra el historial completo si hay poco o ningún texto.
        """
        if len(self.search_input.text()) < 2:
            try:
                model = QStringListModel()
                model.setStringList(self.historial.obtener_todos())
                self.completer.setModel(model)
                self.completer.complete()
            except Exception as e:
                print(f"Error al mostrar historial: {e}")
        
        # Ejecutar evento original para mantener funcionalidad normal
        self.search_input_click_original(event)
    
    def on_search_input_focus(self, event):
        """
        Maneja el evento cuando el campo obtiene el foco.
        Muestra el historial si está vacío.
        """
        self.search_input_focus_original(event)
        
        if not self.search_input.text():
            try:
                model = QStringListModel()
                model.setStringList(self.historial.obtener_todos())
                self.completer.setModel(model)
            except Exception:
                pass
    
    def on_texto_cambiado(self):
        """
        Se ejecuta cuando cambia el texto en el campo de búsqueda.
        Actualiza sugerencias del historial e inicia búsqueda en vivo.
        """
        texto = self.search_input.text()
        
        # Actualizar sugerencias del historial basadas en coincidencias
        coincidencias = self.historial.buscar_coincidencias(texto)
        model = QStringListModel()
        model.setStringList(coincidencias)
        self.completer.setModel(model)
        
        # Iniciar búsqueda en vivo si hay unidad seleccionada
        self.iniciar_autocompletado()