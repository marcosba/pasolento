# Verificación de la entrega

Revisado el 13 de octubre de 2026.

## Estructura y datos

- 284 páginas HTML independientes, incluida la página 404.
- 44 notas, 16 categorías y nueve taxonomías.
- 11.528 referencias locales comprobadas: enlaces, anclas, imágenes, estilos, fuentes e iconos. Sin recursos faltantes en esa verificación.
- 17 feeds RSS con XML válido; JSON Feed y exportación de datos legibles.
- Contadores y métricas consistentes con el corpus: 6.111 palabras, 44 días, 8 libros, 1.504 páginas de ejemplo, 5 caminatas y 51,6 km a pie.
- 31 resúmenes mensuales generados desde las fechas de las entradas.

## Pruebas de interacción

Se probaron en Chromium:

- Navegación principal y accesos directos a entradas.
- Búsqueda sin distinción de acentos, texto del cuerpo y metadatos de autores, obras, países y senderos.
- Filtros combinados, resultados vacíos, orden, paginación y vistas.
- Cambio de tema y persistencia de preferencias.
- Guardados, descarga de la selección, importación y confirmación de borrado.
- Las nueve taxonomías y sus contadores.
- Las cuatro estanterías, búsqueda por autor y valoración.
- Estadísticas por año y navegación mensual.
- Fecha local, sugerencia diaria y cita de Hoy.
- Editor privado, guardado, descarga, temporizador y modo silencio.
- Lectura ampliada, modo solo lectura, código copiable, tabla, nota destacada, acordeón y notas al pie.
- Galería y ampliación de imágenes.
- Contacto sin envío ficticio y enlaces de feeds.

## Compatibilidad

- Navegación y recursos probados desde la raíz y desde `/prueba/`, equivalente al uso de una subcarpeta de un repositorio en GitHub Pages.
- Enlaces de búsqueda y retorno desde la página 404 probados dentro de esa subcarpeta.
- Sin desbordamiento horizontal en diez plantillas representativas a 320, 390, 768 y 1.440 píxeles de ancho.
- Navegación, paginación y cuerpos de entradas probados con JavaScript desactivado.
- Vista previa autónoma probada en un iframe con `sandbox="allow-scripts"`: navegación, filtros, estadísticas, guardados temporales, búsqueda y vista de RSS sin solicitudes de recursos de red.
- No se observaron errores de ejecución de JavaScript en esas pruebas.

Se ejecutó además una comprobación automática de accesibilidad con axe sobre cinco plantillas en tema claro y la portada en tema oscuro, sin infracciones detectadas en los criterios automatizados seleccionados. Esto no constituye una certificación completa de accesibilidad ni sustituye pruebas con usuarios.

## Publicación

El workflow está incluido, pero la entrega **no fue subida ni publicada en una cuenta de GitHub**. El despliegue real requiere crear el repositorio, subir los archivos y habilitar GitHub Actions en Pages, según `README.md`.
