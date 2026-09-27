"""
transformaciones.py
Algoritmos de depuración y conversión a Forma Normal de Chomsky.

Convención de TODAS las funciones "eliminar_*" / "sustituir_*" / "reducir_*":
    recibe:   la gramática actual (no la modifica)
    devuelve: (gramatica_nueva, paso)
El Paso se construye con crear_paso(), que calcula solo las producciones
eliminadas y agregadas comparando el antes y el después.

Orden correcto del proceso completo:
    1. Producciones nulas
    2. Producciones unitarias
    3. Variables inútiles
    4. Variables inalcanzables
    5. Sustituir terminales
    6. Reducir producciones largas
"""

from itertools import product as itertools_product

from historial import crear_paso


def _conjunto_a_texto(simbolos, orden):
    """Muestra un conjunto en el orden de declaración: { A, B } (o ∅)."""
    elementos = [s for s in orden if s in simbolos]
    return "{ " + ", ".join(elementos) + " }" if elementos else "∅"


# ======================================================================
# 1. PRODUCCIONES NULAS  (RF07, RF08)
# ======================================================================

def calcular_anulables(g):
    """Calcula el conjunto de variables que derivan ε por punto fijo.

    Una variable A es anulable si:
      - Tiene A -> ε (cuerpo vacío), o
      - Tiene A -> X1 ... Xn donde todos los Xi ya son anulables.

    Se itera hasta que el conjunto no crezca más (punto fijo)."""
    anulables = set()
    cambio = True
    while cambio:
        cambio = False
        for cabeza, cuerpo in g.todas_las_producciones():
            if cabeza not in anulables:
                # all() es True para cuerpo vacío (), que representa A -> ε
                if all(s in anulables for s in cuerpo):
                    anulables.add(cabeza)
                    cambio = True
    return anulables

def eliminar_producciones_nulas(g):
    """Pendiente."""
    raise NotImplementedError("eliminar_producciones_nulas")



# ======================================================================
# 2. PRODUCCIONES UNITARIAS  (RF09, RF10)
# ======================================================================

def calcular_pares_unitarios(g):
    """Pendiente."""
    raise NotImplementedError("calcular_pares_unitarios")


def eliminar_producciones_unitarias(g):
    """Pendiente."""
    raise NotImplementedError("eliminar_producciones_unitarias")



# ======================================================================
# 3. VARIABLES INÚTILES / NO GENERADORAS  (RF11, RF12)
# ======================================================================

def calcular_generadoras(g):
    """Pendiente."""
    raise NotImplementedError("calcular_generadoras")


def eliminar_variables_inutiles(g):
    """Pendiente."""
    raise NotImplementedError("eliminar_variables_inutiles")



# ======================================================================
# 4. VARIABLES INALCANZABLES  (RF13, RF14)
# ======================================================================

def calcular_alcanzables(g):
    """Pendiente."""
    raise NotImplementedError("calcular_alcanzables")


def eliminar_variables_inalcanzables(g):
    """Pendiente."""
    raise NotImplementedError("eliminar_variables_inalcanzables")



# ======================================================================
# 5 y 6. CONVERSIÓN A FORMA NORMAL DE CHOMSKY  (RF15, RF16, RF17)
# ======================================================================

def sustituir_terminales(g):
    """Pendiente."""
    raise NotImplementedError("sustituir_terminales")


def reducir_producciones_largas(g):
    """Pendiente."""
    raise NotImplementedError("reducir_producciones_largas")




def convertir_a_fnc(g):
    """Devuelve (gramatica_fnc, [paso_terminales, paso_largas])."""
    con_terminales, paso1 = sustituir_terminales(g)
    fnc, paso2 = reducir_producciones_largas(con_terminales)
    return fnc, [paso1, paso2]


# ======================================================================
# PROCESO COMPLETO (modo automático)
# ======================================================================
ETAPAS_EN_ORDEN = [
    eliminar_producciones_nulas,
    eliminar_producciones_unitarias,
    eliminar_variables_inutiles,
    eliminar_variables_inalcanzables,
    sustituir_terminales,
    reducir_producciones_largas,
]


def ejecutar_proceso_completo(g, historial):
    """Ejecuta todas las etapas en orden y registra cada paso.
    Devuelve (gramatica_resultante, nombre_etapa_pendiente).
    Si una etapa aún no está implementada, se detiene ahí."""
    actual = g
    for etapa in ETAPAS_EN_ORDEN:
        try:
            actual, paso = etapa(actual)
        except NotImplementedError:
            return actual, etapa.__name__
        historial.agregar(paso)
    return actual, None
