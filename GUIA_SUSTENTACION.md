# Guía de sustentación: depuración de GLC y FNC

## 1. Idea general del proyecto

El programa recibe una **Gramática Libre de Contexto (GLC)**:

`G = (V, T, P, S)`

- `V`: variables o no terminales.
- `T`: terminales.
- `P`: producciones.
- `S`: símbolo inicial.

Luego ejecuta dos grandes procesos:

1. **Depuración de la gramática:** elimina producciones nulas, producciones
   unitarias, variables inútiles y variables inalcanzables.
2. **Conversión a Forma Normal de Chomsky (FNC):** reemplaza terminales que
   aparecen dentro de cuerpos largos y divide producciones de longitud mayor
   que dos.

El orden completo está definido en
[`ETAPAS_EN_ORDEN`](transformaciones.py:371) y es:

```text
nulas → unitarias → inútiles → inalcanzables → terminales → largas
```

La aplicación conserva un historial de cada etapa para mostrar qué se
identificó, qué producciones se eliminaron, cuáles se agregaron y cuál fue la
gramática resultante.

## 2. Qué hace cada archivo `.py`

### `gramatica.py`: modelo de datos

Contiene la clase [`Gramatica`](gramatica.py:20), que representa `G = (V,T,P,S)`.

Decisiones importantes:

- Las variables y terminales se guardan como listas para conservar el orden.
- Cada cuerpo de producción se guarda como una tupla. Por ejemplo:
  `S -> a B` se representa como `("a", "B")`.
- La producción `A -> ε` se representa como la tupla vacía `()`.
- `producciones` es un diccionario de conjuntos:
  `cabeza -> conjunto de cuerpos`. El conjunto evita duplicados.

Métodos principales:

- [`agregar_produccion`](gramatica.py:61): inserta una producción.
- [`quitar_produccion`](gramatica.py:64): elimina una producción.
- [`quitar_variable`](gramatica.py:70): elimina una variable y sus producciones.
- [`nueva_variable`](gramatica.py:76): genera auxiliares como `X1`, `X2`, etc.
- [`copia`](gramatica.py:96): crea una copia independiente para que cada etapa
  no destruya la gramática anterior.
- [`todas_las_producciones`](gramatica.py:45): devuelve las producciones en un
  orden estable.

**Idea para decir en la sustentación:** este archivo no transforma la
gramática; proporciona la estructura y las operaciones básicas que utilizan
los algoritmos.

### `lector.py`: entrada y análisis del texto

Convierte el formato escrito por el usuario en un objeto `Gramatica`.

Funciones clave:

- [`parsear_lista_simbolos`](lector.py:27): interpreta listas separadas por
  espacios o comas.
- [`parsear_producciones`](lector.py:50): lee líneas como
  `S -> A S | a`, separa alternativas y convierte `ε` en `()`.
- [`gramatica_desde_texto`](lector.py:91): procesa el texto completo y
  construye la gramática.
- [`leer_desde_archivo`](lector.py:124): carga un archivo `.txt`.
- [`leer_desde_consola`](lector.py:129): solicita la gramática de forma
  interactiva.

El lector detecta errores de **sintaxis**, por ejemplo una línea sin `->`.
Los errores semánticos, como usar una variable no declarada, se dejan para
`validador.py`.

### `validador.py`: validación

Tiene dos responsabilidades:

- [`validar_gramatica`](validador.py:14): verifica que existan variables,
  terminales, inicial y producciones; también revisa símbolos no declarados.
- [`validar_fnc`](validador.py:56): comprueba que cada producción final tenga
  una de las formas permitidas:

```text
A -> a       terminal aislado
A -> B C     exactamente dos variables
S -> ε       única excepción permitida, bajo las condiciones del inicial
```

Este módulo no corrige la gramática. Solo reporta errores y verifica el
resultado.

### `historial.py`: explicación de las transformaciones

La clase [`Paso`](historial.py:20) almacena una etapa completa:

- gramática antes;
- elementos identificados;
- producciones eliminadas;
- producciones agregadas;
- gramática después.

[`crear_paso`](historial.py:48) compara automáticamente las producciones
antes y después, por lo que cada algoritmo solo tiene que construir la nueva
gramática. La clase [`Historial`](historial.py:64) guarda todos los pasos en
orden y los imprime.

Este archivo es importante para la sustentación porque permite justificar cada
cambio, no solo mostrar la gramática final.

### `transformaciones.py`: algoritmos centrales

Es el archivo principal de la teoría. Sus funciones reciben una gramática,
**no modifican la original** y devuelven:

```text
(gramática_nueva, paso)
```

Las etapas están explicadas en la sección 3 de esta guía.

### `main.py`: aplicación de consola

La clase [`Aplicacion`](main.py:35) coordina la interacción del usuario.

- `ingresar`: obtiene la gramática desde consola o archivo.
- `cargar`: guarda la original y crea la copia de trabajo.
- `validar`: impide transformar una gramática inválida.
- `ejecutar_etapa`: ejecuta etapas individuales.
- `proceso_completo`: ejecuta todas las etapas automáticamente.
- `mostrar_historial`: imprime o guarda los cambios.
- `mostrar_final`: imprime la gramática final y llama a `validar_fnc`.

[`main`](main.py:191) decide si se usa el menú o el modo automático mediante
un archivo recibido como argumento.

### `app.py`: interfaz web Flask

Es la versión web del programa. No vuelve a implementar los algoritmos:
importa `transformaciones`, `Gramatica`, `Historial`, el lector y el validador.

Funciones importantes:

- [`gramatica_a_json`](app.py:111): convierte la gramática a JSON para la
  interfaz.
- [`paso_a_json`](app.py:133): convierte un objeto `Paso` a información
  mostrable en la web.
- [`verificacion_fnc`](app.py:151): verifica y describe la forma de cada
  producción final.
- [`procesar`](app.py:206): recibe el texto, valida, ejecuta
  [`ejecutar_proceso_completo`](transformaciones.py:379) y devuelve el resultado.

Las constantes `MAX_CARACTERES`, `MAX_PRODUCCIONES` y
`MAX_SIMBOLOS_POR_CUERPO` limitan el tamaño de las entradas públicas.

### `pruebas.py`: verificación automática

Contiene casos de prueba para validar cada etapa. Algunos ejemplos:

- [`prueba_anulables`](pruebas.py:52): verifica el cálculo de anulables.
- [`prueba_eliminar_nulas`](pruebas.py:66): revisa las combinaciones creadas.
- [`prueba_eliminar_unitarias`](pruebas.py:84): comprueba que no queden
  producciones unitarias.
- [`prueba_eliminar_inutiles`](pruebas.py:93): comprueba la eliminación de
  variables no generadoras.
- [`prueba_proceso_completo_en_fnc`](pruebas.py:115): verifica el proceso
  completo.
- [`prueba_ciclo_unitarias`](pruebas.py:172): comprueba que los ciclos no
  produzcan bucles infinitos.
- [`prueba_terminales_repetidos`](pruebas.py:191): verifica que un terminal
  reutilice la misma variable auxiliar.
- [`prueba_produccion_larga`](pruebas.py:209): verifica la binarización.

## 3. Código principal de la depuración

### 3.1 Producciones nulas

Funciones:

- [`calcular_anulables`](transformaciones.py:35)
- [`eliminar_producciones_nulas`](transformaciones.py:55)

Una variable es anulable si puede derivar `ε`. El cálculo usa un **punto
fijo**:

```python
anulables = set()
while cambio:
    ...
    if all(s in anulables for s in cuerpo):
        anulables.add(cabeza)
```

El ciclo continúa hasta que el conjunto deja de crecer. Para eliminar nulas,
cada variable anulable de un cuerpo puede conservarse u omitirse. Si hay `k`
posiciones anulables, se generan `2^k` combinaciones mediante
`itertools_product`.

Ejemplo conceptual:

```text
S -> A S A,  A anulable
```

genera, entre otras:

```text
S -> A S A
S -> S A
S -> A S
S -> S
```

El tratamiento especial del inicial está en el bloque `Tratamiento de ε` de
[`eliminar_producciones_nulas`](transformaciones.py:55). Si el inicial es
anulable y aparece a la derecha, crea `S0 -> S | ε` para conservar el lenguaje
sin violar la condición de FNC.

### 3.2 Producciones unitarias

Funciones:

- [`calcular_pares_unitarios`](transformaciones.py:119)
- [`eliminar_producciones_unitarias`](transformaciones.py:141)

Una producción unitaria tiene forma `A -> B`, donde `B` es variable. Primero se
calculan los pares `(A,B)` alcanzables usando únicamente producciones
unitarias. Se incluyen pares reflexivos `(A,A)` y se repite hasta alcanzar un
punto fijo; esto permite manejar ciclos como `A -> B` y `B -> A`.

Después, para cada par `(A,B)`, las producciones no unitarias de `B` se copian
como producciones de `A`. Las unitarias no se vuelven a copiar.

### 3.3 Variables inútiles o no generadoras

Funciones:

- [`calcular_generadoras`](transformaciones.py:177)
- [`eliminar_variables_inutiles`](transformaciones.py:194)

Una variable es generadora si puede producir una cadena formada únicamente por
terminales, posiblemente pasando por otras variables generadoras. También se
calcula por punto fijo:

```python
if all(g.es_terminal(s) or s in generadoras for s in cuerpo):
    generadoras.add(cabeza)
```

Las variables que no están en `generadoras` se eliminan, al igual que toda
producción que las use. Si el símbolo inicial no es generador, el programa
registra que el lenguaje es vacío.

### 3.4 Variables inalcanzables

Funciones:

- [`calcular_alcanzables`](transformaciones.py:234)
- [`eliminar_variables_inalcanzables`](transformaciones.py:255)

Se hace un recorrido BFS desde el símbolo inicial. Cada variable visitada
permite descubrir los símbolos de sus cuerpos. Las variables y terminales que
nunca se visitan se eliminan.

Esta etapa va después de las inútiles porque eliminar una variable no
generadora puede dejar otras variables sin camino desde el inicial.

## 4. Código principal de la Forma Normal de Chomsky

### 4.1 Sustitución de terminales

Función: [`sustituir_terminales`](transformaciones.py:281).

En FNC, un terminal solo puede aparecer en una producción de un símbolo:

```text
X -> a
```

Por eso, si aparece en un cuerpo de longitud dos o más, se crea una variable
auxiliar:

```text
S -> a A b
```

se transforma en:

```text
S  -> X1 A X2
X1 -> a
X2 -> b
```

El diccionario `terminal_a_var` garantiza que el mismo terminal reutilice la
misma variable auxiliar en todas las producciones.

### 4.2 Reducción de producciones largas

Función: [`reducir_producciones_largas`](transformaciones.py:318).

Una producción de longitud mayor que dos se divide en producciones binarias:

```text
A -> B C D
```

se convierte en:

```text
A  -> B X1
X1 -> C D
```

Para cuerpos más largos se continúa creando una cadena de auxiliares. El
diccionario `cola_a_var` reutiliza una variable cuando ya se procesó la misma
cola de símbolos.

### 4.3 Ejecución completa

[`ejecutar_proceso_completo`](transformaciones.py:379) recorre
`ETAPAS_EN_ORDEN`, actualiza la gramática y agrega cada `Paso` al historial.
Cuando termina, `validar_fnc` confirma que no queden producciones inválidas.

## 5. Flujo que se puede explicar oralmente

1. El usuario escribe una gramática o carga un archivo.
2. `lector.py` convierte el texto a un objeto `Gramatica`.
3. `validador.py` comprueba que los símbolos y producciones sean válidos.
4. `main.py` o `app.py` llama al proceso completo.
5. `transformaciones.py` elimina nulas, unitarias, inútiles e inalcanzables.
6. Luego adapta terminales y divide producciones largas para obtener FNC.
7. `historial.py` registra el antes, el después y las diferencias de cada etapa.
8. `validador.py` revisa que la gramática final cumpla las reglas de FNC.
9. `pruebas.py` confirma casos normales y casos especiales como ciclos, lenguaje
   vacío, `ε`, terminales repetidos y producciones largas.

## 6. Guion corto para la sustentación

> El proyecto recibe una gramática libre de contexto y la representa como
> `G=(V,T,P,S)`. Primero se valida la entrada. Después se aplica una depuración
> en cuatro etapas: se eliminan producciones nulas, unitarias, variables no
> generadoras y símbolos inalcanzables. Cada algoritmo trabaja sobre una copia
> y devuelve una gramática nueva junto con un objeto `Paso`, lo que permite
> mostrar las producciones eliminadas y agregadas.
>
> Finalmente se realiza la conversión a Forma Normal de Chomsky. Los terminales
> que aparecen en cuerpos largos se reemplazan por variables auxiliares y las
> producciones con más de dos símbolos se dividen en producciones binarias.
> El proceso completo está coordinado por `ejecutar_proceso_completo` y el
> resultado se verifica con `validar_fnc`. La interfaz de consola está en
> `main.py`, la interfaz web en `app.py` y las pruebas automáticas en
> `pruebas.py`.

## 7. Diferencia clave que conviene aclarar

La **depuración** busca quitar elementos que sobran o que no aportan al
lenguaje:

```text
nulas, unitarias, no generadoras e inalcanzables
```

La **FNC** no elimina simplemente lo que sobra; reorganiza las producciones
para que tengan las formas restringidas:

```text
A -> a
A -> B C
S -> ε   (solo bajo la condición permitida)
```
