# Referencias para datos legibles

Consulta de documentación primaria: 22 de octubre de 2026. Este contraste complementa la auditoría visual de cmrg.me; no es una auditoría exhaustiva de todos los productos.

| Referencia | Lo observado | Aplicación en Margen |
| --- | --- | --- |
| [Observable Plot: escalas](https://observablehq.github.io/plot/features/scales) | Dominio y rango separados de las marcas; márgenes y separación de ejes. | Núcleo común de escalas y formato, dominio explícito y texto a tamaño real. |
| [Observable Plot: accesibilidad](https://observablehq.github.io/plot/features/accessibility) | Etiquetas y descripciones del gráfico y de las marcas; las decoraciones pueden quedar fuera del árbol accesible. | Descripción de cada punto, navegación con flechas y tabla fuente disponible. |
| [Tremor: líneas](https://www.tremor.so/docs/visualizations/line-chart) | Leyenda interactiva, selección de series, separación entre ticks y controles para valores ausentes. | Leyendas que destacan una serie, etiquetas sin solapamiento y valores completos al enfocar. |
| [Tremor: barras](https://www.tremor.so/docs/visualizations/bar-chart) | Formato numérico compartido entre eje y detalle, diseño adaptado a escritorio y móvil. | Formato por idioma/unidad; el gráfico cambia su geometría y conserva el tamaño del texto. |
| [Evidence: barras](https://docs.evidence.dev/components/bar_chart) | Barras apiladas y anotaciones de referencia integrables en informes. | Nueva receta de columnas agrupadas/apiladas. Meta y antes/después tienen recetas propias. |

Decisión: conservar HTML con tablas fuente y SVG generado localmente. Las referencias orientan el comportamiento, sin incorporar el stack React/Recharts ni una conexión a datos de esos productos en cada archivo portátil. Los datos sintéticos se identifican y la copia/exportación conserva la fuente. Los informes siguen siendo legibles sin JavaScript.

No convertir cada gráfico en una tarjeta de dashboard. El artículo aporta título, explicación y fuente; la figura usa espacio suficiente para datos, rótulos y controles. Los detalles aparecen al interactuar, sin imponer todas las cifras encima de las marcas. El mapa de atención conserva el tratamiento editorial de cmrg.me.

La nueva implementación y sus límites medidos están en [REPORT-CHARTS-ATLAS.md](../REPORT-CHARTS-ATLAS.md). Esta comparación no demuestra rendimiento ni accesibilidad por sí sola: esas propiedades se verifican con los tests de la entrega.
