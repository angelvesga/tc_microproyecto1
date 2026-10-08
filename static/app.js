/* =========================================================
   GLC a Forma Normal de Chomsky — lógica de la interfaz
   Toda la conversión la hace el servidor (Python); aquí solo
   se muestran los resultados. No se usa innerHTML con datos
   del usuario: todo se construye con nodos de texto.
   ========================================================= */
"use strict";

const estado = {
  datos: null,     // respuesta de /api/procesar
  actual: 0,       // 0 = gramática original, 1..6 = etapas, 7 = resultado
  modo: "paso",    // "paso" | "todo"
};

const $ = (sel) => document.querySelector(sel);

/** Crea un elemento: h("div", {class: "x"}, "texto", otroNodo) */
function h(tag, attrs, ...hijos) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === null || v === undefined || v === false) continue;
    if (k === "class") el.className = v;
    else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else el.setAttribute(k, v === true ? "" : v);
  }
  for (const hijo of hijos.flat(Infinity)) {
    if (hijo === null || hijo === undefined || hijo === false) continue;
    el.append(hijo instanceof Node ? hijo : document.createTextNode(String(hijo)));
  }
  return el;
}

const MAX_CARACTERES = 5000;   // mismo límite que app.py

const SUBINDICES = "₀₁₂₃₄₅₆₇₈₉";
const sub = (n) => String(n).split("").map((d) => SUBINDICES[+d]).join("");

/* ---------------------------------------------------------
   Ejemplos y envío
   --------------------------------------------------------- */
async function cargarEjemplos() {
  const select = $("#ejemplos");
  try {
    const lista = await (await fetch("/api/ejemplos")).json();
    select.append(h("option", { value: "" }, "— Elige un ejemplo —"));
    lista.forEach((ej, i) => {
      const nombre = ej.nombre.replace(/\.txt$/, "").replace(/^ejemplo(\d+)_/, "$1. ").replace(/_/g, " ");
      select.append(h("option", { value: String(i), title: ej.descripcion }, nombre));
    });
    select.addEventListener("change", () => {
      if (select.value === "") return;
      $("#texto").value = lista[+select.value].texto;
      convertir();
    });
    // Carga inicial: el primer ejemplo ya procesado, para que la página no empiece vacía
    select.value = "0";
    $("#texto").value = lista[0].texto;
    convertir({ desplazar: false });
  } catch (e) {
    select.append(h("option", { value: "" }, "No se pudieron cargar los ejemplos"));
  }
}

/** Lee un .txt en el navegador, lo pone en el textarea y convierte (igual que un ejemplo). */
function cargarArchivo(input) {
  const archivo = input.files && input.files[0];
  input.value = "";                       // permite volver a cargar el mismo archivo
  if (!archivo) return;
  if (!/\.txt$/i.test(archivo.name)) {
    mostrarErrores(["Error: solo se admiten archivos .txt."]);
    return;
  }
  if (archivo.size > MAX_CARACTERES * 4) {  // un carácter UTF-8 ocupa hasta 4 bytes
    mostrarErrores([`Error: el archivo supera el máximo de ${MAX_CARACTERES} caracteres.`]);
    return;
  }
  const lector = new FileReader();
  lector.onload = () => {
    const texto = String(lector.result);
    if (texto.length > MAX_CARACTERES) {
      mostrarErrores([`Error: el archivo supera el máximo de ${MAX_CARACTERES} caracteres.`]);
      return;
    }
    $("#texto").value = texto;
    $("#ejemplos").value = "";
    convertir();
  };
  lector.onerror = () => mostrarErrores(["Error: no se pudo leer el archivo."]);
  lector.readAsText(archivo, "UTF-8");
}

async function convertir(opciones = {}) {
  const boton = $("#btn-convertir");
  boton.disabled = true;
  boton.textContent = "Procesando…";
  try {
    const resp = await fetch("/api/procesar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ texto: $("#texto").value }),
    });
    const datos = await resp.json();
    mostrarErrores(datos.ok ? [] : datos.errores);
    if (!datos.ok) {
      estado.datos = null;
      $("#proceso").hidden = true;
      return;
    }
    estado.datos = datos;
    estado.actual = 0;
    $("#proceso").hidden = false;
    render();
    if (opciones.desplazar !== false) $("#proceso").scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (e) {
    mostrarErrores(["No fue posible comunicarse con el servidor. Intenta de nuevo en unos segundos."]);
  } finally {
    boton.disabled = false;
    boton.textContent = "Validar y convertir";
  }
}

function mostrarErrores(errores) {
  const caja = $("#errores");
  caja.replaceChildren();
  if (!errores || errores.length === 0) { caja.hidden = true; return; }
  caja.append(
    h("h3", {}, errores.length === 1 ? "La gramática tiene 1 error" : `La gramática tiene ${errores.length} errores`),
    h("p", { style: "margin:0 0 6px" }, "Corrígelos para poder iniciar la conversión:"),
    h("ul", {}, errores.map((e) => h("li", {}, e.replace(/^Error:\s*/, "")))),
  );
  caja.hidden = false;
}

/* ---------------------------------------------------------
   Navegación
   --------------------------------------------------------- */
function totalVistas() { return estado.datos.pasos.length + 2; } // original + etapas + final

function ir(indice) {
  const max = totalVistas() - 1;
  estado.actual = Math.max(0, Math.min(max, indice));
  render();
}

function render() {
  renderCadena();
  const vista = $("#vista");
  vista.replaceChildren();
  const nav = $("#navegacion");
  if (estado.modo === "todo") {
    for (let i = 0; i < totalVistas(); i++) vista.append(vistaPorIndice(i));
    nav.hidden = true;
  } else {
    vista.append(vistaPorIndice(estado.actual));
    nav.hidden = false;
    $("#btn-anterior").disabled = estado.actual === 0;
    const ultimo = estado.actual === totalVistas() - 1;
    $("#btn-siguiente").disabled = ultimo;
    $("#btn-siguiente").textContent = estado.actual === totalVistas() - 2 ? "Ver resultado →" : "Siguiente →";
  }
}

function vistaPorIndice(i) {
  const n = estado.datos.pasos.length;
  if (i === 0) return vistaOriginal();
  if (i <= n) return vistaEtapa(estado.datos.pasos[i - 1]);
  return vistaFinal();
}

function renderCadena() {
  const cadena = $("#cadena");
  cadena.replaceChildren();
  const { pasos } = estado.datos;
  const nodos = [
    { marca: "G" + sub(0), texto: "Original" },
    ...pasos.map((p) => ({ marca: String(p.numero), texto: p.corto })),
    { marca: "FNC ✓", texto: "Resultado", final: true },
  ];
  nodos.forEach((nodo, i) => {
    if (i > 0) cadena.append(h("span", { class: "cadena__flecha", "aria-hidden": "true" }, "⇒"));
    const clases = ["nodo"];
    if (nodo.final) clases.push("final");
    if (estado.modo === "paso") {
      if (i < estado.actual) clases.push("hecho");
      if (i === estado.actual) clases.push("actual");
    } else clases.push("hecho");
    cadena.append(h("button", {
      type: "button", class: clases.join(" "),
      "aria-current": estado.modo === "paso" && i === estado.actual ? "step" : null,
      onclick: () => {
        if (estado.modo === "todo") {
          const destino = document.getElementById("vista-" + i);
          if (destino) destino.scrollIntoView({ behavior: "smooth", block: "start" });
        } else ir(i);
      },
    },
      h("span", { class: "nodo__marca" }, nodo.marca),
      h("span", { class: "nodo__texto" }, nodo.texto)));
  });
  const actual = cadena.querySelector(".actual");
  if (actual) actual.scrollIntoView({ block: "nearest", inline: "center" });
}

/* ---------------------------------------------------------
   Vistas
   --------------------------------------------------------- */
function encabezado(meta, titulo) {
  return h("div", { class: "etapa__encabezado" },
    h("div", { class: "etapa__meta" }, meta),
    h("h3", { class: "etapa__titulo" }, titulo));
}

function vistaOriginal() {
  const g = estado.datos.original;
  return h("article", { class: "etapa", id: "vista-0" },
    encabezado("Punto de partida · RF01–RF06", "Gramática original " + "G" + sub(0)),
    h("div", { class: "aviso aviso--ok" },
      h("span", { class: "aviso__icono", "aria-hidden": "true" }, "✓"),
      h("div", {},
        h("h4", {}, "La gramática es válida"),
        h("p", {}, `Tiene ${g.variables.length} variable${g.variables.length === 1 ? "" : "s"}, ${g.terminales.length} terminal${g.terminales.length === 1 ? "" : "es"} y ${g.total} producci${g.total === 1 ? "ón" : "ones"}. ` +
          `A continuación se aplican ${estado.datos.pasos.length} transformaciones en orden; cada una produce una gramática equivalente.`))),
    h("div", { class: "comparacion", style: "grid-template-columns: minmax(0,1fr)" },
      bloqueGramatica(g, "G" + sub(0), null)));
}

function vistaEtapa(paso) {
  const n = estado.datos.pasos.length;
  const antesNombre = "G" + sub(paso.numero - 1);
  const despuesNombre = "G" + sub(paso.numero);
  const sinCambios = paso.eliminadas.length === 0 && paso.agregadas.length === 0;

  return h("article", { class: "etapa", id: "vista-" + paso.numero },
    encabezado(`Paso ${paso.numero} de ${n} · ${paso.rf}`, paso.titulo),

    h("div", { class: "bloques" },
      h("section", { class: "bloque bloque--explica" },
        h("h4", {}, "¿Qué hace esta etapa?"),
        h("p", {}, paso.que_hace),
        h("p", { class: "detalle" }, paso.detalle)),
      h("section", { class: "bloque bloque--encontro" },
        h("h4", {}, "¿Qué encontró?"),
        paso.identificados.map(hallazgo))),

    h("div", { class: "cambios" },
      h("h4", {}, `¿Qué cambió? ${antesNombre} ⇒ ${despuesNombre}`),
      h("div", { class: "contadores" },
        sinCambios
          ? h("span", { class: "contador contador--igual" }, "Sin cambios en esta etapa")
          : [
            h("span", { class: "contador contador--menos" }, `− ${paso.eliminadas.length} eliminada${paso.eliminadas.length === 1 ? "" : "s"}`),
            h("span", { class: "contador contador--mas" }, `+ ${paso.agregadas.length} agregada${paso.agregadas.length === 1 ? "" : "s"}`),
          ])),

    h("div", { class: "comparacion" },
      bloqueGramatica(paso.antes, "Antes · " + antesNombre, paso.despues, "antes"),
      h("div", { class: "comparacion__flecha", "aria-hidden": "true" }, "⇒"),
      bloqueGramatica(paso.despues, "Después · " + despuesNombre, paso.antes, "despues")),

    h("div", { class: "leyenda" },
      h("span", {}, h("span", { class: "cuerpo cuerpo--eliminada" }, "A B"), "producción eliminada"),
      h("span", {}, h("span", { class: "cuerpo cuerpo--agregada" }, "A B"), "producción agregada"),
      h("span", {}, h("span", { class: "sim-nuevo" }, "X1"), "variable nueva"),
      h("span", {}, h("span", { class: "sim-quitado" }, "D"), "variable o terminal eliminado")));
}

function vistaFinal() {
  const d = estado.datos;
  const g = d.final;
  const i = d.pasos.length + 1;
  const aviso = d.fnc.valida
    ? h("div", { class: "aviso aviso--ok" },
        h("span", { class: "aviso__icono", "aria-hidden": "true" }, "✓"),
        h("div", {},
          h("h4", {}, "La gramática está en Forma Normal de Chomsky"),
          h("p", {}, g.total === 0
            ? "La gramática no tiene producciones, así que ninguna viola la forma A → BC o A → a (validación automática, RNF12)."
            : (g.total === 1 ? "La producción tiene" : `Las ${g.total} producciones tienen`) + " la forma A → BC o A → a (validación automática, RNF12).")))
    : h("div", { class: "aviso aviso--error" },
        h("span", { class: "aviso__icono", "aria-hidden": "true" }, "✕"),
        h("div", {},
          h("h4", {}, "La gramática no cumple la FNC"),
          h("ul", {}, d.fnc.violaciones.map((v) => h("li", {}, v)))));

  const avisoVacio = d.lenguaje_vacio
    ? h("div", { class: "aviso aviso--atencion" },
        h("span", { class: "aviso__icono", "aria-hidden": "true" }, "!"),
        h("div", {},
          h("h4", {}, "El lenguaje de esta gramática es vacío"),
          h("p", {}, "El símbolo inicial no genera ninguna cadena de terminales, así que la gramática no genera ninguna palabra.")))
    : null;

  const filas = d.fnc.producciones.map((p) =>
    h("tr", {},
      h("td", {}, p.texto),
      h("td", {}, p.forma),
      h("td", { class: p.ok ? "ok" : "mal", "aria-label": p.ok ? "cumple" : "no cumple" }, p.ok ? "✓" : "✕")));

  return h("article", { class: "etapa", id: "vista-" + i },
    encabezado("Resultado · RF19, RNF12", "Gramática en Forma Normal de Chomsky"),
    aviso, avisoVacio,
    h("div", { class: "final" },
      bloqueGramatica(g, "Gramática final", d.original, "despues"),
      h("div", { class: "verificacion" },
        h("div", { class: "verificacion__scroll" },
          h("table", {},
            h("thead", {}, h("tr", {}, h("th", {}, "Producción"), h("th", {}, "Forma"), h("th", {}, "FNC"))),
            h("tbody", {}, filas))))),
    h("div", { class: "acciones-final" },
      h("button", { type: "button", class: "boton boton--primario", onclick: descargarHistorial }, "Descargar historial (.txt)"),
      h("button", { type: "button", class: "boton", onclick: copiarFinal }, "Copiar gramática final"),
      h("button", { type: "button", class: "boton", onclick: () => { cambiarModo("paso"); ir(0); } }, "Repasar desde el inicio")));
}

/* ---------------------------------------------------------
   Componentes
   --------------------------------------------------------- */
/** Una línea de "elementos identificados": "Etiqueta: { A, B }" → etiqueta + chips */
function hallazgo(linea) {
  const m = linea.match(/^([^:]{1,40}):\s(.+)$/);
  if (!m) return h("p", { class: "hallazgo" }, "• " + linea);
  const [, etiqueta, valor] = m;
  let contenido;
  if (valor === "∅") {
    contenido = h("span", { class: "chips" }, h("span", { class: "chip chip--vacio" }, "ninguno (∅)"));
  } else if (/^\{.*\}$/.test(valor)) {
    const interior = valor.slice(1, -1).trim();
    const elementos = interior ? interior.split(/,\s(?![^()]*\))/) : [];
    contenido = h("span", { class: "chips" },
      elementos.length ? elementos.map((e) => h("span", { class: "chip" }, e.trim()))
                       : h("span", { class: "chip chip--vacio" }, "ninguno (∅)"));
  } else if (/→/.test(valor) && /,\s/.test(valor)) {
    contenido = h("span", { class: "chips" }, valor.split(/,\s/).map((e) => h("span", { class: "chip" }, e)));
  } else {
    contenido = h("span", {}, valor);
  }
  return h("div", { class: "hallazgo" }, h("span", { class: "hallazgo__etiqueta" }, etiqueta + ":"), contenido);
}

/** Dibuja una gramática; "otra" sirve para marcar símbolos nuevos o quitados */
function bloqueGramatica(g, titulo, otra, lado) {
  const marcar = (lista, otraLista) => {
    const partes = [];
    lista.forEach((s, i) => {
      if (i > 0) partes.push(", ");
      let clase = null;
      if (otra && lado === "despues" && !otraLista.includes(s)) clase = "sim-nuevo";
      if (otra && lado === "antes" && !otraLista.includes(s)) clase = "sim-quitado";
      partes.push(clase ? h("span", { class: clase }, s) : s);
    });
    return partes;
  };
  const conjuntos = h("div", { class: "conjuntos" },
    h("div", {}, "V = { ", marcar(g.variables, otra ? otra.variables : []), " }"),
    h("div", {}, "T = { ", marcar(g.terminales, otra ? otra.terminales : []), " }"),
    h("div", {}, "S = ", g.inicial));

  const producciones = g.producciones.length
    ? g.producciones.map((p) =>
        h("div", { class: "prod" },
          h("span", { class: "prod__cabeza" }, p.cabeza),
          h("span", { class: "prod__flecha" }, "→"),
          h("span", { class: "prod__cuerpos" },
            p.cuerpos.map((c, i) => [
              i > 0 ? h("span", { class: "barra-alt", "aria-hidden": "true" }, "|") : null,
              h("span", {
                class: "cuerpo" + (c.estado !== "normal" ? " cuerpo--" + c.estado : ""),
                title: c.estado === "eliminada" ? "Producción eliminada" : c.estado === "agregada" ? "Producción agregada" : null,
              }, c.texto),
            ]))))
    : h("div", { class: "vacia" }, "(sin producciones)");

  return h("div", { class: "gramatica" },
    h("div", { class: "gramatica__titulo" }, h("span", {}, titulo), h("span", {}, `${g.total} ${g.total === 1 ? "producción" : "producciones"}`)),
    conjuntos, producciones);
}

/* ---------------------------------------------------------
   Acciones
   --------------------------------------------------------- */
function descargarHistorial() {
  const blob = new Blob([estado.datos.historial], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = h("a", { href: url, download: "historial_fnc.txt" });
  document.body.append(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

async function copiarFinal(ev) {
  const g = estado.datos.final;
  const texto = [
    "V: " + g.variables.join(" "),
    "T: " + g.terminales.join(" "),
    "S: " + g.inicial,
    "P:",
    ...g.producciones.map((p) => `${p.cabeza} -> ${p.cuerpos.map((c) => c.texto).join(" | ")}`),
  ].join("\n");
  try {
    await navigator.clipboard.writeText(texto);
    ev.target.textContent = "¡Copiada!";
  } catch (e) {
    ev.target.textContent = "No se pudo copiar";
  }
  setTimeout(() => { ev.target.textContent = "Copiar gramática final"; }, 1800);
}

function cambiarModo(modo) {
  estado.modo = modo;
  document.querySelectorAll(".modo__op").forEach((b) => {
    const activo = b.dataset.modo === modo;
    b.classList.toggle("activo", activo);
    b.setAttribute("aria-pressed", String(activo));
  });
  if (estado.datos) render();
}

/* ---------------------------------------------------------
   Eventos
   --------------------------------------------------------- */
document.addEventListener("DOMContentLoaded", () => {
  $("#btn-convertir").addEventListener("click", () => convertir());
  $("#btn-archivo").addEventListener("click", () => $("#archivo").click());
  $("#archivo").addEventListener("change", (e) => cargarArchivo(e.target));
  $("#texto").addEventListener("keydown", (e) => {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) { e.preventDefault(); convertir(); }
  });
  $("#btn-anterior").addEventListener("click", () => ir(estado.actual - 1));
  $("#btn-siguiente").addEventListener("click", () => ir(estado.actual + 1));
  document.querySelectorAll(".modo__op").forEach((b) => b.addEventListener("click", () => cambiarModo(b.dataset.modo)));
  document.addEventListener("keydown", (e) => {
    if (!estado.datos || estado.modo !== "paso") return;
    const etiqueta = document.activeElement && document.activeElement.tagName;
    if (etiqueta === "TEXTAREA" || etiqueta === "SELECT" || etiqueta === "INPUT") return;
    if (e.key === "ArrowRight") ir(estado.actual + 1);
    if (e.key === "ArrowLeft") ir(estado.actual - 1);
  });
  cargarEjemplos();
});
