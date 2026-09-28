"""
app.py
Interfaz web del aplicativo (Flask), pensada para desplegarse en Render.

La interfaz NO reimplementa ningún algoritmo: importa los mismos módulos
que usa el menú de consola (lector, validador, transformaciones, historial)
y solo convierte sus resultados a JSON para mostrarlos paso a paso.

Ejecución local:   python app.py              -> http://127.0.0.1:5000
Producción:        gunicorn app:app           (Render define la variable PORT)
"""

import glob
import os

from flask import Flask, jsonify, render_template, request

import transformaciones as tr
from gramatica import Gramatica
from historial import Historial
from lector import gramatica_desde_texto
from validador import validar_fnc, validar_gramatica

app = Flask(__name__)

BASE = os.path.dirname(os.path.abspath(__file__))

# Límites para proteger el servidor público (la eliminación de nulas
# genera 2^k variantes por producción).
MAX_CARACTERES = 5000
MAX_PRODUCCIONES = 150
MAX_SIMBOLOS_POR_CUERPO = 12

# Explicación de cada etapa, en el mismo orden de ETAPAS_EN_ORDEN
EXPLICACIONES = [
    {
        "corto": "Nulas",
        "titulo": "Eliminación de producciones nulas",
        "rf": "RF07, RF08",
        "que_hace": "Una variable es anulable si puede derivar la cadena vacía ε. "
                    "Cada producción se reescribe en todas sus versiones posibles, "
                    "conservando u omitiendo cada variable anulable, y se eliminan "
                    "las producciones A → ε.",
        "detalle": "Si el símbolo inicial es anulable, ε pertenece al lenguaje y se "
                   "conserva solo en el inicial (con un nuevo S0 → S | ε si S aparece "
                   "en algún lado derecho).",
    },
    {
        "corto": "Unitarias",
        "titulo": "Eliminación de producciones unitarias",
        "rf": "RF09, RF10",
        "que_hace": "Una producción unitaria tiene la forma A → B, con B variable. "
                    "Se calculan los pares (A, B) tales que A llega a B usando solo "
                    "producciones unitarias, y A recibe las producciones no unitarias de B.",
        "detalle": "Va después de las nulas porque eliminar nulas puede crear "
                   "producciones unitarias nuevas, como S → S.",
    },
    {
        "corto": "Inútiles",
        "titulo": "Eliminación de variables inútiles",
        "rf": "RF11, RF12",
        "que_hace": "Una variable es generadora si puede derivar alguna cadena de "
                    "terminales. Las no generadoras nunca terminan en una palabra, "
                    "así que se eliminan junto con toda producción que las use.",
        "detalle": "Se calcula por punto fijo: se repite hasta que el conjunto de "
                   "generadoras deja de crecer.",
    },
    {
        "corto": "Inalcanzables",
        "titulo": "Eliminación de variables inalcanzables",
        "rf": "RF13, RF14",
        "que_hace": "Se recorre la gramática desde el símbolo inicial. Las variables "
                    "y terminales que nunca aparecen en ese recorrido no participan en "
                    "ninguna derivación y se eliminan.",
        "detalle": "Va después de las inútiles porque quitar una variable no "
                   "generadora puede dejar a otras sin camino desde el inicial.",
    },
    {
        "corto": "Terminales",
        "titulo": "Sustitución de terminales",
        "rf": "RF15, RF17",
        "que_hace": "En la FNC un terminal solo puede aparecer solo (A → a). En los "
                    "cuerpos de dos o más símbolos, cada terminal se reemplaza por una "
                    "variable auxiliar Xk con la producción Xk → a.",
        "detalle": "El mismo terminal usa siempre la misma variable auxiliar, así "
                   "no se duplican producciones.",
    },
    {
        "corto": "Largas",
        "titulo": "Reducción de producciones largas",
        "rf": "RF16, RF17",
        "que_hace": "Las producciones con más de dos variables se parten en una cadena "
                    "de producciones binarias: A → B C D se convierte en A → B X y X → C D.",
        "detalle": "Si la misma secuencia de símbolos aparece en varias producciones, "
                   "se reutiliza la misma variable auxiliar.",
    },
]

EJEMPLO_EPSILON = """# Cadena vacía en el lenguaje: S es anulable y aparece a la derecha
V: S
T: a b
S: S
P:
S -> a S b | ε
"""


# ----------------------------------------------------------------------
# Conversión a JSON
# ----------------------------------------------------------------------
def gramatica_a_json(g, eliminadas=(), agregadas=()):
    """Serializa la gramática marcando cada producción como
    'normal', 'eliminada' o 'agregada' para dibujar el antes/después."""
    eliminadas = set(eliminadas)
    agregadas = set(agregadas)
    producciones = []
    for cabeza in g.cabezas_ordenadas():
        cuerpos = []
        for cuerpo in Gramatica.ordenar_cuerpos(g.producciones[cabeza]):
            par = (cabeza, cuerpo)
            estado = "eliminada" if par in eliminadas else "agregada" if par in agregadas else "normal"
            cuerpos.append({"texto": Gramatica.cuerpo_a_texto(cuerpo), "estado": estado})
        producciones.append({"cabeza": cabeza, "cuerpos": cuerpos})
    return {
        "variables": list(g.variables),
        "terminales": list(g.terminales),
        "inicial": g.inicial,
        "producciones": producciones,
        "total": len(g.conjunto_producciones()),
    }


def paso_a_json(indice, paso):
    info = EXPLICACIONES[indice]
    texto = lambda par: Gramatica.produccion_a_texto(*par).replace("->", "→")
    return {
        "numero": indice + 1,
        "titulo": paso.titulo,
        "corto": info["corto"],
        "rf": info["rf"],
        "que_hace": info["que_hace"],
        "detalle": info["detalle"],
        "identificados": [x.replace(" -> ", " → ") for x in paso.identificados],
        "eliminadas": [texto(p) for p in paso.eliminadas],
        "agregadas": [texto(p) for p in paso.agregadas],
        "antes": gramatica_a_json(paso.antes, eliminadas=paso.eliminadas),
        "despues": gramatica_a_json(paso.despues, agregadas=paso.agregadas),
    }


def verificacion_fnc(g):
    """Revisa cada producción de la gramática final usando validar_fnc."""
    violaciones = validar_fnc(g)
    detalle = []
    for cabeza, cuerpo in g.todas_las_producciones():
        texto = g.produccion_a_texto(cabeza, cuerpo)
        if len(cuerpo) == 0:
            forma = "S → ε (cadena vacía en el inicial)"
        elif len(cuerpo) == 1:
            forma = "A → a (un terminal)"
        elif len(cuerpo) == 2:
            forma = "A → BC (dos variables)"
        else:
            forma = "más de dos símbolos"
        ok = not any(v.startswith(texto + ":") for v in violaciones)
        detalle.append({"texto": texto.replace("->", "→"), "forma": forma, "ok": ok})
    return {"valida": not violaciones, "violaciones": violaciones, "producciones": detalle}


def errores_de_limites(texto, g):
    if len(texto) > MAX_CARACTERES:
        return [f"Error: la gramática supera el máximo de {MAX_CARACTERES} caracteres."]
    if len(g.conjunto_producciones()) > MAX_PRODUCCIONES:
        return [f"Error: la gramática supera el máximo de {MAX_PRODUCCIONES} producciones."]
    for cabeza, cuerpo in g.todas_las_producciones():
        if len(cuerpo) > MAX_SIMBOLOS_POR_CUERPO:
            return [f"Error: la producción {g.produccion_a_texto(cabeza, cuerpo)} tiene más de "
                    f"{MAX_SIMBOLOS_POR_CUERPO} símbolos."]
    return []


# ----------------------------------------------------------------------
# Rutas
# ----------------------------------------------------------------------
@app.get("/")
def inicio():
    return render_template("index.html")


@app.get("/api/ejemplos")
def ejemplos():
    lista = []
    for ruta in sorted(glob.glob(os.path.join(BASE, "ejemplos", "*.txt"))):
        with open(ruta, encoding="utf-8") as archivo:
            texto = archivo.read()
        lista.append({"nombre": os.path.basename(ruta), "texto": texto})
    lista.append({"nombre": "cadena_vacia (S → aSb | ε)", "texto": EJEMPLO_EPSILON})
    for ej in lista:
        comentario = next((l.lstrip("# ").strip() for l in ej["texto"].splitlines()
                           if l.startswith("#")), "")
        ej["descripcion"] = comentario
    return jsonify(lista)


@app.post("/api/procesar")
def procesar():
    datos = request.get_json(silent=True) or {}
    texto = str(datos.get("texto", ""))[: MAX_CARACTERES + 1]

    gramatica, errores = gramatica_desde_texto(texto)
    errores = errores_de_limites(texto, gramatica) + errores + validar_gramatica(gramatica)
    errores = list(dict.fromkeys(errores))          # sin repetidos, en orden
    if errores:
        return jsonify({"ok": False, "errores": errores,
                        "original": gramatica_a_json(gramatica)})

    historial = Historial()
    final, pendiente = tr.ejecutar_proceso_completo(gramatica.copia(), historial)
    if pendiente:
        return jsonify({"ok": False, "errores": [f"La etapa {pendiente} no está implementada."]})

    pasos = [paso_a_json(i, p) for i, p in enumerate(historial.pasos)]
    lenguaje_vacio = any("vacío" in linea for p in historial.pasos for linea in p.identificados)
    return jsonify({
        "ok": True,
        "original": gramatica_a_json(gramatica),
        "pasos": pasos,
        "final": gramatica_a_json(final),
        "fnc": verificacion_fnc(final),
        "lenguaje_vacio": lenguaje_vacio,
        "historial": historial.a_texto(),
    })


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5000)), debug=False)
