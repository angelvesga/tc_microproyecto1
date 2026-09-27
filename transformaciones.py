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
    """Calcula los pares (A, B) tales que A =>* B usando solo producciones
    unitarias, incluyendo los reflexivos (A, A). Funciona con ciclos.

    1. Inicializar con {(A, A) para toda A en V}.
    2. Si (A, B) está y B -> C es unitaria (len=1, C variable), agregar (A, C).
    3. Repetir hasta punto fijo."""
    pares = {(v, v) for v in g.variables}
    cambio = True
    while cambio:
        cambio = False
        nuevos = set()
        for a, b in pares:
            for cabeza, cuerpo in g.todas_las_producciones():
                if cabeza == b and len(cuerpo) == 1 and g.es_variable(cuerpo[0]):
                    c = cuerpo[0]
                    if (a, c) not in pares:
                        nuevos.add((a, c))
                        cambio = True
        pares |= nuevos
    return pares

def eliminar_producciones_unitarias(g):
    """Para cada par unitario (A, B), agrega A -> α por cada producción
    NO unitaria B -> α. S0 -> ε no es unitaria y se conserva."""
    pares = calcular_pares_unitarios(g)
    nueva = g.copia()
    nueva.producciones = {}

    unitarias_orig = [
        (cab, cuerpo)
        for cab, cuerpo in g.todas_las_producciones()
        if len(cuerpo) == 1 and g.es_variable(cuerpo[0])
    ]

    for a, b in sorted(pares):
        for cabeza, cuerpo in g.todas_las_producciones():
            if cabeza != b:
                continue
            es_unitaria = len(cuerpo) == 1 and g.es_variable(cuerpo[0])
            if not es_unitaria:
                nueva.agregar_produccion(a, cuerpo)

    texto_unitarias = ", ".join(
        g.produccion_a_texto(c, b) for c, b in unitarias_orig
    ) or "∅"
    texto_pares = ", ".join(f"({a}, {b})" for a, b in sorted(pares))
    identificados = [
        f"Producciones unitarias: {texto_unitarias}",
        f"Pares unitarios: {{ {texto_pares} }}",
    ]
    return nueva, crear_paso("Eliminación de producciones unitarias", g, nueva, identificados)


# ======================================================================
# 3. VARIABLES INÚTILES / NO GENERADORAS  (RF11, RF12)
# ======================================================================

def calcular_generadoras(g):
    """Variables que derivan alguna cadena de terminales (incluyendo ε).

    A es generadora si tiene A -> α donde cada símbolo de α es terminal o
    ya es variable generadora. Un cuerpo vacío () también cuenta.
    Se aplica punto fijo igual que calcular_anulables."""
    generadoras = set()
    cambio = True
    while cambio:
        cambio = False
        for cabeza, cuerpo in g.todas_las_producciones():
            if cabeza not in generadoras:
                if all(g.es_terminal(s) or s in generadoras for s in cuerpo):
                    generadoras.add(cabeza)
                    cambio = True
    return generadoras

def eliminar_variables_inutiles(g):
    """Elimina variables no generadoras y todas las producciones que las
    usan en el lado derecho.

    Si el símbolo inicial no es generador, el lenguaje es vacío: se
    informa en 'identificados' sin que el programa falle."""
    generadoras = calcular_generadoras(g)
    no_generadoras = set(g.variables) - generadoras

    nueva = g.copia()

    identificados_base = [
        f"Variables generadoras: {_conjunto_a_texto(generadoras, g.variables)}",
        f"Variables no generadoras: {_conjunto_a_texto(no_generadoras, g.variables)}",
    ]

    if g.inicial not in generadoras:
        identificados_base.append(
            "El lenguaje es vacío: el símbolo inicial no genera ninguna cadena terminal."
        )
        return nueva, crear_paso("Eliminación de variables inútiles", g, nueva, identificados_base)

    for v in list(no_generadoras):
        nueva.quitar_variable(v)

    for cabeza in list(nueva.producciones):
        cuerpos_a_quitar = [
            cuerpo for cuerpo in list(nueva.producciones.get(cabeza, set()))
            if any(s in no_generadoras for s in cuerpo)
        ]
        for cuerpo in cuerpos_a_quitar:
            nueva.quitar_produccion(cabeza, cuerpo)

    return nueva, crear_paso("Eliminación de variables inútiles", g, nueva, identificados_base)


# ======================================================================
# 4. VARIABLES INALCANZABLES  (RF13, RF14)
# ======================================================================

def calcular_alcanzables(g):
    """Recorre en BFS desde el símbolo inicial para hallar todos los
    símbolos alcanzables (variables y terminales).

    1. alcanzables = {g.inicial}; pendientes = [g.inicial]
    2. Por cada variable pendiente, agregar cada símbolo de sus cuerpos;
       si es variable nueva, agregarla también a pendientes."""
    alcanzables = {g.inicial}
    pendientes = [g.inicial]
    while pendientes:
        variable = pendientes.pop(0)
        for cabeza, cuerpo in g.todas_las_producciones():
            if cabeza != variable:
                continue
            for s in cuerpo:
                if s not in alcanzables:
                    alcanzables.add(s)
                    if g.es_variable(s):
                        pendientes.append(s)
    return alcanzables

def eliminar_variables_inalcanzables(g):
    """Quita variables (y terminales) que no son alcanzables desde el
    símbolo inicial. Usa calcular_alcanzables para el BFS."""
    alcanzables = calcular_alcanzables(g)
    inalcanzables_vars = set(g.variables) - alcanzables
    inalcanzables_terms = set(g.terminales) - alcanzables

    nueva = g.copia()
    for v in list(inalcanzables_vars):
        nueva.quitar_variable(v)
    for t in list(inalcanzables_terms):
        nueva.terminales.remove(t)

    orden = g.variables + g.terminales
    identificados = [
        f"Símbolos alcanzables: {_conjunto_a_texto(alcanzables, orden)}",
        f"Variables inalcanzables: {_conjunto_a_texto(inalcanzables_vars, g.variables)}",
        f"Terminales inalcanzables: {_conjunto_a_texto(inalcanzables_terms, g.terminales)}",
    ]
    return nueva, crear_paso("Eliminación de variables inalcanzables", g, nueva, identificados)


# ======================================================================
# 5 y 6. CONVERSIÓN A FORMA NORMAL DE CHOMSKY  (RF15, RF16, RF17)
# ======================================================================

def sustituir_terminales(g):
    """En cuerpos de longitud >= 2, reemplaza cada terminal 'a' por una
    variable auxiliar Xk con producción Xk -> a.

    Reutiliza la misma variable para el mismo terminal (un dict
    terminal -> variable), evitando duplicar Xi -> a.
    Recorre g.todas_las_producciones() para que los nombres de variables
    sean siempre los mismos (RNF11)."""
    nueva = g.copia()
    nueva.producciones = {}
    terminal_a_var = {}

    for cabeza, cuerpo in g.todas_las_producciones():
        if len(cuerpo) < 2:
            nueva.agregar_produccion(cabeza, cuerpo)
            continue
        nuevo_cuerpo = []
        for s in cuerpo:
            if g.es_terminal(s):
                if s not in terminal_a_var:
                    xv = nueva.nueva_variable()
                    terminal_a_var[s] = xv
                    nueva.agregar_produccion(xv, (s,))
                nuevo_cuerpo.append(terminal_a_var[s])
            else:
                nuevo_cuerpo.append(s)
        nueva.agregar_produccion(cabeza, tuple(nuevo_cuerpo))

    if terminal_a_var:
        identificados = [
            f"Terminal '{t}' sustituido por variable {v}"
            for t, v in sorted(terminal_a_var.items())
        ]
    else:
        identificados = ["No se encontraron terminales en cuerpos de longitud >= 2."]
    return nueva, crear_paso("Sustitución de terminales", g, nueva, identificados)

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
