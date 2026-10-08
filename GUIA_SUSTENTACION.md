# Guía de sustentación: depuración de GLC y FNC

## 1. Idea general del proyecto

El programa recibe una **Gramática Libre de Contexto (GLC)**:

`G = (V, T, P, S)`

- `V`: variables o no terminales.
- `T`: terminales.
- `P`: producciones.
- `S`: símbolo inicial.

Luego ejecuta dos grandes procesos:

1. **Depuración de la gramática:** elimina variables inútiles, variables
   inalcanzables, producciones nulas y producciones unitarias.
2. **Conversión a Forma Normal de Chomsky (FNC):** reemplaza terminales que
   aparecen dentro de cuerpos largos y divide producciones de longitud mayor
   que dos.

El orden completo está definido en
[`ETAPAS_EN_ORDEN`](transformaciones.py:396) y es:

```text
inútiles → inalcanzables → nulas → unitarias → terminales → largas
```

En la interfaz web los seis pasos se rotulan: Inútiles, Inalcanzables, Nulas,
Unitarias, Terminales y **Chomsky** (este último es la reducción de producciones
largas, que cierra la conversión). En el menú de consola, las opciones 4 a 7 son
inútiles, inalcanzables, nulas y unitarias, y la 8 es la conversión a Chomsky
(terminales + largas).

**Por qué este orden:**

- Primero se limpia lo que sobra (inútiles e inalcanzables), así las etapas
  siguientes no trabajan con símbolos que luego se descartarían (por ejemplo, no
  se generan las `2^k` versiones de una producción que iba a desaparecer).
- Inútiles va antes que inalcanzables, porque quitar una variable no generadora
  puede dejar otras variables sin camino desde el inicial.
- Nulas va antes que unitarias, porque quitar nulas puede crear unitarias
  nuevas (por ejemplo `S -> S`).
- Unitarias va antes de la FNC, porque la FNC no admite producciones `A -> B`.

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
- `implicitas` es la lista de variables que el usuario usó en un cuerpo sin
  declararlas en `V` (ver `lector.py`).

Métodos principales:

- [`agregar_produccion`](gramatica.py:77): inserta una producción.
- [`quitar_produccion`](gramatica.py:80): elimina una producción.
- [`quitar_variable`](gramatica.py:87): elimina una variable y sus producciones.
- [`nueva_variable`](gramatica.py:93): genera auxiliares como `X1`, `X2`, etc.
- [`copia`](gramatica.py:113): crea una copia independiente para que cada etapa
  no destruya la gramática anterior.
- [`todas_las_producciones`](gramatica.py:61): devuelve las producciones en un
  orden estable.

**Idea para decir en la sustentación:** este archivo no transforma la
gramática; proporciona la estructura y las operaciones básicas que utilizan
los algoritmos.

### `lector.py`: entrada y análisis del texto

Convierte el formato escrito por el usuario en un objeto `Gramatica`.

Funciones clave:

- [`parsear_lista_simbolos`](lector.py:28): interpreta listas separadas por
  espacios o comas.
- [`parsear_producciones`](lector.py:51): lee líneas como
  `S -> A S | a`, separa alternativas y convierte `ε` en `()`.
- [`registrar_variables_implicitas`](lector.py:92): si un símbolo que empieza en
  mayúscula se usa en un cuerpo pero no está declarado en `V` ni en `T`, se
  agrega a `V` como **variable implícita** (y se anota en `g.implicitas`).
- [`gramatica_desde_texto`](lector.py:107): procesa el texto completo, construye
  la gramática y registra las variables implícitas.
- [`leer_desde_archivo`](lector.py:141): carga un archivo `.txt`.
- [`leer_desde_consola`](lector.py:146): solicita la gramática de forma
  interactiva.

El registro de variables implícitas está en **un solo punto**, y tanto la
consola como la web leen con `gramatica_desde_texto`, por eso no se duplica
lógica. Una variable implícita no tiene producciones, así que es no generadora
y la etapa de inútiles la elimina junto con las producciones que la usan.

El lector detecta errores de **sintaxis**, por ejemplo una línea sin `->` o una
alternativa vacía. Los errores semánticos los deja para `validador.py`.

### `validador.py`: validación

Tiene dos responsabilidades:

- [`validar_gramatica`](validador.py:14): reporta solo **errores reales**:
  que no haya variables, terminales, inicial o producciones; que el inicial no
  esté en `V` o no tenga producciones; que un símbolo sea variable y terminal a
  la vez; que se use un terminal (minúscula) sin declarar; o que el lado
  izquierdo de una producción no sea una variable declarada.
- [`validar_fnc`](validador.py:58): comprueba que cada producción final tenga
  una de las formas permitidas:

```text
A -> a       terminal aislado
A -> B C     exactamente dos variables
S -> ε       única excepción permitida, bajo las condiciones del inicial
```

**Qué NO es un error:** tener variables o producciones inútiles o
inalcanzables, terminales declarados que nunca se usan, o variables usadas sin
declarar (se registran como implícitas). Todo eso lo resuelve el proceso de
depuración, no la validación. Una gramática con lenguaje vacío tampoco es un
error: el proceso termina con una gramática sin producciones, que
`validar_fnc` considera válida porque no hay ninguna producción que viole la
forma.

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

Las etapas están explicadas en las secciones 3 y 4 de esta guía.

### `main.py`: aplicación de consola

La clase [`Aplicacion`](main.py:35) coordina la interacción del usuario.

- `ingresar`: obtiene la gramática desde consola o archivo.
- `cargar`: guarda la original y crea la copia de trabajo.
- [`validar`](main.py:72): impide transformar una gramática inválida.
- [`ejecutar_etapa`](main.py:88): ejecuta etapas individuales (opciones 4 a 8 del
  menú, en el orden del proceso).
- `proceso_completo`: ejecuta todas las etapas automáticamente (opción 9).
- `mostrar_historial`: imprime o guarda los cambios.
- `mostrar_final`: imprime la gramática final y llama a `validar_fnc`.

[`main`](main.py:191) decide si se usa el menú o el modo automático mediante
un archivo recibido como argumento, por ejemplo
`python main.py ejemplos/ejemplo1_inutiles_inalcanzables.txt`.

### `app.py`: interfaz web Flask

Es la versión web del programa. No vuelve a implementar los algoritmos:
importa `transformaciones`, `Gramatica`, `Historial`, el lector y el validador.

Funciones importantes:

- [`gramatica_a_json`](app.py:109): convierte la gramática a JSON para la
  interfaz.
- [`paso_a_json`](app.py:131): convierte un objeto `Paso` a información
  mostrable en la web. Los textos de cada paso están en la lista
  `EXPLICACIONES`, en el mismo orden que `ETAPAS_EN_ORDEN`.
- [`verificacion_fnc`](app.py:149): verifica y describe la forma de cada
  producción final.
- [`procesar`](app.py:203): recibe el texto, valida, ejecuta
  [`ejecutar_proceso_completo`](transformaciones.py:406) y devuelve el resultado.

Las constantes `MAX_CARACTERES`, `MAX_PRODUCCIONES` y
`MAX_SIMBOLOS_POR_CUERPO` limitan el tamaño de las entradas públicas.

En la tarjeta de entrada de la web se puede escribir la gramática, elegir uno
de los **5 ejemplos** o usar el botón **«Cargar archivo .txt»**, que lee el
archivo en el navegador (solo `.txt`, máximo `MAX_CARACTERES`), lo pone en el
cuadro de texto y lo convierte.

### Ejemplos (`ejemplos/`)

Hay cinco, uno por etapa y numerados en el orden del proceso:

| Archivo | Para mostrar |
|---|---|
| `ejemplo1_inutiles_inalcanzables.txt` | `B` no genera nada y `D` es inalcanzable; al quitar `B`, `A` también queda inalcanzable |
| `ejemplo2_nulas_unitarias.txt` | producciones `ε` y unitarias |
| `ejemplo3_terminales_repetidos.txt` | el mismo terminal reutiliza una sola variable auxiliar |
| `ejemplo4_chomsky.txt` | gramática sin nulas ni unitarias, solo conversión a FNC |
| `ejemplo5_errores.txt` | errores reales: inicial `X` fuera de `V` y terminal `c` sin declarar |

### `pruebas.py`: verificación automática

Contiene casos de prueba para validar cada etapa. Algunos ejemplos:

- [`prueba_validacion_errores`](pruebas.py:40): comprueba los errores reales y
  que `D` (mayúscula sin declarar) ya no es error sino variable implícita.
- [`prueba_anulables`](pruebas.py:54): verifica el cálculo de anulables.
- [`prueba_eliminar_nulas`](pruebas.py:68): revisa las combinaciones creadas.
- [`prueba_eliminar_unitarias`](pruebas.py:86): comprueba que no queden
  producciones unitarias.
- [`prueba_eliminar_inutiles`](pruebas.py:95): comprueba la eliminación de
  variables no generadoras.
- [`prueba_proceso_completo_en_fnc`](pruebas.py:117): verifica el proceso
  completo.
- [`prueba_ciclo_unitarias`](pruebas.py:174): comprueba que los ciclos no
  produzcan bucles infinitos.
- [`prueba_terminales_repetidos`](pruebas.py:193): verifica que un terminal
  reutilice la misma variable auxiliar.
- [`prueba_produccion_larga`](pruebas.py:211): verifica la binarización.
- [`prueba_orden_de_etapas`](pruebas.py:255): fija el orden de
  `ETAPAS_EN_ORDEN`.
- [`prueba_inutiles_e_inalcanzables_no_son_error`](pruebas.py:266): gramáticas
  con inútiles/inalcanzables validan bien y terminan en FNC.
- [`prueba_lenguaje_vacio_proceso_completo`](pruebas.py:280): el lenguaje vacío
  recorre los 6 pasos y termina sin producciones.
- [`prueba_nulas_no_deja_variables_sin_producciones`](pruebas.py:295): una
  variable que solo derivaba `ε` no queda en ningún cuerpo.
- [`prueba_variable_no_declarada_se_elimina`](pruebas.py:319): la variable `F`
  usada sin declarar se elimina con `A -> F`.
- [`prueba_errores_reales_siguen_siendo_errores`](pruebas.py:337): el inicial sin
  producciones y los terminales sin declarar siguen siendo errores.

## 3. Código principal de la depuración

Las cuatro etapas se explican en el orden en que se ejecutan.

### 3.1 Variables inútiles o no generadoras

Funciones:

- [`calcular_generadoras`](transformaciones.py:195)
- [`eliminar_variables_inutiles`](transformaciones.py:212)

Una variable es generadora si puede producir una cadena formada únicamente por
terminales, posiblemente pasando por otras variables generadoras. Se calcula por
punto fijo:

```python
if all(g.es_terminal(s) or s in generadoras for s in cuerpo):
    generadoras.add(cabeza)
```

Las variables que no están en `generadoras` se eliminan **de `V`**, junto con
sus propias producciones y con toda producción que las use en el cuerpo. Una
variable usada sin declarar (variable implícita) no tiene producciones, así que
cae aquí; el paso la indica en «Elementos identificados» como *Variables
implícitas (no declaradas)*.

**Lenguaje vacío:** si el símbolo inicial no es generador, no hay ninguna cadena
que generar. El paso lo informa, y la gramática queda **solo con el inicial y sin
producciones**. Las demás etapas se ejecutan igual (sin error) y la web muestra
el aviso amarillo de «lenguaje vacío», no el rojo de error de FNC.

### 3.2 Variables inalcanzables

Funciones:

- [`calcular_alcanzables`](transformaciones.py:261)
- [`eliminar_variables_inalcanzables`](transformaciones.py:282)

Se hace un recorrido BFS desde el símbolo inicial. Cada variable visitada
permite descubrir los símbolos de sus cuerpos. Las variables y terminales que
nunca se visitan se eliminan, junto con las producciones de esas variables.

Esta etapa va después de las inútiles porque eliminar una variable no
generadora puede dejar otras variables sin camino desde el inicial.

### 3.3 Producciones nulas

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

**Efecto del nuevo orden:** ya no hay una etapa de inútiles después, así que
esta función se encarga de no dejar variables colgadas. Si una variable solo
derivaba `ε` (por ejemplo `A -> ε`, o `A -> ε | A`), al quitar sus producciones
no le queda ninguna cadena terminal que generar. Las versiones que la conservan
se **descartan** y la variable se elimina de `V` (se calcula con
`calcular_generadoras` sobre la gramática nueva). Así `S -> A a, A -> ε` queda
como `S -> a`.

El tratamiento especial del inicial está en el bloque `Tratamiento de ε` de
[`eliminar_producciones_nulas`](transformaciones.py:55). Si el inicial es
anulable y aparece a la derecha, crea `S0 -> S | ε` para conservar el lenguaje
sin violar la condición de FNC.

### 3.4 Producciones unitarias

Funciones:

- [`calcular_pares_unitarios`](transformaciones.py:137)
- [`eliminar_producciones_unitarias`](transformaciones.py:159)

Una producción unitaria tiene forma `A -> B`, donde `B` es variable. Primero se
calculan los pares `(A,B)` alcanzables usando únicamente producciones
unitarias. Se incluyen pares reflexivos `(A,A)` y se repite hasta alcanzar un
punto fijo; esto permite manejar ciclos como `A -> B` y `B -> A`.

Después, para cada par `(A,B)`, las producciones no unitarias de `B` se copian
como producciones de `A`. Las unitarias no se vuelven a copiar.

**Efecto del nuevo orden:** esta etapa puede dejar variables que ya nadie usa.
Por ejemplo, `S -> A, A -> a` queda como `S -> a, A -> a`, y `A` es inalcanzable.
No es un error: la gramática sigue siendo equivalente y válida para la FNC. Es
una consecuencia de que las inalcanzables se eliminan antes que las unitarias,
y no se agregó una etapa adicional (el proceso sigue siendo de 6 pasos).

## 4. Código principal de la Forma Normal de Chomsky

### 4.1 Sustitución de terminales

Función: [`sustituir_terminales`](transformaciones.py:308).

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

Función: [`reducir_producciones_largas`](transformaciones.py:345).

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

[`ejecutar_proceso_completo`](transformaciones.py:406) recorre
`ETAPAS_EN_ORDEN`, actualiza la gramática y agrega cada `Paso` al historial.
Cuando termina, `validar_fnc` confirma que no queden producciones inválidas.

## 5. Flujo que se puede explicar oralmente

1. El usuario escribe una gramática, elige un ejemplo o carga un archivo `.txt`.
2. `lector.py` convierte el texto a un objeto `Gramatica` y registra como
   variables implícitas las que se usaron sin declarar.
3. `validador.py` comprueba que no haya errores reales (inicial inválido,
   terminales sin declarar, etc.). Las variables inútiles o inalcanzables no se
   consideran errores.
4. `main.py` o `app.py` llama al proceso completo.
5. `transformaciones.py` elimina inútiles, inalcanzables, nulas y unitarias.
6. Luego adapta terminales y divide producciones largas para obtener FNC.
7. `historial.py` registra el antes, el después y las diferencias de cada etapa.
8. `validador.py` revisa que la gramática final cumpla las reglas de FNC.
9. `pruebas.py` confirma casos normales y casos especiales como ciclos, lenguaje
   vacío, `ε`, variables no declaradas, terminales repetidos y producciones
   largas.

## 6. Guion corto para la sustentación

> El proyecto recibe una gramática libre de contexto y la representa como
> `G=(V,T,P,S)`. Primero se valida la entrada: solo son errores los problemas
> reales, como un inicial fuera de `V` o un terminal sin declarar; las variables
> inútiles o inalcanzables no lo son, y una variable usada sin declarar se
> registra como implícita. Después se aplica una depuración en cuatro etapas: se
> eliminan las variables no generadoras, las inalcanzables, las producciones
> nulas y las unitarias. Cada algoritmo trabaja sobre una copia y devuelve una
> gramática nueva junto con un objeto `Paso`, lo que permite mostrar las
> producciones eliminadas y agregadas.
>
> Finalmente se realiza la conversión a Forma Normal de Chomsky. Los terminales
> que aparecen en cuerpos largos se reemplazan por variables auxiliares y las
> producciones con más de dos símbolos se dividen en producciones binarias.
> El proceso completo está coordinado por `ejecutar_proceso_completo` y el
> resultado se verifica con `validar_fnc`. Si el lenguaje es vacío, el proceso
> termina igual con una gramática sin producciones y lo informa. La interfaz de
> consola está en `main.py`, la interfaz web en `app.py` y las pruebas
> automáticas en `pruebas.py`.

## 7. Diferencia clave que conviene aclarar

La **depuración** busca quitar elementos que sobran o que no aportan al
lenguaje:

```text
no generadoras, inalcanzables, nulas y unitarias
```

La **FNC** no elimina simplemente lo que sobra; reorganiza las producciones
para que tengan las formas restringidas:

```text
A -> a
A -> B C
S -> ε   (solo bajo la condición permitida)
```
