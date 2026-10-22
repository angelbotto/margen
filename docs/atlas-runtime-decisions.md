# Decisiones pendientes de implementación para el atlas

Coordinador, 22 de octubre de 2026. Este documento distingue investigación de funcionalidad implementada. Aún no describe una versión desplegada.

## Código con colores del tema

La referencia usa Shiki. Su [documentación de colores](https://shiki.style/guide/theme-colors) admite variables CSS como colores de tokens, de modo que no hace falta fijar una paleta oscura en el HTML. Los [bundles](https://shiki.style/guide/bundles) completos tienen un coste innecesario para un documento portátil: la documentación recomienda seleccionar núcleo, lenguajes y motor. [Prism](https://prismjs.com/) ofrece gramáticas por lenguaje y clases semánticas; documenta límites de su análisis por expresiones regulares y de la conservación de marcado previo.

La elección debe comparar tamaño comprimido, tiempo de tokenización y precisión sobre los ejemplos reales. No basta un mapa de palabras clave compartido entre lenguajes. El consumidor de un HTML y el CLI Python deben seguir funcionando sin Node ni red; Node puede generar un bundle reproducible durante el desarrollo. Si se incorpora una dependencia, fijar versión, guardar licencia/procedencia y no usar un CDN en cada artefacto.

Conservar exactamente el texto copiado, tabs, saltos, entidades, `mark`, rangos y números de 1–1000. Tokens como comentarios, strings, funciones, etiquetas y propiedades deben tomar variables del tema, sin retokenizar al alternar claro/oscuro. Lenguaje desconocido debe conservar texto legible y nombre original. Un bloque muy grande debe seguir siendo copiable si se pospone o limita el coloreado.

Prueba aislada de candidato: Prism 1.30.0, núcleo y 21 gramáticas: 54.392 bytes, 19.361 bytes gzip; tokenizar mil líneas JavaScript en Node tomó 12,5 ms en la primera pasada y 4–5,6 ms en cuatro pasadas calientes. Se descargó el tarball oficial con scripts desactivados; integridad y ensayo en `/tmp/margen-syntax-evaluation/`. No incluye DOM ni carga del navegador y no es aún una mejora integrada.

## Páginas y coste inicial

El atlas base tiene diez páginas, 90 recetas y unas 35.000 etiquetas tras inicializar. `chapters.js` cambia `hidden`, pero los runtimes ya recorrieron todo el documento. El contenido de ejemplo también contiene artículos anidados: una sustitución con regex hasta el primer `</article>` no puede convertirlo correctamente a carga diferida.

Preferir un ciclo explícito de montaje por página y detalles visibles, o templates construidos a partir del árbol validado. Deben sobrevivir enlaces a IDs de una página nunca visitada, historial, foco, comentarios anclados, búsqueda, impresión y lectura sin JavaScript. No separar una variante del atlas que arregle solo la demostración. Todo ajuste debe funcionar en documentos generados por el contrato compartido.

La sonda `scripts/check_component_atlas.py` pasa 128 comprobaciones contra la base con solicitudes externas bloqueadas. Comprueba navegación por cada ID, temas, anchos, copia exacta de mil líneas y contenido sin JavaScript. No demuestra por sí sola que todos los gráficos se hayan dibujado ni que la capa de índice sea correcta; esas pruebas son de cada frente y de la integración final. La simulación lazy de la auditoría de datos sigue siendo provisional y no es evidencia de mejora implementada.

## Proveedores de medios

La referencia representa el tweet como una tarjeta HTML propia, no como un script de X. Se puede ofrecer esa pieza portátil con autor, fecha, contenido y fuente explícitos, sin fingir verificación ni métricas. Un ejemplo inventado debe estar rotulado como ejemplo. La carga de un proveedor vivo es una función adicional y debe requerir una acción del lector.

YouTube documenta el [iframe y sus parámetros](https://developers.google.com/youtube/player_parameters), con un tamaño mínimo de 200×200. Su [modo de privacidad mejorada](https://support.google.com/youtube/answer/171780?hl=en) usa `www.youtube-nocookie.com`; no equivale a cero comunicaciones con Google. La misma documentación requiere un referrer HTTP para evitar el error 153. En Margen, `portal/app.py` establece `Referrer-Policy: no-referrer` y un sandbox opaco; estos requisitos deben comprobarse con el reproductor real. El iframe específico puede transmitir solo el origen, nunca el ID o la URL privada del artefacto, si el navegador y el proveedor lo admiten. El enlace para abrir el origen debe permanecer disponible.

La [documentación oficial actual de Instagram oEmbed](https://developers.facebook.com/documentation/instagram-platform/oembed), leída en Chromium el 22 de octubre (HTTP 200; actualización indicada 15 de mayo de 2026), muestra una consulta a `graph.facebook.com/v26.0/instagram_oembed?url=…` y el procesamiento de `embed.js`. Admite publicaciones públicas y reels; excluye cuentas privadas, inactivas, restringidas por edad, con inserciones desactivadas, historias y Shadow DOM. No asumir requisitos históricos de tokens sin verificarlos. El fetch textual de la herramienta web devolvió 429, por eso se consultó la página oficial renderizada.

Las respuestas de oEmbed y cualquier texto remoto son datos, no código de confianza. No ejecutar HTML/scripts arbitrarios del proveedor dentro del DOM de la cuenta. No almacenar sus metadatos para analítica. Probar el comportamiento del iframe permitido y conservar una tarjeta/enlace útil cuando no haya conexión o el proveedor deniegue el embed. Añadir dominios exactos a `frame-src` solo donde se necesiten; mantener `connect-src 'none'`, separación de origen y ausencia de scripts de proveedor en el documento de la cuenta. Cualquier cambio de sandbox necesita revisión de seguridad y una prueba real de lectura entre cuentas, además de la prueba visual.

## Hallazgos de identidad que deben cerrarse

La revisión independiente `REVIEW-IDENTITY-INDEPENDENT.md` confirma la corrección del pin/composer. Quedan diferencias de confianza de identidad fuera del lector: usar los campos registrados `agent` y `verified`, una marca visual separada y campos inequívocos en la exportación; no inferir tipo de autor por el formato de su nombre. Normalizar controles y saltos solo al presentar identidades y al crear etiquetas nuevas, sin reescribir autores históricos. Avisar al crear un token que su etiqueta aparece en comentarios y sobrevive a su revocación. Mantener permisos existentes.
