#!/usr/bin/env python3
"""Verifica enlaces y recursos locales, feeds y métricas sin dependencias externas."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
from collections import Counter
import argparse, json, re, sys, xml.etree.ElementTree as ET

class Document(HTMLParser):
    def __init__(self,text):
        super().__init__();self.refs=[];self.ids=set();self.duplicates=[];self.h1=0;self.title=False;self.lang=False
        self.feed(text)
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=='html':self.lang=bool(attrs.get('lang'))
        if tag=='h1':self.h1+=1
        if tag=='title':self.title=True
        if 'id' in attrs:
            if attrs['id'] in self.ids:self.duplicates.append(attrs['id'])
            self.ids.add(attrs['id'])
        for key in ['href','src']:
            if key in attrs:self.refs.append((tag,key,attrs[key]))


def verify(folder):
    root=Path(folder).resolve();errors=[];docs={};references=0
    data=json.loads((root/'data.json').read_text(encoding='utf-8'))
    base=data['site'].get('site_url','').rstrip('/')
    for file in sorted(root.rglob('*.html')):
        if '_site' in file.relative_to(root).parts or '__pycache__' in file.parts:continue
        doc=Document(file.read_text(encoding='utf-8'));docs[file]=doc
        if not doc.lang:errors.append(f'{file.relative_to(root)}: falta idioma')
        if not doc.title:errors.append(f'{file.relative_to(root)}: falta título')
        if doc.h1!=1:errors.append(f'{file.relative_to(root)}: {doc.h1} encabezados h1')
        for ident in doc.duplicates:errors.append(f'{file.relative_to(root)}: id repetido {ident}')
    for file,doc in docs.items():
        for tag,key,ref in doc.refs:
            if not ref or ref.startswith(('mailto:','tel:','data:','blob:','javascript:')):continue
            parsed=urlsplit(ref)
            if parsed.scheme or parsed.netloc:
                if not base or not ref.startswith(base+'/'):continue
                local=urlsplit(ref[len(base)+1:])
                target=root/unquote(local.path);fragment=unquote(local.fragment)
            else:
                if parsed.path.startswith('/'):
                    target=root/unquote(parsed.path.lstrip('/'))
                else:target=(file.parent/unquote(parsed.path)).resolve() if parsed.path else file
                fragment=unquote(parsed.fragment)
            if not target.is_relative_to(root):errors.append(f'{file.relative_to(root)}: sale del sitio {ref}');continue
            if target.is_dir():target=target/'index.html'
            references+=1
            if not target.is_file():errors.append(f'{file.relative_to(root)}: recurso ausente {ref}')
            elif fragment and target.suffix=='.html':
                other=docs.get(target)
                if other and fragment not in other.ids:errors.append(f'{file.relative_to(root)}: ancla ausente {ref}')
    for css in (root/'assets/css').glob('*.css'):
        for match in re.finditer(r'url\([\'"]?([^\)\'"\s]+)',css.read_text(encoding='utf-8')):
            ref=match[1]
            if ref.startswith(('data:','http:','https:','#')):continue
            references+=1
            if not (css.parent/ref).resolve().is_file():errors.append(f'{css.relative_to(root)}: recurso ausente {ref}')
    feeds=list(root.rglob('rss.xml'))
    for feed in feeds:
        if '_site' in feed.relative_to(root).parts:continue
        try:
            tree=ET.parse(feed);items=tree.findall('.//item')
            # RSS admite feeds vacíos, por ejemplo para una categoría aún sin notas.
            if base:
                for item in items:
                    if not item.findtext('link','').startswith(base+'/'):errors.append(f'{feed.relative_to(root)}: URL del feed fuera de la base')
        except ET.ParseError as exc:errors.append(f'{feed.relative_to(root)}: XML inválido {exc}')
    for path in ['sitemap.xml','feed.json']:
        try:
            if path.endswith('.xml'):ET.parse(root/path)
            else:json.loads((root/path).read_text(encoding='utf-8'))
        except Exception as exc:errors.append(f'{path}: {exc}')
    posts=data['posts'];metrics=data['metrics']['all'];cats=Counter(p['category'] for p in posts)
    expected={'posts':len(posts),'words':sum(p['words'] for p in posts),'days':len({p['date'] for p in posts}),
              'books':sum(p['category']=='books' and p.get('media',{}).get('status')=='Leído' for p in posts),
              'pages':sum(p.get('media',{}).get('pages',0) for p in posts if p['category']=='books' and p.get('media',{}).get('status')=='Leído'),
              'hikes':sum(p['category']=='hiking' for p in posts),'hiking_km':round(sum(p.get('distance_km',0) for p in posts if p['category']=='hiking'),1),
              'distance':round(sum(p.get('distance_km',0) for p in posts),1)}
    for key,val in expected.items():
        if metrics[key]!=val:errors.append(f'métricas: {key} no coincide')
    for cat,count in data['taxonomies']['categories'].items():
        if cats[cat]!=count:errors.append(f'categoría {cat}: contador incorrecto')
    for p in posts:
        if not (root/p['url']/'index.html').exists():errors.append(f'nota ausente: {p["slug"]}')
    if errors:
        print('\n'.join(errors));print(f'ERROR: {len(errors)} problemas.');return False
    print(f'OK: {len(docs)} HTML, {references} referencias locales, {len([f for f in feeds if '_site' not in f.relative_to(root).parts])} feeds RSS y métricas consistentes.')
    return True

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('folder',nargs='?',default=str(Path(__file__).resolve().parents[1]));args=parser.parse_args()
    sys.exit(0 if verify(args.folder) else 1)
