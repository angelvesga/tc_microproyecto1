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
    """Elimina producciones nulas generando todas las versiones posibles
    de cada producción según qué variables anulables se omiten o conservan.

    Para A -> α con k posiciones anulables en α, se generan 2^k versiones
    (itertools.product([True, False], repeat=k)), descartando las vacías.

    Tratamiento de ε (RNF07):
      - Si el inicial es anulable y aparece en algún lado derecho, se crea
        un nuevo símbolo inicial S0 -> S | ε (S0 va primero en variables).
      - Si el inicial es anulable y NO aparece en lados derechos, se
        conserva S -> ε."""
    anulables = calcular_anulables(g)
    nueva = g.copia()
    nueva.producciones = {}

    for cabeza, cuerpo in g.todas_las_producciones():
        if not cuerpo:
            # Saltar las producciones A -> ε originales; se tratan al final.
            continue
        posiciones_anulables = [i for i, s in enumerate(cuerpo) if s in anulables]
        k = len(posiciones_anulables)
        # 2^k combinaciones: True = conservar el símbolo anulable, False = omitir
        for conservar in itertools_product([True, False], repeat=k):
            nuevo_cuerpo = tuple(
                s for i, s in enumerate(cuerpo)
                if i not in posiciones_anulables
                or conservar[posiciones_anulables.index(i)]
            )
            if nuevo_cuerpo:
                nueva.agregar_produccion(cabeza, nuevo_cuerpo)

    # Tratamiento de ε (RNF07)
    if g.inicial in anulables:
        inicial_en_derecha = any(
            g.inicial in cuerpo
            for _, cuerpo in g.todas_las_producciones()
        )
        if inicial_en_derecha:
            s0 = nueva.variable_con_base(g.inicial + "0")
            nueva.variables.remove(s0)
            nueva.variables.insert(0, s0)
            nueva.inicial = s0
            nueva.agregar_produccion(s0, (g.inicial,))
            nueva.agregar_produccion(s0, ())
            decision_eps = f"nuevo símbolo inicial {s0} -> {g.inicial} | ε"
        else:
            nueva.agregar_produccion(g.inicial, ())
            decision_eps = f"se conserva {g.inicial} -> ε (inicial no aparece en lados derechos)"
    else:
        decision_eps = "el lenguaje no contiene ε"

    orden = g.variables + g.terminales
    identificados = [
        f"Variables anulables: {_conjunto_a_texto(anulables, orden)}",
        f"Decisión ε: {decision_eps}",
    ]
    return nueva, crear_paso("Eliminación de producciones nulas", g, nueva, identificados)


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
