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

## Estado de integración — 05:25 UTC

- Generador del atlas: `4394481`, diez páginas y cobertura de los 90 IDs actuales. CLI y contrato válidos; recorrido a 320/390/1440 sin desbordamiento horizontal. Prueba local de estrés de 1.000 líneas. Pendiente de incorporar las mejoras siguientes; aún no publicado.
- Identidad: fuente `294a697`, integrado como `7d2135e`. Harness de navegador: 18/26 antes, 26/26 después. Suite portal del autor: 197 OK. Root verificó `npm run build` y 25/25 tests de React/composer; el conteo 89/90 informado antes del build era un prerrequisito omitido. Revisión independiente en curso, sin despliegue aún.
- Auditoría visual: `7efc71c`, integrado como `deb3f61`. Las 16 rutas visitadas y medidas; alcance y exclusiones en `atlas-reference-audit.md`. Capturas largas limitadas a ocho tramos por ruta; no afirmar inspección visual completa de todos sus finales.
- Auditoría de datos: `c69c2dc`, integrado como `3274687`. Corrección del coordinador: su comparación con `/now` no corresponde al treemap de aplicaciones de la portada; usar §3.10 de la auditoría visual. La simulación lazy es provisional, no una mejora implementada.
- Editorial: Task `task_cfe19fb4cad5`, Dispatch `ctx_ee82c996dde4`, worktree `margen-atlas-editorial`; propietario de CSS editorial, lector/capítulos, generador de metadatos/footer y sus tests.
- Gráficas: Task `task_b89d6825ae03`, Dispatch `ctx_510fc530d555`, worktree `margen-atlas-graficas`; propietario de runtimes de gráficos, nuevo núcleo/estilo dedicado y recetas. Wiring de generador/build reservado hasta integración con editorial.
- Revisión de identidad: Task `task_944a4410fdcb`, Dispatch `ctx_1720c891b6c2`, worktree `margen-atlas-review-identidad`; solo lectura de producto, contexto independiente.
- Próximas tareas necesarias: resaltado por lenguaje, montaje diferido y recursos offline, embeds X/YouTube/Instagram, revisión integrada, despliegue/paquete y publicación privada. No confundir el cierre de una auditoría con haber implementado esas tareas.

Los tres workers de la primera fase se liberaron tras entregar. Los worktrees activos cuelgan de `margen-atlas-main`. Se conservan los worktrees de voz y el checkout original.
