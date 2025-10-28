import os
import sys
import string
import threading
import subprocess
import platform
from typing import List, Dict, Optional
import win32file
from collections import defaultdict

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
from lectores import leer_contenido_archivo as leer_contenido_archivo_factory


# CONSTANTES
EXTENSIONES_TEXTO = {
    '.txt', '.log', '.csv', '.json', '.xml', '.html', 
    '.py', '.js', '.css', '.md', '.ini', '.conf'
}

ENCODINGS_TEXTO = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']


# SEÑALES
class Signals(QObject):
    """Señales para comunicación thread-safe."""
    progreso_actualizado = pyqtSignal(int, int, int)
    busqueda_finalizada = pyqtSignal(list, str)
    error_busqueda = pyqtSignal(str)
    indexacion_completa = pyqtSignal(int)


# FUNCIONES AUXILIARES
def detectar_unidades_disponibles() -> List[Dict[str, str]]:
    """Detecta unidades extraíbles USB."""
    import win32api
    unidades = []
    
    for letra in string.ascii_uppercase:
        unidad = f"{letra}:\\"
        
        if letra in ['A', 'B', 'C']:
            continue
        
        if not os.path.exists(unidad):
            continue
        
        try:
            tipo_unidad = win32file.GetDriveType(unidad)
            
            if tipo_unidad not in [2, 3]:
                continue
            
            # Obtener etiqueta del volumen
            try:
                volume_info = win32api.GetVolumeInformation(unidad)
                etiqueta = volume_info[0]
                
                if etiqueta:
                    texto = f"{letra}:/ {etiqueta}"
                else:
                    texto = f"{letra}:/ {'USB Removible' if tipo_unidad == 2 else 'Disco Externo'}"
            except:
                texto = f"{letra}:/"
            
            unidades.append({
                'texto': texto,
                'ruta': unidad
            })
        except:
            continue
    
    return unidades


def leer_contenido_archivo(ruta: str) -> str:
    """Lee contenido de un archivo usando Factory Pattern."""
    return leer_contenido_archivo_factory(ruta)


# CLASE PRINCIPAL
class BuscadorArchivos(VentanaBase):
    """Clase principal del buscador - Corregida sin duplicación."""
    
    INTERVALO_DETECCION_USB = 3000
    DELAY_BUSQUEDA_VIVO = 200
    MAX_ARCHIVOS_MOSTRADOS = 999999999
    UPDATE_INTERVAL = 2500
    
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
        self.indexando = False
        
        # Control de threads
        self.thread_indexacion_activo = None
        self.cancelar_indexacion = False
        self.lock_indexacion = threading.Lock()
        
        # Índices para búsqueda ultra-rápida
        self.indice_nombres = defaultdict(list)
        self.indice_extensiones = defaultdict(list)
        
        # Señales
        self.signals = Signals()
        self.signals.progreso_actualizado.connect(self._on_progreso_actualizado)
        self.signals.busqueda_finalizada.connect(self._on_busqueda_finalizada)
        self.signals.error_busqueda.connect(self._on_error_busqueda)
        self.signals.indexacion_completa.connect(self._on_indexacion_completa)
        
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
    
    # AUTOCOMPLETADO
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
        """Cuando cambia el texto."""
        try:
            if self.buscando_contenido or self.indexando:
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
            elif texto_limpio.startswith('@'):
                self.tipo_busqueda = self.BUSQUEDA_CONTENIDO
            elif texto_limpio.startswith('.'):
                self.tipo_busqueda = self.BUSQUEDA_EXTENSION
            else:
                self.tipo_busqueda = self.BUSQUEDA_NOMBRE
        except:
            self.tipo_busqueda = self.BUSQUEDA_NOMBRE
    
    # USB
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
                if self.unidad_seleccionada:
                    letra_seleccionada = self.unidad_seleccionada[0] + ":/"
                    
                    if letra_seleccionada not in letras_actuales:
                        # Cancelar indexación si está en proceso
                        self.cancelar_indexacion = True
                        
                        self.unidad_seleccionada = None
                        self.resultados = []
                        self.todos_los_archivos = []
                        self.indice_nombres.clear()
                        self.indice_extensiones.clear()
                        self.indexando = False
                        self.mostrar_mensaje_inicial()
                
                self.cargar_unidades()
            
            self.unidades_previas = actuales
        except:
            pass
    
    # INDEXACIÓN SIN DUPLICADOS
    def seleccionar_unidad(self, unidad: Dict[str, str]):
        """Selecciona unidad sin duplicar indexación."""
        try:
            # Si ya está indexando, cancelar y esperar
            if self.indexando:
                print("Ya hay una indexacion en proceso, cancelando...")
                self.cancelar_indexacion = True
                
                # Esperar a que termine el thread anterior
                if self.thread_indexacion_activo and self.thread_indexacion_activo.is_alive():
                    self.thread_indexacion_activo.join(timeout=2.0)
                
                self.indexando = False
            
            # Limpiar estado anterior
            with self.lock_indexacion:
                self.todos_los_archivos = []
                self.indice_nombres.clear()
                self.indice_extensiones.clear()
                self.resultados = []
                self.cancelar_indexacion = False
            
            self.unidad_seleccionada = unidad['ruta']
            self.indexando = True
            
            self.results_list.clear()
            self.results_list.addItem("")
            self.results_list.addItem(f"  Unidad seleccionada: {unidad['texto']}")
            self.results_list.addItem(f"  Ruta: {unidad['ruta']}")
            self.results_list.addItem("")
            self.results_list.addItem("  Indexando archivos...")
            self.results_list.addItem("  Progreso: 0 archivos")
            
            # Iniciar nuevo thread
            self.thread_indexacion_activo = threading.Thread(
                target=self.indexar_unidad_ultra_optimizado, 
                daemon=True
            )
            self.thread_indexacion_activo.start()
            
        except Exception as e:
            print(f"Error seleccionando unidad: {e}")
            self.indexando = False
    
    def indexar_unidad_ultra_optimizado(self):
        """Indexa archivos de forma ultra-optimizada con índices."""
        archivos_temp = []
        indices_nombres_temp = defaultdict(list)
        indices_ext_temp = defaultdict(list)
        
        try:
            if not self.unidad_seleccionada:
                return
            
            contador = 0
            ultimo_update = 0
            
            # Directorios a ignorar
            DIRS_IGNORAR = {
                '$RECYCLE.BIN', 'System Volume Information', '$Recycle.Bin',
                'RECYCLER', 'Config.Msi', 'Recovery', '$Windows.~BT',
                'Windows.old', 'PerfLogs', 'hiberfil.sys', 'pagefile.sys'
            }
            
            for root, dirs, files in os.walk(self.unidad_seleccionada):
                # Verificar cancelación
                if self.cancelar_indexacion:
                    print("Indexacion cancelada")
                    return
                
                # Filtrar directorios del sistema (in-place)
                dirs[:] = [d for d in dirs if d not in DIRS_IGNORAR and not d.startswith('$')]
                
                for nombre_archivo in files:
                    # Verificar cancelación
                    if self.cancelar_indexacion:
                        print("Indexacion cancelada")
                        return
                    
                    try:
                        ruta_completa = os.path.join(root, nombre_archivo)
                        extension = os.path.splitext(nombre_archivo)[1].lower()
                        
                        # Agregar archivo a lista temporal
                        archivo_dict = {
                            'nombre': nombre_archivo,
                            'ruta': ruta_completa,
                            'extension': extension
                        }
                        
                        indice = len(archivos_temp)
                        archivos_temp.append(archivo_dict)
                        
                        # Crear índices temporales
                        nombre_sin_ext = os.path.splitext(nombre_archivo)[0].lower()
                        indices_nombres_temp[nombre_sin_ext].append(indice)
                        indices_ext_temp[extension].append(indice)
                        
                        contador += 1
                        
                        # Actualizar progreso cada UPDATE_INTERVAL archivos
                        if contador - ultimo_update >= self.UPDATE_INTERVAL:
                            self.signals.progreso_actualizado.emit(contador, 0, 0)
                            ultimo_update = contador
                    except Exception as e:
                        continue
            
            # Solo actualizar si no fue cancelado
            if not self.cancelar_indexacion:
                with self.lock_indexacion:
                    self.todos_los_archivos = archivos_temp
                    self.indice_nombres = indices_nombres_temp
                    self.indice_extensiones = indices_ext_temp
                
                # Notificar finalización
                self.signals.indexacion_completa.emit(len(self.todos_los_archivos))
            
        except Exception as e:
            print(f"Error indexando: {e}")
            self.indexando = False
    
    def _on_indexacion_completa(self, total):
        """Callback cuando termina la indexación."""
        try:
            self.indexando = False
            self.cancelar_indexacion = False
            
            print(f"Indexacion completa: {total:,} archivos")
            print(f"Indices creados: {len(self.indice_nombres)} nombres, {len(self.indice_extensiones)} extensiones")
            
            self.mostrar_todos_los_archivos()
        except:
            pass
    
    def _on_progreso_actualizado(self, actual, total, porcentaje):
        """Actualiza progreso de indexación."""
        try:
            if self.indexando and self.results_list.count() >= 6:
                item = self.results_list.item(5)
                if item:
                    item.setText(f"  Progreso: {actual:,} archivos")
        except:
            pass
    
    def mostrar_todos_los_archivos(self):
        """Muestra todos los archivos de forma eficiente."""
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
            
            total = len(self.todos_los_archivos)
            self.results_list.addItem(f"  Total: {total:,} archivos indexados")
            self.results_list.addItem(f"  Indices: {len(self.indice_nombres):,} nombres, {len(self.indice_extensiones):,} extensiones")
            self.results_list.addItem("  " + "_" * 80)
            
            # Mostrar solo los primeros archivos
            limite = min(self.MAX_ARCHIVOS_MOSTRADOS, total)
            for archivo in self.todos_los_archivos[:limite]:
                self.results_list.addItem(f"  {archivo['nombre']}")
            
            if total > self.MAX_ARCHIVOS_MOSTRADOS:
                restantes = total - self.MAX_ARCHIVOS_MOSTRADOS
                self.results_list.addItem("")
                self.results_list.addItem(f"  ... y {restantes:,} archivos mas (usa busqueda)")
        
        except Exception as e:
            print(f"Error mostrando archivos: {e}")
    
    # BÚSQUEDA ULTRA-RÁPIDA CON ÍNDICES
    def _ejecutar_busqueda_diferida(self):
        """Ejecuta búsqueda diferida."""
        try:
            if self.buscando_contenido or self.indexando:
                return
            
            if not self.unidad_seleccionada:
                return
            
            texto = self.search_input.text().strip()
            
            if not texto:
                self.mostrar_todos_los_archivos()
                return
            
            # Búsqueda por contenido
            if self.tipo_busqueda == self.BUSQUEDA_CONTENIDO:
                self._buscar_por_contenido_automatico(texto)
                return
            
            texto_lower = texto.lower()
            
            if self.tipo_busqueda == self.BUSQUEDA_EXTENSION:
                coincidencias = self._buscar_por_extension_indexado(texto_lower)
            else:
                coincidencias = self._buscar_por_nombre_indexado(texto_lower)
            
            self._mostrar_resultados(coincidencias, texto_lower)
        except Exception as e:
            print(f"Error en busqueda: {e}")
    
    def _buscar_por_nombre_indexado(self, texto: str) -> List[Dict]:
        """Búsqueda por nombre ultra-rápida usando índice."""
        try:
            coincidencias = []
            indices_encontrados = set()
            
            # Buscar en índice de nombres
            for nombre_indexado, lista_indices in self.indice_nombres.items():
                if texto in nombre_indexado:
                    indices_encontrados.update(lista_indices)
            
            # Obtener archivos usando índices
            for idx in sorted(indices_encontrados):
                if idx < len(self.todos_los_archivos):
                    coincidencias.append(self.todos_los_archivos[idx])
                    if len(coincidencias) >= 50000:
                        break
            
            return coincidencias
        except Exception as e:
            print(f"Error en busqueda indexada: {e}")
            return []
    
    def _buscar_por_extension_indexado(self, texto: str) -> List[Dict]:
        """Búsqueda por extensión ultra-rápida usando índice."""
        try:
            if not texto.startswith('.'):
                texto = '.' + texto
            
            # Búsqueda directa en índice
            indices = self.indice_extensiones.get(texto, [])
            
            coincidencias = []
            for idx in indices:
                if idx < len(self.todos_los_archivos):
                    coincidencias.append(self.todos_los_archivos[idx])
            
            return coincidencias
        except Exception as e:
            print(f"Error en busqueda extension: {e}")
            return []
    
    def _buscar_por_contenido_automatico(self, texto: str):
        """Búsqueda por contenido."""
        try:
            texto_busqueda = texto[1:].strip() if texto.startswith('@') else texto.strip()
            
            if not texto_busqueda:
                self.alerta("Escribe algo despues del @")
                return
            
            if not self.unidad_seleccionada:
                self.alerta("Selecciona una unidad USB primero")
                return
            
            if not self.todos_los_archivos:
                self.alerta("No hay archivos indexados")
                return
            
            if self.buscando_contenido:
                return
            
            self.buscando_contenido = True
            
            self.historial.agregar(texto)
            self.actualizar_completer()
            
            self.btn_buscar.setEnabled(False)
            self.search_input.setEnabled(False)
            
            self.results_list.clear()
            self.results_list.addItem("")
            self.results_list.addItem("  BUSCANDO EN CONTENIDO...")
            self.results_list.addItem("")
            self.results_list.addItem("  Por favor espera...")
            self.results_list.addItem("")
            self.results_list.addItem("  Progreso: 0%")
            
            threading.Thread(
                target=self._ejecutar_busqueda_contenido_thread, 
                args=(texto_busqueda,), 
                daemon=True
            ).start()
            
        except Exception as e:
            print(f"Error iniciando busqueda por contenido: {e}")
            self.buscando_contenido = False
    
    def _ejecutar_busqueda_contenido_thread(self, texto: str):
        """Thread de búsqueda por contenido."""
        try:
            texto_lower = texto.lower()
            coincidencias = []
            total = len(self.todos_los_archivos)
            
            for idx, archivo in enumerate(self.todos_los_archivos):
                try:
                    if idx % 10 == 0:
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
    
    def _on_busqueda_finalizada(self, coincidencias: List[Dict], texto: str):
        """Finaliza búsqueda."""
        try:
            self.buscando_contenido = False
            
            self.btn_buscar.setEnabled(True)
            self.search_input.setEnabled(True)
            
            self._mostrar_resultados_contenido(coincidencias, texto)
        except:
            pass
    
    def _on_error_busqueda(self, error: str):
        """Error en búsqueda."""
        try:
            self.buscando_contenido = False
            
            self.btn_buscar.setEnabled(True)
            self.search_input.setEnabled(True)
            
            self.results_list.clear()
            self.results_list.addItem("")
            self.results_list.addItem(f"  Error: {error}")
        except:
            pass
    
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
            
            tipo_str = "extension" if self.tipo_busqueda == self.BUSQUEDA_EXTENSION else "nombre"
            
            self.results_list.addItem("")
            self.results_list.addItem(f"  Busqueda por {tipo_str}: '{texto}'")
            self.results_list.addItem(f"  Resultados: {len(coincidencias):,} archivo(s)")
            self.results_list.addItem("")
            self.results_list.addItem("  " + "=" * 80)
            
            if not coincidencias:
                self.results_list.addItem("")
                self.results_list.addItem("  No se encontraron archivos")
                return
            
            limite = min(self.MAX_ARCHIVOS_MOSTRADOS, len(coincidencias))
            for archivo in coincidencias[:limite]:
                self.results_list.addItem(f"  {archivo['nombre']}")
            
            if len(coincidencias) > self.MAX_ARCHIVOS_MOSTRADOS:
                restantes = len(coincidencias) - self.MAX_ARCHIVOS_MOSTRADOS
                self.results_list.addItem("")
                self.results_list.addItem(f"  ... y {restantes:,} mas")
        except Exception as e:
            print(f"Error mostrando resultados: {e}")
    
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
            self.results_list.addItem(f"  Busqueda por CONTENIDO: '{texto}'")
            self.results_list.addItem(f"  Resultados: {len(coincidencias):,} archivo(s)")
            self.results_list.addItem("")
            self.results_list.addItem("  " + "=" * 80)
            
            if not coincidencias:
                self.results_list.addItem("")
                self.results_list.addItem("  No se encontraron archivos")
                self.results_list.addItem("")
                self.results_list.addItem("  Consejos:")
                self.results_list.addItem("     - Verifica la ortografia")
                self.results_list.addItem("     - Intenta palabras mas simples")
                return
            
            self.results_list.addItem("")
            limite = min(self.MAX_ARCHIVOS_MOSTRADOS, len(coincidencias))
            for archivo in coincidencias[:limite]:
                self.results_list.addItem(f"   {archivo['nombre']}")
            
            if len(coincidencias) > self.MAX_ARCHIVOS_MOSTRADOS:
                restantes = len(coincidencias) - self.MAX_ARCHIVOS_MOSTRADOS
                self.results_list.addItem("")
                self.results_list.addItem(f"  ... y {restantes:,} mas")
        except Exception as e:
            print(f"Error mostrando resultados contenido: {e}")
    
    # ACCIONES
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
            texto = item.text().strip()
            
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
            self.results_list.addItem("  Buscador de Archivos USB")
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


# MAIN
def main():
    """Main."""
    try:
        app = QApplication(sys.argv)
        ventana = BuscadorArchivos()
        ventana.show()
        sys.exit(app.exec_())
    except Exception as e:
        print(f"Error critico: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()