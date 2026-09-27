"""
main.py
Menú de consola del aplicativo (sección 12 del enunciado).

Uso:
    python main.py                        -> menú interactivo
    python main.py ejemplos/ejemplo1.txt  -> modo automático con ese archivo
"""

import sys

import transformaciones as tr
from historial import Historial
from lector import leer_desde_archivo, leer_desde_consola
from validador import validar_fnc, validar_gramatica

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
        """RF20: borra todo el estado para empezar con otra gramática."""
        self.original = None     # gramática tal como la ingresó el usuario
        self.actual = None       # gramática después de la última etapa
        self.errores_sintaxis = []
        self.validada = False
        self.historial = Historial()

    # ------------------------------------------------------------------
    # Ingreso y validación
    # ------------------------------------------------------------------
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
            for error in dict.fromkeys(errores):   # sin repetidos, en orden
                print("  " + error)
        else:
            self.validada = True
            print("\nLa gramática es válida.")

    # ------------------------------------------------------------------
    # Etapas
    # ------------------------------------------------------------------
    def ejecutar_etapa(self, *funciones):
        """Aplica una o varias etapas sobre la gramática actual (modo paso a paso)."""
        if not self._lista_para_transformar():
            return
        for funcion in funciones:
            try:
                nueva, paso = funcion(self.actual)
            except NotImplementedError:
                print(f"\n[Pendiente] La etapa '{funcion.__name__}' aún no está "
                      f"implementada (ver TODO en transformaciones.py).")
                return
            self.actual = nueva
            self.historial.agregar(paso)
            print(paso.a_texto(len(self.historial.pasos)))

    def proceso_completo(self):
        """Modo automático: siempre parte de la gramática original."""
        if not self._lista_para_transformar():
            return
        self.historial.limpiar()
        self.actual, pendiente = tr.ejecutar_proceso_completo(self.original.copia(), self.historial)
        print(self.historial.a_texto())
        if pendiente:
            print(f"[Pendiente] El proceso se detuvo en '{pendiente}' "
                  f"(ver TODO en transformaciones.py).")
        else:
            self.mostrar_final()

    def mostrar_historial(self):
        texto = self.historial.a_texto()
        print(texto)
        respuesta = input("\n¿Desea guardar el historial en un archivo .txt? (s/n): ").strip().lower()
        if respuesta in ("s", "si", "sí", "y", "yes"):
            nombre = input("Nombre del archivo (sin extensión): ").strip()
            if not nombre:
                nombre = "historial"
            ruta = nombre + ".txt"
            try:
                with open(ruta, "w", encoding="utf-8") as archivo:
                    archivo.write(texto)
                print(f"Historial guardado en {ruta}.")
            except OSError as error:
                print(f"Error al guardar: {error}.")

    def mostrar_final(self):
        if not self._hay_gramatica():
            return
        print("\nGRAMÁTICA FINAL:")
        print(self.actual)
        violaciones = validar_fnc(self.actual)
        if violaciones:
            print("\nLa gramática todavía NO está en Forma Normal de Chomsky:")
            for v in violaciones:
                print("  - " + v)
        else:
            print("\nValidación automática: la gramática está en Forma Normal de Chomsky.")

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------
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
            "10": self.mostrar_historial,
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
        # Modo automático directo: python main.py archivo.txt
        gramatica, errores = leer_desde_archivo(sys.argv[1])
        app.cargar(gramatica, errores)
        if app.validada:
            app.proceso_completo()
    else:
        app.ejecutar_menu()


if __name__ == "__main__":
    main()
