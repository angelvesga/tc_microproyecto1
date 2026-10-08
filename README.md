# Depuración de GLC y conversión a Forma Normal de Chomsky

Microproyecto #1 — Teoría de la Computación (UFPS 2026/02)

## Requisitos

Python 3.10 o superior. No usa librerías externas.

## Cómo ejecutar

```bash
python main.py                                   # menú interactivo
python main.py ejemplos/ejemplo1_inutiles_inalcanzables.txt   # modo automático con un archivo
python pruebas.py                                # pruebas automáticas
```

## Formato de entrada

```
V: S A B
T: a b
S: S
P:
S -> A S A | a B
A -> B | S
B -> b | ε
```

- Símbolos separados por espacios o comas.
- ε se escribe `ε`, `eps`, `epsilon` o `λ`.
- Si todos los símbolos son de un carácter, se puede escribir pegado (`S -> aB`).
- Líneas que empiezan con `#` son comentarios.

## Estructura

| Archivo | Contenido | Estado |
|---|---|---|
| `gramatica.py` | Clase `Gramatica` (V, T, P, S), copia, impresión, variables auxiliares únicas X1, X2… | Listo |
| `lector.py` | Lectura desde consola y desde archivo | Listo |
| `validador.py` | Validación inicial (sección 8) y validación de FNC (RNF12) | Listo |
| `historial.py` | `Paso` (antes, identificados, eliminadas, agregadas, después) e `Historial` | Listo |
| `main.py` | Menú de 13 opciones, modo paso a paso y automático | Listo |
| `transformaciones.py` | Algoritmos | Ver abajo |
| `pruebas.py` | Pruebas de todas las etapas | Listo |
| `ejemplos/` | 5 gramáticas, una por etapa: `ejemplo1_inutiles_inalcanzables`, `ejemplo2_nulas_unitarias`, `ejemplo3_terminales_repetidos`, `ejemplo4_chomsky` y `ejemplo5_errores` (con errores a propósito) | Listo |

### Algoritmos en `transformaciones.py`

| Etapa | Función | Estado |
|---|---|---|
| Producciones nulas | `calcular_anulables`, `eliminar_producciones_nulas` | **TODO** |
| Producciones unitarias | `calcular_pares_unitarios`, `eliminar_producciones_unitarias` | **TODO** |
| Variables inútiles | `calcular_generadoras`, `eliminar_variables_inutiles` | **TODO** |
| Variables inalcanzables | `calcular_alcanzables`, `eliminar_variables_inalcanzables` | **TODO** |
| Sustituir terminales | `sustituir_terminales` | **TODO** |
| Reducir producciones largas | `reducir_producciones_largas` | **TODO** |

Cada función pendiente tiene en su docstring los pasos del algoritmo.
Todas siguen la misma convención: reciben la gramática, **no la modifican**,
y devuelven `(gramatica_nueva, paso)`, donde `paso = crear_paso(titulo, g, nueva, identificados)`.
Las producciones eliminadas y agregadas se calculan solas.

Cuando implementen una función, `python pruebas.py` debe pasar de `PENDIENTE` a `OK`.
La meta es: **19 ok, 0 pendientes, 0 fallas**.

## Decisiones de diseño (para el documento técnico)

- Cada cuerpo de producción es una tupla de símbolos; ε es la tupla vacía `()`.
  Así los nombres de varios caracteres (X1, S0, id) nunca se confunden.
- P es un `dict` de cabeza a `set` de cuerpos: no puede haber duplicados (RNF08).
- V y T son listas en orden de declaración y los cuerpos se recorren ordenados:
  la misma gramática produce siempre el mismo resultado (RNF11).
- Tratamiento de ε (RNF07): si el inicial es anulable, se conserva `S -> ε`;
  si además S aparece en algún lado derecho, se crea un inicial nuevo `S0 -> S | ε`.
- Orden del proceso: inútiles → inalcanzables → nulas → unitarias → terminales → largas
  (en la web, el último paso se rotula «Chomsky»; en el menú de consola son las opciones 4 a 8).
  Las inalcanzables van después de las inútiles porque quitar una variable inútil
  puede dejar otras inalcanzables (ver `ejemplo1`).
- Variables o producciones inútiles/inalcanzables y terminales sin usar no son errores
  de validación. Si el símbolo inicial no genera ninguna cadena (lenguaje vacío), el paso
  de inútiles lo informa y la gramática queda solo con el inicial y sin producciones.
- Al eliminar nulas, una variable que solo derivaba ε (o `A -> ε | A`) se elimina junto con
  las versiones que la conservaban, para no dejar variables sin producciones en los cuerpos.
  Eliminar unitarias puede dejar variables sin uso (`S -> A`, `A -> a`); es válido para la FNC.
