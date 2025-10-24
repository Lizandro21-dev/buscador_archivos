"""
Ventana - Módulo de interfaz gráfica base
Define la estructura visual de la aplicación usando PyQt5.
Implementa un diseño moderno con gradientes, bordes redondeados y efectos hover.
"""

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QListWidget, QLabel, QMessageBox, 
    QFrame, QButtonGroup
)
from PyQt5.QtCore import Qt
from typing import Optional


class VentanaBase(QMainWindow):
    """
    Clase base que define la interfaz gráfica del buscador de archivos.
    
    Proporciona:
    - Layout principal con barra de búsqueda
    - Botones de tipo de búsqueda (nombre, extensión, contenido)
    - Panel lateral para unidades USB
    - Panel principal para resultados
    """
    
    # Constantes de diseño
    VENTANA_ANCHO = 1100
    VENTANA_ALTO = 700
    PANEL_USB_ANCHO = 260
    
    # Paleta de colores
    COLOR_PRIMARIO = "#E32D64"      # Rosa principal
    COLOR_PRIMARIO_HOVER = "#FF3D7F"  # Rosa hover
    COLOR_PRIMARIO_PRESSED = "#C02556"  # Rosa presionado
    COLOR_FONDO_OSCURO = "#2B313F"  # Fondo oscuro
    COLOR_FONDO_CLARO = "#3a3a3c"   # Fondo claro
    
    def init_ui(self):
        """
        Inicializa y configura todos los elementos de la interfaz gráfica.
        Estructura jerárquica:
        - Ventana principal
          ├── Barra de búsqueda (superior)
          ├── Botones de tipo de búsqueda
          └── Paneles horizontales
              ├── Panel izquierdo (unidades USB)
              └── Panel derecho (resultados)
        """
        self._configurar_ventana_principal()
        
        # Widget central con layout vertical
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Agregar componentes en orden vertical
        layout.addLayout(self._crear_barra_busqueda())
        layout.addLayout(self._crear_botones_tipo_busqueda())
        
        # Paneles principales (horizontal)
        paneles = QHBoxLayout()
        paneles.setSpacing(15)
        self._crear_panel_izquierdo(paneles)
        self._crear_panel_derecho(paneles)
        layout.addLayout(paneles)
        
        self.mostrar_mensaje_inicial()
    
    def _configurar_ventana_principal(self):
        """Configura las propiedades básicas de la ventana principal."""
        self.setWindowTitle("Buscador de Archivos USB")
        self.setGeometry(100, 100, self.VENTANA_ANCHO, self.VENTANA_ALTO)
        
        # Gradiente de fondo (oscuro arriba, más claro abajo)
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #161239,
                    stop: 1 {self.COLOR_FONDO_OSCURO}
                );
                color: white;
            }}
        """)
    
    def _crear_barra_busqueda(self) -> QHBoxLayout:
        """
        Crea la barra de búsqueda superior con campo de texto y botones.
        
        Returns:
            Layout horizontal con: campo de búsqueda, botón buscar, botón limpiar
        """
        barra = QHBoxLayout()
        barra.setSpacing(10)
        
        # Campo de entrada de texto con autocompletado
        self.search_input = self._crear_campo_busqueda()
        
        # Botón principal de búsqueda
        self.btn_buscar = self._crear_boton_buscar()
        
        # Botón para limpiar historial
        self.btn_historial = self._crear_boton_limpiar()
        
        barra.addWidget(self.search_input)
        barra.addWidget(self.btn_buscar)
        barra.addWidget(self.btn_historial)
        
        return barra
    
    def _crear_campo_busqueda(self) -> QLineEdit:
        """
        Crea el campo de entrada de texto para búsquedas.
        
        Features:
        - Placeholder dinámico
        - Bordes redondeados
        - Efecto de foco con cambio de color
        - Conectado a eventos de cambio de texto y Enter
        
        Returns:
            Campo de texto configurado
        """
        campo = QLineEdit()
        campo.setPlaceholderText("Escribe el nombre del archivo...")
        campo.setStyleSheet(f"""
            QLineEdit {{
                background-color: {self.COLOR_FONDO_OSCURO};
                color: white;
                padding: 12px 20px;
                border: 2px solid {self.COLOR_PRIMARIO};
                border-radius: 25px;
                font-size: 18px;
            }}
            QLineEdit:focus {{
                border: 2px solid {self.COLOR_PRIMARIO_HOVER};
                background-color: #353B4F;
            }}
        """)
        
        # Conectar eventos (se implementan en la clase derivada)
        campo.textChanged.connect(self.on_texto_cambiado)
        campo.returnPressed.connect(self.buscar_archivos)
        
        return campo
    
    def _crear_boton_buscar(self) -> QPushButton:
        """
        Crea el botón principal de búsqueda.
        
        Returns:
            Botón de búsqueda con estilo y efectos hover
        """
        boton = QPushButton("BUSCAR")
        boton.setFixedSize(140, 50)
        boton.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.COLOR_PRIMARIO};
                color: white;
                font-size: 16px;
                font-weight: bold;
                border: none;
                border-radius: 25px;
            }}
            QPushButton:hover {{
                background-color: {self.COLOR_PRIMARIO_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {self.COLOR_PRIMARIO_PRESSED};
            }}
        """)
        boton.setCursor(Qt.PointingHandCursor)
        boton.clicked.connect(self.buscar_archivos)
        
        return boton
    
    def _crear_boton_limpiar(self) -> QPushButton:
        """
        Crea el botón para limpiar el historial de búsquedas.
        
        Returns:
            Botón de limpiar con tooltip y estilo secundario
        """
        boton = QPushButton("LIMPIAR")
        boton.setFixedSize(100, 50)
        boton.setToolTip("Limpiar historial de búsquedas")
        boton.setStyleSheet(f"""
            QPushButton {{
                background-color: #DB7093;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border: 2px solid #666;
                border-radius: 25px;
            }}
            QPushButton:hover {{
                background-color: {self.COLOR_PRIMARIO};
                border-color: {self.COLOR_PRIMARIO};
            }}
            QPushButton:pressed {{
                background-color: {self.COLOR_PRIMARIO_PRESSED};
            }}
        """)
        boton.setCursor(Qt.PointingHandCursor)
        boton.clicked.connect(self.limpiar_historial)
        
        return boton
    
    def _crear_botones_tipo_busqueda(self) -> QHBoxLayout:
        """
        Crea los botones para seleccionar el tipo de búsqueda.
        
        Tipos disponibles:
        1. Por Nombre: Busca en el nombre del archivo
        2. Por Extensión: Busca por tipo de archivo (.pdf, .txt, etc.)
        3. Por Contenido: Busca dentro del contenido del archivo
        
        Returns:
            Layout horizontal con los tres botones de tipo de búsqueda
        """
        layout_botones = QHBoxLayout()
        layout_botones.setSpacing(10)
        
        # Grupo de botones mutuamente excluyentes (solo uno activo a la vez)
        self.grupo_busqueda = QButtonGroup()
        
        # Crear los tres botones de tipo de búsqueda
        self.btn_nombre = self._crear_boton_tipo("Por Nombre", 1, checked=True)
        self.btn_extension = self._crear_boton_tipo("Por Extension", 2)
        self.btn_contenido = self._crear_boton_tipo("Por Contenido", 3)
        
        # Agregar botones al grupo
        self.grupo_busqueda.addButton(self.btn_nombre, 1)
        self.grupo_busqueda.addButton(self.btn_extension, 2)
        self.grupo_busqueda.addButton(self.btn_contenido, 3)
        
        # Conectar señal para actualizar búsqueda al cambiar tipo
        self.grupo_busqueda.buttonClicked.connect(self.cambiar_tipo_busqueda)
        
        # Centrar botones en el layout
        layout_botones.addStretch()
        layout_botones.addWidget(self.btn_nombre)
        layout_botones.addWidget(self.btn_extension)
        layout_botones.addWidget(self.btn_contenido)
        layout_botones.addStretch()
        
        return layout_botones
    
    def _crear_boton_tipo(self, texto: str, id_tipo: int, checked: bool = False) -> QPushButton:
        """
        Crea un botón de tipo de búsqueda.
        
        Args:
            texto: Texto a mostrar en el botón
            id_tipo: ID del tipo de búsqueda (1, 2 o 3)
            checked: Si debe estar seleccionado por defecto
            
        Returns:
            Botón configurado con estilo toggle
        """
        boton = QPushButton(texto)
        boton.setCheckable(True)
        boton.setChecked(checked)
        boton.setFixedHeight(40)
        boton.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.COLOR_FONDO_CLARO};
                color: white;
                font-size: 14px;
                font-weight: bold;
                border: 2px solid #666;
                border-radius: 20px;
                padding: 0 20px;
            }}
            QPushButton:hover {{
                background-color: #4a4a4c;
                border-color: {self.COLOR_PRIMARIO};
            }}
            QPushButton:checked {{
                background-color: {self.COLOR_PRIMARIO};
                border-color: {self.COLOR_PRIMARIO_HOVER};
            }}
        """)
        boton.setCursor(Qt.PointingHandCursor)
        
        return boton
    
    def _crear_panel_izquierdo(self, parent: QHBoxLayout):
        """
        Crea el panel lateral izquierdo para mostrar unidades USB detectadas.
        
        El panel contiene:
        - Título "UNIDADES USB"
        - Área dinámica donde se agregan botones de unidades detectadas
        
        Args:
            parent: Layout padre donde se agregará este panel
        """
        panel = QFrame()
        panel.setFixedWidth(self.PANEL_USB_ANCHO)
        panel.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(227, 45, 100, 0.3);
                border: 2px solid {self.COLOR_PRIMARIO};
                border-radius: 20px;
            }}
        """)
        
        vbox = QVBoxLayout(panel)
        vbox.setContentsMargins(15, 15, 15, 15)
        vbox.setSpacing(10)
        
        # Título del panel
        titulo = QLabel("UNIDADES USB")
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 10px;
                background-color: rgba(0, 0, 0, 0.3);
                border-radius: 10px;
            }
        """)
        vbox.addWidget(titulo)
        
        # Layout dinámico donde se agregarán los botones de unidades
        # Este layout se llena desde la clase derivada
        self.units_layout = QVBoxLayout()
        self.units_layout.setSpacing(10)
        vbox.addLayout(self.units_layout)
        vbox.addStretch()
        
        parent.addWidget(panel)
    
    def _crear_panel_derecho(self, parent: QHBoxLayout):
        """
        Crea el panel principal derecho para mostrar resultados de búsqueda.
        
        Features:
        - Lista de resultados con scroll automático
        - Estilo semi-transparente con bordes redondeados
        - Selección y hover con efectos visuales
        
        Args:
            parent: Layout padre donde se agregará este panel
        """
        panel = QFrame()
        panel.setStyleSheet(f"""
            QFrame {{ 
                background-color: rgba(43, 49, 63, 0.8); 
                border: 2px solid {self.COLOR_PRIMARIO};
                border-radius: 20px; 
            }}
        """)
        
        vbox = QVBoxLayout(panel)
        vbox.setContentsMargins(20, 20, 20, 20)
        
        # Lista de resultados con estilo personalizado
        self.results_list = QListWidget()
        self.results_list.setStyleSheet(f"""
            QListWidget {{
                background-color: transparent;
                color: white;
                font-family: 'Segoe UI', Arial;
                font-size: 14px;
                border: none;
                outline: none;
            }}
            QListWidget::item {{
                padding: 8px;
                border-radius: 5px;
                margin: 2px;
            }}
            QListWidget::item:selected {{ 
                background-color: {self.COLOR_PRIMARIO};
                color: white;
            }}
            QListWidget::item:hover {{
                background-color: rgba(227, 45, 100, 0.3);
            }}
        """)
        
        vbox.addWidget(self.results_list)
        parent.addWidget(panel, 1)  # Factor de expansión 1
    
    # ========== Métodos abstractos (deben implementarse en clase derivada) ==========
    
    def on_texto_cambiado(self):
        """Evento cuando el texto del campo de búsqueda cambia."""
        pass
    
    def buscar_archivos(self):
        """Ejecuta la búsqueda de archivos."""
        pass
    
    def limpiar_historial(self):
        """Limpia el historial de búsquedas."""
        pass
    
    def cambiar_tipo_busqueda(self, boton):
        """Cambia el tipo de búsqueda activo."""
        pass
    
    def mostrar_mensaje_inicial(self):
        """Muestra el mensaje inicial en la lista de resultados."""
        pass