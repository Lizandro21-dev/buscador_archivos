from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QListWidget, QLabel, QMessageBox, QFrame,
    QButtonGroup
)
from PyQt5.QtCore import Qt


class VentanaBase(QMainWindow):
    """Clase base que define la interfaz gráfica"""
    
    def init_ui(self):
        """Inicializa todos los elementos de la interfaz"""
        self.setWindowTitle("Buscador de Archivos USB")
        self.setGeometry(100, 100, 1100, 700)
        self.setStyleSheet("""
            QMainWindow {
                background-color: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #161239,
                    stop: 1 #2B313F
                );
                color: white;
            }
        """)
        
        # Widget central
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Barra de búsqueda con botones
        layout.addLayout(self.crear_barra_busqueda())
        
        # Botones de tipo de búsqueda
        layout.addLayout(self.crear_botones_tipo_busqueda())
        
        # Paneles principales
        paneles = QHBoxLayout()
        paneles.setSpacing(15)
        self.crear_panel_izquierdo(paneles)
        self.crear_panel_derecho(paneles)
        layout.addLayout(paneles)
        
        self.mostrar_mensaje_inicial()
    
    def crear_barra_busqueda(self):
        """Crea la barra de búsqueda superior"""
        barra = QHBoxLayout()
        barra.setSpacing(10)
        
        # Campo de entrada de texto
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Escribe el nombre del archivo...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #2B313F;
                color: white;
                padding: 12px 20px;
                border: 2px solid #E32D64;
                border-radius: 25px;
                font-size: 18px;
            }
            QLineEdit:focus {
                border: 2px solid #FF3D7F;
                background-color: #353B4F;
            }
        """)
        self.search_input.textChanged.connect(self.on_texto_cambiado)
        self.search_input.returnPressed.connect(self.buscar_archivos)
        
        # Botón de buscar
        self.btn_buscar = QPushButton("BUSCAR")
        self.btn_buscar.setFixedSize(140, 50)
        self.btn_buscar.setStyleSheet("""
            QPushButton {
                background-color: #E32D64;
                color: white;
                font-size: 16px;
                font-weight: bold;
                border: none;
                border-radius: 25px;
            }
            QPushButton:hover {
                background-color: #FF3D7F;
            }
            QPushButton:pressed {
                background-color: #C02556;
            }
        """)
        self.btn_buscar.setCursor(Qt.PointingHandCursor)
        self.btn_buscar.clicked.connect(self.buscar_archivos)
        
        # Botón de limpiar historial
        self.btn_historial = QPushButton("LIMPIAR")
        self.btn_historial.setFixedSize(100, 50)
        self.btn_historial.setToolTip("Limpiar historial de búsquedas")
        self.btn_historial.setStyleSheet("""
            QPushButton {
                background-color: #DB7093;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border: 2px solid #666;
                border-radius: 25px;
            }
            QPushButton:hover {
                background-color: #E32D64;
                border-color: #E32D64;
            }
            QPushButton:pressed {
                background-color: #C02556;
            }
        """)
        self.btn_historial.setCursor(Qt.PointingHandCursor)
        self.btn_historial.clicked.connect(self.limpiar_historial)
        
        barra.addWidget(self.search_input)
        barra.addWidget(self.btn_buscar)
        barra.addWidget(self.btn_historial)
        
        return barra
    
    def crear_botones_tipo_busqueda(self):
        """Crea los botones para seleccionar tipo de búsqueda"""
        layout_botones = QHBoxLayout()
        layout_botones.setSpacing(10)
        
        # Grupo de botones para que solo uno esté activo
        self.grupo_busqueda = QButtonGroup()
        
        # Botón 1: Búsqueda por nombre
        self.btn_nombre = QPushButton("Por Nombre")
        self.btn_nombre.setCheckable(True)
        self.btn_nombre.setChecked(True)  # Activo por defecto
        self.btn_nombre.setFixedHeight(40)
        
        # Botón 2: Búsqueda por extensión
        self.btn_extension = QPushButton("Por Extension")
        self.btn_extension.setCheckable(True)
        self.btn_extension.setFixedHeight(40)
        
        # Botón 3: Búsqueda por contenido
        self.btn_contenido = QPushButton("Por Contenido")
        self.btn_contenido.setCheckable(True)
        self.btn_contenido.setFixedHeight(40)
        
        # Agregar botones al grupo
        self.grupo_busqueda.addButton(self.btn_nombre, 1)
        self.grupo_busqueda.addButton(self.btn_extension, 2)
        self.grupo_busqueda.addButton(self.btn_contenido, 3)
        
        # Estilo para los botones
        estilo_boton = """
            QPushButton {
                background-color: #3a3a3c;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border: 2px solid #666;
                border-radius: 20px;
            }
            QPushButton:hover {
                background-color: #4a4a4c;
                border-color: #E32D64;
            }
            QPushButton:checked {
                background-color: #E32D64;
                border-color: #FF3D7F;
            }
        """
        
        self.btn_nombre.setStyleSheet(estilo_boton)
        self.btn_extension.setStyleSheet(estilo_boton)
        self.btn_contenido.setStyleSheet(estilo_boton)
        
        # Conectar señales para actualizar búsqueda
        self.grupo_busqueda.buttonClicked.connect(self.cambiar_tipo_busqueda)
        
        layout_botones.addStretch()
        layout_botones.addWidget(self.btn_nombre)
        layout_botones.addWidget(self.btn_extension)
        layout_botones.addWidget(self.btn_contenido)
        layout_botones.addStretch()
        
        return layout_botones
    
    def crear_panel_izquierdo(self, parent):
        """Crea el panel de unidades USB"""
        panel = QFrame()
        panel.setFixedWidth(260)
        panel.setStyleSheet("""
            QFrame {
                background-color: rgba(227, 45, 100, 0.3);
                border: 2px solid #E32D64;
                border-radius: 20px;
            }
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
        
        # Layout donde se agregarán los botones de unidades
        self.units_layout = QVBoxLayout()
        self.units_layout.setSpacing(10)
        vbox.addLayout(self.units_layout)
        vbox.addStretch()
        
        parent.addWidget(panel)
    
    def crear_panel_derecho(self, parent):
        """Crea el panel de resultados"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame { 
                background-color: rgba(43, 49, 63, 0.8); 
                border: 2px solid #E32D64;
                border-radius: 20px; 
            }
        """)
        
        vbox = QVBoxLayout(panel)
        vbox.setContentsMargins(20, 20, 20, 20)
        
        # Lista de resultados
        self.results_list = QListWidget()
        self.results_list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                color: white;
                font-family: 'Segoe UI', Arial;
                font-size: 14px;
                border: none;
                outline: none;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 5px;
                margin: 2px;
            }
            QListWidget::item:selected { 
                background-color: #E32D64;
                color: white;
            }
            QListWidget::item:hover {
                background-color: rgba(227, 45, 100, 0.3);
            }
        """)
        vbox.addWidget(self.results_list)
        parent.addWidget(panel, 1)