"""
VentanaInstrucciones - Ventana independiente para mostrar instrucciones de uso
Muestra guías, consejos y ejemplos de cómo usar el buscador de archivos USB
"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, 
    QPushButton, QTextEdit
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class VentanaInstrucciones(QMainWindow):
    """
    Ventana independiente que muestra las instrucciones de uso del programa.
    
    Características:
    - Siempre visible al frente
    - Independiente (no bloquea ventana principal)
    - Diseño moderno con HTML estilizado
    - Se puede cerrar con botón o tecla X
    """
    
    def __init__(self, parent=None):
        """
        Inicializa la ventana de instrucciones.
        
        Args:
            parent: Ventana padre (opcional)
        """
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """Configura la interfaz gráfica de la ventana."""
        self.setWindowTitle("Instrucciones de Uso")
        self.setFixedSize(600, 500)
        
        # Configurar flags para mantener la ventana al frente
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |  # Siempre al frente
            Qt.Window |                 # Ventana independiente
            Qt.WindowCloseButtonHint    # Botón de cerrar
        )
        
        # Widget central
        widget_central = QWidget()
        self.setCentralWidget(widget_central)
        
        # Layout principal
        layout = QVBoxLayout(widget_central)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        
        # Agregar componentes
        layout.addWidget(self._crear_titulo())
        layout.addWidget(self._crear_area_instrucciones())
        layout.addWidget(self._crear_boton_cerrar())
        
        # Aplicar estilo de fondo
        self._aplicar_estilos()
    
    def _crear_titulo(self) -> QLabel:
        """
        Crea el título de la ventana.
        
        Returns:
            QLabel con el título estilizado
        """
        titulo = QLabel("Bienvenido al Buscador de Archivos")
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setFont(QFont("Segoe UI", 16, QFont.Bold))
        titulo.setStyleSheet("color: #E32D64; padding: 10px;")
        return titulo
    
    def _crear_area_instrucciones(self) -> QTextEdit:
        """
        Crea el área de texto con las instrucciones en formato HTML.
        
        Returns:
            QTextEdit con instrucciones formateadas
        """
        texto = QTextEdit()
        texto.setReadOnly(True)
        texto.setHtml(self._obtener_html_instrucciones())
        texto.setStyleSheet("""
            QTextEdit {
                background-color: #2B313F;
                border: 2px solid #E32D64;
                border-radius: 15px;
                padding: 15px;
            }
        """)
        return texto
    
    def _obtener_html_instrucciones(self) -> str:
        """
        Retorna el HTML con las instrucciones formateadas.
        
        Returns:
            String con HTML de instrucciones
        """
        return """
            <div style='font-family: Segoe UI; font-size: 20px; line-height: 1.8; color: white;'>
                <h3 style='color: #E32D64; margin-top: 16px;'> Instrucciones:</h3>
                <ol style='padding-left: 24px;'>
                    <li><b>Selecciona una unidad USB</b> del panel izquierdo</li>
                    <li><b>Espera</b> a que se indexen todos los archivos</li>
                    <li><b>Escribe</b> para buscar o explora todos los archivos</li>
                </ol>
                
                <h3 style='color: #E32D64; margin-top: 20px;'> Detección Automática:</h3>
                <ul style='padding-left: 20px;'>
                    <li><b>Búsqueda por nombre:</b> Escribe texto normal<br>
                        <i style='color: #aaa;'>Ejemplo: "documento", "foto", "informe"</i></li>
                    
                    <li style='margin-top: 10px;'><b>Búsqueda por extensión:</b> Empieza con punto<br>
                        <i style='color: #aaa;'>Ejemplo: ".pdf", ".txt", ".jpg"</i></li>
                </ul>
            </div>
        """
    
    def _crear_boton_cerrar(self) -> QPushButton:
        """
        Crea el botón para cerrar la ventana.
        
        Returns:
            QPushButton estilizado
        """
        btn_cerrar = QPushButton("¡Entendido!")
        btn_cerrar.setFixedHeight(45)
        btn_cerrar.setStyleSheet("""
            QPushButton {
                background-color: #E32D64;
                color: white;
                font-size: 16px;
                font-weight: bold;
                border: none;
                border-radius: 22px;
            }
            QPushButton:hover {
                background-color: #FF3D7F;
            }
            QPushButton:pressed {
                background-color: #C02556;
            }
        """)
        btn_cerrar.setCursor(Qt.PointingHandCursor)
        btn_cerrar.clicked.connect(self.close)
        return btn_cerrar
    
    def _aplicar_estilos(self):
        """Aplica los estilos de fondo a la ventana."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #161239,
                    stop: 1 #2B313F
                );
            }
        """)
    
    def mostrar(self):
        """
        Muestra la ventana al frente y la activa.
        Método de conveniencia para mostrar la ventana correctamente.
        """
        self.show()
        self.raise_()
        self.activateWindow()