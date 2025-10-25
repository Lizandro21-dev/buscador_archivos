"""
Utils - Módulo principal del Buscador de Archivos USB
Versión 100% estable - sin crashes
"""

import os
import sys
import string
import threading
import subprocess
import platform
from typing import List, Dict, Optional
import win32file

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QListWidget, QLabel, QMessageBox, 
    QFrame, QCompleter, QTextEdit
)
from PyQt5.QtCore import Qt, QTimer, QStringListModel, pyqtSignal, QObject
from PyQt5.QtGui import QFont

from ventana import VentanaBase
from GestorHistorial import GestorHistorial
from ventana_instrucciones import VentanaInstrucciones


# ========== CONSTANTES ==========

EXTENSIONES_TEXTO = {
    '.txt', '.log', '.csv', '.json', '.xml', '.html', 
    '.py', '.js', '.css', '.md', '.ini', '.conf'
}

ENCODINGS_TEXTO = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']


# ========== SEÑALES ==========

class Signals(QObject):
    """Señales para comunicación thread-safe."""
    progreso_actualizado = pyqtSignal(int, int, int)
    busqueda_finalizada = pyqtSignal(list, str)
    error_busqueda = pyqtSignal(str)


# ========== FUNCIONES AUXILIARES ==========

def detectar_unidades_disponibles() -> List[Dict[str, str]]:
    """Detecta unidades extraíbles USB."""
    unidades = []
    
    for letra in string.ascii_uppercase:
        unidad = f"{letra}:\\"
        
        if letra in ['A', 'B', 'C']:
            continue
        
        if not os.path.exists(unidad):
            continue
        
        try:
            tipo_unidad = win32file.GetDriveType(unidad)
            
            if tipo_unidad == 2:
                unidades.append({
                    'texto': f"{letra}:/", 
                    'ruta': unidad
                })
        except:
            continue
    
    return unidades


def leer_contenido_archivo(ruta: str) -> str:
    """Lee contenido de un archivo."""
    try:
        extension = os.path.splitext(ruta)[1].lower()
        
        if extension in EXTENSIONES_TEXTO:
            return _leer_archivo_texto(ruta)
        elif extension == '.docx':
            return _leer_docx(ruta)
        elif extension == '.pptx':
            return _leer_pptx(ruta)
        elif extension == '.xlsx':
            return _leer_xlsx(ruta)
        elif extension == '.pdf':
            return _leer_pdf(ruta)
        
        return ""
    except:
        return ""


def _leer_archivo_texto(ruta: str) -> str:
    """Lee archivos de texto."""
    for encoding in ENCODINGS_TEXTO:
        try:
            with open(ruta, 'r', encoding=encoding) as f:
                return f.read().lower()
        except:
            continue
    return ""


def _leer_docx(ruta: str) -> str:
    """Lee archivos .docx."""
    try:
        import docx
        doc = docx.Document(ruta)
        texto = '\n'.join([p.text for p in doc.paragraphs])
        return texto.lower()
    except:
        return ""


def _leer_pptx(ruta: str) -> str:
    """Lee archivos .pptx."""
    try:
        from pptx import Presentation
        prs = Presentation(ruta)
        texto = ''
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    texto += shape.text + '\n'
        return texto.lower()
    except:
        return ""


def _leer_xlsx(ruta: str) -> str:
    """Lee archivos .xlsx."""
    try:
        from openpyxl import load_workbook
        wb = load_workbook(ruta, read_only=True, data_only=True)
        texto = ''
        for sheet in wb.worksheets:
            for row in sheet.iter_rows(values_only=True):
                for cell in row:
                    if cell is not None:
                        texto += str(cell) + ' '
                texto += '\n'
        wb.close()
        return texto.lower()
    except:
        return ""


def _leer_pdf(ruta: str) -> str:
    """Lee archivos .pdf."""
    try:
        import PyPDF2
        with open(ruta, 'rb') as f:
            pdf = PyPDF2.PdfReader(f)
            texto = ''
            for page in pdf.pages:
                texto += page.extract_text()
            return texto.lower()
    except:
        return ""


# ========== CLASE PRINCIPAL ==========

class BuscadorArchivos(VentanaBase):
    """Clase principal del buscador - Versión estable."""
    
    INTERVALO_DETECCION_USB = 2000
    DELAY_BUSQUEDA_VIVO = 500
    MAX_ARCHIVOS_MOSTRADOS = 100
    
    BUSQUEDA_NOMBRE = 1
    BUSQUEDA_EXTENSION = 2
    BUSQUEDA_CONTENIDO = 3
    
    def __init__(self):
        """Inicializa el buscador."""
        super().__init__()
        
        # Estado
        self.unidad_seleccionada = None
        self.resultados = []
        self.todos_los_archivos = []
        self.unidades_previas = []
        self.tipo_busqueda = self.BUSQUEDA_NOMBRE
        self.buscando_contenido = False
        
        # Señales
        self.signals = Signals()
        self.signals.progreso_actualizado.connect(self._on_progreso_actualizado)
        self.signals.busqueda_finalizada.connect(self._on_busqueda_finalizada)
        self.signals.error_busqueda.connect(self._on_error_busqueda)
        
        # Historial
        self.historial = GestorHistorial()
        self.completer = None
        self.historial.limpiar()
        
        # Inicializar UI
        self.init_ui()
        self.cargar_unidades()
        self.configurar_autocompletado()
        
        # Instrucciones
        QTimer.singleShot(100, self.mostrar_ventana_instrucciones)
        
        # Timers
        self.timer_usb = QTimer()
        self.timer_usb.timeout.connect(self.verificar_cambios_usb)
        self.timer_usb.start(self.INTERVALO_DETECCION_USB)
        
        self.timer_autocompletar = QTimer()
        self.timer_autocompletar.setSingleShot(True)
        self.timer_autocompletar.timeout.connect(self._ejecutar_busqueda_diferida)
    
    def mostrar_ventana_instrucciones(self):
        """Muestra ventana de instrucciones."""
        try:
            self.ventana_instrucciones = VentanaInstrucciones(self)
            self.ventana_instrucciones.mostrar()
        except:
            pass
    
    # ========== AUTOCOMPLETADO ==========
    
    def configurar_autocompletado(self):
        """Configura autocompletado."""
        try:
            self.completer = QCompleter()
            self.completer.setCaseSensitivity(Qt.CaseInsensitive)
            self.completer.setFilterMode(Qt.MatchContains)
            self.completer.setMaxVisibleItems(20)
            
            popup = self.completer.popup()
            popup.setStyleSheet("""
                QListView {
                    background-color: #2B313F;
                    color: white;
                    border: 3px solid #E32D64;
                    border-radius: 12px;
                    padding: 10px;
                    font-size: 16px;
                }
                QListView::item {
                    padding: 12px;
                    border-radius: 8px;
                    margin: 3px;
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
        except Exception as e:
            print(f"Error configurando autocompletado: {e}")
    
    def actualizar_completer(self):
        """Actualiza completer."""
        try:
            if self.completer:
                model = QStringListModel()
                model.setStringList(self.historial.obtener_todos())
                self.completer.setModel(model)
        except:
            pass
    
    def on_texto_cambiado(self):
        """Cuando cambia el texto - CRÍTICO PARA ESTABILIDAD."""
        try:
            if self.buscando_contenido:
                return
            
            texto = self.search_input.text()
            
            # Detectar tipo
            self._detectar_tipo_busqueda(texto)
            
            # Actualizar historial
            try:
                coincidencias = self.historial.buscar_coincidencias(texto)
                if self.completer:
                    model = QStringListModel()
                    model.setStringList(coincidencias)
                    self.completer.setModel(model)
            except:
                pass
            
            # Si vacío, mostrar todo
            if not texto.strip():
                self.timer_autocompletar.stop()
                if self.unidad_seleccionada and self.todos_los_archivos:
                    QTimer.singleShot(50, self.mostrar_todos_los_archivos)
                return
            
            # Búsqueda con delay
            if self.tipo_busqueda != self.BUSQUEDA_CONTENIDO:
                self.timer_autocompletar.stop()
                self.timer_autocompletar.start(self.DELAY_BUSQUEDA_VIVO)
        
        except Exception as e:
            print(f"Error en on_texto_cambiado: {e}")
    
    def _detectar_tipo_busqueda(self, texto: str):
        """Detecta tipo de búsqueda."""
        try:
            texto_limpio = texto.strip()
            
            if not texto_limpio:
                self.tipo_busqueda = self.BUSQUEDA_NOMBRE
            elif texto_limpio.startswith('.'):
                self.tipo_busqueda = self.BUSQUEDA_EXTENSION
            else:
                self.tipo_busqueda = self.BUSQUEDA_NOMBRE
        except:
            self.tipo_busqueda = self.BUSQUEDA_NOMBRE
    
    # ========== USB ==========
    
    def cargar_unidades(self):
        """Carga unidades USB."""
        try:
            unidades = detectar_unidades_disponibles()
            
            # Limpiar
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
                btn.setCursor(Qt.PointingHandCursor)
                btn.clicked.connect(lambda _, i=info: self.seleccionar_unidad(i))
                self.units_layout.addWidget(btn)
        except Exception as e:
            print(f"Error cargando unidades: {e}")
    
    def verificar_cambios_usb(self):
        """Verifica cambios en USB."""
        try:
            actuales = detectar_unidades_disponibles()
            letras_actuales = {u['texto'] for u in actuales}
            letras_previas = {u['texto'] for u in self.unidades_previas}
            
            if letras_actuales != letras_previas:
                self.cargar_unidades()
            
            self.unidades_previas = actuales
        except:
            pass
    
    # ========== INDEXACIÓN ==========
    
    def seleccionar_unidad(self, unidad: Dict[str, str]):
        """Selecciona unidad."""
        try:
            self.unidad_seleccionada = unidad['ruta']
            
            self.results_list.clear()
            self.results_list.addItem("")
            self.results_list.addItem(f"  Unidad seleccionada: {unidad['texto']}")
            self.results_list.addItem(f"  Ruta: {unidad['ruta']}")
            self.results_list.addItem("")
            self.results_list.addItem("  Indexando archivos...")
            
            threading.Thread(target=self.indexar_unidad, daemon=True).start()
        except Exception as e:
            print(f"Error seleccionando unidad: {e}")
    
    def indexar_unidad(self):
        """Indexa archivos."""
        try:
            self.todos_los_archivos = []
            
            if not self.unidad_seleccionada:
                return
            
            for root, dirs, files in os.walk(self.unidad_seleccionada):
                for nombre_archivo in files:
                    try:
                        ruta_completa = os.path.join(root, nombre_archivo)
                        self.todos_los_archivos.append({
                            'nombre': nombre_archivo,
                            'ruta': ruta_completa,
                            'extension': os.path.splitext(nombre_archivo)[1].lower()
                        })
                    except:
                        continue
            
            self.todos_los_archivos.sort(key=lambda x: x['nombre'].lower())
            QTimer.singleShot(0, self.mostrar_todos_los_archivos)
        except Exception as e:
            print(f"Error indexando: {e}")
    
    def mostrar_todos_los_archivos(self):
        """Muestra todos los archivos."""
        try:
            self.results_list.clear()
            self.resultados = self.todos_los_archivos
            
            try:
                self.results_list.itemDoubleClicked.disconnect()
            except:
                pass
            self.results_list.itemDoubleClicked.connect(self.abrir_item)
            
            if not self.todos_los_archivos:
                self.results_list.addItem("")
                self.results_list.addItem("  No hay archivos")
                return
            
            self.results_list.addItem("")
            self.results_list.addItem(f"  Total: {len(self.todos_los_archivos)} archivos")
            self.results_list.addItem("")
            self.results_list.addItem("  Doble clic para abrir | Escribe para buscar")
            self.results_list.addItem("")
            self.results_list.addItem("  " + "=" * 80)
            
            for archivo in self.todos_los_archivos[:self.MAX_ARCHIVOS_MOSTRADOS]:
                self.results_list.addItem(f"  {archivo['nombre']}")
            
            restantes = len(self.todos_los_archivos) - self.MAX_ARCHIVOS_MOSTRADOS
            if restantes > 0:
                self.results_list.addItem("")
                self.results_list.addItem(f"  ... y {restantes} archivos más")
        except Exception as e:
            print(f"Error mostrando archivos: {e}")
    
    # ========== BÚSQUEDA ==========
    
    def cambiar_tipo_busqueda(self, boton):
        """Compatibilidad."""
        pass
    
    def _ejecutar_busqueda_diferida(self):
        """Ejecuta búsqueda después del delay."""
        try:
            if not self.unidad_seleccionada or not self.todos_los_archivos:
                return
            
            texto = self.search_input.text().strip().lower()
            
            if not texto:
                self.mostrar_todos_los_archivos()
                return
            
            if self.tipo_busqueda == self.BUSQUEDA_EXTENSION:
                coincidencias = self._buscar_por_extension(texto)
            else:
                coincidencias = self._buscar_por_nombre(texto)
            
            self._mostrar_resultados(coincidencias, texto)
        except Exception as e:
            print(f"Error en búsqueda: {e}")
    
    def buscar_sugerencias(self):
        """Compatibilidad."""
        try:
            self._ejecutar_busqueda_diferida()
        except:
            pass
    
    def _buscar_por_nombre(self, texto: str) -> List[Dict]:
        """Busca por nombre."""
        try:
            coincidencias = []
            for archivo in self.todos_los_archivos:
                try:
                    nombre = os.path.splitext(archivo['nombre'])[0].lower()
                    if texto in nombre:
                        coincidencias.append(archivo)
                except:
                    continue
            return coincidencias
        except:
            return []
    
    def _buscar_por_extension(self, texto: str) -> List[Dict]:
        """Busca por extensión."""
        try:
            if not texto.startswith('.'):
                texto = '.' + texto
            
            coincidencias = []
            for archivo in self.todos_los_archivos:
                try:
                    if archivo['extension'] == texto:
                        coincidencias.append(archivo)
                except:
                    continue
            return coincidencias
        except:
            return []
    
    def _mostrar_resultados(self, coincidencias: List[Dict], texto: str):
        """Muestra resultados."""
        try:
            self.results_list.clear()
            self.resultados = coincidencias
            
            try:
                self.results_list.itemDoubleClicked.disconnect()
            except:
                pass
            self.results_list.itemDoubleClicked.connect(self.abrir_item)
            
            tipo_str = "extensión" if self.tipo_busqueda == self.BUSQUEDA_EXTENSION else "nombre"
            
            self.results_list.addItem("")
            self.results_list.addItem(f"  Búsqueda por {tipo_str}: '{texto}'")
            self.results_list.addItem(f"  Resultados: {len(coincidencias)} archivo(s)")
            self.results_list.addItem("")
            self.results_list.addItem("  " + "=" * 80)
            
            if not coincidencias:
                self.results_list.addItem("")
                self.results_list.addItem("  No se encontraron archivos")
                return
            
            for archivo in coincidencias[:self.MAX_ARCHIVOS_MOSTRADOS]:
                self.results_list.addItem(f"  {archivo['nombre']}")
            
            if len(coincidencias) > self.MAX_ARCHIVOS_MOSTRADOS:
                restantes = len(coincidencias) - self.MAX_ARCHIVOS_MOSTRADOS
                self.results_list.addItem("")
                self.results_list.addItem(f"  ... y {restantes} más")
        except Exception as e:
            print(f"Error mostrando resultados: {e}")
    
    # ========== BÚSQUEDA CONTENIDO ==========
    
    def buscar_por_contenido(self):
        """Busca por contenido."""
        try:
            texto = self.search_input.text().strip()
            
            if not texto:
                self.alerta("Escribe algo para buscar")
                return
            
            if not self.unidad_seleccionada:
                self.alerta("Selecciona una unidad USB")
                return
            
            if not self.todos_los_archivos:
                self.alerta("No hay archivos indexados")
                return
            
            if self.buscando_contenido:
                return
            
            self.buscando_contenido = True
            
            self.historial.agregar(texto)
            self.actualizar_completer()
            
            self.btn_buscar_contenido.setEnabled(False)
            self.btn_buscar_contenido.setText("⏳ BUSCANDO...")
            self.btn_buscar.setEnabled(False)
            self.search_input.setEnabled(False)
            
            self.results_list.clear()
            self.results_list.addItem("")
            self.results_list.addItem("  ⏳ BUSCANDO EN CONTENIDO...")
            self.results_list.addItem("")
            self.results_list.addItem("  📄 Por favor espera...")
            self.results_list.addItem("")
            self.results_list.addItem("  Progreso: 0%")
            
            threading.Thread(
                target=self._ejecutar_busqueda_contenido_thread, 
                args=(texto,), 
                daemon=True
            ).start()
        except Exception as e:
            print(f"Error iniciando búsqueda: {e}")
            self.buscando_contenido = False
    
    def _ejecutar_busqueda_contenido_thread(self, texto: str):
        """Thread de búsqueda."""
        try:
            texto_lower = texto.lower()
            coincidencias = []
            total = len(self.todos_los_archivos)
            
            for idx, archivo in enumerate(self.todos_los_archivos):
                try:
                    if idx % 5 == 0:
                        progreso = int((idx / total) * 100)
                        self.signals.progreso_actualizado.emit(idx, total, progreso)
                    
                    contenido = leer_contenido_archivo(archivo['ruta'])
                    
                    if texto_lower in contenido:
                        coincidencias.append(archivo)
                except:
                    continue
            
            self.signals.busqueda_finalizada.emit(coincidencias, texto)
        except Exception as e:
            self.signals.error_busqueda.emit(str(e))
    
    def _on_progreso_actualizado(self, actual: int, total: int, porcentaje: int):
        """Actualiza progreso."""
        try:
            if self.results_list.count() >= 6:
                item = self.results_list.item(5)
                if item:
                    item.setText(f"  Progreso: {actual}/{total} ({porcentaje}%)")
        except:
            pass
    
    def _on_busqueda_finalizada(self, coincidencias: List[Dict], texto: str):
        """Finaliza búsqueda."""
        try:
            self.buscando_contenido = False
            
            self.btn_buscar_contenido.setEnabled(True)
            self.btn_buscar_contenido.setText("🔍 CONTENIDO")
            self.btn_buscar.setEnabled(True)
            self.search_input.setEnabled(True)
            
            self._mostrar_resultados_contenido(coincidencias, texto)
        except:
            pass
    
    def _on_error_busqueda(self, error: str):
        """Error en búsqueda."""
        try:
            self.buscando_contenido = False
            
            self.btn_buscar_contenido.setEnabled(True)
            self.btn_buscar_contenido.setText("🔍 CONTENIDO")
            self.btn_buscar.setEnabled(True)
            self.search_input.setEnabled(True)
            
            self.results_list.clear()
            self.results_list.addItem("")
            self.results_list.addItem(f"  ❌ Error: {error}")
        except:
            pass
    
    def _mostrar_resultados_contenido(self, coincidencias: List[Dict], texto: str):
        """Muestra resultados de contenido."""
        try:
            self.results_list.clear()
            self.resultados = coincidencias
            
            try:
                self.results_list.itemDoubleClicked.disconnect()
            except:
                pass
            self.results_list.itemDoubleClicked.connect(self.abrir_item)
            
            self.results_list.addItem("")
            self.results_list.addItem(f"  🔍 Búsqueda por CONTENIDO: '{texto}'")
            self.results_list.addItem(f"  ✅ Resultados: {len(coincidencias)} archivo(s)")
            self.results_list.addItem("")
            self.results_list.addItem("  " + "=" * 80)
            
            if not coincidencias:
                self.results_list.addItem("")
                self.results_list.addItem("  ❌ No se encontraron archivos")
                self.results_list.addItem("")
                self.results_list.addItem("  💡 Consejos:")
                self.results_list.addItem("     • Verifica la ortografía")
                self.results_list.addItem("     • Intenta palabras más simples")
                return
            
            self.results_list.addItem("")
            for archivo in coincidencias[:self.MAX_ARCHIVOS_MOSTRADOS]:
                self.results_list.addItem(f"  📄 {archivo['nombre']}")
            
            if len(coincidencias) > self.MAX_ARCHIVOS_MOSTRADOS:
                restantes = len(coincidencias) - self.MAX_ARCHIVOS_MOSTRADOS
                self.results_list.addItem("")
                self.results_list.addItem(f"  ... y {restantes} más")
        except Exception as e:
            print(f"Error mostrando resultados contenido: {e}")
    
    # ========== ACCIONES ==========
    
    def buscar_archivos(self):
        """Buscar archivos."""
        try:
            texto = self.search_input.text().strip()
            
            if not texto:
                return
            
            if not self.unidad_seleccionada:
                self.alerta("Selecciona una unidad USB")
                return
            
            self.historial.agregar(texto)
            self.actualizar_completer()
            
            self._ejecutar_busqueda_diferida()
        except Exception as e:
            print(f"Error buscando: {e}")
    
    def abrir_item(self, item):
        """Abre archivo."""
        try:
            texto = item.text().strip().replace("📄", "").strip()
            
            for archivo in self.resultados:
                if archivo['nombre'] == texto:
                    if platform.system() == 'Windows':
                        os.startfile(archivo['ruta'])
                    elif platform.system() == 'Darwin':
                        subprocess.call(['open', archivo['ruta']])
                    else:
                        subprocess.call(['xdg-open', archivo['ruta']])
                    return
        except Exception as e:
            print(f"Error abriendo: {e}")
    
    def limpiar_historial(self):
        """Limpia historial."""
        try:
            self.historial.limpiar()
            self.actualizar_completer()
        except:
            pass
    
    def mostrar_mensaje_inicial(self):
        """Mensaje inicial."""
        try:
            self.results_list.clear()
            self.results_list.addItem("")
            self.results_list.addItem("  🔍 Buscador de Archivos USB")
            self.results_list.addItem("")
            self.results_list.addItem("  Selecciona una unidad USB...")
            self.results_list.addItem("")
        except:
            pass
    
    def alerta(self, mensaje: str, tipo=QMessageBox.Warning):
        """Muestra alerta."""
        try:
            msg = QMessageBox()
            msg.setIcon(tipo)
            msg.setText(mensaje)
            msg.setWindowTitle("Aviso")
            msg.exec_()
        except:
            pass


# ========== MAIN ==========

def main():
    """Main."""
    try:
        app = QApplication(sys.argv)
        ventana = BuscadorArchivos()
        ventana.show()
        sys.exit(app.exec_())
    except Exception as e:
        print(f"Error crítico: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()