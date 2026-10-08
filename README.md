# Depuración de GLC y conversión a Forma Normal de Chomsky

Microproyecto #1 — Teoría de la Computación (UFPS 2026/02)

Recibe una Gramática Libre de Contexto `G = (V, T, P, S)`, la depura y la convierte
a Forma Normal de Chomsky (FNC), mostrando cada paso. Tiene un menú de consola y una
interfaz web.

## Requisitos

- Consola: Python 3.10 o superior, sin librerías externas.
- Web: Flask (`pip install -r requirements.txt`).

## Cómo ejecutar

```bash
python main.py                                   # menú interactivo
python main.py ejemplos/ejemplo1_inutiles_inalcanzables.txt   # modo automático con un archivo
python pruebas.py                                # pruebas automáticas
python app.py                                    # interfaz web en http://127.0.0.1:5000
```

En producción (Render): `gunicorn app:app`, según `render.yaml`.

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
- Una variable (mayúscula) usada en un cuerpo sin declararla en `V` no es un error:
  se registra como variable implícita y la etapa de inútiles la elimina.

## Proceso (6 pasos)

| # | Etapa | Función | Rótulo en la web |
|---|---|---|---|
| 1 | Variables inútiles | `calcular_generadoras`, `eliminar_variables_inutiles` | Inútiles |
| 2 | Variables inalcanzables | `calcular_alcanzables`, `eliminar_variables_inalcanzables` | Inalcanzables |
| 3 | Producciones nulas | `calcular_anulables`, `eliminar_producciones_nulas` | Nulas |
| 4 | Producciones unitarias | `calcular_pares_unitarios`, `eliminar_producciones_unitarias` | Unitarias |
| 5 | Sustituir terminales | `sustituir_terminales` | Terminales |
| 6 | Reducir producciones largas | `reducir_producciones_largas` | Chomsky |

El orden está en `ETAPAS_EN_ORDEN` (`transformaciones.py`). Todas las funciones siguen la
misma convención: reciben la gramática, **no la modifican**, y devuelven
`(gramatica_nueva, paso)`, donde `paso = crear_paso(titulo, g, nueva, identificados)`.
Las producciones eliminadas y agregadas se calculan solas.

### Menú de consola

| Opción | Acción |
|---|---|
| 1 | Ingresar gramática (escribirla o cargar un archivo) |
| 2 | Mostrar gramática original |
| 3 | Validar gramática |
| 4 | Eliminar variables inútiles |
| 5 | Eliminar variables inalcanzables |
| 6 | Eliminar producciones nulas |
| 7 | Eliminar producciones unitarias |
| 8 | Convertir a Forma Normal de Chomsky (terminales + largas) |
| 9 | Ejecutar proceso completo |
| 10 | Mostrar historial de transformaciones |
| 11 | Mostrar gramática final |
| 12 | Ingresar nueva gramática |
| 13 | Salir |

El paso a paso son las opciones 4 a 8 en ese orden; el modo automático es la 9.

### Interfaz web

Se escribe la gramática, se elige uno de los ejemplos o se usa **Cargar archivo .txt**
(solo `.txt`, máximo 5000 caracteres). Luego se recorren los 6 pasos con el antes y el
después de cada uno, o se ven todos juntos, y se puede descargar el historial.

## Estructura

| Archivo | Contenido |
|---|---|
| `gramatica.py` | Clase `Gramatica` (V, T, P, S), copia, impresión, variables auxiliares únicas X1, X2… |
| `lector.py` | Lectura desde consola, archivo o texto; registro de variables implícitas |
| `validador.py` | Validación inicial (sección 8) y validación de FNC (RNF12) |
| `historial.py` | `Paso` (antes, identificados, eliminadas, agregadas, después) e `Historial` |
| `transformaciones.py` | Algoritmos de depuración y conversión a FNC |
| `main.py` | Menú de consola de 13 opciones, modo paso a paso y automático |
| `app.py`, `templates/`, `static/` | Interfaz web (Flask); usa los mismos módulos que la consola |
| `pruebas.py` | Pruebas de todas las etapas |
| `ejemplos/` | 5 gramáticas, una por etapa (ver abajo) |

### Ejemplos

| Archivo | Muestra |
|---|---|
| `ejemplo1_inutiles_inalcanzables.txt` | `B` no genera nada, `D` es inalcanzable y, al quitar `B`, `A` también |
| `ejemplo2_nulas_unitarias.txt` | producciones `ε` y unitarias |
| `ejemplo3_terminales_repetidos.txt` | un mismo terminal reutiliza la misma variable auxiliar |
| `ejemplo4_chomsky.txt` | gramática sin nulas ni unitarias: solo la conversión a FNC |
| `ejemplo5_errores.txt` | errores a propósito (inicial `X` fuera de `V`, terminal `c` sin declarar) |

## Pruebas

`python pruebas.py` debe terminar con **21 ok, 0 pendientes, 0 fallas**.

## Decisiones de diseño (para el documento técnico)

- Cada cuerpo de producción es una tupla de símbolos; ε es la tupla vacía `()`.
  Así los nombres de varios caracteres (X1, S0, id) nunca se confunden.
- P es un `dict` de cabeza a `set` de cuerpos: no puede haber duplicados (RNF08).
- V y T son listas en orden de declaración y los cuerpos se recorren ordenados:
  la misma gramática produce siempre el mismo resultado (RNF11).
- Tratamiento de ε (RNF07): si el inicial es anulable, se conserva `S -> ε`;
  si además S aparece en algún lado derecho, se crea un inicial nuevo `S0 -> S | ε`.
- Orden del proceso: inútiles → inalcanzables → nulas → unitarias → terminales → largas.
  Las inalcanzables van después de las inútiles porque quitar una variable inútil
  puede dejar otras inalcanzables (ver `ejemplo1`).
- Variables o producciones inútiles/inalcanzables y terminales sin usar no son errores
  de validación. Los errores reales son: inicial fuera de `V` o sin producciones,
  terminal (minúscula) sin declarar, símbolo declarado como variable y terminal, y falta de
  variables, terminales, inicial o producciones, además de los de sintaxis del lector.
- Lenguaje vacío: si el inicial no genera ninguna cadena, el paso de inútiles lo informa y
  la gramática queda solo con el inicial y sin producciones. El proceso completa los 6 pasos
  y `validar_fnc` no reporta violaciones.
- Al eliminar nulas, una variable que solo derivaba ε (o `A -> ε | A`) se elimina junto con
  las versiones que la conservaban, para no dejar variables sin producciones en los cuerpos.
  Eliminar unitarias puede dejar variables sin uso (`S -> A`, `A -> a`); es válido para la FNC.
