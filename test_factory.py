"""Test rápido del Factory Pattern"""

from lectores import leer_contenido_archivo, LectorFactory

# Ver extensiones soportadas
print("Extensiones soportadas:")
print(LectorFactory.obtener_extensiones_soportadas())

# Probar con un archivo
print("\nProbando lectura:")
lector = LectorFactory.crear_lector('test.pdf')
print(f"Lector seleccionado: {type(lector).__name__}")