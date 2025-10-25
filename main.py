"""
Script de prueba para verificar el funcionamiento del GestorHistorial
"""

import sys
import os

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(__file__))

from GestorHistorial import GestorHistorial

def main():
    print("=" * 60)
    print("PRUEBA DEL GESTOR DE HISTORIAL")
    print("=" * 60)
    
    # Crear instancia del gestor
    historial = GestorHistorial('test_historial.json')
    
    # Agregar búsquedas
    print("\n1. Agregando búsquedas...")
    historial.agregar("archivo1")
    print("   ✓ Agregado: archivo1")
    
    historial.agregar("documento2")
    print("   ✓ Agregado: documento2")
    
    historial.agregar("imagen3")
    print("   ✓ Agregado: imagen3")
    
    historial.agregar("python")
    print("   ✓ Agregado: python")
    
    # Mostrar todo el historial
    print("\n2. Historial completo (más recientes primero):")
    todos = historial.obtener_todos()
    for i, item in enumerate(todos, 1):
        print(f"   {i}. {item}")
    
    # Intentar agregar duplicado
    print("\n3. Intentando agregar duplicado 'python'...")
    resultado = historial.agregar("python")
    if resultado:
        print("   ✓ No se agregó (ya existe)")
    
    print("\n4. Historial después del duplicado:")
    todos = historial.obtener_todos()
    for i, item in enumerate(todos, 1):
        print(f"   {i}. {item}")
    
    # Agregar más búsquedas
    print("\n5. Agregando más búsquedas...")
    historial.agregar("javascript")
    print("   ✓ Agregado: javascript")
    
    historial.agregar("css")
    print("   ✓ Agregado: css")
    
    # Mostrar historial final
    print("\n6. Historial final (más recientes primero):")
    todos = historial.obtener_todos()
    for i, item in enumerate(todos, 1):
        print(f"   {i}. {item}")
    
    # Verificar total
    print(f"\n7. Total de búsquedas: {historial.total_busquedas()}")
    
    # Buscar coincidencias
    print("\n8. Buscando coincidencias con 'java':")
    coincidencias = historial.buscar_coincidencias("java")
    for i, item in enumerate(coincidencias, 1):
        print(f"   {i}. {item}")
    
    # Limpiar al final
    print("\n9. Limpiando historial...")
    historial.cerrar_sesion()
    print("   ✓ Historial limpiado y archivo eliminado")
    
    print("\n" + "=" * 60)
    print("✅ PRUEBA COMPLETADA EXITOSAMENTE")
    print("=" * 60)

if __name__ == "__main__":
    main()