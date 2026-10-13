# a paso lento

Un blog personal estático, en español, listo para publicar en **GitHub Pages**. Incluye contenido de demostración, todas las páginas HTML ya construidas y las fuentes para editarlo.

## Qué incluye

- **44 notas** originales de muestra, en **16 categorías**, entre 2022 y 2026.
- Navegación breve: Inicio · Blog · Sobre mí · Más.
- Una página Más como mapa editorial de las secciones secundarias.
- Búsqueda local de texto, filtros combinables, orden, paginación y vistas de cuadrícula/lista.
- Nueve taxonomías: categorías, etiquetas, años, colecciones, países, géneros, parques, personas y senderos. Todos sus contadores se calculan desde las notas.
- Cuatro estanterías: libros, discos, películas y series. Búsqueda, filtro por año de la nota, valoración y orden.
- Citas favoritas con enlace a la nota original y botón para copiar.
- Estadísticas totales y por año: notas, palabras, días, libros, páginas, caminatas y kilómetros. Incluye tabla y barras accesibles.
- Archivo mensual generado automáticamente.
- Tema claro/oscuro persistente, tamaño de lectura, modo solo lectura, tabla de contenido y progreso.
- Guardados locales con exportación/importación JSON.
- Una página Hoy con fecha de Buenos Aires, cita diaria, sugerencia y aniversarios.
- Página en blanco con escritura privada, guardado local, descarga y temporizador.
- Páginas personales, listas, recomendaciones, contacto, colofón, cambios, transparencia, seguridad y textos legales de ejemplo.
- RSS global, RSS para cada categoría y JSON Feed.
- Sitemap, metadatos sociales, datos estructurados de entradas, 404 y `.nojekyll`.
- Tipografías, iconos e imágenes **locales**; no usa una CDN ni un backend.

El sitio tiene una dirección HTML real para cada entrada y sección. **No necesita un fallback de SPA** para GitHub Pages. Las rutas relativas funcionan tanto en la raíz como dentro de `/nombre-del-repositorio/`.

## Publicar en GitHub Pages — recomendado

1. Descomprimí el ZIP. Creá un repositorio en GitHub, por ejemplo `mi-cuaderno`.
2. Subí **el contenido de la carpeta del proyecto a la raíz del repositorio**, no la carpeta contenedora. `index.html`, `content/`, `tools/`, `assets/` y `.github/` deben quedar en el primer nivel. Recordá incluir los archivos ocultos.
3. Usá la rama `main`. Si elegís otra, cambiá `branches: [main]` en `.github/workflows/pages.yml`.
4. En **Settings → Pages → Build and deployment → Source**, elegí **GitHub Actions**.
5. Abrí **Actions** y ejecutá «Publicar el cuaderno en GitHub Pages», o hacé un nuevo commit.
6. Cuando termine, GitHub mostrará la URL pública. Para un sitio de proyecto será `https://TU_USUARIO.github.io/TU_REPOSITORIO/`.

El workflow construye, verifica y publica el blog. También detecta la URL real, incluida la carpeta del repositorio, para completar RSS, sitemap, enlaces canónicos, imagen social y página 404.

**El proyecto se entrega preparado; no fue subido a una cuenta de GitHub ni publicado en tu nombre.**

### Alternativa: publicar desde una rama

Las páginas ya están generadas. Para que RSS y metadatos usen tu dominio real:

```bash
python -m pip install -r requirements.txt
python tools/build.py --url https://TU_USUARIO.github.io/TU_REPOSITORIO
python tools/check_site.py .
```

Subí el resultado y seleccioná **Deploy from a branch → main → / (root)** en Settings → Pages. En ese modo, tenés que reconstruir y subir los HTML cuando cambies el contenido.

Para `TU_USUARIO.github.io` o un dominio propio, pasá su URL sin carpeta. Si usás dominio propio, configurá además el dominio y DNS en GitHub; el proyecto no los modifica.

## Verlo en tu computadora

No hace falta Node, npm ni una base de datos.

```bash
cd carpeta-del-proyecto
python -m http.server 8000
```

Abrí `http://localhost:8000/`. El servidor local no es necesario en producción. Los archivos se pueden abrir individualmente, pero un servidor reproduce mejor las URLs de directorio.

La vista previa HTML autónoma entregada por separado tiene todos los recursos incorporados y es solo para explorar el diseño. **Publicá este proyecto, no la vista previa autónoma.** El visor aislado puede bloquear almacenamiento permanente, portapapeles o descargas; para probar esas funciones sin las restricciones del visor, abrí el sitio en una pestaña normal o usá el servidor local.

## Hacerlo tuyo

Editá `content/site.json`:

```json
{
  "name": "Mi cuaderno",
  "author": "Tu nombre",
  "location": "Tu ciudad",
  "site_url": "https://TU_USUARIO.github.io/TU_REPOSITORIO",
  "email": "tu-correo@tu-dominio.com",
  "demo": false
}
```

Estos son los campos a modificar dentro del archivo existente; **no borres** las categorías ni las taxonomías. `site_url` puede quedar vacío si usás la publicación automática. La dirección de email también es opcional.

- Textos de identidad y páginas: `content/pages/*.md`.
- Metadatos de páginas: `content/pages.json`.
- Notas: `content/posts/*.md`.
- Metadatos de notas: `content/posts.json`.
- Citas: `content/quotes.json`.
- Diseño: `assets/css/site.css`. `base.css` es la hoja de estilos adaptada del archivo aportado.
- Interacciones: `assets/js/app.js`.

Reemplazá la identidad ficticia, las escenas, las preferencias y los textos legales antes de presentarlos como propios. Las fotografías son ilustraciones generadas y las cubiertas no son oficiales. En `CREDITOS.md` se documentan los recursos y licencias.

### Agregar una entrada

1. Creá `content/posts/mi-nueva-nota.md` con el cuerpo en Markdown.
2. Agregá un objeto al array de `content/posts.json`:

```json
{
  "slug": "mi-nueva-nota",
  "title": "Mi nueva nota",
  "date": "2026-10-13",
  "category": "journal",
  "excerpt": "Un resumen breve para las tarjetas y el feed.",
  "tags": ["atención", "cuadernos"],
  "collections": ["Pequeñas ceremonias"]
}
```

3. Construí de nuevo, o hacé commit y dejá que GitHub Actions lo haga.

Los campos opcionales `countries`, `genres`, `parks`, `people` y `trails` son listas. `distance_km` es un número. Para caminatas también podés usar `elevation_m`, `duration_minutes` y `difficulty`.

Para una obra en una estantería, agregá `media`:

```json
{
  "title": "Título del libro",
  "creator": "Autoría",
  "year": 2026,
  "pages": 240,
  "rating": 4,
  "status": "Leído",
  "color": "#64765b"
}
```

La categoría determina la estantería: `books`, `music`, `movies` o `tvseries`. En los números de libros solo se cuentan los que tienen estado `Leído`. La cubierta ilustrada se genera automáticamente. Las páginas de los libros, tiempos y distancias del corpus de muestra son ilustrativos.

### Enlaces y formato dentro de Markdown

- Enlace interno: `[Blog](site:blog/)`.
- Imagen local: `![Descripción](asset:images/mi-imagen.jpg)`.
- Encabezados `##` y `###` generan la tabla de contenido.
- Se admiten tablas, código cercado, citas, listas, notas al pie y notas destacadas.
- La entrada «Una web que pesa menos que una foto» muestra todos esos formatos.

## Datos, privacidad y límites

- La búsqueda se ejecuta en el navegador; no envía consultas.
- Tema, vistas, tamaño de lectura, guardados y texto privado usan almacenamiento local.
- Los datos locales no se sincronizan. Se pueden exportar o borrar.
- Si el navegador bloquea el almacenamiento, la demo usa memoria temporal y avisa.
- Contacto no simula un envío: sin email configurado, solo permite preparar/copiar un mensaje. Con email, abre el cliente del visitante mediante `mailto:`; no hay envío desde el servidor.
- No se inventa una clave pública verificada. La sección explica cómo publicar la propia.
- RSS y sitemap necesitan una URL pública real. El workflow la completa; en la entrega local, aún no está configurada.
- JavaScript mejora la experiencia. Las entradas, índices, métricas y navegación siguen siendo HTML estático sin él.

## Verificación

```bash
python -m pip install -r requirements.txt
python tools/build.py --output _site --url https://ejemplo.github.io/cuaderno
python tools/check_site.py _site
```

El comprobador revisa enlaces y anclas internos, recursos locales, XML de feeds y consistencia de las métricas. El workflow ejecuta la misma verificación antes de publicar.
