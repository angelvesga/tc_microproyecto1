"""
gramatica.py
Modelo de datos de una Gramática Libre de Contexto G = (V, T, P, S).

Decisiones de representación:
  - Cada símbolo es un string ("S", "a", "X1", ...). Así los nombres de
    varios caracteres (X1, X12, S0) nunca se confunden.
  - Cada cuerpo de producción es una TUPLA de símbolos:
        S -> a B     se guarda como  ("a", "B")
        S -> ε       se guarda como  ()          (tupla vacía)
  - P es un diccionario  cabeza -> set de cuerpos. El set impide
    producciones duplicadas (RNF08) sin esfuerzo adicional.
"""

import copy

EPSILON = "ε"


class Gramatica:
    """Gramática Libre de Contexto G = (V, T, P, S)."""

    def __init__(self, variables=None, terminales=None, inicial=None):
        # Se usan listas para V y T para conservar el orden en que el
        # usuario los declaró: así la salida es siempre la misma (RNF11).
        self.variables = list(variables or [])
        self.terminales = list(terminales or [])
        self.inicial = inicial
        self.producciones = {}          # dict[str, set[tuple[str, ...]]]
        self.contador_auxiliares = 0    # para generar X1, X2, X3, ...
        self.implicitas = []            # variables usadas en un cuerpo sin declarar en V

    # ------------------------------------------------------------------
    # Consultas básicas
    # ------------------------------------------------------------------
    def es_variable(self, simbolo):
        return simbolo in self.variables

    def es_terminal(self, simbolo):
        return simbolo in self.terminales

    def cabezas_ordenadas(self):
        """Cabezas en orden estable: símbolo inicial primero, luego V en
        orden de declaración y al final cualquier cabeza no declarada."""
        orden = []
        if self.inicial in self.producciones:
            orden.append(self.inicial)
        for v in self.variables:
            if v in self.producciones and v not in orden:
                orden.append(v)
        for cabeza in self.producciones:
            if cabeza not in orden:
                orden.append(cabeza)
        return orden

    @staticmethod
    def ordenar_cuerpos(cuerpos):
        """Orden estable de cuerpos; ε se muestra al final."""
        return sorted(cuerpos, key=lambda c: (len(c) == 0, c))

    def todas_las_producciones(self):
        """Lista ordenada de pares (cabeza, cuerpo)."""
        resultado = []
        for cabeza in self.cabezas_ordenadas():
            for cuerpo in self.ordenar_cuerpos(self.producciones[cabeza]):
                resultado.append((cabeza, cuerpo))
        return resultado

    def conjunto_producciones(self):
        """Todas las producciones como set de (cabeza, cuerpo)."""
        return {(c, cuerpo) for c, cuerpos in self.producciones.items()
                for cuerpo in cuerpos}

    # ------------------------------------------------------------------
    # Modificación
    # ------------------------------------------------------------------
    def agregar_produccion(self, cabeza, cuerpo):
        self.producciones.setdefault(cabeza, set()).add(tuple(cuerpo))

    def quitar_produccion(self, cabeza, cuerpo):
        cuerpos = self.producciones.get(cabeza)
        if cuerpos is not None:
            cuerpos.discard(tuple(cuerpo))
            if not cuerpos:
                del self.producciones[cabeza]

    def quitar_variable(self, variable):
        """Elimina la variable de V y sus producciones (como cabeza)."""
        if variable in self.variables:
            self.variables.remove(variable)
        self.producciones.pop(variable, None)

    def nueva_variable(self, prefijo="X"):
        """Crea una variable auxiliar con nombre único: X1, X2, ...
        Salta cualquier nombre que ya exista en V o en T (RF17, RNF09)."""
        while True:
            self.contador_auxiliares += 1
            nombre = f"{prefijo}{self.contador_auxiliares}"
            if nombre not in self.variables and nombre not in self.terminales:
                self.variables.append(nombre)
                return nombre

    def variable_con_base(self, base):
        """Crea una variable nueva a partir de un nombre base (p. ej. S0),
        agregando un sufijo si ese nombre ya está ocupado."""
        nombre, i = base, 1
        while nombre in self.variables or nombre in self.terminales:
            nombre = f"{base}_{i}"
            i += 1
        self.variables.append(nombre)
        return nombre

    def copia(self):
        """Copia profunda: cada etapa trabaja sobre su propia gramática
        para poder mostrar el 'antes' y el 'después'."""
        return copy.deepcopy(self)

    # ------------------------------------------------------------------
    # Presentación
    # ------------------------------------------------------------------
    @staticmethod
    def cuerpo_a_texto(cuerpo):
        return " ".join(cuerpo) if cuerpo else EPSILON

    @staticmethod
    def produccion_a_texto(cabeza, cuerpo):
        return f"{cabeza} -> {Gramatica.cuerpo_a_texto(cuerpo)}"

    def a_texto(self):
        lineas = [
            f"V = {{ {', '.join(self.variables)} }}",
            f"T = {{ {', '.join(self.terminales)} }}",
            f"S = {self.inicial}",
            "P:",
        ]
        if not self.producciones:
            lineas.append("   (sin producciones)")
        for cabeza in self.cabezas_ordenadas():
            cuerpos = self.ordenar_cuerpos(self.producciones[cabeza])
            alternativas = " | ".join(self.cuerpo_a_texto(c) for c in cuerpos)
            lineas.append(f"   {cabeza} -> {alternativas}")
        return "\n".join(lineas)

    def __str__(self):
        return self.a_texto()
