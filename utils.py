import os
import sys
import string
import threading
import subprocess
import platform
import win32file
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QListWidget, QLabel, QMessageBox, QFrame
)
from PyQt5.QtCore import Qt, QTimer
from ventana import VentanaBase


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

        self.init_ui()
        self.cargar_unidades()

        # Detectar cambios en USB
        self.timer_usb = QTimer()
        self.timer_usb.timeout.connect(self.verificar_cambios_usb)
        self.timer_usb.start(2000)

        # Temporizador para búsqueda en vivo
        self.timer_autocompletar = QTimer()
        self.timer_autocompletar.setSingleShot(True)
        self.timer_autocompletar.timeout.connect(self.buscar_sugerencias)

    # ---------- DETECCIÓN USB ----------
    def cargar_unidades(self):
        unidades = detectar_unidades_disponibles()
        for i in reversed(range(self.units_layout.count())):
            widget = self.units_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        if not unidades:
            lbl = QLabel("No hay unidades externas detectadas")
            lbl.setAlignment(Qt.AlignCenter)
            self.units_layout.addWidget(lbl)
            return

        for info in unidades:
            btn = QPushButton(info['texto'])
            btn.setFixedHeight(60)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #2B313F; color: white;
                    font-size: 20px;
                    border-radius: 15px;
                } QPushButton:hover { background-color: #4a4a4c; }
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
        self.results_list.addItem(f"Unidad seleccionada: {unidad['texto']}")
        self.results_list.addItem("Escribe un nombre de archivo para buscar...")
        # Indexar archivos en segundo plano (una sola vez)
        threading.Thread(target=self.indexar_unidad, daemon=True).start()

    def indexar_unidad(self):
        """Recorre la unidad y guarda todos los nombres de archivo"""
        self.todos_los_archivos = []
        if not self.unidad_seleccionada:
            return
        for root, _, files in os.walk(self.unidad_seleccionada):
            for f in files:
                self.todos_los_archivos.append({'nombre': f, 'ruta': os.path.join(root, f)})
        # Ordenar solo una vez
        self.todos_los_archivos.sort(key=lambda x: x['nombre'].lower())

    def iniciar_autocompletado(self):
        """Activa el temporizador para búsqueda"""
        if not self.unidad_seleccionada or not self.todos_los_archivos:
            return
        self.timer_autocompletar.start(300)  # Espera 300 ms tras dejar de teclear

    def buscar_sugerencias(self):
        """Filtra coincidencias en vivo según lo tecleado"""
        texto = self.search_input.text().strip().lower()
        if not texto:
            self.results_list.clear()
            return
        coincidencias = [f for f in self.todos_los_archivos if f['nombre'].lower().startswith(texto)]
        coincidencias = sorted(coincidencias, key=lambda x: x['nombre'].lower())
        self.mostrar_sugerencias(coincidencias)

    def mostrar_sugerencias(self, coincidencias):
        self.results_list.clear()
        self.resultados = coincidencias
        if not coincidencias:
            self.results_list.addItem("Sin coincidencias...")
            return
        for c in coincidencias[:200]:  # límite para mantener fluidez
            self.results_list.addItem(c['nombre'])
        self.results_list.itemDoubleClicked.connect(self.abrir_item)

    def buscar_archivos(self):
        """Búsqueda manual con botón"""
        texto = self.search_input.text().strip().lower()
        if not texto:
            self.alerta("Escribe un nombre para buscar.")
            return
        self.buscar_sugerencias()  # reutiliza el mismo filtrado

    def abrir_item(self, item):
        nombre = item.text().strip()
        for r in self.resultados:
            if r['nombre'] == nombre:
                self.abrir_archivo(r['ruta'])
                break

    # ---------- UTILIDADES ----------
    def abrir_archivo(self, ruta):
        """Abre solo archivos permitidos (.mp3, .docx, .xlsx, .pdf, .txt, .exe, .mp4, .jpg, .jpeg, .rar, .zip, .gif)."""
        try:
            extension = os.path.splitext(ruta)[1].lower()
            extensiones_permitidas = {
                '.mp3', '.docx', '.xlsx', '.pdf', '.txt', '.exe', '.mp4', '.jpg', '.jpeg', '.rar', '.zip', '.gif'
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


    def alerta(self, mensaje):
        QMessageBox.warning(self, "Aviso", mensaje)

    def mostrar_mensaje_inicial(self):
        self.results_list.clear()
        self.results_list.addItem("1. Selecciona una unidad del panel izquierdo")
        self.results_list.addItem("2. Escribe el nombre del archivo")
        self.results_list.addItem("3. Doble clic para abrir el archivo")


# ---------- MAIN ----------
def main():
    app = QApplication(sys.argv)
    ventana = BuscadorArchivos()
    ventana.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()