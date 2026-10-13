#!/usr/bin/env python3
"""Generador estático de a paso lento. Uso: python tools/build.py --url URL --output CARPETA."""
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime, timezone
from email.utils import format_datetime
from html import escape, unescape
from urllib.parse import urlparse
import argparse, json, math, re, shutil, unicodedata, xml.etree.ElementTree as ET
import markdown
from prepare_assets import svg, create_icons, create_covers

ROOT=Path(__file__).resolve().parents[1]
MONTHS=['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre']
SHORT=['ene','feb','mar','abr','may','jun','jul','ago','sep','oct','nov','dic']
SHELVES=[('book-shelf','Libros','books','book'),('album-shelf','Discos','music','music'),('movie-shelf','Películas','movies','film'),('tv-series-shelf','Series','tvseries','tv'),('favourite-quotes','Citas','quotes','pen')]


def slug(text, separator='-'):
    return re.sub(r'[^a-z0-9]+',separator,unicodedata.normalize('NFKD',str(text)).encode('ascii','ignore').decode().lower()).strip(separator)


def stripped(text):
    return re.sub(r'\s+',' ',unescape(re.sub(r'<[^>]*>',' ',text))).strip()


def date_label(d,long=False):
    y,m,day=map(int,d.split('-'))
    return f'{day} de {MONTHS[m-1]} de {y}' if long else f'{day} {SHORT[m-1]} {y}'


def number(n):
    if isinstance(n,float) and not n.is_integer():return f'{n:,.1f}'.replace(',','X').replace('.',',').replace('X','.')
    return f'{int(n):,}'.replace(',','.')


def rel(route,target=''):
    depth=len([x for x in route.strip('/').split('/') if x])
    return ('../'*depth if depth else './')+target.lstrip('/')


def a(route,target,label,cls='',icon=None):
    return f'<a href="{escape(rel(route,target))}"'+(f' class="{cls}"' if cls else '')+f'>{label}'+(svg(icon) if icon else '')+'</a>'


def md_render(text,route):
    engine=markdown.Markdown(extensions=['extra','toc','admonition','sane_lists'],extension_configs={'toc':{'slugify':slug,'toc_depth':'2-3'}})
    out=engine.convert(text)
    def link(m):
        typ,path=m.group(2),m.group(3)
        target=path if typ=='site' else 'assets/'+path
        return m.group(1)+'="'+escape(rel(route,target))+'"'
    out=re.sub(r'(href|src)="(site|asset):/?([^"\s]*)"',link,out)
    out=re.sub(r'<table>(.*?)</table>',r'<div class="table-wrap"><table>\1</table></div>',out,flags=re.S)
    return out,engine.toc


class Site:
    def __init__(self,output,url=None):
        self.output=Path(output).resolve()
        self.config=json.loads((ROOT/'content/site.json').read_text(encoding='utf-8'))
        self.url=(url if url is not None else self.config.get('site_url','')).rstrip('/')
        if self.url:
            parsed=urlparse(self.url)
            if parsed.scheme not in ['https','http'] or not parsed.netloc:raise ValueError('--url debe ser una dirección absoluta http(s).')
        self.config['site_url']=self.url
        self.categories={c['slug']:c for c in self.config['categories']}
        self.page_metadata=json.loads((ROOT/'content/pages.json').read_text(encoding='utf-8'))
        self.quotes=json.loads((ROOT/'content/quotes.json').read_text(encoding='utf-8'))
        self.posts=json.loads((ROOT/'content/posts.json').read_text(encoding='utf-8'))
        seen=set()
        for p in self.posts:
            if p['slug'] in seen:raise ValueError('Slug de nota repetido: '+p['slug'])
            seen.add(p['slug'])
            datetime.strptime(p['date'],'%Y-%m-%d')
            if p['category'] not in self.categories:raise ValueError('Categoría desconocida: '+p['category'])
            p['source']=(ROOT/'content/posts'/f'{p["slug"]}.md').read_text(encoding='utf-8')
            p['html'],p['toc']=md_render(p['source'],'blog/'+p['slug']+'/')
            p['text']=stripped(p['html'])
            p['words']=len(re.findall(r'\b\w+\b',p['text'],flags=re.U))
            p['minutes']=max(1,math.ceil(p['words']/200))
            p['url']='blog/'+p['slug']+'/'
            p['category_name']=self.categories[p['category']]['name']
        self.posts.sort(key=lambda p:(p['date'],p['slug']),reverse=True)
        self.postmap={p['slug']:p for p in self.posts}
        for q in self.quotes:
            if q['post'] not in self.postmap:raise ValueError('Cita con nota inexistente: '+q['post'])
        self.terms={key:defaultdict(list) for key in self.config['taxonomies']}
        for p in self.posts:
            for tax in self.terms:
                if tax=='categories':values=[p['category']]
                elif tax=='years':values=[p['date'][:4]]
                else:values=p.get(tax,[])
                for value in dict.fromkeys(values):self.terms[tax][value].append(p)
        self.months=defaultdict(list)
        for p in self.posts:self.months[p['date'][:7]].append(p)
        self.years=sorted(self.terms['years'],reverse=True)
        self.generated=[]
        self.search_pages=[{'title':info['name'],'url':key+'/','excerpt':info['description'],'text':info['description'],'category_name':'Archivo','date':''} for key,info in self.config['taxonomies'].items()]
        self.search_pages += [{'title':title,'url':route,'excerpt':description,'text':description,'category_name':'Sección','date':''} for route,title,description in [('more/','Más: mapa del cuaderno','Todas las secciones, listas y colecciones.'),('numbers/','El cuaderno en números','Estadísticas: notas, palabras, libros, páginas, kilómetros y años.'),('book-shelf/','Estantería de libros','Lecturas, títulos y autores.'),('album-shelf/','Estantería de discos','Álbumes, artistas y valoraciones.'),('movie-shelf/','Estantería de películas','Cine, películas, directores y valoraciones.'),('tv-series-shelf/','Estantería de series','Series y estados de lectura.'),('favourite-quotes/','Citas favoritas','Frases del cuaderno para copiar y guardar.'),('feeds/','Feeds RSS','Seguir el blog por RSS global, categorías y JSON Feed.'),('save/','Notas guardadas','Tu selección local con importación y exportación.'),('today/','Hoy','Una cita diaria, una lectura y aniversarios.'),('blank/','Una página en blanco','Texto privado, guardado local y temporizador.'),('monthly/','Archivo mensual','Resúmenes mensuales y notas agrupadas por mes.')]]

    def esc(self,text):return escape(str(text),quote=True)

    def style(self,c):
        return f'--cat-color:{c["color"]};--cat-pale:{c["pale"]}'

    def absolute(self,target):return self.url+'/'+target.lstrip('/') if self.url else './'+target.lstrip('/')

    def metric(self,posts):
        return {'posts':len(posts),'words':sum(p['words'] for p in posts),'days':len(set(p['date'] for p in posts)),
          'books':sum(p['category']=='books' and 'media' in p and p['media'].get('status')=='Leído' for p in posts),
          'pages':sum(p.get('media',{}).get('pages',0) for p in posts if p['category']=='books' and p.get('media',{}).get('status')=='Leído'),
          'hikes':sum(p['category']=='hiking' for p in posts),'hiking_km':round(sum(p.get('distance_km',0) for p in posts if p['category']=='hiking'),1),
          'distance':round(sum(p.get('distance_km',0) for p in posts),1)}

    def category_label(self,p,route):
        c=self.categories[p['category']]
        return a(route,'categories/'+c['slug']+'/',svg(c['icon'])+self.esc(c['name']),'category-label')

    def header(self,route,active):
        nav=[('','Inicio','home'),('blog/','Blog','blog'),('about/','Sobre mí','about'),('more/','Más','more')]
        links=''.join(a(route,path,label+(svg('arrow-up') if key=='more' else ''),'active' if active==key else '') .replace(' class="active"',' class="active" aria-current="page"') for path,label,key in nav)
        brand=a(route,'',f'<span class="brand-mark">{svg("path")}</span><span>{self.esc(self.config["name"])}<span class="brand-dot">.</span></span>','brand')
        return f'''<a class="skip-link" href="#main">Saltar al contenido</a><header class="site-header"><div class="header-inner">{brand}<nav class="primary-nav" aria-label="Navegación principal">{links}</nav><div class="header-tools"><button class="icon-button search-trigger" type="button" data-open-search aria-label="Buscar en el cuaderno" aria-haspopup="dialog">{svg('search')}<span class="shortcut" aria-hidden="true">/</span></button><span class="tool-divider" aria-hidden="true"></span><button class="icon-button" type="button" data-theme-toggle aria-label="Activar tema oscuro" title="Cambiar tema">{svg('sun')}</button><a class="icon-button" href="{rel(route,'save/')}" title="Notas guardadas" aria-label="Notas guardadas">{svg('bookmark')}<span class="save-count" data-save-count hidden>0</span></a></div></div></header>'''

    def footer(self,route):
        brand=a(route,'',f'<span class="brand-mark">{svg("path")}</span><span>{self.esc(self.config["name"])}.</span>','brand')
        links=''.join(a(route,path,label) for path,label in [('now/','Ahora'),('contact/','Contacto'),('feeds/','RSS'),('colophon/','Colofón'),('privacy/','Privacidad')])
        demo='Contenido de demostración · ' if self.config.get('demo') else ''
        return f'''<footer class="site-footer"><div class="footer-inner"><div class="footer-top"><div class="footer-brand">{brand}<p>Hecho para quedarse un rato.</p></div><nav class="footer-links" aria-label="Enlaces del pie">{links}</nav></div><div class="footer-bottom"><p>© {self.config['updated'][:4]} {self.esc(self.config['author'])} · {demo}Sin prisa, sin rastreadores.</p><p>{a(route,'terms/','Condiciones')} &nbsp;·&nbsp; {a(route,'guide/','Recorrido de la demo') if self.config.get('demo') else a(route,'more/','Mapa del sitio')}</p><a href="#top" class="text-link back-to-top">Volver arriba {svg('arrow-up')}</a></div></div></footer>'''

    def dialogs(self):
        return f'''<dialog id="search-dialog" aria-labelledby="search-title"><div class="dialog-head"><h2 id="search-title">Buscar en el cuaderno</h2><button class="icon-button" type="button" data-close-dialog aria-label="Cerrar búsqueda">{svg('x')}</button></div><div class="dialog-search"><div class="field">{svg('search')}<label class="sr-only" for="global-search">Buscar por título, tema o contenido</label><input id="global-search" type="search" placeholder="Un libro, una idea, un lugar…" autocomplete="off"></div></div><div id="search-status" class="search-status" role="status">Empezá a escribir o explorá las últimas notas.</div><div id="search-results" class="search-results"></div><div class="dialog-help"><kbd>↑ ↓</kbd> recorrer &nbsp; <kbd>Enter</kbd> abrir &nbsp; <kbd>Esc</kbd> cerrar <span style="margin-left:auto">La búsqueda sucede en tu navegador.</span></div></dialog><dialog id="lightbox-dialog" class="lightbox-dialog" aria-label="Imagen ampliada"><button type="button" class="icon-button" data-close-dialog aria-label="Cerrar imagen">{svg('x')}</button><img alt="" id="lightbox-image"><p class="lightbox-caption" id="lightbox-caption"></p></dialog><div class="toast" id="toast" role="status" aria-live="polite"></div><button class="button exit-focus" type="button" data-exit-focus>{svg('x')}Volver al cuaderno</button>'''

    def write_file(self,path,content):
        dest=self.output/path;dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_text(content,encoding='utf-8');self.generated.append(path)

    def write_page(self,route,title,description,content,active='more',bodyclass='',post=None,extrahead=''):
        doc_title=title+' · '+self.config['name']
        canonical=f'<link rel="canonical" href="{self.esc(self.absolute(route))}"><meta property="og:url" content="{self.esc(self.absolute(route))}">' if self.url else ''
        ogimage='<meta property="og:image" content="'+self.esc(self.absolute('assets/images/'+(post.get('image','patagonia.jpg') if post else 'patagonia.jpg')))+'">' if self.url else ''
        base=''
        if bodyclass=='page-404':base=f'<base href="{self.esc(self.url+"/" if self.url else "/")}">'
        structured=''
        if post and self.url:
            obj={'@context':'https://schema.org','@type':'BlogPosting','headline':post['title'],'description':post['excerpt'],'datePublished':post['date'],'dateModified':post['date'],'author':{'@type':'Person','name':self.config['author']},'mainEntityOfPage':self.absolute(post['url']),'inLanguage':self.config['language'],'wordCount':post['words']}
            structured='<script type="application/ld+json">'+json.dumps(obj,ensure_ascii=False).replace('<','\\u003c')+'</script>'
        out=f'''<!doctype html><html lang="es-AR" data-theme="light"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{self.esc(doc_title)}</title><meta name="description" content="{self.esc(description)}"><meta name="theme-color" content="#faf9f6"><meta property="og:site_name" content="{self.esc(self.config['name'])}"><meta property="og:title" content="{self.esc(title)}"><meta property="og:description" content="{self.esc(description)}"><meta property="og:type" content="{'article' if post else 'website'}"><meta name="twitter:card" content="summary_large_image">{base}{canonical}{ogimage}{structured}<link rel="icon" type="image/svg+xml" href="{rel(route,'favicon.svg')}"><link rel="alternate" type="application/rss+xml" title="{self.esc(self.config['name'])}" href="{rel(route,'rss.xml')}"><link rel="preload" href="{rel(route,'assets/fonts/lora-400-normal.ttf')}" as="font" type="font/ttf" crossorigin><script>try{{document.documentElement.dataset.theme=localStorage.getItem('paso-theme')==='dark'?'dark':'light';document.documentElement.style.setProperty('--reader-scale',localStorage.getItem('paso-reader-scale')||'1')}}catch(e){{}}</script><link rel="stylesheet" href="{rel(route,'assets/css/base.css')}"><link rel="stylesheet" href="{rel(route,'assets/css/site.css')}"><script defer src="{rel(route,'assets/js/data.js')}"></script><script defer src="{rel(route,'assets/js/app.js')}"></script>{extrahead}</head><body id="top" class="{bodyclass}" data-base="{rel(route)}" data-route="{route}" {'data-post="'+post['slug']+'"' if post else ''}>{self.header(route,active)}<main id="main" tabindex="-1">{content}</main>{self.footer(route)}{self.dialogs()}</body></html>'''
        self.write_file(route+'index.html',out)

    def breadcrumb(self,route,label,parent=None):
        return '<nav class="breadcrumb" aria-label="Ubicación">'+a(route,'','Inicio')+'<span>/</span>'+(a(route,parent[0],parent[1])+'<span>/</span>' if parent else '')+'<span aria-current="page">'+self.esc(label)+'</span></nav>'

    def heading(self,title,description,kicker,count=None):
        return f'<div class="page-heading"><div class="eyebrow"><span class="dot"></span>{self.esc(kicker)}</div><h1>{self.esc(title)}'+(f'<span class="page-count">{count}</span>' if count is not None else '')+f'</h1><p>{self.esc(description)}</p></div>'

    def thumbnail(self,p,route):
        c=self.categories[p['category']];m=p.get('media')
        if p.get('image'):
            img=f'<img src="{rel(route,"assets/images/"+p["image"])}" alt="Ilustración de '+('un paisaje patagónico' if p['image']=='patagonia.jpg' else 'un libro abierto junto a una taza' if p['image']=='lectura.jpg' else 'una calle de Buenos Aires')+'" loading="lazy" width="640" height="400">'
            if m and p['category']=='books':img+=f'<img class="thumb-book" src="{rel(route,"assets/covers/"+p["slug"]+".svg")}" alt="" loading="lazy">'
            return img
        if p['category']=='development':return '<div class="card-art code-art"><div class="code-window"><span>const</span> cuaderno = {<br>&nbsp; ritmo: <span>"propio"</span>,<br>&nbsp; curiosidad: <span>true</span><br>};</div></div>'
        if m:return f'<div class="card-art" style="{self.style(c)}"><img class="art-cover" src="{rel(route,"assets/covers/"+p["slug"]+".svg")}" alt="Cubierta ilustrada de {self.esc(m["title"])}" loading="lazy"><span class="art-icon">{svg(c["icon"])}</span><span class="art-label">{self.esc(c["name"])}</span></div>'
        texts={'journal':'Guardar lo que<br>pasa cerca.','monthlyupdates':'Un mes,<br>muchas escenas.','essays':'Las preguntas<br>también cuentan.','general':'Hacer lugar<br>para lo simple.','remembering':'Lo que elegimos<br>conservar.','mac':'Menos cosas.<br>Más espacio.','projects':'Empezar<br>en pequeño.','biking':'El mundo<br>a dos ruedas.'}
        return f'<div class="card-art" style="{self.style(c)}"><span class="card-text-art">{texts.get(p["category"],"Mirar<br>más despacio.")}</span><span class="art-icon">{svg(c["icon"])}</span></div>'

    def card(self,p,route,hidden=False):
        c=self.categories[p['category']]
        return f'''<article class="post-card" data-card="{p['slug']}" style="{self.style(c)}" {'hidden' if hidden else ''}><a href="{rel(route,p['url'])}" class="card-image-link" aria-label="Leer {self.esc(p['title'])}">{self.thumbnail(p,route)}</a><div class="card-body"><div class="card-topline">{self.category_label(p,route)}<time datetime="{p['date']}">{date_label(p['date'])}</time></div><h3>{a(route,p['url'],self.esc(p['title']))}</h3><p class="excerpt">{self.esc(p['excerpt'])}</p><div class="card-footer"><span class="reading-time">{svg('clock')}{p['minutes']} min de lectura</span><button class="card-save" type="button" data-save="{p['slug']}" aria-label="Guardar: {self.esc(p['title'])}" aria-pressed="false" title="Guardar nota">{svg('bookmark')}</button></div></div></article>'''

    def empty(self,title='No apareció ninguna nota.',message='Probá otra búsqueda o quitá algún filtro.',hidden=True,reset=True):
        return f'<div class="empty-state" data-empty {"hidden" if hidden else ""}>{svg("search")}<h3>{title}</h3><p>{message}</p>'+(f'<button type="button" class="button" data-reset-filters>Limpiar filtros {svg("arrow")}</button>' if reset else '')+'</div>'

    def rss_callout(self,route):
        return f'<div class="rss-callout"><div class="rss-text">{svg("rss")}<div><h3>Nos leemos, sin algoritmos.</h3><p>Seguí este cuaderno con tu lector RSS. A tu ritmo, sin compartir tu email.</p></div></div>{a(route,"feeds/","Suscribirme por RSS "+svg("arrow"),"button primary")}</div>'

    def home(self):
        r='';feature=next(p for p in self.posts if p.get('featured'))
        intro=f'''<section aria-labelledby="home-title"><div class="home-intro"><div><div class="eyebrow"><span class="dot"></span>UN CUADERNO PERSONAL · {self.esc(self.config["location"].split(",")[0].upper())}</div><h1 id="home-title">Menos prisa.<br><em>Más curiosidad.</em></h1></div><div class="hero-copy"><p>Historias de libros, caminos y pequeñas cosas que hacen grande lo cotidiano.<br>Un lugar para mirar más despacio.</p>{a(r,'about/','Conocé este cuaderno '+svg('arrow-up'),'text-link')}</div></div><a class="hero-banner" href="{rel(r,feature['url'])}" aria-label="Leer: {self.esc(feature['title'])}"><img src="{rel(r,'assets/images/patagonia.jpg')}" alt="Ilustración de montañas patagónicas, un río y pastizales dorados" width="1376" height="768" fetchpriority="high"><span class="hero-shade"></span><span class="hero-location">{svg('pin')}El Chaltén, Argentina</span><div class="hero-caption"><div><span class="category-label">{svg('mountain')}Caminatas</span><span class="banner-date">11 OCT 2026</span><h2>A veces, el mejor plan<br>es seguir el sendero.</h2></div><span class="read-link">Leer la última caminata {svg('arrow-up')}</span></div></a></section>'''
        tabs=[('','Todo'),('books','Lecturas'),('hiking','Caminatas'),('journal','Diario'),('music','Música'),('development','Tecnología')]
        filters='<div class="filter-tabs" role="group" aria-label="Filtrar notas recientes">'+''.join(f'<button type="button" data-home-filter="{key}" class="{"active" if not key else ""}" aria-pressed="{"true" if not key else "false"}">'+(svg(self.categories[key]['icon']) if key else '')+label+'</button>' for key,label in tabs)+'</div>'
        nonfeature=[p for p in self.posts if p['slug']!=feature['slug']]
        shown=set(p['slug'] for p in nonfeature[:6])
        grid=f'<div class="post-grid" id="home-posts" data-post-grid data-mode="home" data-per-page="6" data-exclude="{feature["slug"]}">'+''.join(self.card(p,r,p['slug'] not in shown) for p in self.posts)+self.empty()+'</div>'
        notes=f'<section class="section" aria-labelledby="recent-title"><div class="section-head"><div><h2 id="recent-title">Notas recientes</h2><p>Lo que fui encontrando por el camino.</p></div>{a(r,"blog/","Todo el archivo "+svg("arrow"),"text-link")}</div>{filters}{grid}<p class="result-hint" data-home-status>Seis notas para empezar. El archivo tiene {len(self.posts)}.</p></section>'
        shelves='<section class="section" aria-labelledby="shelves-title"><div class="section-head"><div><h2 id="shelves-title">En las estanterías</h2><p>Historias que se quedan, en distintos formatos.</p></div>'+a(r,'favourite-quotes/','Citas para guardar '+svg('arrow'),'text-link')+'</div><div class="shelf-teasers">'
        for path,label,cat,icon in SHELVES[:4]:
            count=sum('media' in p for p in self.terms['categories'][cat])
            shelves+=a(r,path+'/',svg(icon)+f'<span><strong>{label}</strong><small>{count} '+('libros leídos' if cat=='books' else 'discos escuchados' if cat=='music' else 'películas vistas' if cat=='movies' else 'historias reunidas')+'</small></span>'+svg('arrow-up','ui-icon teaser-arrow'),'shelf-teaser')
        shelves+='</div></section>'
        m=self.metric(self.posts)
        stats='<div class="home-stats" aria-label="El cuaderno en cifras">'+''.join(f'<div class="stat"><b>{number(val)}</b><span>{name}</span></div>' for val,name in [(m['posts'],'notas publicadas'),(m['books'],'libros leídos'),(m['hiking_km'],'km caminados'),(len(self.years),'años de cuaderno')])+a(r,'numbers/','El cuaderno en números '+svg('arrow-up'),'text-link')+'</div>'
        self.write_page(r,'Menos prisa. Más curiosidad.',self.config['description'],intro+notes+shelves+stats+self.rss_callout(r),'home','page-home')

    def toolbar(self,r,shelf=False):
        category='<div class="field"><label for="archive-category">Categoría</label><select id="archive-category" data-filter-category><option value="">Todas las categorías</option>'+''.join(f'<option value="{c["slug"]}">{self.esc(c["name"])}</option>' for c in self.categories.values())+'</select></div>' if not shelf else ''
        years='<div class="field"><label for="archive-year">Año de la nota</label><select id="archive-year" data-filter-year><option value="">Todos los años</option>'+''.join(f'<option>{y}</option>' for y in self.years)+'</select></div>'
        rating='<div class="field"><label for="shelf-rating">Valoración</label><select id="shelf-rating" data-filter-rating><option value="">Todas</option><option value="5">★★★★★</option><option value="4">★★★★ o más</option></select></div>' if shelf else ''
        sorts=[('title','Título A–Z'),('recent','Más recientes'),('rating','Mejor valorados')] if shelf else [('recent','Más recientes'),('oldest','Más antiguas'),('title','Título A–Z')]
        sort='<div class="field sort-field"><label for="archive-sort">Ordenar</label><select id="archive-sort" data-filter-sort>'+''.join(f'<option value="{v}">{label}</option>' for v,label in sorts)+'</select></div>'
        return f'<div class="archive-toolbar" data-filters><div class="field search-field"><label for="archive-search">Buscar {"en la estantería" if shelf else "en el archivo"}</label>{svg("search")}<input id="archive-search" type="search" data-filter-search placeholder="{"Título o autor…" if shelf else "Título, tema o una palabra…"}" autocomplete="off"></div>{category}{years}{rating}{sort}<div class="view-toggle" role="group" aria-label="Vista del catálogo"><button class="active" type="button" data-view="grid" aria-label="Vista de cuadrícula" aria-pressed="true">{svg("grid")}</button><button type="button" data-view="list" aria-label="Vista de lista" aria-pressed="false">{svg("list")}</button></div></div>'

    def archive(self,page=1):
        r='blog/' if page==1 else f'blog/page/{page}/'
        per=9;npages=math.ceil(len(self.posts)/per)
        out=self.breadcrumb(r,'Blog')+self.heading('Todas las notas.','Lecturas, caminos y pequeñas observaciones. Un archivo que crece a su propio ritmo.','EL BLOG',str(len(self.posts)))
        out+=self.toolbar(r)+'<div class="archive-meta"><span data-result-status>'+f'{len(self.posts)} notas · página {page} de {npages}'+'</span><button type="button" data-reset-filters>Limpiar filtros</button></div>'
        out+=f'<div class="post-grid" id="archive-posts" data-post-grid data-mode="archive" data-per-page="{per}" data-page="{page}">'+''.join(self.card(p,r,not ((page-1)*per<=i<page*per)) for i,p in enumerate(self.posts))+self.empty()+'</div>'
        out+='<nav class="pagination" data-pagination aria-label="Páginas del archivo">'+''.join(f'<a href="{rel(r,"blog/" if n==1 else f"blog/page/{n}/")}" data-page-link="{n}" '+(f'class="active" aria-current="page"' if n==page else '')+f'>{n}</a>' for n in range(1,npages+1))+'</nav>'
        out+='<noscript><p class="noscript-note">El contenido y los enlaces funcionan sin JavaScript. Para buscar, combinar filtros o cambiar la vista, activalo en tu navegador.</p></noscript>'
        self.write_page(r,'Blog',self.config['description'],out,'blog','page-blog')

    def more(self):
        r='more/'
        groups=[('Seguir en contacto','mail',[('contact/','Contacto'),('feeds/','Feeds RSS'),('save/','Notas guardadas')]),
        ('Un poco más de mí','pen',[('death/','Lo que quisiera dejar'),('hills/','Convicciones'),('interests/','Intereses'),('top4/','Cuatro favoritos'),('where/','Dónde'),('yep/','A lo que digo sí'),('nope/','A lo que digo no')]),
        ('Listas vivas','bulb',[('now/','Ahora'),('ideas/','Ideas'),('someday/','Algún día')]),
        ('Las estanterías','book',[(p+'/',l) for p,l,_,_ in SHELVES]),
        ('Recomendaciones','arrow-up',[('blogroll/','Otros blogs'),('links/','Enlaces'),('podroll/','Podcasts')]),
        ('Detrás del cuaderno','code',[('numbers/','En números'),('monthly/','Archivo mensual'),('today/','Hoy'),('blank/','Una página en blanco'),('uses/','Herramientas'),('colophon/','Colofón'),('changelog/','Registro de cambios'),('ai/','Inteligencia artificial'),('public-keys/','Claves públicas'),('guide/','Recorrido de la demo')]),
        ('Explorar el archivo','layers',[(t+'/',meta['name']) for t,meta in self.config['taxonomies'].items()]),
        ('Lo importante, claro','info',[('privacy/','Privacidad'),('terms/','Condiciones')])]
        out=self.breadcrumb(r,'Más')+self.heading('Hay más por acá.','Un mapa de los rincones de este cuaderno. Elegí una curiosidad y seguí el hilo.','EXPLORAR')
        out+=f'<div class="more-intro">{svg("path")}<span>¿Es tu primera visita? {a(r,"guide/","Este recorrido te muestra todas las funciones del blog.")}</span></div><div class="more-grid">'
        for title,icon,links in groups:
            out+=f'<section class="more-group"><h2>{svg(icon)}{title}</h2><ul>'
            for path,label in links:
                badge=f'<span class="link-note">{len(self.terms[path.strip("/")])}</span>' if path.strip('/') in self.terms else ''
                out+='<li>'+a(r,path,label+badge+svg('arrow-up'))+'</li>'
            out+='</ul></section>'
        out+='</div>'
        self.write_page(r,'Más', 'El mapa completo de a paso lento: listas, estanterías, taxonomías y herramientas.',out,'more','page-more')

    def static_pages(self):
        for meta in self.page_metadata:
            name=meta['slug'];r=name+'/'
            src=(ROOT/'content/pages'/f'{name}.md').read_text(encoding='utf-8')
            out,toc=md_render(src,r)
            heading=self.breadcrumb(r,meta['title'])+self.heading(meta['title'],meta['description'],meta['kicker'])
            sidebar=f'<aside><div class="aside-card"><img src="{rel(r,"assets/images/buenos-aires.jpg")}" alt="Ilustración de una calle de Buenos Aires" loading="lazy"><div class="aside-card-body"><div class="author-monogram">{self.esc("".join(w[0] for w in self.config["author"].split()[:2]))}</div><h3>Hola, soy {self.esc(self.config["author"].split()[0])}.</h3><p>{self.esc(self.config["tagline"])} Desde {self.esc(self.config["location"])}.</p>{a(r,"now/","Lo que me ocupa ahora "+svg("arrow-up"),"text-link")}</div></div><p class="subtle-note">{self.esc("Esta edición contiene relatos y una identidad de demostración. Hacé lugar para tu propia voz." if self.config.get("demo") else "Un cuaderno propio, hecho para quedarse un rato.")}</p></aside>' if name=='about' else f'<aside><div class="aside-card"><div class="aside-card-body">{svg(meta["icon"])}<h3 style="margin-top:17px">Seguí explorando.</h3><p>El mapa del cuaderno reúne todos sus rincones, desde listas personales hasta el archivo completo.</p>{a(r,"more/","Volver al mapa "+svg("arrow"),"text-link")}</div></div></aside>'
            if name=='contact':out+=self.contact_form()
            if name=='privacy':out+='<div class="button-row"><button type="button" class="button danger" data-reset-local>'+svg('trash')+'Borrar todos los datos locales</button></div>'
            content=heading+f'<div class="prose-layout"><div class="prose">{out}</div>{sidebar}</div>'
            self.write_page(r,meta['title'],meta['description'],content,'about' if name=='about' else 'more','page-static page-'+name)
            self.search_pages.append({'title':meta['title'],'url':r,'excerpt':meta['description'],'text':stripped(out),'category_name':'Página','date':''})

    def contact_form(self):
        configured=bool(self.config.get('email'))
        return f'''<form class="contact-form" data-contact-form><div class="field"><label for="contact-subject">Asunto</label><input id="contact-subject" name="subject" required maxlength="180" placeholder="Una recomendación para el cuaderno"></div><div class="field"><label for="contact-message">Mensaje</label><textarea id="contact-message" name="message" required maxlength="10000" placeholder="Hola, quería compartir…"></textarea></div><div class="button-row"><button type="button" class="button" data-copy-message>{svg('copy')}Copiar mensaje</button><button type="submit" class="button primary" {'disabled aria-disabled="true"' if not configured else ''}>{svg('mail')}Abrir mi correo</button></div><p class="subtle-note" style="margin:0">{'Se abrirá tu aplicación de correo; este sitio no enviará el mensaje.' if configured else 'El envío está desactivado hasta configurar un email propio. Copiar sí funciona.'}</p></form>'''

    def taxonomy_index(self,tax):
        r=tax+'/';meta=self.config['taxonomies'][tax]
        out=self.breadcrumb(r,meta['name'])+self.heading(meta['name'],meta['description'],'EXPLORAR EL ARCHIVO',str(len(self.terms[tax])))
        out+='<nav class="taxonomy-nav" aria-label="Tipos de archivo">'+''.join(a(r,t+'/',info['name'],'active' if t==tax else '') for t,info in self.config['taxonomies'].items())+'</nav>'
        out+='<div class="archive-toolbar"><div class="field search-field"><label for="term-search">Buscar '+meta['name'].lower()+'</label>'+svg('search')+'<input id="term-search" type="search" data-term-search placeholder="Encontrar un término…"></div><div class="field"><label for="term-sort">Orden</label><select id="term-sort" data-term-sort><option value="name">'+('Más recientes' if tax=='years' else 'Alfabético')+'</option><option value="count">Más notas</option></select></div></div>'
        terms=sorted(self.terms[tax],reverse=tax=='years',key=lambda term:term if tax=='years' else slug(self.categories[term]['name'] if tax=='categories' else term))
        out+='<div class="term-grid" data-term-grid data-taxonomy="'+tax+'">'
        for term in terms:
            label=self.categories[term]['name'] if tax=='categories' else term
            count=len(self.terms[tax][term]);c=self.categories.get(term) if tax=='categories' else None
            content=svg(c['icon'] if c else meta['icon'])+f'<div class="term-name">{self.esc(label)}'+(f'<p class="term-description">{self.esc(c["description"])}</p>' if c else '')+f'</div><span class="count">{count}</span>'
            out+=f'<a class="term-card {"category-term" if c else ""}" href="{rel(r,tax+"/"+slug(term)+"/")}" data-term="{self.esc(label)}" data-count="{count}"'+(f' style="{self.style(c)}"' if c else '')+'>'+content+'</a>'
        out+=self.empty('No encontré ese término.','Probá una palabra diferente.',True,False)+'</div>'
        self.write_page(r,meta['name'],meta['description'],out,'more','page-taxonomy')

    def taxonomy_detail(self,tax,term,posts):
        r=tax+'/'+slug(term)+'/';meta=self.config['taxonomies'][tax]
        label=self.categories[term]['name'] if tax=='categories' else term
        description=self.categories[term]['description'] if tax=='categories' else f'Las {len(posts)} notas que se conectan con '+str(term)+'.'
        out=self.breadcrumb(r,label,(tax+'/',meta['name']))+self.heading(label,description,meta['singular'],str(len(posts)))
        out+='<div class="taxonomy-detail-bar">'+a(r,tax+'/',svg('back')+'Todos los '+meta['name'].lower(),'text-link')+(a(r,tax+'/'+slug(term)+'/rss.xml',svg('rss')+'Seguir esta categoría','button small') if tax=='categories' else f'<span style="color:var(--muted);font-size:11px">{len(posts)} notas, de la más reciente a la más antigua</span>')+'</div>'
        out+='<div class="post-grid">'+''.join(self.card(p,r) for p in posts)+'</div>'
        self.write_page(r,label,description,out,'more','page-taxonomy-detail')

    def shelf(self,path,label,cat,icon):
        r=path+'/';posts=sorted([p for p in self.posts if p['category']==cat and 'media' in p],key=lambda p:slug(p['media']['title']))
        desc={'books':'Libros leídos, preguntas abiertas y páginas que dejaron una marca.','music':'Discos escuchados de principio a fin. Un archivo para volver a oír.','movies':'Películas que siguieron conversando después de los créditos.','tvseries':'Historias largas, con espacio entre un capítulo y el siguiente.'}[cat]
        out=self.breadcrumb(r,'Estantería de '+label.lower())+self.heading('La estantería de '+label.lower()+'.',desc,'COLECCIONES',str(len(posts)))
        out+='<nav class="shelf-navigation" aria-label="Estanterías">'+''.join(a(r,name+'/',svg(ico)+lab,'active' if path==name else '') for name,lab,_,ico in SHELVES)+'</nav>'+self.toolbar(r,True)
        out+='<div class="archive-meta"><span data-result-status>'+str(len(posts))+' títulos</span><button type="button" data-reset-filters>Limpiar filtros</button></div>'
        out+='<div class="shelf-grid" data-shelf-grid data-category="'+cat+'">'
        for p in posts:
            m=p['media'];stars='★'*m['rating']+'☆'*(5-m['rating'])
            out+=f'<article class="shelf-item" data-shelf-item="{p["slug"]}"><a class="cover-link" href="{rel(r,p["url"])}"><img src="{rel(r,"assets/covers/"+p["slug"]+".svg")}" alt="Cubierta ilustrada de {self.esc(m["title"])}" loading="lazy" width="300" height="450"></a><div><h3>{a(r,p["url"],self.esc(m["title"]))}</h3><p>{self.esc(m["creator"])} · {m["year"]}</p></div><div class="shelf-bottom"><span class="stars" aria-label="{m["rating"]} de 5 estrellas">{stars}</span><span class="shelf-status">{self.esc(m["status"])}</span></div></article>'
        out+=self.empty('No hay títulos con esos filtros.','Probá otro año o valoración.')+'</div><p class="shelf-info">Las cubiertas son ilustraciones creadas para la demo, no portadas oficiales. Cada título enlaza a su nota. Las valoraciones y los datos de edición son de ejemplo.</p>'
        self.write_page(r,'Estantería de '+label.lower(),desc,out,'more','page-shelf')

    def favourite_quotes(self):
        r='favourite-quotes/'
        out=self.breadcrumb(r,'Citas')+self.heading('Frases para llevarse.','Pequeños fragmentos de este cuaderno que merecen una segunda lectura.','CITAS FAVORITAS',str(len(self.quotes)))
        out+='<nav class="shelf-navigation" aria-label="Estanterías">'+''.join(a(r,name+'/',svg(ico)+lab,'active' if name=='favourite-quotes' else '') for name,lab,_,ico in SHELVES)+'</nav><div class="quotes-grid">'
        for q in self.quotes:
            p=self.postmap[q['post']]
            out+=f'<figure class="quote-panel" style="margin:0"><span class="quote-mark" aria-hidden="true">“</span><blockquote>{self.esc(q["text"])}</blockquote><figcaption class="quote-author">{self.esc(self.config["author"])} · de este cuaderno</figcaption><div class="quote-actions">{a(r,p["url"],self.esc(p["title"])+svg("arrow-up"),"text-link")}<button type="button" data-copy-text="{self.esc(q["text"])}" aria-label="Copiar cita">{svg("copy")}</button></div></figure>'
        out+='</div>'
        self.write_page(r,'Citas favoritas','Fragmentos originales de las notas del cuaderno.',out,'more','page-quotes')

    def numbers(self):
        r='numbers/';m=self.metric(self.posts)
        out=self.breadcrumb(r,'En números')+'<div class="numbers-heading">'+self.heading('El cuaderno en números.','Una mirada al archivo desde lejos. Cada cifra sale de las notas y sus metadatos.','ESTADÍSTICAS')+'<div class="field year-select"><label for="numbers-year">Mirar un año</label><select id="numbers-year" data-numbers-year><option value="">Todo el cuaderno</option>'+''.join(f'<option>{y}</option>' for y in self.years)+'</select></div></div><div class="stats-grid">'
        for key,label,icon,detail in [('posts','notas publicadas','pen',f'<span data-stat="days">{number(m["days"])}</span> días con una nota'),('words','palabras escritas','book','En el cuerpo de las entradas'),('books','libros leídos','book',f'<span data-stat="pages">{number(m["pages"])}</span> páginas de ejemplo'),('hikes','caminatas','mountain',f'<span data-stat="hiking_km">{number(m["hiking_km"])}</span> km recorridos')]:
            out+=f'<div class="metric-card">{svg(icon)}<div class="metric-value" data-stat="{key}">{number(m[key])}</div><div class="metric-label">{label}</div><div class="metric-detail">{detail}</div></div>'
        out+='</div><div class="numbers-panels"><section class="stats-panel"><h2>Notas a lo largo del tiempo</h2><p>El archivo por año. Elegí una barra para explorar sus notas.</p><div class="bar-chart" aria-label="Cantidad de notas por año">'
        highest=max(len(ps) for ps in self.terms['years'].values())
        for year in sorted(self.years):
            count=len(self.terms['years'][year])
            out+=f'<div class="bar-row {"latest" if year==self.years[0] else ""}" data-bar-year="{year}">{a(r,"years/"+year+"/",year)}<a class="bar-track" href="{rel(r,"years/"+year+"/")}" aria-label="{year}: {count} notas"><div class="bar-fill" style="width:{round(count/highest*100,1)}%"></div></a><strong>{count}</strong></div>'
        out+='</div></section><section class="stats-panel"><h2>Todo está conectado</h2><p>Términos únicos de las nueve taxonomías del archivo.</p><div class="taxonomy-metrics">'
        for tax,meta in self.config['taxonomies'].items():out+=a(r,tax+'/',f'<strong>{len(self.terms[tax])}</strong><span>{meta["name"]}</span>')
        out+='</div></section></div><section class="section" style="margin-top:35px"><div class="section-head"><div><h2 style="font-size:26px">El detalle, año por año</h2><p>Lecturas, caminos y distancias registradas.</p></div><span style="color:var(--muted);font-size:11px">Distancia total: <b data-stat="distance">'+number(m['distance'])+'</b> km</span></div><div class="stats-table-wrap"><table class="stats-table"><thead><tr><th>Año</th><th>Notas</th><th>Palabras</th><th>Libros</th><th>Páginas</th><th>Caminatas</th><th>Km a pie</th><th>Km totales</th></tr></thead><tbody>'
        for y in self.years:
            ym=self.metric(self.terms['years'][y]);out+=f'<tr data-year-row="{y}"><td>{a(r,"years/"+y+"/",y)}</td>'+''.join(f'<td>{number(ym[k])}</td>' for k in ['posts','words','books','pages','hikes','hiking_km','distance'])+'</tr>'
        out+='</tbody><tfoot><tr><td data-stats-total-label>Total</td>'+''.join(f'<td data-stat="{k}">{number(m[k])}</td>' for k in ['posts','words','books','pages','hikes','hiking_km','distance'])+'</tr></tfoot></table></div><p class="numbers-caption">La distancia total incluye caminatas, bicicleta y viajes; no representa solo senderismo. Los datos de recorrido y edición son de demostración. Palabras, días, relaciones y conteos se calculan al construir el sitio. Actualizado el '+date_label(self.config['updated'],True)+'.</p></section>'
        self.write_page(r,'En números','Estadísticas calculadas desde las notas: lecturas, palabras, caminos y distancias.',out,'more','page-numbers')

    def feeds(self):
        r='feeds/'
        out=self.breadcrumb(r,'Feeds RSS')+self.heading('Seguir el cuaderno, a tu ritmo.','Un lector RSS reúne las notas nuevas sin algoritmos, cuentas ni una bandeja llena de emails.','FEEDS Y SUSCRIPCIÓN')
        out+='<div class="feed-grid"><section class="feed-card feed-featured"><div><h3>'+svg('rss')+'Todo el cuaderno</h3><p>Todas las entradas, en orden cronológico.</p></div><div class="button-row">'+a(r,'rss.xml','Abrir RSS '+svg('arrow-up'),'button primary')+f'<button type="button" class="button" data-copy-url="rss.xml">{svg("copy")}Copiar enlace</button>'+a(r,'feed.json','JSON Feed','button')+'</div></section>'
        for cat,c in self.categories.items():
            path='categories/'+cat+'/rss.xml'
            out+=f'<section class="feed-card"><h3>{svg(c["icon"])}{self.esc(c["name"])}</h3><p>{len(self.terms["categories"][cat])} notas · solo esta categoría</p><div class="button-row">{a(r,path,"Abrir RSS "+svg("arrow-up"),"button small")}<button type="button" class="button small" data-copy-url="{path}">{svg("copy")}Copiar enlace</button></div></section>'
        out+='</div><div class="prose" style="margin-top:38px"><h2>¿Cómo lo uso?</h2><p>Copiá el enlace del feed y agregalo a tu lector RSS. Las nuevas notas aparecerán allí cuando actualices el contenido y publiques de nuevo. No hace falta suscribirse con una dirección de email.</p><p class="subtle-note">Durante la publicación automática, los feeds incorporan la URL real de GitHub Pages. Si publicás los archivos manualmente, configurá <code>site_url</code> y reconstruí primero.</p></div>'
        self.write_page(r,'Feeds RSS','Suscripción RSS global y por categoría, más un JSON Feed.',out,'more','page-feeds')

    def save(self):
        r='save/'
        out=self.breadcrumb(r,'Guardados')+self.heading('Notas para volver.','Tu selección, guardada solo en este navegador. Sin cuenta y sin sincronización.','GUARDADOS')
        out+='<div class="saved-tools"><button class="button" type="button" data-export-saved>'+svg('download')+'Exportar selección</button><button class="button" type="button" data-import-saved>'+svg('upload')+'Importar selección</button><input class="sr-only" id="import-saved-file" type="file" accept="application/json,.json" aria-label="Archivo JSON de selección"><button class="button quiet danger" type="button" data-clear-saved>'+svg('trash')+'Vaciar guardados</button></div><div class="archive-meta"><span data-saved-status>Tu selección aparecerá aquí.</span>'+a(r,'blog/','Explorar el archivo '+svg('arrow'),'text-link')+'</div><div class="post-grid" data-saved-grid>'
        out+=''.join(self.card(p,r,True) for p in self.posts)+self.empty('Todavía no guardaste ninguna nota.','Usá el marcador de una entrada y volvé por acá cuando quieras.',False,False)+'</div><noscript><p class="noscript-note">Los guardados necesitan JavaScript y almacenamiento local. El resto del blog sigue siendo legible sin ellos.</p></noscript>'
        self.write_page(r,'Notas guardadas','Guardá notas en tu navegador y exportá tu selección.',out,'more','page-save')

    def monthly(self):
        r='monthly/'
        out=self.breadcrumb(r,'Archivo mensual')+self.heading('Un mes a la vez.','Resúmenes generados automáticamente: las notas y las cifras de cada mes, reunidas en un lugar.','ARCHIVO MENSUAL',str(len(self.months)))+'<div class="month-grid">'
        for key,ps in sorted(self.months.items(),reverse=True):
            y,m=map(int,key.split('-'));metric=self.metric(ps);label=MONTHS[m-1].capitalize()+' de '+str(y)
            out+=a(r,'monthly/'+key+'/',f'<h3>{label}</h3><p>{len(ps)} notas · {number(metric["words"])} palabras · {number(metric["hiking_km"])} km a pie</p><span class="text-link">Abrir el mes {svg("arrow")}</span>','month-card')
        out+='</div>'
        self.write_page(r,'Archivo mensual','Notas y métricas agrupadas por mes automáticamente.',out,'more','page-monthly')
        for key,ps in self.months.items():
            r='monthly/'+key+'/';y,m=map(int,key.split('-'));label=MONTHS[m-1].capitalize()+' de '+str(y);metrics=self.metric(ps)
            out=self.breadcrumb(r,label,('monthly/','Archivo mensual'))+self.heading(label,'Las escenas de un mes, vistas juntas.','RESUMEN AUTOMÁTICO')
            out+='<div class="stats-grid">'+''.join(f'<div class="metric-card"><div class="metric-value">{number(metrics[k])}</div><div class="metric-label">{lab}</div></div>' for k,lab in [('posts','notas'),('words','palabras'),('books','libros leídos'),('hiking_km','km caminados')])+'</div><div class="post-grid">'+''.join(self.card(p,r) for p in ps)+'</div>'
            self.write_page(r,label,'Las notas y métricas del mes de '+label.lower()+'.',out,'more','page-month')

    def today(self):
        r='today/';d=self.config['updated'];ordinal=datetime.strptime(d,'%Y-%m-%d').timetuple().tm_yday
        quote=self.quotes[ordinal%len(self.quotes)];p=self.posts[ordinal%len(self.posts)]
        on=[p for p in self.posts if p['date'][5:]==d[5:]]
        out=self.breadcrumb(r,'Hoy')+self.heading('Un pequeño lugar para hoy.','Una fecha, una frase y una nota del archivo. No hace falta más para empezar.','HOY')+f'<div class="today-layout"><section class="today-card"><div class="today-date" data-today-date>{date_label(d,True)}</div><h2>Una frase para llevar.</h2><blockquote data-daily-quote>{self.esc(quote["text"])}</blockquote><a class="text-link" data-daily-quote-link href="{rel(r,self.postmap[quote["post"]]["url"])}">Volver a la nota {svg("arrow")}</a></section><section class="today-card"><div class="eyebrow">DEL ARCHIVO</div><h2 data-daily-post-title>{self.esc(p["title"])}</h2><p data-daily-post-excerpt>{self.esc(p["excerpt"])}</p><a class="button" data-daily-post-link href="{rel(r,p["url"])}">Leer esta nota {svg("arrow")}</a></section></div><p class="today-note">La fecha usa el horario de Buenos Aires. La sugerencia y la cita rotan cada día en tu navegador, sin contactar a ningún servicio.</p><section class="section" data-on-this-day><div class="section-head"><div><h2>Un día como hoy</h2><p>Notas publicadas en esta misma fecha, en otros años.</p></div></div><div class="post-grid" data-anniversary-posts>'+''.join(self.card(p,r) for p in on)+('</div>' if on else self.empty('Hoy el archivo no tiene un aniversario.','Hay otras historias esperando una lectura.',False,False)+'</div>')+'</section>'
        self.write_page(r,'Hoy','Una cita y una sugerencia diaria del archivo.',out,'more','page-today')

    def blank(self):
        r='blank/'
        out=self.breadcrumb(r,'Una página en blanco')+self.heading('Acá no hace falta publicar.','Un espacio para pensar en privado. El texto se guarda solo en este navegador.','PÁGINA EN BLANCO')+f'''<div class="blank-toolbar"><button type="button" class="button" data-quiet-mode>{svg('leaf')}Modo silencio</button><button type="button" class="button" data-download-note>{svg('download')}Descargar texto</button><button type="button" class="button quiet" data-clear-note>{svg('trash')}Limpiar</button><div class="timer-controls"><label class="sr-only" for="timer-duration">Tiempo de escritura</label><select id="timer-duration"><option value="300">5 minutos</option><option value="600">10 minutos</option><option value="900">15 minutos</option></select><span class="timer-display" data-timer-display aria-live="off">05:00</span><button type="button" class="button" data-timer-toggle>{svg('clock')}Empezar</button><button type="button" class="icon-button" data-timer-reset aria-label="Reiniciar temporizador">{svg('back')}</button></div></div><label class="sr-only" for="blank-text">Tu texto privado</label><textarea class="blank-editor" id="blank-text" data-blank-text placeholder="Una frase alcanza para empezar…" spellcheck="true"></textarea><div class="blank-status"><span data-note-status>Guardado local, no sincronizado.</span><span data-note-words>0 palabras</span></div><noscript><p class="noscript-note">Podés escribir, pero necesitás JavaScript para guardar y descargar el texto.</p></noscript>'''
        self.write_page(r,'Una página en blanco','Un editor privado con guardado local, descarga y temporizador.',out,'more','page-blank')

    def post(self,p,index):
        r=p['url'];out=self.breadcrumb(r,p['title'],('blog/','Blog'))
        out+='<div class="reading-progress" aria-hidden="true"></div><div class="article-heading" style="'+self.style(self.categories[p['category']])+'"><div class="eyebrow">'+self.category_label(p,r)+'</div><h1>'+self.esc(p['title'])+'</h1><p class="dek">'+self.esc(p['excerpt'])+'</p><div class="post-meta"><span>'+svg('calendar')+'<time datetime="'+p['date']+'">'+date_label(p['date'],True)+'</time></span><span>'+svg('clock')+str(p['minutes'])+' min de lectura</span><span>'+svg('pen')+number(p['words'])+' palabras</span></div></div>'
        out+=f'<div class="article-toolbar"><button class="button" type="button" data-save="{p["slug"]}" aria-label="Guardar nota" aria-pressed="false">{svg("bookmark")}<span data-save-label>Guardar nota</span></button><button class="button quiet" type="button" data-copy-page>{svg("copy")}Copiar enlace</button><button class="button quiet" type="button" data-share-page>{svg("share")}Compartir</button></div>'
        if p.get('image'):
            out+=f'<div class="article-image"><img class="lightbox-trigger" src="{rel(r,"assets/images/"+p["image"])}" alt="Ilustración de {"un paisaje patagónico" if p["image"]=="patagonia.jpg" else "una escena de lectura" if p["image"]=="lectura.jpg" else "Buenos Aires"}" data-lightbox tabindex="0" role="button" aria-label="Ampliar la ilustración" width="1376" height="768"></div><p class="image-caption">Ilustración generada para esta demostración · No es una fotografía documental.</p>'
        reader=f'<div class="reader-controls"><span class="control-label">COMODIDAD DE LECTURA</span><div class="reader-size-buttons"><button type="button" data-reader-size="-1" aria-label="Reducir tamaño del texto">A−</button><button type="button" data-reader-size="0" aria-label="Restablecer tamaño del texto">A</button><button type="button" data-reader-size="1" aria-label="Aumentar tamaño del texto">A+</button></div><button class="reader-focus" type="button" data-reader-focus>{svg("book")}Solo lectura</button></div>'
        out+='<div class="article-layout"><aside class="article-toc" aria-label="En esta nota"><div class="toc-title">EN ESTA NOTA</div>'+p['toc']+reader+'</aside><div class="article-prose prose">'
        if p.get('media'):
            m=p['media'];out+=f'<div class="media-factbox"><img src="{rel(r,"assets/covers/"+p["slug"]+".svg")}" alt="Cubierta ilustrada"><div><strong>{self.esc(m["title"])}</strong><p>{self.esc(m["creator"])} · {m["year"]}'+(f' · {m["pages"]} páginas' if 'pages' in m else '')+f'</p><p>{m["status"]} · <span class="stars" aria-label="{m["rating"]} de 5 estrellas">'+('★'*m['rating']+'☆'*(5-m['rating']))+'</span></p></div></div>'
        if p['category']=='hiking':
            out+='<div class="trail-facts">'+''.join(f'<div><strong>{self.esc(val)}</strong><span>{label}</span></div>' for val,label in [(number(p.get('distance_km',0))+' km','distancia ilustrativa'),(str(p.get('elevation_m',0))+' m','desnivel ilustrativo'),(number(p.get('duration_minutes',0)/60)+' h','tiempo ilustrativo'),(p.get('difficulty',''),'dificultad de ejemplo')])+'</div>'
        out+=p['html']+'<div class="post-relations">'
        for tax in ['tags','collections','countries','people','genres','parks','trails']:
            if p.get(tax):out+='<div class="relation-row"><span>'+self.config['taxonomies'][tax]['name']+'</span><div class="relation-chips">'+''.join(a(r,tax+'/'+slug(term)+'/',self.esc(term)) for term in p[tax])+'</div></div>'
        out+='</div><nav class="post-pagination" aria-label="Otras notas">'
        for i,label in [(index+1,'← UNA NOTA ANTERIOR'),(index-1,'UNA NOTA MÁS RECIENTE →')]:
            if 0<=i<len(self.posts):other=self.posts[i];out+=a(r,other['url'],f'<small>{label}</small><strong>{self.esc(other["title"])}</strong>')
            else:out+='<span></span>'
        out+='</nav></div></div>'
        related=sorted([q for q in self.posts if q['slug']!=p['slug']],key=lambda q:-(int(q['category']==p['category'])*5+len(set(p['tags'])&set(q['tags']))))[:3]
        out+='<section class="related-posts"><h2>Quizá quieras seguir por acá.</h2><div class="post-grid">'+''.join(self.card(q,r) for q in related)+'</div></section>'
        self.write_page(r,p['title'],p['excerpt'],out,'blog','page-post',p)

    def error404(self):
        out='<div class="not-found"><div class="error-number" aria-hidden="true">404</div><div class="eyebrow" style="justify-content:center">UN DESVÍO EN EL CAMINO</div><h1>Por acá todavía no hay una nota.</h1><p>Puede que el enlace haya cambiado o que te hayas adelantado al cuaderno. Volvamos a un lugar conocido.</p><div class="button-row">'+a('','','Volver al inicio '+svg('home'),'button primary')+a('','blog/','Explorar el archivo '+svg('arrow'),'button')+'</div></div>'
        self.write_page('','Página no encontrada','El enlace no lleva a una nota del cuaderno.',out,'','page-404',extrahead='<meta name="robots" content="noindex">')
        # The home page is restored by calling home after creating this document.
        self.output.joinpath('404.html').write_text(self.output.joinpath('index.html').read_text(encoding='utf-8'),encoding='utf-8')
        self.generated.append('404.html')

    def write_feed(self,path,posts,title):
        rss=ET.Element('rss',{'version':'2.0'});ch=ET.SubElement(rss,'channel')
        def field(parent,name,value):ET.SubElement(parent,name).text=str(value)
        field(ch,'title',title);field(ch,'link',self.url+'/' if self.url else './');field(ch,'description',self.config['description']);field(ch,'language',self.config['language'])
        if posts:field(ch,'lastBuildDate',format_datetime(datetime.strptime(posts[0]['date'],'%Y-%m-%d').replace(tzinfo=timezone.utc)))
        for p in posts[:50]:
            item=ET.SubElement(ch,'item');field(item,'title',p['title']);field(item,'link',self.absolute(p['url']));field(item,'description',p['excerpt']);field(item,'pubDate',format_datetime(datetime.strptime(p['date'],'%Y-%m-%d').replace(tzinfo=timezone.utc)));field(item,'category',p['category_name']);ET.SubElement(item,'guid',{'isPermaLink':'false'}).text='a-paso-lento:'+p['slug']
        ET.indent(rss,space='  ')
        self.write_file(path,'<?xml version="1.0" encoding="UTF-8"?>\n'+ET.tostring(rss,encoding='unicode')+'\n')

    def exports(self):
        public_posts=[{k:v for k,v in p.items() if k not in ['html','toc','source']} for p in self.posts]
        data={'site':{k:v for k,v in self.config.items() if k not in ['taxonomies']},'posts':public_posts,'pages':self.search_pages,'quotes':self.quotes,'metrics':{'all':self.metric(self.posts),**{y:self.metric(self.terms['years'][y]) for y in self.years}},'taxonomies':{tax:{term:len(ps) for term,ps in terms.items()} for tax,terms in self.terms.items()}}
        self.write_file('assets/js/data.js','window.BLOG_DATA = '+json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')+';\n')
        self.write_file('data.json',json.dumps(data,ensure_ascii=False,indent=2)+'\n')
        self.write_feed('rss.xml',self.posts,self.config['name'])
        for cat,c in self.categories.items():self.write_feed('categories/'+cat+'/rss.xml',self.terms['categories'][cat],self.config['name']+' · '+c['name'])
        feed={'version':'https://jsonfeed.org/version/1.1','title':self.config['name'],'home_page_url':self.url+'/' if self.url else './','feed_url':self.absolute('feed.json'),'description':self.config['description'],'language':self.config['language'],'items':[{'id':p['slug'],'url':self.absolute(p['url']),'title':p['title'],'content_text':p['text'],'summary':p['excerpt'],'date_published':p['date']+'T12:00:00-03:00','tags':p['tags']} for p in self.posts]}
        self.write_file('feed.json',json.dumps(feed,ensure_ascii=False,indent=2)+'\n')
        if self.url:
            urls=ET.Element('urlset',{'xmlns':'http://www.sitemaps.org/schemas/sitemap/0.9'})
            for path in sorted(set(self.generated)):
                if not path.endswith('index.html'):continue
                target=path[:-len('index.html')]
                node=ET.SubElement(urls,'url');ET.SubElement(node,'loc').text=self.absolute(target);ET.SubElement(node,'lastmod').text=self.config['updated']
            ET.indent(urls,space='  ')
            self.write_file('sitemap.xml','<?xml version="1.0" encoding="UTF-8"?>\n'+ET.tostring(urls,encoding='unicode')+'\n')
            self.write_file('robots.txt','User-agent: *\nAllow: /\nSitemap: '+self.absolute('sitemap.xml')+'\n')
        else:
            self.write_file('sitemap.xml','<?xml version="1.0" encoding="UTF-8"?>\n<!-- La publicación automática agrega aquí las URLs reales. -->\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"/>\n')
            self.write_file('robots.txt','User-agent: *\nAllow: /\n')
        self.write_file('.nojekyll','')
        self.write_file('.generated-pages.json',json.dumps(sorted(set(self.generated)),ensure_ascii=False,indent=2)+'\n')

    def build(self):
        self.output.mkdir(parents=True,exist_ok=True)
        # Delete only previously generated files, never content or hand-written assets.
        manifest=self.output/'.generated-pages.json'
        if manifest.exists():
            for f in json.loads(manifest.read_text(encoding='utf-8')):
                dest=(self.output/f).resolve()
                if dest.is_relative_to(self.output) and dest.is_file():dest.unlink()
        create_icons();create_covers(self.posts)
        if self.output!=ROOT:
            shutil.copytree(ROOT/'assets',self.output/'assets',dirs_exist_ok=True)
            shutil.copy2(ROOT/'favicon.svg',self.output/'favicon.svg')
        self.error404();self.home()
        for page in range(1,math.ceil(len(self.posts)/9)+1):self.archive(page)
        self.more();self.static_pages()
        for tax,terms in self.terms.items():
            self.taxonomy_index(tax)
            for term,posts in terms.items():self.taxonomy_detail(tax,term,posts)
        for args in SHELVES[:4]:self.shelf(*args)
        self.favourite_quotes();self.numbers();self.feeds();self.save();self.monthly();self.today();self.blank()
        for i,p in enumerate(self.posts):self.post(p,i)
        self.exports()
        html_count=len(set(path for path in self.generated if path.endswith('.html')))
        print(f'{html_count} páginas HTML · {len(self.posts)} notas · {len(self.categories)} categorías')
        print(f'Salida: {self.output}')
        print('URL: '+(self.url or 'sin configurar; GitHub Actions la resuelve al publicar'))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url',default=None,help='URL pública, incluyendo la carpeta del repositorio, sin barra final.')
    parser.add_argument('--output',default=str(ROOT),help='Carpeta de salida; por defecto, la raíz del proyecto.')
    args=parser.parse_args()
    Site(args.output,args.url).build()
