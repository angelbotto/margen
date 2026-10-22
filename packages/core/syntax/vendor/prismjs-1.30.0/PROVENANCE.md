# Prism 1.30.0 — procedencia

Archivos sin modificar del paquete oficial `prismjs@1.30.0` de npm, obtenido el 22 de octubre de 2026
con `npm pack prismjs@1.30.0 --ignore-scripts` (no se ejecutó código del paquete). Integridad del
tarball según el registro: `sha512-DEvV2ZF2r2/63V+tK8hQvrR2ZGn10srHbXviTlcv7Kpzw8jWiNTqbVgjO3IY8RxrrOUF8VPMQQFysYYYv0YZxw==`
(SHA-256 `ac16a9106a28c53b6a6313993c816a3a02525fdfefd7614fc1703df915a9fc11`). Licencia MIT, © 2012 Lea Verou;
aviso completo en `licenses/prismjs-MIT.txt` (bytes idénticos al `LICENSE` del paquete; `lock.json` fija su SHA-256).

Solo se guardan el núcleo y las gramáticas minificadas que usa Margen. `lock.json` fija la ruta y el
SHA-256 de cada archivo; `scripts/build_syntax.py` se niega a generar `packages/core/components/code.js`
si alguno cambia. No hay CDN ni descarga en tiempo de lectura: el bundle queda incrustado en cada artefacto.

Para cambiar de versión o de lenguajes: descargar el nuevo tarball con scripts desactivados, verificar su
integridad contra `npm view prismjs@<v> dist.integrity`, copiar los `.min.js` necesarios en el orden de
dependencias de `components.json`, actualizar `lock.json` y la lista `LANGUAGES` de `scripts/build_syntax.py`.
