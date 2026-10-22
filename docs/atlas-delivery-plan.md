# Atlas de componentes — entrega del 22 de octubre de 2026

Coordinación: `run_d4fd3704f129`. Base: `d61743a` (PR #47).

El pedido de Ángel exige corregir el sistema compartido y entregar un nuevo artefacto privado, multipágina, que permita explorar todos los componentes. Las capturas muestran defectos reales que sobrevivieron a la entrega anterior. No se considera resuelto por cambiar solamente el ejemplo.

## Criterios de aceptación

| Frente | Evidencia exigida antes de publicar |
| --- | --- |
| Referencia | Inventario de todas las rutas internas accesibles de cmrg.me, mediciones y comportamiento; exclusiones explícitas. No afirmar igualdad exacta si quedan diferencias. |
| Capas y lectura | Galerías, detalles abiertos, código largo y figuras no quedan debajo del índice; hit testing y capturas durante scroll, teclado, móvil y temas claros/oscuros. Mantener navegación y no ocultar overflow globalmente. |
| Tipografía y espacio | Anchos, tamaños, interlineados, separación de títulos y contenido, marcos y gutters contrastados contra mediciones. Licencias de fuentes respetadas; sustituciones documentadas. |
| Detalle editorial | Encabezados con fecha, progreso/tachado del índice, fades/sombras, callouts y reacciones; movimiento reducido y foco visible. |
| Código | Resaltado por lenguaje que respete temas, rangos resaltados/resto atenuado, etiquetas, copia exacta y números legibles de 1–1000. Bloques grandes sin bloqueo del lector. |
| Gráficos | Treemap/attention map y mejoras de visualizaciones con unidades, leyendas, formatos, acceso por teclado/táctil, alternativas tabulares y datos de ejemplo identificados. |
| Embeds | X, YouTube e Instagram con carga explícita, fallback enlazado, límites del proveedor y pruebas sin conexión; no scripts externos arbitrarios. |
| Footer | Configurable por documento/autor, redes opcionales y atribución de plataforma independiente; no imponer la identidad de Ángel a otros usuarios. |
| Comentarios | Dos cuentas distintas conservan autores correctos al publicar, responder, recargar, editar y exportar contexto. No reatribuir datos históricos sin evidencia ni filtrar email. |
| Atlas | Cada ID del registro tiene una demostración real y navegación a su página; cobertura comprobable, interacciones ejercitadas, carga progresiva de páginas y copia/descarga útiles. |
| Rendimiento | Medición reproducible de carga, scroll, render y tareas largas; no afirmar mejoras por intuición ni comparar mediciones incompatibles. |
| Entrega | Revisión independiente, pruebas del commit integrado, CI, despliegue comprobado, paquete firmado y artefacto privado publicado con enlace estable. |

## Propiedad inicial

- `margen-atlas-identidad`: autoría de comentarios, APIs/store/bridge y revisión. Task `task_75c14e6b2aad`, dispatch `ctx_1ef18e98e0a7`.
- `margen-atlas-referencia`: auditoría de referencia, solo documentación/evidencia. Task `task_87957df930f6`, dispatch `ctx_5c44e67d5df7`.
- `margen-atlas-datos`: auditoría de catálogo/gráficos/embeds, solo documentación/evidencia. Task `task_cd74624a920f`, dispatch `ctx_057cf51eacd9`.
- `margen-atlas-main`: coordinación, integración, revisión de aceptación, atlas final, publicación y despliegue.

Se asignarán las implementaciones posteriores según los hallazgos, con propiedad de archivos separada. Máximo inicial: dos escritores de producto simultáneos. Los checkouts originales y los worktrees de voz se preservan.

## Identidad del entregable

Nuevo documento: `margen-atlas-componentes-20261022`. Audiencia privada. La muestra anterior `margen-mejoras-visuales-cmrg-20261021` conserva su identidad y comentarios.

Capturas de cmrg.me solo como evidencia privada; no redistribuir sus fotografías ni fuentes propietarias. Los datos sintéticos se señalan como demostraciones.

## Estado de integración — 05:36 UTC

- Generador del atlas: `4394481`, diez páginas y cobertura de los 90 IDs actuales. CLI y contrato válidos; recorrido a 320/390/1440 sin desbordamiento horizontal. Prueba local de estrés de 1.000 líneas. Pendiente de incorporar las mejoras siguientes; aún no publicado.
- Identidad: fuente `294a697`, integrado como `7d2135e`. Harness de navegador: 18/26 antes, 26/26 después. Suite portal del autor: 197 OK. Root verificó `npm run build` y 25/25 tests de React/composer; el conteo 89/90 informado antes del build era un prerrequisito omitido. Revisión independiente `f515d56`: defecto original corregido; un P2 y tres P3 en distinción de agentes fuera del lector, etiquetas con controles, aviso de visibilidad y validación local. Corregir antes de desplegar.
- Auditoría visual: `7efc71c`, integrado como `deb3f61`. Las 16 rutas visitadas y medidas; alcance y exclusiones en `atlas-reference-audit.md`. El coordinador completó los 41 tramos pendientes hasta los pies a 1440/390; cobertura en `tail-coverage.json`. Inspección manual representativa, sin afirmar comparación de cada píxel.
- Auditoría de datos: `c69c2dc`, integrado como `3274687`. Corrección del coordinador: su comparación con `/now` no corresponde al treemap de aplicaciones de la portada; usar §3.10 de la auditoría visual. La simulación lazy es provisional, no una mejora implementada.
- Editorial: Task `task_cfe19fb4cad5`, Dispatch `ctx_ee82c996dde4`, worktree `margen-atlas-editorial`; propietario de CSS editorial, lector/capítulos, generador de metadatos/footer y sus tests.
- Gráficas: Task `task_b89d6825ae03`, Dispatch `ctx_510fc530d555`, worktree `margen-atlas-graficas`; propietario de runtimes de gráficos, nuevo núcleo/estilo dedicado y recetas. Wiring de generador/build reservado hasta integración con editorial.
- Revisión de identidad: Task `task_944a4410fdcb`, Dispatch `ctx_1720c891b6c2`, completada y worker liberado. Informe integrado como `f515d56`; pendiente subsanación y revisión del delta.
- Próximas tareas necesarias: resaltado por lenguaje, montaje diferido y recursos offline, embeds X/YouTube/Instagram, revisión integrada, despliegue/paquete y publicación privada. No confundir el cierre de una auditoría con haber implementado esas tareas.

Los tres workers de la primera fase y el revisor de identidad se liberaron tras entregar. Sus cuatro worktrees se retiraron después de integrar entregables, guardar bundles y conservar evidencia privada; archivo `~/.local/share/margen/worktree-archive/20261022-atlas-first-wave/`. Los worktrees activos cuelgan de `margen-atlas-main`. Se conservan los worktrees de voz y el checkout original.

Capacidad comprobada antes del tercer escritor: 12 CPU, carga 3.89/3.32/3.27, 55 % memoria libre, 87 GiB disponibles. Root asume solo la subsanación de identidad en main, sin pisar archivos editoriales ni de gráficas. El worker de embeds es de investigación, sin escritura de producto.

## Actualización — 06:02 UTC

- Identidad: subsanación `1cab2ed`, generados `51f5b9a`; 22 tests del cliente y cinco de identidad del servidor pasan. Falta revisión independiente de este delta y revisión integrada.
- Atlas offline: Chromium pasa los 128 checks. WebKit 26 encontró un desbordamiento de 22 px a 320 px y siete avisos de ResizeObserver. No son evidencia suficiente para atribuir el destello blanco observado por Ángel.
- Desbordamiento: el contenido interno del select de imagen anotada amplía el área desplazable en WebKit aunque su rectángulo externo quepa. `overflow:hidden` solo en ese control lo resuelve; asignado al writer editorial para incluirlo en las reglas que refrescan históricos.
- ResizeObserver: cuatro avisos corresponden al visor de prototipos al aparecer. Root difiere sus escrituras al siguiente frame y cancela el trabajo al destruirlo. `test_prototype_resize.py` falla con el código anterior en WebKit y pasa con el cambio en ambos motores; conserva orientación, ajuste y limpieza. Los otros avisos corresponden a barras al redibujar; asignados al writer de gráficas. Evidencia privada en `~/.local/share/margen-review/atlas-root-20261022/webkit-RO-diagnosis/`.
- Embeds: investigación `b31bb83`, integrada en `c3c4451`; el worker terminó y fue liberado. YouTube reproduce realmente en un diálogo montado por el portal, conservando el artefacto opaco. Ver `atlas-embed-compatibility.md`; aún falta implementación. La siguiente tarea sustituye la escritura de root por el writer de embeds, manteniendo tres propietarios de producto con archivos separados. Root queda en revisión/integración.
- No hay nuevos cambios desplegados ni atlas publicado todavía.

### Segunda convergencia — 06:12 UTC

UI integrada en `7b4e2db` y generados en `7e238af`; worker y worktree cerrados con bundle y evidencia preservados. Se aceptan capas/metadatos, pero sus diferencias deliberadas no satisfacen toda la fidelidad solicitada. Root conserva `editorial-reference.css`, `editorial-pieces.js`, recetas editoriales y atlas para completar el corte del índice, máscara progresiva, trazo irregular, títulos móviles y distribución del pie. Runtime `ctx_9abbeba78a6a` posee gramáticas, capítulos y wiring; embeds `ctx_ddf25c132218` posee piezas de medios y portal; gráficas conserva su propiedad. Capacidad para la corrección acotada adicional de root: 12 CPU, carga 4.00/4.06/3.83, sin nuevos procesos de agentes. Se escalonan las pruebas pesadas.

### Integración — 06:23 UTC

Root completó geometría del índice a partir de 1328 px, máscara ligada al artículo, tachado SVG por renglón, h2 móvil 28,5/38, pie en dos columnas y recorte específico del select en WebKit. Reacciones locales distinguen almacenamiento temporal en el iframe. Las 27 pruebas editoriales/de referencia pasan; sonometría visual adicional en Chromium/WebKit a 390/1440 sin errores, con evidencia privada `atlas-root-20261022/ui-fidelity/`. Las recetas de fecha y reacciones quedan listas, pendientes de alta conjunta en el registro.

Gráficas entregó `ffa532f..1792dd5`; worker liberado. Fuente pendiente de integración, wiring asignado al worker runtime. No aceptar los clics programáticos como verificación de los botones de exportación: repetir interacción real tras integrar capas. Coste y límites en `REPORT-CHARTS-ATLAS.md`.

### Revisión integrada — 06:37 UTC

- Gráficas: fuentes integradas hasta `c55385d`; las tres recetas nuevas más fecha/reacciones y medios dejan 98 componentes (los dos layouts se cuentan aparte). Prueba acotada de exportaciones con clic real en Chromium/WebKit: seis descargas por motor, cero errores; las referencias SVG siguen siendo fragmentos locales. La suite CI exige ahora clic real.
- Medios: checkpoint `b4064a4`, cierre `a11aa1d`. Reproducción real local HTTPS con dos cuentas en Chromium/WebKit; límites de proveedores y reel no ensayado en `REPORT-EMBEDS-ATLAS.md`. Worker liberado, bundle validado y worktree retirado.
- Identidad: revisor independiente `ctx_86f5da08fa32` encontró edición ajena autorizada por la API. `b6bef04` limita edición al autor de la cuenta; `3b1ae3c` alinea proyecciones de históricos en los dos lectores. Los eventos anteriores se conservan. Catorce pruebas del servidor, seis del fallback y contrato del store pasan; queda revisión independiente del delta.
- Código: fuente `37a88b1`, generado `357b8bc`; Prism 1.30.0 con procedencia/licencia y generación Python sin red, montaje diferido de bloques. Runtime `ctx_9abbeba78a6a` termina wiring conjunto, Three diferido y refresco de módulos históricos.
- Revisión UI/gráficas/runtime: `ctx_d0066062ca25`, task `task_6f01971f0bb2`, worktree `margen-atlas-review-ui-runtime`. Revisión identidad/medios: task `task_98e8270420fb`, worktree `margen-atlas-review-identidad-medios`. Ambos son checkers de contexto nuevo y no escriben producto.
- Nueva secuencia preparada: `2026.10.22-library.1` / `2026102201`. Todavía no firmada, desplegada ni publicada. Producción continúa en PR #47 / `d61743a`; el PR #41 de voz queda separado como borrador y se preservan sus worktrees.


### Verificación integrada — 06:55 UTC

- PR #48 abierto como borrador; fuente integrada `7c59dc6`, corrección Windows `2e95fd9`.
- Atlas: 98 recetas, diez páginas, 406 comprobaciones pasan en cada motor (Chromium y WebKit), incluyendo cinco anchos, tres familias y ambos modos. Flujo editorial: cinco tests pasan; no se debilitaron sus umbrales. Capturas privadas representativas en `atlas-root-20261022/final-visual/`.
- Portal: 209 pruebas; React/componentes: 141 pruebas, typecheck y build pasan. El fallo Windows era conversión CRLF de la licencia de Prism: reproducción local con autocrlf, preservación de bytes con gitattributes y CI Windows verde tras `2e95fd9`.
- Identidad: `280ab18` oculta edición ajena, muestra última edición humana/agente y conserva autor original, tanto en lector como export. Las seis regresiones independientes D1/D4/D6 pasan; navegador real con cuentas sintéticas confirma autoría, respuestas y recarga en ambos motores. Permanecen observaciones de severidad baja sobre nombres de cuenta coincidentes y etiquetas libres; las insignias de invitado/agente sí se distinguen.
- Revisor de identidad/medios entregó `546a844`, integrado como `eb87698`; liberado y worktree retirado con bundle verificado. D2 de medios se asignó a `ctx_77e8d86474a0`: exigir acción en un control del portal antes de abrir URL/proveedor, conservando el aislamiento. Revisión independiente final sigue en curso.
- Respaldo previo con restauración aislada: `/backups/snapshot-20261022-065232-cac2c4`. Todavía no hay despliegue nuevo, firma ni publicación del atlas.
