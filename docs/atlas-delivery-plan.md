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
