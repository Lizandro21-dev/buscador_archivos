from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QListWidget, QLabel, QMessageBox, QFrame
)
class VentanaBase(QMainWindow):
     # ---------- INTERFAZ ----------
    def init_ui(self):
        self.setWindowTitle("Buscador de Archivos")
        self.setGeometry(100, 100, 900, 600)
        self.setStyleSheet("""
                    background-color: qlineargradient(
                        x1: 0, y1: 0, x2: 0, y2: 1,
                        stop: 0 #161239,
                        stop: 1 #2B313F
                    );
                    color: white;
                """)
 
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
 
        # --- Barra de búsqueda ---
        barra = QHBoxLayout()
        self.search_input = QLineEdit(placeholderText="Escribe el nombre del archivo...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #2B313F;
                color: white;
                padding: 10px 15px;
                border: 1px solid white;
                border-radius: 20px;
               
                font-size: 20px;
            }
        """)
        self.search_input.textChanged.connect(self.iniciar_autocompletado)
        self.search_input.returnPressed.connect(self.buscar_archivos)
 
 
        barra.addWidget(self.search_input)
 
        layout.addLayout(barra)
 
        # --- Paneles principales ---
        paneles = QHBoxLayout()
        self.crear_panel_izquierdo(paneles)
        self.crear_panel_derecho(paneles)
        layout.addLayout(paneles)
 
        self.mostrar_mensaje_inicial()
 
    def crear_panel_izquierdo(self, parent):
        panel = QFrame()
        panel.setFixedWidth(240)
        panel.setStyleSheet("""
        QFrame {
            background-color: rgba(227, 45, 100, 0.5);  /* color con opacidad */
                         
            border-radius: 20px;                         /* esquinas redondeadas */
            }
        """)
       
        vbox = QVBoxLayout(panel)
        vbox.setContentsMargins(15, 15, 15, 15)
        self.units_layout = QVBoxLayout()
        vbox.addLayout(self.units_layout)
        vbox.addStretch()
        parent.addWidget(panel)
       
   
 
    def crear_panel_derecho(self, parent):
        panel = QFrame()
        panel.setStyleSheet("QFrame { background-color: #2B313F; border-radius: 20px; }")
        vbox = QVBoxLayout(panel)
        self.results_list = QListWidget()
        self.results_list.setStyleSheet("""
            QListWidget {
                background-color: #2B313F; color: white;
                font-family: Arial; font-size: 20px;
            }
            QListWidget::item:selected { background-color: #4a4a4c; }
        """)
        vbox.addWidget(self.results_list)
        parent.addWidget(panel, 1)