#!/usr/bin/env python3
"""Crea una vista previa autónoma, navegable y sin recursos de red. No es el sitio de publicación."""
from pathlib import Path
from urllib.parse import urlsplit, unquote
import argparse, base64, gzip, json, mimetypes, posixpath, re

ROOT=Path(__file__).resolve().parents[1]


def safe_json(value):
    return json.dumps(value,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')


def make(site,output):
    site=Path(site).resolve();output=Path(output).resolve()
    assets={}
    for folder in ['images','covers','icons','fonts']:
        for file in (site/'assets'/folder).glob('*'):
            if not file.is_file() or file.suffix=='.txt':continue
            mime='font/ttf' if file.suffix=='.ttf' else mimetypes.guess_type(file.name)[0] or 'application/octet-stream'
            assets[file.relative_to(site).as_posix()]='data:'+mime+';base64,'+base64.b64encode(file.read_bytes()).decode()
    def css_inline(file):
        css=file.read_text(encoding='utf-8')
        def replace(m):
            ref=m.group(1).strip('"\'')
            if ref.startswith(('data:','http:','https:','#')):return m.group(0)
            key=(file.parent/ref).resolve().relative_to(site).as_posix()
            return 'url("'+assets[key]+'")'
        return re.sub(r'url\(([^)]+)\)',replace,css)
    css=css_inline(site/'assets/css/base.css')+'\n'+css_inline(site/'assets/css/site.css')
    def convert_body(body,route):
        def replace(m):
            attr,ref=m[1],m[2]
            if not ref or ref.startswith(('http:','https:','mailto:','tel:','data:','blob:','#')):return m[0]
            parsed=urlsplit(ref);path=posixpath.normpath(posixpath.join(route,unquote(parsed.path)))
            if path=='.':path=''
            if parsed.path.endswith('/') and path:path+='/'
            if attr=='src' and path in assets:return 'data-asset="'+path+'"'
            return attr+'="https://preview.local/'+path+('?' + parsed.query if parsed.query else '')+('#'+parsed.fragment if parsed.fragment else '')+'"'
        return re.sub(r'(href|src)="([^"]*)"',replace,body)
    pages={}
    manifest=json.loads((site/'.generated-pages.json').read_text(encoding='utf-8'))
    for path in manifest:
        if not path.endswith('.html'):continue
        doc=(site/path).read_text(encoding='utf-8');body=re.search(r'<body([^>]*)>(.*)</body>',doc,re.S)
        attrs=body[1];route=re.search(r'data-route="([^"]*)"',attrs)[1]
        if path=='404.html':route='404.html'
        post=re.search(r'data-post="([^"]*)"',attrs);cls=re.search(r'class="([^"]*)"',attrs)
        title=re.search(r'<title>(.*?)</title>',doc,re.S)[1]
        pages[route]={'body':convert_body(body[2],'' if path=='404.html' else route),'className':cls[1] if cls else '', 'post':post[1] if post else '', 'title':title}
    files={path:(site/path).read_text(encoding='utf-8') for path in manifest if path.endswith(('rss.xml','feed.json','data.json'))}
    packed=base64.b64encode(gzip.compress(safe_json(pages).encode(),compresslevel=9,mtime=0)).decode()
    data=(site/'assets/js/data.js').read_text(encoding='utf-8');app=(site/'assets/js/app.js').read_text(encoding='utf-8')
    visible_assets={key:value for key,value in assets.items() if not key.startswith('assets/fonts/') and not key.startswith('assets/icons/')}
    favicon='data:image/svg+xml;base64,'+base64.b64encode((site/'favicon.svg').read_bytes()).decode()
    router=r'''
(() => {
  const encoded = PACKED_PAGES;
  const decode = async () => {
    if (!('DecompressionStream' in window)) throw new Error('Tu navegador necesita soporte moderno para explorar esta vista previa. El sitio de publicación no tiene este requisito.');
    const bytes = Uint8Array.from(atob(encoded), c => c.charCodeAt(0));
    const text = await new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'))).text();
    return JSON.parse(text);
  };
  const pagesPromise = decode();
  const hydrate = () => document.querySelectorAll('img[data-asset]').forEach(img => {img.src=window.PREVIEW_ASSETS[img.dataset.asset];});
  hydrate();
  function fileDialog(path) {
    const content=window.PREVIEW_FILES[path];if(!content)return;
    const dialog=document.createElement('dialog');dialog.setAttribute('aria-label','Archivo del sitio');
    dialog.innerHTML='<div class="dialog-head"><h2>Archivo del sitio</h2><button class="icon-button" data-close-dialog aria-label="Cerrar">×</button></div><div style="padding:24px"><p style="font-size:12px;color:var(--muted)">Vista local de <b></b>. El RSS publicado usará la URL real de tu blog.</p><textarea readonly style="width:100%;min-height:300px;padding:14px;border:1px solid var(--line);background:var(--soft);border-radius:6px;font:11px/1.8 monospace"></textarea><div class="button-row" style="margin-top:18px"><button class="button" data-preview-download>Descargar archivo</button><button class="button" data-copy-text>Copiar contenido</button></div></div>';
    dialog.querySelector('b').textContent=path;dialog.querySelector('textarea').value=content;dialog.querySelector('[data-copy-text]').dataset.copyText=content;
    dialog.querySelector('[data-preview-download]').onclick=()=>{const href=URL.createObjectURL(new Blob([content],{type:path.endsWith('.xml')?'application/rss+xml':'application/json'}));const link=document.createElement('a');link.href=href;link.download=path.split('/').pop();document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(href),1500);};
    dialog.addEventListener('close',()=>{document.body.classList.remove('modal-open');dialog.remove();});
    document.body.append(dialog);dialog.showModal();document.body.classList.add('modal-open');
  }
  async function render() {
    try {
      const pages=await pagesPromise;
      const hash=location.hash.startsWith('#/')?location.hash.slice(1):'/';
      const dest=new URL(hash,window.PREVIEW_ROOT);let route=decodeURIComponent(dest.pathname.slice(1));
      if(route.endsWith('index.html'))route=route.slice(0,-10);
      if(window.PREVIEW_FILES[route]){fileDialog(route);return;}
      const page=pages[route]||pages['404.html'];
      window.flushBlogNote?.();
      window.PREVIEW_QUERY=dest.search;
      document.body.className=page.className;document.body.innerHTML=page.body;document.body.dataset.base='./';document.body.dataset.route=route;
      if(page.post)document.body.dataset.post=page.post;else delete document.body.dataset.post;
      document.title=page.title.replace(/&amp;/g,'&');hydrate();window.initBlog?.();window.scrollTo(0,0);
      document.getElementById('main')?.focus({preventScroll:true});
      if(dest.hash){const target=document.getElementById(decodeURIComponent(dest.hash.slice(1)));target?.scrollIntoView();}
    }catch(error){console.error(error);const hint=document.createElement('p');hint.className='noscript-note';hint.textContent=error.message;document.getElementById('main').prepend(hint);}
  }
  document.addEventListener('click',event=>{
    if(event.defaultPrevented||event.button!==0||event.ctrlKey||event.metaKey||event.shiftKey||event.altKey)return;
    const link=event.target.closest('a[href]');if(!link)return;
    const raw=link.getAttribute('href');
    if(raw.startsWith('#')&&!raw.startsWith('#/')){const target=document.getElementById(decodeURIComponent(raw.slice(1)));if(target){event.preventDefault();target.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion:reduce)').matches?'auto':'smooth'});if(target.hasAttribute('tabindex'))target.focus({preventScroll:true});}return;}
    let dest;try{dest=new URL(link.href);}catch(_){return;}
    if(dest.origin!==new URL(window.PREVIEW_ROOT).origin)return;
    event.preventDefault();const route=decodeURIComponent(dest.pathname.slice(1));
    if(window.PREVIEW_FILES[route]){fileDialog(route);return;}
    const next='#/'+route+dest.search+(dest.hash?dest.hash:'');
    if(location.hash===next)render();else location.hash=next.slice(1);
  });
  window.addEventListener('hashchange',()=>{if(location.hash.startsWith('#/'))render();});
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>render(),{once:true});else render();
})();
'''.replace('PACKED_PAGES',safe_json(packed))
    payload='<script>window.PREVIEW_ROOT="https://preview.local/";window.PREVIEW_ASSETS='+safe_json(visible_assets)+';window.PREVIEW_FILES='+safe_json(files)+';'+data+'</script>'
    html='<!doctype html><html lang="es-AR" data-theme="light"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>a paso lento · Vista previa</title><link rel="icon" href="'+favicon+'"><style>'+css+'</style></head><body id="top" class="page-home" data-base="./" data-route="">'+pages['']['body']+payload+'<script>'+app+'</script><script>'+router+'</script></body></html>'
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(html,encoding='utf-8')
    print(f'Vista previa: {output} · {len(pages)} páginas · {output.stat().st_size/1024/1024:.2f} MB')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--site',default=str(ROOT));parser.add_argument('--output',default=str(ROOT.parent/'Vista-previa.html'));args=parser.parse_args();make(args.site,args.output)
