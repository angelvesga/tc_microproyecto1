"""
pruebas.py
Pruebas automáticas mínimas. Ejecutar con:  python pruebas.py
"""

import transformaciones as tr
from lector import gramatica_desde_texto
from validador import validar_fnc, validar_gramatica


def g(texto):
    gramatica, errores = gramatica_desde_texto(texto)
    assert not errores, errores
    return gramatica


EJEMPLO_NULAS = """
V: S A B
T: a b
S: S
P:
S -> A S A | a B
A -> B | S
B -> b | ε
"""

EJEMPLO_INUTILES = """
V: S A B C D
T: a b
S: S
P:
S -> A B | a
A -> b
B -> B C
C -> a
D -> a
"""


def prueba_validacion_errores():
    gramatica, _ = gramatica_desde_texto("V: S A\nT: a b\nS: X\nP:\nS -> AD | a c\nA -> b")
    errores = validar_gramatica(gramatica)
    assert "Error: el símbolo inicial X no pertenece al conjunto de variables." in errores
    assert any("la variable D utilizada en la producción S -> A D" in e for e in errores)
    assert any("el símbolo c no fue declarado como terminal" in e for e in errores)


def prueba_validacion_correcta():
    assert validar_gramatica(g(EJEMPLO_NULAS)) == []


def prueba_anulables():
    # S no es anulable: S -> A S A necesita a S, y S -> a B tiene un terminal.
    assert tr.calcular_anulables(g(EJEMPLO_NULAS)) == {"A", "B"}


if __name__ == "__main__":
    pruebas = [f for nombre, f in list(globals().items()) if nombre.startswith("prueba_")]
    resumen = {"ok": 0, "pendiente": 0, "falla": 0}
    for prueba in pruebas:
        try:
            prueba()
            print(f"[ OK ]       {prueba.__name__}")
            resumen["ok"] += 1
        except NotImplementedError as e:
            print(f"[PENDIENTE]  {prueba.__name__}  ({e})")
            resumen["pendiente"] += 1
        except AssertionError as e:
            print(f"[FALLA]      {prueba.__name__}  {e}")
            resumen["falla"] += 1
    print(f"\n{resumen['ok']} ok, {resumen['pendiente']} pendientes, {resumen['falla']} fallas")
