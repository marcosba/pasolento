Este cuaderno empezó con una pregunta: ¿cuánta infraestructura necesita un lugar para escribir? Mucho menos de la que solemos imaginar. Un archivo de texto, una hoja de estilos y una carpeta pueden ser una casa perfectamente habitable.

## El contenido primero

Cada nota vive en un archivo Markdown. La fecha, las etiquetas y las relaciones se guardan aparte, en un pequeño índice. Al construir el sitio, esos datos se convierten en páginas HTML independientes.

```python
from pathlib import Path

cuaderno = Path("content/posts")
for nota in sorted(cuaderno.glob("*.md")):
    print(nota.stem)
```

El servidor no tiene que calcular nada al recibir una visita. Solo entrega archivos. Esa sencillez también significa que una nota se puede leer con JavaScript desactivado.[^1]

## Pequeñas mejoras, no dependencias

La búsqueda, el cambio de tema y las notas guardadas suceden en el navegador. Son una capa adicional, no el requisito para llegar al contenido.

| Función | Dónde sucede | Qué guarda |
| --- | --- | --- |
| Estadísticas | Durante la construcción | HTML y JSON |
| Búsqueda | En tu navegador | Nada en el servidor |
| Guardados | En tu navegador | Identificadores locales |
| RSS | Archivo estático | Entradas y enlaces |

!!! note "Una regla para los enlaces"
    Las rutas son relativas. El mismo sitio funciona en un dominio propio y dentro de una carpeta de GitHub Pages, sin un servidor de rutas especiales.

## Una web que se puede llevar

Podés descargar el sitio y conservarlo. Los estilos, las tipografías y las ilustraciones están incluidos: no dependen de una red de terceros para aparecer.

<details>
<summary>¿Qué cambia si publico en GitHub Pages?</summary>
<p>El workflow incluido construye las páginas y publica el resultado. La dirección real del sitio se usa para los enlaces del RSS y los metadatos. No hace falta un backend ni una base de datos.</p>
</details>

## El formato también cuenta

Un título claro, una tabla legible, una cita, una lista y suficiente aire. El diseño ayuda cuando desaparece lo justo para que podamos seguir leyendo.

> La mejor herramienta es la que no se interpone entre una idea y su forma.

La tabla de contenido, el botón para copiar código, las notas al pie y el modo de lectura de esta página sirven como recorrido por las posibilidades del editor.

[^1]: Las funciones interactivas sí necesitan JavaScript; la navegación, las notas, los índices y las estadísticas siguen siendo HTML estático.
