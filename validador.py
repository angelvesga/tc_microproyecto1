"""
validador.py
Validación inicial de la gramática (sección 8 del enunciado, RF06) y
validación automática de la Forma Normal de Chomsky (RNF12).
"""


def _es_nombre_de_variable(simbolo):
    """Heurística para redactar el mensaje de un símbolo NO declarado:
    si empieza en mayúscula se asume que se quiso usar como variable."""
    return simbolo[:1].isupper()


def validar_gramatica(g):
    """Devuelve la lista de errores. Lista vacía = gramática válida."""
    errores = []

    if not g.variables:
        errores.append("Error: debe existir al menos una variable.")
    if not g.terminales:
        errores.append("Error: debe existir al menos un terminal.")
    if not g.inicial:
        errores.append("Error: no se definió el símbolo inicial.")
    elif g.inicial not in g.variables:
        errores.append(f"Error: el símbolo inicial {g.inicial} no pertenece al conjunto de variables.")

    comunes = set(g.variables) & set(g.terminales)
    for simbolo in sorted(comunes):
        errores.append(f"Error: el símbolo {simbolo} está declarado como variable y como terminal.")

    # Que el inicial no tenga producciones (o no genere nada) no es un error:
    # el lenguaje es vacío y el proceso lo informa en la etapa de inútiles.
    if not g.producciones:
        errores.append("Error: la gramática no tiene producciones.")

    # Cada símbolo desconocido se reporta una sola vez por producción.
    for cabeza, cuerpo in g.todas_las_producciones():
        texto = g.produccion_a_texto(cabeza, cuerpo)
        if cabeza not in g.variables:
            errores.append(f"Error: el lado izquierdo de la producción {texto} "
                           f"({cabeza}) no es una variable declarada.")
        reportados = set()
        for simbolo in cuerpo:
            if simbolo in g.variables or simbolo in g.terminales or simbolo in reportados:
                continue
            reportados.add(simbolo)
            if _es_nombre_de_variable(simbolo):
                errores.append(f"Error: la variable {simbolo} utilizada en la producción "
                               f"{texto} no fue declarada.")
            else:
                errores.append(f"Error: el símbolo {simbolo} no fue declarado como terminal "
                               f"(producción {texto}).")
    return errores


def validar_fnc(g):
    """Comprueba que TODA producción tenga la forma A -> B C o A -> a.
    Única excepción: S -> ε, si S no aparece en ningún lado derecho.
    Devuelve la lista de producciones que violan la FNC."""
    violaciones = []
    inicial_en_derecha = any(g.inicial in cuerpo for _, cuerpo in g.todas_las_producciones())

    for cabeza, cuerpo in g.todas_las_producciones():
        texto = g.produccion_a_texto(cabeza, cuerpo)
        if len(cuerpo) == 0:
            if cabeza != g.inicial:
                violaciones.append(f"{texto}: solo el símbolo inicial puede producir ε.")
            elif inicial_en_derecha:
                violaciones.append(f"{texto}: el inicial produce ε pero aparece en un lado derecho.")
        elif len(cuerpo) == 1:
            if not g.es_terminal(cuerpo[0]):
                violaciones.append(f"{texto}: con un símbolo, el cuerpo debe ser un terminal.")
        elif len(cuerpo) == 2:
            if not (g.es_variable(cuerpo[0]) and g.es_variable(cuerpo[1])):
                violaciones.append(f"{texto}: con dos símbolos, ambos deben ser variables.")
        else:
            violaciones.append(f"{texto}: el cuerpo tiene más de dos símbolos.")
    return violaciones
