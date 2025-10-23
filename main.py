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
from GestorHistorial import GestorHistorial  # NUEVO: Importar desde archivo separado


def detectar_unidades_disponibles():
    """Detecta unidades extraíbles (USB) en Windows"""
    unidades = []
    for letra in string.ascii_uppercase:
        unidad = f"{letra}:\\"
        if not os.path.exists(unidad) or letra in ['A', 'B', 'C']:
            continue
        try:
            if win32file.GetDriveType(unidad) == 2:  # 2 = Removable
                unidades.append({'texto': f"{letra}:/", 'ruta': unidad})
        except Exception:
            continue
    return unidades


class BuscadorArchivos(VentanaBase):
    def __init__(self):
        super().__init__()
        self.unidad_seleccionada = None
        self.resultados = []
        self.todos_los_archivos = []
        self.unidades_previas = []
        
        # NUEVO: Gestor de historial (importado desde GestorHistorial.py)
        self.historial = GestorHistorial()
        self.completer = None

        self.init_ui()
        self.cargar_unidades()
        self.configurar_autocompletado()

        # Detectar cambios en USB
        self.timer_usb = QTimer()
        self.timer_usb.timeout.connect(self.verificar_cambios_usb)
        self.timer_usb.start(2000)

        # Temporizador para búsqueda en vivo
        self.timer_autocompletar = QTimer()
        self.timer_autocompletar.setSingleShot(True)
        self.timer_autocompletar.timeout.connect(self.buscar_sugerencias)

    # ---------- AUTOCOMPLETADO CON HISTORIAL ----------
    def configurar_autocompletado(self):
        """Configura el autocompletado con historial"""
        self.completer = QCompleter()
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchContains)
        
        # Configurar tamaño del popup
        self.completer.setMaxVisibleItems(15)  # Mostrar hasta 15 items
        
        # Ajustar tamaño del popup
        popup = self.completer.popup()
        popup.setMinimumWidth(600)  # Ancho mínimo
        popup.setMinimumHeight(150)  # Alto mínimo
        
        # Estilo del popup de sugerencias
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
    
    def actualizar_completer(self):
        """Actualiza las sugerencias del completer con el historial"""
        model = QStringListModel()
        model.setStringList(self.historial.historial)
        self.completer.setModel(model)
    
    def on_texto_cambiado(self):
        """Se ejecuta cuando el usuario escribe"""
        texto = self.search_input.text()
        
        # Actualizar sugerencias según el texto
        coincidencias = self.historial.buscar_coincidencias(texto)
        model = QStringListModel()
        model.setStringList(coincidencias)
        self.completer.setModel(model)
        
        # Iniciar búsqueda en vivo
        self.iniciar_autocompletado()

    # ---------- DETECCIÓN USB ----------
    def cargar_unidades(self):
        unidades = detectar_unidades_disponibles()
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
            btn.clicked.connect(lambda _, i=info: self.seleccionar_unidad(i))
            self.units_layout.addWidget(btn)

    def verificar_cambios_usb(self):
        actuales = detectar_unidades_disponibles()
        letras_actuales = {u['texto'] for u in actuales}
        letras_previas = {u['texto'] for u in self.unidades_previas}
        if letras_actuales != letras_previas:
            self.cargar_unidades()
        self.unidades_previas = actuales

    # ---------- FUNCIONALIDAD ----------
    def seleccionar_unidad(self, unidad):
        self.unidad_seleccionada = unidad['ruta']
        self.results_list.clear()
        self.results_list.addItem("")
        self.results_list.addItem(f"  ✓ Unidad seleccionada: {unidad['texto']}")
        self.results_list.addItem(f"  📁 Ruta: {unidad['ruta']}")
        self.results_list.addItem("")
        self.results_list.addItem("  ⏳ Indexando archivos...")
        self.results_list.addItem("")
        
        # Indexar archivos en segundo plano
        threading.Thread(target=self.indexar_unidad, daemon=True).start()

    def indexar_unidad(self):
        """Recorre la unidad y guarda todos los nombres de archivo"""
        self.todos_los_archivos = []
        if not self.unidad_seleccionada:
            return
        
        try:
            for root, _, files in os.walk(self.unidad_seleccionada):
                for f in files:
                    self.todos_los_archivos.append({
                        'nombre': f, 
                        'ruta': os.path.join(root, f)
                    })
            
            # Ordenar
            self.todos_los_archivos.sort(key=lambda x: x['nombre'].lower())
            
            # Mostrar confirmación
            self.results_list.clear()
            self.results_list.addItem("")
            self.results_list.addItem(f"  ✅ {len(self.todos_los_archivos)} archivos indexados")
            self.results_list.addItem("")
            self.results_list.addItem("  💡 Empieza a escribir para buscar...")
            
        except Exception as e:
            self.alerta(f"Error al indexar: {e}")

    def iniciar_autocompletado(self):
        """Activa el temporizador para búsqueda"""
        if not self.unidad_seleccionada or not self.todos_los_archivos:
            return
        self.timer_autocompletar.start(300)

    def buscar_sugerencias(self):
        """Filtra coincidencias en vivo según lo tecleado"""
        texto = self.search_input.text().strip().lower()
        if not texto:
            self.results_list.clear()
            self.results_list.addItem("")
            self.results_list.addItem("  💡 Escribe para buscar archivos...")
            return
        
        coincidencias = [
            f for f in self.todos_los_archivos 
            if texto in f['nombre'].lower()
        ]
        coincidencias = sorted(coincidencias, key=lambda x: x['nombre'].lower())
        self.mostrar_sugerencias(coincidencias)

    def mostrar_sugerencias(self, coincidencias):
        self.results_list.clear()
        self.resultados = coincidencias

        # Evitar conexiones múltiples
        try:
            self.results_list.itemDoubleClicked.disconnect()
        except TypeError:
            pass

        self.results_list.itemDoubleClicked.connect(self.abrir_item)

        if not coincidencias:
            self.results_list.addItem("")
            self.results_list.addItem("  ❌ Sin coincidencias...")
            self.results_list.addItem("")
            return

        

        # Limitar a 200 resultados para no saturar
        for c in coincidencias[:200]:
            self.results_list.addItem(f"  📄 {c['nombre']}")

    def buscar_archivos(self):
        """Búsqueda manual con botón"""
        texto = self.search_input.text().strip()
        
        if not self.unidad_seleccionada:
            self.alerta("Por favor, selecciona una unidad primero.")
            return
        
        if not texto:
            self.alerta("Escribe un nombre para buscar.")
            return
        
        # Agregar al historial
        self.historial.agregar(texto)
        self.actualizar_completer()
        
        # Realizar búsqueda
        self.buscar_sugerencias()

    def abrir_item(self, item):
        nombre = item.text().strip()
        
        # Remover emoji si existe
        if nombre.startswith("📄"):
            nombre = nombre[2:].strip()
        
        for r in self.resultados:
            if r['nombre'] == nombre:
                # Agregar al historial al abrir
                self.historial.agregar(r['nombre'])
                self.actualizar_completer()
                self.abrir_archivo(r['ruta'])
                break

    # ---------- UTILIDADES ----------
    def abrir_archivo(self, ruta):
        """Abre archivos permitidos"""
        try:
            extension = os.path.splitext(ruta)[1].lower()
            extensiones_permitidas = {
                '.mp3', '.docx', '.xlsx', '.pdf', '.txt', '.exe', '.mp4', 
                '.jpg', '.jpeg', '.rar', '.zip', '.gif', '.png', '.pptx',
                '.wav', '.avi', '.mkv', '.mov', '.ppt', '.xls', '.doc'
            }

            if extension not in extensiones_permitidas:
                self.alerta(
                    f"No se permite abrir archivos con la extensión '{extension}'.\n"
                    f"Solo se admiten: {', '.join(sorted(extensiones_permitidas))}"
                )
                return

            sistema = platform.system()
            if sistema == "Windows":
                os.startfile(ruta)
            elif sistema == "Darwin":
                subprocess.run(["open", ruta])
            else:
                subprocess.run(["xdg-open", ruta])

        except Exception as e:
            self.alerta(f"No se pudo abrir el archivo:\n{e}")

    def limpiar_historial(self):
        """Limpia todo el historial"""
        respuesta = QMessageBox.question(
            self, 
            "Limpiar Historial",
            "¿Estás seguro de que quieres borrar todo el historial de búsquedas?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if respuesta == QMessageBox.Yes:
            self.historial.limpiar()
            self.actualizar_completer()
            self.alerta("Historial limpiado correctamente")

    def alerta(self, mensaje):
        msg = QMessageBox(self)
        msg.setWindowTitle("Aviso")
        msg.setText(mensaje)
        msg.setStyleSheet("""
            QMessageBox {
                background-color: #2B313F;
                color: white;
            }
            QLabel {
                color: white;
                font-size: 14px;
            }
            QPushButton {
                background-color: #E32D64;
                color: white;
                padding: 8px 20px;
                border-radius: 5px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #FF3D7F;
            }
        """)
        msg.exec_()

    def mostrar_mensaje_inicial(self):
        self.results_list.clear()
        self.results_list.addItem("")
        self.results_list.addItem("  1️  Conecta y selecciona una USB del panel izquierdo")
        self.results_list.addItem("")
        self.results_list.addItem("  2️  Escribe el nombre del archivo")
        self.results_list.addItem("")

        # NUEVO: mostrar historial completo al hacer clic
        self.search_input.mousePressEvent = self.mostrar_historial_al_click

    def mostrar_historial_al_click(self, event):
        """Muestra el historial completo al hacer clic en la barra de búsqueda"""
        try:
            # Actualizar modelo del completer con todo el historial
            model = QStringListModel()
            model.setStringList(self.historial.historial)
            self.completer.setModel(model)

            # Mostrar manualmente el popup del completer
            self.completer.complete()
        except Exception as e:
            print("Error al mostrar historial:", e)

        # Ejecutar el evento normal del click para que no se pierda el foco
        QLineEdit.mousePressEvent(self.search_input, event)


# ---------- MAIN ----------
def main():
    app = QApplication(sys.argv)
    ventana = BuscadorArchivos()
    ventana.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()