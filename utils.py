import os
import sys
import string
import threading
import subprocess
import platform
import win32file
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QListWidget, QLabel, QMessageBox, QFrame,
    QCompleter
)
from PyQt5.QtCore import Qt, QTimer, QStringListModel
from ventana import VentanaBase
from GestorHistorial import GestorHistorial


def detectar_unidades_disponibles():
    """Detecta solo unidades extraíbles USB en Windows"""
    unidades = []
    for letra in string.ascii_uppercase:
        unidad = f"{letra}:\\"
        # Saltar si no existe o es A, B, C (disqueteras y sistema)
        if not os.path.exists(unidad) or letra in ['A', 'B', 'C']:
            continue
        try:
            # Tipo 2 = Removable (USB)
            if win32file.GetDriveType(unidad) == 2:
                unidades.append({'texto': f"{letra}:/", 'ruta': unidad})
        except Exception:
            continue
    return unidades


def leer_contenido_archivo(ruta):
    """Lee el contenido de archivos de texto compatibles"""
    try:
        extension = os.path.splitext(ruta)[1].lower()
        
        # Solo leer archivos de texto
        extensiones_texto = {'.txt', '.log', '.csv', '.json', '.xml', '.html', '.py', '.js', '.css'}
        
        if extension in extensiones_texto:
            # Intentar con diferentes encodings
            encodings = ['utf-8', 'latin-1', 'cp1252']
            for encoding in encodings:
                try:
                    with open(ruta, 'r', encoding=encoding) as f:
                        return f.read().lower()
                except:
                    continue
        
        # Para archivos .docx (requiere python-docx)
        elif extension == '.docx':
            try:
                import docx
                doc = docx.Document(ruta)
                texto = '\n'.join([p.text for p in doc.paragraphs])
                return texto.lower()
            except:
                pass
        
        # Para archivos .pptx (requiere python-pptx)
        elif extension == '.pptx':
            try:
                from pptx import Presentation
                prs = Presentation(ruta)
                texto = ''
                # Recorrer todas las diapositivas
                for slide in prs.slides:
                    # Recorrer todas las formas en cada diapositiva
                    for shape in slide.shapes:
                        if hasattr(shape, "text"):
                            texto += shape.text + '\n'
                return texto.lower()
            except:
                pass
        
        # Para archivos .xlsx (requiere openpyxl)
        elif extension == '.xlsx':
            try:
                from openpyxl import load_workbook
                wb = load_workbook(ruta, read_only=True, data_only=True)
                texto = ''
                # Recorrer todas las hojas
                for sheet in wb.worksheets:
                    # Recorrer todas las celdas con valores
                    for row in sheet.iter_rows(values_only=True):
                        for cell in row:
                            if cell is not None:
                                texto += str(cell) + ' '
                        texto += '\n'
                wb.close()
                return texto.lower()
            except:
                pass
        
        # Para archivos .pdf (requiere PyPDF2)
        elif extension == '.pdf':
            try:
                import PyPDF2
                with open(ruta, 'rb') as f:
                    pdf = PyPDF2.PdfReader(f)
                    texto = ''
                    for page in pdf.pages:
                        texto += page.extract_text()
                    return texto.lower()
            except:
                pass
        
        return ""
    except:
        return ""


class BuscadorArchivos(VentanaBase):
    """Clase principal del buscador de archivos"""
    
    def __init__(self):
        super().__init__()
        # Variables de estado
        self.unidad_seleccionada = None  # Ruta de la unidad actual
        self.resultados = []  # Lista de resultados de búsqueda
        self.todos_los_archivos = []  # Cache de todos los archivos indexados
        self.unidades_previas = []  # Para detectar cambios en USBs
        self.tipo_busqueda = 1  # 1=nombre, 2=extensión, 3=contenido
        
        # Gestor de historial
        self.historial = GestorHistorial()
        self.completer = None
        
        # Inicializar interfaz
        self.init_ui()
        self.cargar_unidades()
        self.configurar_autocompletado()
        
        # Timer para detectar cambios en USBs (cada 2 segundos)
        self.timer_usb = QTimer()
        self.timer_usb.timeout.connect(self.verificar_cambios_usb)
        self.timer_usb.start(2000)
        
        # Timer para búsqueda en vivo (espera 300ms después de teclear)
        self.timer_autocompletar = QTimer()
        self.timer_autocompletar.setSingleShot(True)
        self.timer_autocompletar.timeout.connect(self.buscar_sugerencias)
    
    # ========== AUTOCOMPLETADO ==========
    
    def configurar_autocompletado(self):
        """Configura el autocompletado con historial ordenado"""
        self.completer = QCompleter()
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchContains)
        self.completer.setMaxVisibleItems(20)
        
        # Configurar popup
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
        
        # Configurar eventos de mouse y teclado para selección
        self.configurar_eventos_seleccion()
    
    def actualizar_completer(self):
        """Actualiza sugerencias del completer con historial ordenado"""
        model = QStringListModel()
        model.setStringList(self.historial.obtener_todos())
        self.completer.setModel(model)
    
    def configurar_eventos_seleccion(self):
        """Configura eventos para permitir selección de texto completa"""
        # Guardar evento original
        self.search_input_click_original = self.search_input.mousePressEvent
        self.search_input_focus_original = self.search_input.focusInEvent
        
        # Asignar nuevos eventos
        self.search_input.mousePressEvent = self.on_search_input_click
        self.search_input.focusInEvent = self.on_search_input_focus
    
    def on_search_input_click(self, event):
        """Maneja clicks en la barra de búsqueda mostrando historial"""
        # Mostrar historial si está vacío o con poco texto
        if len(self.search_input.text()) < 2:
            try:
                model = QStringListModel()
                model.setStringList(self.historial.obtener_todos())
                self.completer.setModel(model)
                self.completer.complete()
            except Exception as e:
                print("Error al mostrar historial:", e)
        
        # Ejecutar evento normal para permitir selección
        self.search_input_click_original(event)
    
    def on_search_input_focus(self, event):
        """Maneja cuando la barra obtiene el foco"""
        # Ejecutar evento normal primero
        self.search_input_focus_original(event)
        
        # Mostrar historial si está vacío
        if not self.search_input.text():
            try:
                model = QStringListModel()
                model.setStringList(self.historial.obtener_todos())
                self.completer.setModel(model)
            except:
                pass
    
    def on_texto_cambiado(self):
        """Se ejecuta cuando el usuario escribe en la barra de búsqueda"""
        texto = self.search_input.text()
        
        # Actualizar sugerencias del historial
        coincidencias = self.historial.buscar_coincidencias(texto)
        model = QStringListModel()
        model.setStringList(coincidencias)
        self.completer.setModel(model)
        
        # Iniciar búsqueda en vivo si hay unidad seleccionada
        self.iniciar_autocompletado()
    
    # ========== DETECCIÓN DE USB ==========
    
    def cargar_unidades(self):
        """Detecta y carga botones de unidades USB disponibles"""
        unidades = detectar_unidades_disponibles()
        
        # Limpiar botones anteriores
        for i in reversed(range(self.units_layout.count())):
            widget = self.units_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        if not unidades:
            lbl = QLabel("No hay unidades\nexternas detectadas")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("color: white; font-size: 14px;")
            self.units_layout.addWidget(lbl)
            return
        
        # Crear botón para cada unidad
        for info in unidades:
            btn = QPushButton(info['texto'])
            btn.setFixedHeight(60)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #2B313F; 
                    color: white;
                    font-size: 20px;
                    font-weight: bold;
                    border: 2px solid #E32D64;
                    border-radius: 15px;
                } 
                QPushButton:hover { 
                    background-color: #4a4a4c; 
                }
                QPushButton:pressed {
                    background-color: #E32D64;
                }
            """)
            btn.clicked.connect(lambda _, i=info: self.seleccionar_unidad(i))
            self.units_layout.addWidget(btn)
    
    def verificar_cambios_usb(self):
        """Verifica cada 2 segundos si hay cambios en las USBs conectadas"""
        actuales = detectar_unidades_disponibles()
        letras_actuales = {u['texto'] for u in actuales}
        letras_previas = {u['texto'] for u in self.unidades_previas}
        
        # Si hay cambios, recargar
        if letras_actuales != letras_previas:
            self.cargar_unidades()
        
        self.unidades_previas = actuales
    
    # ========== SELECCIÓN Y INDEXACIÓN ==========
    
    def seleccionar_unidad(self, unidad):
        """Selecciona una unidad e indexa todos sus archivos"""
        self.unidad_seleccionada = unidad['ruta']
        self.results_list.clear()
        self.results_list.addItem("")
        self.results_list.addItem(f"  Unidad seleccionada: {unidad['texto']}")
        self.results_list.addItem(f"  Ruta: {unidad['ruta']}")
        self.results_list.addItem("")
        self.results_list.addItem("  Indexando archivos...")
        
        # Indexar en segundo plano
        threading.Thread(target=self.indexar_unidad, daemon=True).start()
    
    def indexar_unidad(self):
        """Recorre toda la unidad y guarda información de archivos"""
        self.todos_los_archivos = []
        if not self.unidad_seleccionada:
            return
        
        try:
            # Recorrer todos los directorios
            for root, _, files in os.walk(self.unidad_seleccionada):
                for f in files:
                    ruta_completa = os.path.join(root, f)
                    self.todos_los_archivos.append({
                        'nombre': f,
                        'ruta': ruta_completa,
                        'extension': os.path.splitext(f)[1].lower()
                    })
            
            # Ordenar alfabéticamente
            self.todos_los_archivos.sort(key=lambda x: x['nombre'].lower())
            
            # Mostrar todos los archivos inmediatamente
            self.mostrar_todos_los_archivos()
            
        except Exception as e:
            self.alerta(f"Error al indexar: {e}")
    
    def mostrar_todos_los_archivos(self):
        """Muestra todos los archivos indexados en la lista"""
        self.results_list.clear()
        self.resultados = self.todos_los_archivos
        
        # Conectar doble click
        try:
            self.results_list.itemDoubleClicked.disconnect()
        except TypeError:
            pass
        self.results_list.itemDoubleClicked.connect(self.abrir_item)
        
        if not self.todos_los_archivos:
            self.results_list.addItem("")
            self.results_list.addItem("  No hay archivos en esta unidad")
            return
        
        # Mostrar header
        self.results_list.addItem("")
        self.results_list.addItem(f"  Total: {len(self.todos_los_archivos)} archivos")
        self.results_list.addItem("")
        self.results_list.addItem("  Doble clic para abrir | Escribe para buscar")
        self.results_list.addItem("")
        self.results_list.addItem("  " + "=" * 80)
        
        # Mostrar archivos (limitar a 500 para rendimiento)
        for archivo in self.todos_los_archivos[:500]:
            self.results_list.addItem(f"  {archivo['nombre']}")
        
        if len(self.todos_los_archivos) > 500:
            self.results_list.addItem("")
            self.results_list.addItem(f"  ... y {len(self.todos_los_archivos) - 500} archivos mas")
    
    # ========== TIPOS DE BÚSQUEDA ==========
    
    def cambiar_tipo_busqueda(self, boton):
        """Cambia el tipo de búsqueda activo"""
        self.tipo_busqueda = self.grupo_busqueda.id(boton)
        
        # Actualizar placeholder según tipo
        if self.tipo_busqueda == 1:
            self.search_input.setPlaceholderText("Buscar por nombre de archivo...")
        elif self.tipo_busqueda == 2:
            self.search_input.setPlaceholderText("Buscar por extension (ej: .pdf, .txt)...")
        elif self.tipo_busqueda == 3:
            self.search_input.setPlaceholderText("Buscar por contenido dentro de archivos...")
        
        # Re-ejecutar búsqueda si hay texto
        if self.search_input.text().strip():
            self.buscar_sugerencias()
    
    def iniciar_autocompletado(self):
        """Inicia timer para búsqueda en vivo"""
        if not self.unidad_seleccionada or not self.todos_los_archivos:
            return
        self.timer_autocompletar.start(300)
    
    def buscar_sugerencias(self):
        """Filtra archivos según el tipo de búsqueda seleccionado"""
        texto = self.search_input.text().strip().lower()
        
        if not texto:
            # Si no hay texto, mostrar todos los archivos
            self.mostrar_todos_los_archivos()
            return
        
        coincidencias = []
        
        # Tipo 1: Búsqueda por nombre (SIN incluir extensión)
        if self.tipo_busqueda == 1:
            coincidencias = []