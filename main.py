"""
main.py
Menú de consola del aplicativo (sección 12 del enunciado, RF20).
"""

import sys

import transformaciones as tr
from historial import Historial
from lector import leer_desde_archivo, leer_desde_consola
from validador import validar_gramatica

MENU = """
========== DEPURACIÓN Y FORMA NORMAL DE CHOMSKY ==========
 1. Ingresar gramática
 2. Mostrar gramática original
 3. Validar gramática
 4. Eliminar producciones nulas
 5. Eliminar producciones unitarias
 6. Eliminar variables inútiles
 7. Eliminar variables inalcanzables
 8. Convertir a Forma Normal de Chomsky
 9. Ejecutar proceso completo
10. Mostrar historial de transformaciones
11. Mostrar gramática final
12. Ingresar nueva gramática
13. Salir
(Modo paso a paso: opciones 4 a 8 en ese orden. Modo automático: opción 9.)"""


class Aplicacion:
    def __init__(self):
        self.reiniciar()

    def reiniciar(self):
        self.original = None
        self.actual = None
        self.errores_sintaxis = []
        self.validada = False
        self.historial = Historial()

    def ingresar(self):
        forma = input("¿Cómo desea ingresarla? 1) Escribirla  2) Cargar archivo: ").strip()
        try:
            if forma == "2":
                ruta = input("Ruta del archivo: ").strip().strip('"')
                gramatica, errores = leer_desde_archivo(ruta)
            else:
                gramatica, errores = leer_desde_consola()
        except OSError as error:
            print(f"Error: no se pudo abrir el archivo ({error}).")
            return
        self.cargar(gramatica, errores)

    def cargar(self, gramatica, errores_sintaxis):
        self.reiniciar()
        self.original = gramatica
        self.actual = gramatica.copia()
        self.errores_sintaxis = list(errores_sintaxis)
        print("\nGramática registrada:")
        print(self.original)
        self.validar()

    def validar(self):
        if not self._hay_gramatica():
            return
        errores = self.errores_sintaxis + validar_gramatica(self.original)
        if errores:
            self.validada = False
            print("\nLa gramática tiene errores. Corríjalos antes de transformarla:")
            for error in dict.fromkeys(errores):
                print("  " + error)
        else:
            self.validada = True
            print("\nLa gramática es válida.")

    def ejecutar_etapa(self, *funciones):
        if not self._lista_para_transformar():
            return
        for funcion in funciones:
            try:
                nueva, paso = funcion(self.actual)
            except NotImplementedError:
                print(f"\n[Pendiente] La etapa '{funcion.__name__}' aún no está implementada.")
                return
            self.actual = nueva
            self.historial.agregar(paso)
            print(paso.a_texto(len(self.historial.pasos)))

    def proceso_completo(self):
        if not self._lista_para_transformar():
            return
        self.historial.limpiar()
        self.actual, pendiente = tr.ejecutar_proceso_completo(self.original.copia(), self.historial)
        print(self.historial.a_texto())
        if pendiente:
            print(f"[Pendiente] El proceso se detuvo en '{pendiente}'.")
        else:
            self.mostrar_final()

    def mostrar_final(self):
        if not self._hay_gramatica():
            return
        print("\nGRAMÁTICA FINAL:")
        print(self.actual)

    def _hay_gramatica(self):
        if self.original is None:
            print("Primero ingrese una gramática (opción 1).")
            return False
        return True

    def _lista_para_transformar(self):
        if not self._hay_gramatica():
            return False
        if not self.validada:
            print("La gramática no ha sido validada o tiene errores (opción 3).")
            return False
        return True

    def ejecutar_menu(self):
        acciones = {
            "1": self.ingresar,
            "2": lambda: print(self.original) if self._hay_gramatica() else None,
            "3": self.validar,
            "4": lambda: self.ejecutar_etapa(tr.eliminar_producciones_nulas),
            "5": lambda: self.ejecutar_etapa(tr.eliminar_producciones_unitarias),
            "6": lambda: self.ejecutar_etapa(tr.eliminar_variables_inutiles),
            "7": lambda: self.ejecutar_etapa(tr.eliminar_variables_inalcanzables),
            "8": lambda: self.ejecutar_etapa(tr.sustituir_terminales,
                                             tr.reducir_producciones_largas),
            "9": self.proceso_completo,
            "10": lambda: print(self.historial.a_texto()),
            "11": self.mostrar_final,
            "12": lambda: (self.reiniciar(), self.ingresar()),
        }
        while True:
            print(MENU)
            opcion = input("Seleccione una opción: ").strip()
            if opcion == "13":
                print("Hasta luego.")
                break
            accion = acciones.get(opcion)
            if accion:
                accion()
            else:
                print("Opción no válida. Escriba un número del 1 al 13.")


def main():
    app = Aplicacion()
    if len(sys.argv) > 1:
        gramatica, errores = leer_desde_archivo(sys.argv[1])
        app.cargar(gramatica, errores)
        if app.validada:
            app.proceso_completo()
    else:
        app.ejecutar_menu()


if __name__ == "__main__":
    main()
