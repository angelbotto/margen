## Editorial footer

<!-- nota:ejemplo pie-editorial -->

```html
{{EXAMPLE}}
```

**Uso:** cierra con la identidad y los enlaces de quien escribe. Las dos columnas se apilan en móvil; las descripciones de enlaces se difuminan solo con puntero fino y se revelan también con foco de teclado. La atribución a Margen queda separada.

El generador ofrece la misma pieza mediante `footer: {author, note, links: [{label, href, detail}], platform}`. No añadas un segundo pie manual cuando uses esa opción. Se aceptan HTTPS sin credenciales y correo `mailto:`. No se inventan redes, licencias, estadísticas ni autoría: los enlaces de esta muestra usan example.com como marcadores para sustituir. El pie sigue al contenido y conserva la identidad del documento.

Es opcional: omite `footer` para no añadir ningún pie. `platform` vale `false` por defecto. En una presentación, compón una diapositiva de cierre si la necesitas; el generador no inserta un pie de artículo.
