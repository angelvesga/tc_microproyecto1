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


EJEMPLO_EPSILON = """
V: S
T: a b
S: S
P:
S -> a S b | ε
"""


def prueba_eliminar_nulas():
    nueva, paso = tr.eliminar_producciones_nulas(g(EJEMPLO_NULAS))
    assert nueva.inicial == "S"
    assert nueva.producciones["S"] == {
        ("A", "S", "A"), ("S", "A"), ("A", "S"), ("S",), ("a", "B"), ("a",)}
    assert nueva.producciones["B"] == {("b",)}
    assert ("B", ()) in paso.eliminadas


def prueba_epsilon_en_el_lenguaje():
    # S es anulable y aparece a la derecha -> nuevo inicial S0 -> S | ε
    nueva, _ = tr.eliminar_producciones_nulas(g(EJEMPLO_EPSILON))
    assert nueva.inicial == "S0"
    assert nueva.variables[0] == "S0"
    assert nueva.producciones["S0"] == {("S",), ()}
    assert nueva.producciones["S"] == {("a", "S", "b"), ("a", "b")}


def prueba_eliminar_unitarias():
    for texto in (EJEMPLO_NULAS, EJEMPLO_EPSILON):
        base, _ = tr.eliminar_producciones_nulas(g(texto))
        nueva, _ = tr.eliminar_producciones_unitarias(base)
        for cabeza, cuerpo in nueva.todas_las_producciones():
            assert not (len(cuerpo) == 1 and nueva.es_variable(cuerpo[0])), (cabeza, cuerpo)
    assert () in nueva.producciones["S0"]   # S0 -> ε se conserva


def prueba_eliminar_inutiles():
    sin_inutiles, _ = tr.eliminar_variables_inutiles(g(EJEMPLO_INUTILES))
    assert "B" not in sin_inutiles.variables


def prueba_eliminar_inalcanzables():
    nueva, paso = tr.eliminar_variables_inalcanzables(g(EJEMPLO_INUTILES))
    assert "D" not in nueva.variables
    assert "D" not in nueva.producciones
    assert ("D", ("a",)) in paso.eliminadas


def prueba_eliminar_inutiles_e_inalcanzables():
    gramatica = g(EJEMPLO_INUTILES)
    sin_inutiles, _ = tr.eliminar_variables_inutiles(gramatica)
    assert "B" not in sin_inutiles.variables
    final, _ = tr.eliminar_variables_inalcanzables(sin_inutiles)
    # Al quitar B, S -> A B desaparece y A queda inalcanzable.
    assert final.variables == ["S"]
    assert final.producciones == {"S": {("a",)}}


def prueba_proceso_completo_en_fnc():
    from historial import Historial
    for texto in (EJEMPLO_NULAS, EJEMPLO_INUTILES, EJEMPLO_EPSILON):
        final, pendiente = tr.ejecutar_proceso_completo(g(texto), Historial())
        if pendiente:
            raise NotImplementedError(pendiente)
        assert validar_fnc(final) == [], validar_fnc(final)


def prueba_reproducible():
    from historial import Historial
    a, _ = tr.ejecutar_proceso_completo(g(EJEMPLO_NULAS), Historial())
    b, _ = tr.ejecutar_proceso_completo(g(EJEMPLO_NULAS), Historial())
    assert a.a_texto() == b.a_texto()


# ======================================================================
# CASOS ADICIONALES
# ======================================================================

EJEMPLO_CICLO_UNITARIAS = """
V: S A B
T: a
S: S
P:
S -> A | a
A -> B
B -> A | a
"""

EJEMPLO_LENGUAJE_VACIO = """
V: S A
T: a
S: S
P:
S -> A a
A -> A a
"""

EJEMPLO_TERMINALES_REPETIDOS = """
V: S A
T: a b
S: S
P:
S -> a A b
A -> a b a
"""

EJEMPLO_PRODUCCION_LARGA = """
V: S
T: a b c d e
S: S
P:
S -> a b c d e
"""


def prueba_ciclo_unitarias():
    """El ciclo A -> B -> A no debe provocar bucle infinito ni
    dejar producciones unitarias en el resultado."""
    base, _ = tr.eliminar_producciones_nulas(g(EJEMPLO_CICLO_UNITARIAS))
    nueva, _ = tr.eliminar_producciones_unitarias(base)
    for cabeza, cuerpo in nueva.todas_las_producciones():
        assert not (len(cuerpo) == 1 and nueva.es_variable(cuerpo[0])), (cabeza, cuerpo)
    for var in ("S", "A", "B"):
        assert ("a",) in nueva.producciones.get(var, set()), var


def prueba_lenguaje_vacio():
    """Si el símbolo inicial no genera ninguna cadena, el proceso no
    debe fallar y debe registrar el mensaje de lenguaje vacío."""
    nueva, paso = tr.eliminar_variables_inutiles(g(EJEMPLO_LENGUAJE_VACIO))
    assert tr.calcular_generadoras(g(EJEMPLO_LENGUAJE_VACIO)) == set()
    assert any("vacío" in linea.lower() for linea in paso.identificados)


def prueba_terminales_repetidos():
    """El mismo terminal debe recibir siempre la misma variable auxiliar,
    sin crear duplicados como X1 -> a y X2 -> a."""
    from historial import Historial
    final, pendiente = tr.ejecutar_proceso_completo(
        g(EJEMPLO_TERMINALES_REPETIDOS), Historial()
    )
    assert pendiente is None
    assert validar_fnc(final) == [], validar_fnc(final)
    var_por_terminal = {}
    for cabeza, cuerpo in final.todas_las_producciones():
        if len(cuerpo) == 1 and final.es_terminal(cuerpo[0]):
            t = cuerpo[0]
            assert t not in var_por_terminal or var_por_terminal[t] == cabeza, \
                f"Terminal '{t}' tiene más de una variable: {var_por_terminal[t]} y {cabeza}"
            var_por_terminal[t] = cabeza


def prueba_produccion_larga():
    """Una producción de longitud 5 debe quedar en FNC tras el proceso."""
    from historial import Historial
    final, pendiente = tr.ejecutar_proceso_completo(
        g(EJEMPLO_PRODUCCION_LARGA), Historial()
    )
    assert pendiente is None
    assert validar_fnc(final) == [], validar_fnc(final)
    for cabeza, cuerpo in final.todas_las_producciones():
        assert len(cuerpo) in (1, 2), f"{cabeza} -> {cuerpo}: longitud {len(cuerpo)}"


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
