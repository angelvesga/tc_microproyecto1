"""
lector.py
Lectura de una gramática desde la consola o desde un archivo de texto.

Formato (igual en consola y en archivo):
    V: S A B
    T: a b
    S: S
    P:
    S -> A S A | a B
    A -> B | S
    B -> b | ε

  - Los símbolos se separan con espacios o comas.
  - La cadena vacía se escribe ε (también se acepta eps, epsilon o λ).
  - Si TODOS los símbolos declarados son de un solo carácter, se puede
    escribir pegado (S -> aB); el lector lo separa en a, B.
"""

import re

from gramatica import Gramatica

PALABRAS_EPSILON = {"ε", "eps", "epsilon", "λ", "lambda"}


def parsear_lista_simbolos(texto):
    """'S, A B' -> ['S', 'A', 'B'] sin repetidos y en orden."""
    simbolos = []
    for s in re.split(r"[,\s]+", texto.strip()):
        if s and s not in simbolos:
            simbolos.append(s)
    return simbolos


def _separar_cuerpo(texto, declarados, todos_de_un_caracter):
    """Convierte el texto de una alternativa en una lista de símbolos."""
    simbolos = []
    for token in texto.split():
        if token in PALABRAS_EPSILON:
            simbolos.append("ε")
        elif token in declarados or not todos_de_un_caracter or len(token) == 1:
            simbolos.append(token)
        else:
            # Escritura pegada (aB): se separa carácter por carácter.
            simbolos.extend(list(token))
    return simbolos


def parsear_producciones(lineas, gramatica):
    """Agrega a la gramática las producciones de las líneas dadas.
    Devuelve la lista de errores de SINTAXIS (flecha faltante, etc.).
    Los errores de SEMÁNTICA (símbolos no declarados) los detecta el
    validador, para que se reporten todos juntos."""
    errores = []
    declarados = set(gramatica.variables) | set(gramatica.terminales)
    todos_de_un_caracter = all(len(s) == 1 for s in declarados)

    for numero, linea in enumerate(lineas, start=1):
        linea = linea.strip()
        if not linea:
            continue
        linea = linea.replace("→", "->")
        if "->" not in linea:
            errores.append(f"Error: la línea {numero} de producciones no tiene '->': {linea}")
            continue

        cabeza, _, derecha = linea.partition("->")
        cabeza = cabeza.strip()
        if not cabeza or len(cabeza.split()) != 1:
            errores.append(f"Error: el lado izquierdo de '{linea}' debe ser una sola variable.")
            continue

        for alternativa in derecha.split("|"):
            if not alternativa.strip():
                errores.append(
                    f"Error: en '{linea}' hay una alternativa vacía; "
                    f"para la cadena vacía escriba ε.")
                continue
            simbolos = _separar_cuerpo(alternativa, declarados, todos_de_un_caracter)
            if "ε" in simbolos:
                if len(simbolos) > 1:
                    errores.append(
                        f"Error: en '{linea}', ε debe aparecer sola en su alternativa.")
                    continue
                simbolos = []          # ε se guarda como tupla vacía
            gramatica.agregar_produccion(cabeza, simbolos)
    return errores


def gramatica_desde_texto(texto):
    """Construye una gramática a partir del texto completo con el formato
    descrito arriba. Devuelve (gramatica, errores_de_sintaxis)."""
    secciones = {"V": "", "T": "", "S": ""}
    lineas_producciones = []
    en_producciones = False

    for linea in texto.splitlines():
        limpia = linea.strip()
        if not limpia or limpia.startswith("#"):
            continue
        encabezado = re.match(r"^([VTSP])\s*:\s*(.*)$", limpia)
        if encabezado and "->" not in limpia:
            clave, valor = encabezado.groups()
            if clave == "P":
                en_producciones = True
                if valor:
                    lineas_producciones.append(valor)
            else:
                secciones[clave] = valor
                en_producciones = False
        elif en_producciones:
            lineas_producciones.append(limpia)

    gramatica = Gramatica(
        variables=parsear_lista_simbolos(secciones["V"]),
        terminales=parsear_lista_simbolos(secciones["T"]),
        inicial=secciones["S"].strip() or None,
    )
    errores = parsear_producciones(lineas_producciones, gramatica)
    return gramatica, errores


def leer_desde_archivo(ruta):
    with open(ruta, encoding="utf-8") as archivo:
        return gramatica_desde_texto(archivo.read())


def leer_desde_consola():
    """Pide al usuario cada componente de la gramática (RF01 a RF05)."""
    print("\nSepare los símbolos con espacios. Use ε (o eps) para la cadena vacía.")
    variables = input("Variables (no terminales), ej. S A B: ")
    terminales = input("Terminales, ej. a b: ")
    inicial = input("Símbolo inicial, ej. S: ")
    print("Producciones, una variable por línea (ej. S -> a B | b).")
    print("Deje una línea vacía para terminar.")
    lineas = []
    while True:
        linea = input("  ")
        if not linea.strip():
            break
        lineas.append(linea)

    texto = f"V: {variables}\nT: {terminales}\nS: {inicial}\nP:\n" + "\n".join(lineas)
    return gramatica_desde_texto(texto)
