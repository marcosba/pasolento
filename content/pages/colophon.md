## Un sitio estático de verdad

Cada entrada, página, taxonomía y colección tiene un `index.html` propio. GitHub Pages puede servirlo directamente: no hay rutas que dependan de un servidor ni una aplicación que deba iniciarse.

## La construcción

`tools/build.py` lee las notas Markdown y los metadatos JSON. Calcula las palabras, los tiempos de lectura, las relaciones, las estadísticas y los archivos mensuales. También crea el RSS global y los feeds de cada categoría.

```bash
python -m pip install -r requirements.txt
python tools/build.py --url https://usuario.github.io/repositorio
python -m http.server 8000
```

## En el navegador

JavaScript agrega búsqueda local, filtros, orden de las estanterías, notas guardadas, tema claro y oscuro, modo de lectura y una página en blanco. Los guardados no se sincronizan entre dispositivos.

## El diseño

Una navegación en cápsula, color por categoría y espacio para leer. La hoja de estilos de base fue adaptada a recursos locales y acompañada por una capa editorial propia. Lora y DM Sans se distribuyen con sus licencias abiertas.

Las fotografías son ilustraciones generadas para esta demostración. Las cubiertas geométricas son diseños propios, no las portadas oficiales de las obras.

## Publicación

El workflow incluido descubre automáticamente la dirección de GitHub Pages y la incorpora al RSS y al mapa del sitio. Las instrucciones completas están en `README.md`.
