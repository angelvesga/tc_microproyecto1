"""
historial.py
Registro de cada transformación (RF18, RNF10, sección 9 del enunciado).

Cada etapa genera un objeto Paso con:
  - gramática inicial de la etapa (antes)
  - elementos identificados (anulables, pares unitarios, generadoras, ...)
  - producciones eliminadas y agregadas (calculadas automáticamente)
  - gramática resultante (despues)
"""

from dataclasses import dataclass, field

from gramatica import Gramatica

SEPARADOR = "=" * 60


@dataclass
class Paso:
    titulo: str
    antes: Gramatica
    despues: Gramatica
    identificados: list = field(default_factory=list)
    eliminadas: list = field(default_factory=list)
    agregadas: list = field(default_factory=list)

    def a_texto(self, numero=None):
        encabezado = f"PASO {numero}: {self.titulo}" if numero else self.titulo
        partes = [SEPARADOR, encabezado, SEPARADOR,
                  "Gramática inicial de la etapa:", self.antes.a_texto(), ""]

        partes.append("Elementos identificados:")
        partes += [f"   - {x}" for x in self.identificados] or ["   (ninguno)"]

        partes.append("Producciones eliminadas:")
        partes += [f"   - {Gramatica.produccion_a_texto(c, b)}" for c, b in self.eliminadas] \
            or ["   (ninguna)"]

        partes.append("Producciones agregadas:")
        partes += [f"   + {Gramatica.produccion_a_texto(c, b)}" for c, b in self.agregadas] \
            or ["   (ninguna)"]

        partes += ["", "Gramática resultante:", self.despues.a_texto(), ""]
        return "\n".join(partes)


def crear_paso(titulo, antes, despues, identificados):
    """Construye el Paso comparando las producciones de antes y después,
    así ninguna función de transformación tiene que llevar la cuenta."""
    orden = lambda par: (par[0], len(par[1]) == 0, par[1])
    prods_antes = antes.conjunto_producciones()
    prods_despues = despues.conjunto_producciones()
    return Paso(
        titulo=titulo,
        antes=antes.copia(),
        despues=despues.copia(),
        identificados=list(identificados),
        eliminadas=sorted(prods_antes - prods_despues, key=orden),
        agregadas=sorted(prods_despues - prods_antes, key=orden),
    )


class Historial:
    def __init__(self):
        self.pasos = []

    def agregar(self, paso):
        self.pasos.append(paso)

    def limpiar(self):
        self.pasos.clear()

    def a_texto(self):
        if not self.pasos:
            return "El historial está vacío."
        return "\n".join(p.a_texto(i) for i, p in enumerate(self.pasos, start=1))
