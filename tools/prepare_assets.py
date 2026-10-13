"""Crea las ilustraciones originales de la biblioteca y los iconos locales."""
from pathlib import Path
import json, html, re, textwrap

ROOT = Path(__file__).resolve().parents[1]
ICONS = {
 'home':'<path d="m3 10 9-7 9 7v10a1 1 0 0 1-1 1h-6v-7h-4v7H4a1 1 0 0 1-1-1z"/>',
 'book':'<path d="M12 5c-3-2-6-2-10-1v15c4-1 7-1 10 1 3-2 6-2 10-1V4c-4-1-7-1-10 1zM12 5v15"/>',
 'mountain':'<path d="m2 20 8-16 5 10 3-5 4 11zM7 10l3 2 3-2"/>',
 'pen':'<path d="m15 4 5 5M3 21l5-1L21 7a2 2 0 0 0-5-5L3 15zM3 15l5 5"/>',
 'music':'<path d="M9 18V5l12-2v13M9 8l12-2"/><ellipse cx="6" cy="18" rx="3" ry="3"/><ellipse cx="18" cy="16" rx="3" ry="3"/>',
 'film':'<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M7 3v18M17 3v18M3 8h4M3 16h4M17 8h4M17 16h4M7 12h10"/>',
 'tv':'<rect x="2" y="7" width="20" height="14" rx="3"/><path d="m7 2 5 5 5-5"/>',
 'code':'<path d="m7 7-5 5 5 5m10-10 5 5-5 5M14 3l-4 18"/>',
 'compass':'<circle cx="12" cy="12" r="9"/><path d="m16 8-3 5-5 3 3-5z"/>',
 'bulb':'<path d="M9 18h6M9 21h6M8 15a7 7 0 1 1 8 0l-1 3H9z"/>',
 'leaf':'<path d="M20 3C11 2 3 8 5 15c2 8 16 5 15-12zM4 21l11-12"/>',
 'bike':'<circle cx="5" cy="17" r="4"/><circle cx="19" cy="17" r="4"/><path d="m5 17 6-9 5 9H5M9 5h4M11 8 9 5M16 4h3l3 5M16 17 19 4"/>',
 'camera':'<path d="M3 7h4l2-3h6l2 3h4v14H3z"/><circle cx="12" cy="14" r="4"/>',
 'laptop':'<rect x="4" y="3" width="16" height="13" rx="2"/><path d="M2 20h20M8 20l1-4M16 20l-1-4"/>',
 'heart':'<path d="M20 4a5 5 0 0 0-8 2 5 5 0 0 0-8-2c-6 5 1 11 8 17 7-6 14-12 8-17z"/>',
 'coffee':'<path d="M3 4h14v10a6 6 0 0 1-12 0V4M17 5h2a3 3 0 0 1 0 6h-2M2 21h18"/>',
 'calendar':'<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M7 2v6M17 2v6M3 11h18M7 15h2M13 15h2"/>',
 'search':'<circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/>',
 'sun':'<circle cx="12" cy="12" r="4"/><path d="M12 1v2M12 21v2M1 12h2M21 12h2M4 4l2 2M18 18l2 2M4 20l2-2M18 6l2-2"/>',
 'moon':'<path d="M21 13A9 9 0 1 1 11 3a7 7 0 0 0 10 10z"/>',
 'arrow':'<path d="M4 12h16m-6-6 6 6-6 6"/>',
 'arrow-up':'<path d="M6 18 18 6M6 6h12v12"/>',
 'back':'<path d="M20 12H4m6-6-6 6 6 6"/>',
 'bookmark':'<path d="M6 3h12v18l-6-4-6 4z"/>',
 'check':'<path d="m4 12 5 5L20 6"/>',
 'x':'<path d="m6 6 12 12M6 18 18 6"/>',
 'rss':'<circle cx="5" cy="19" r="1"/><path d="M4 11a9 9 0 0 1 9 9M4 4a16 16 0 0 1 16 16"/>',
 'mail':'<rect x="2" y="4" width="20" height="16" rx="2"/><path d="m2 5 10 8L22 5"/>',
 'chart':'<path d="M4 3v18h18M8 17v-5M13 17V8M18 17V4"/>',
 'grid':'<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
 'list':'<path d="M8 6h13M8 12h13M8 18h13M3 6h1M3 12h1M3 18h1"/>',
 'clock':'<circle cx="12" cy="12" r="9"/><path d="M12 6v6l4 2"/>',
 'pin':'<path d="M20 10c0 6-8 12-8 12S4 16 4 10a8 8 0 1 1 16 0z"/><circle cx="12" cy="10" r="2.5"/>',
 'tag':'<path d="M3 3h8l10 10-8 8L3 11z"/><circle cx="7.5" cy="7.5" r="1"/>',
 'copy':'<rect x="8" y="8" width="13" height="13" rx="2"/><path d="M16 8V3H3v13h5"/>',
 'share':'<circle cx="18" cy="4" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="20" r="3"/><path d="m9 10 6-4M9 14l6 4"/>',
 'download':'<path d="M12 3v12m-5-5 5 5 5-5M3 16v5h18v-5"/>',
 'upload':'<path d="M12 16V3m-5 5 5-5 5 5M3 16v5h18v-5"/>',
 'trash':'<path d="M3 6h18M9 6V3h6v3M5 6l1 15h12l1-15M10 10v6M14 10v6"/>',
 'globe':'<circle cx="12" cy="12" r="9"/><ellipse cx="12" cy="12" rx="4" ry="9"/><path d="M3 12h18"/>',
 'star':'<path d="m12 2 3 6 7 1-5 5 1 7-6-3-6 3 1-7-5-5 7-1z"/>',
 'layers':'<path d="m12 3 10 6-10 6L2 9zm-10 11 10 6 10-6M2 18l10 6 10-6"/>',
 'plus':'<path d="M12 4v16M4 12h16"/>',
 'minus':'<path d="M4 12h16"/>',
 'info':'<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7v1"/>',
 'key':'<circle cx="8" cy="8" r="5"/><path d="m11.5 11.5 9 9M16 16l3-3M19 19l3-3"/>',
 'spark':'<path d="m12 3 2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5z"/>',
 'path':'<path d="M4 21c-2-5 15-5 14-9s-12-2-9-6c1-1 5-2 7-3"/>',
}

def svg(name, cls='ui-icon'):
    return f'<svg xmlns="http://www.w3.org/2000/svg" class="{cls}" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONS.get(name,ICONS["leaf"])}</svg>'


def create_icons():
    mapping={'books':'book','christianity':'leaf','gems':'camera','gem':'camera','general':'pen','hiking':'mountain','remember':'heart','monthly-update':'calendar','development':'code','projects':'bulb','trips':'compass','keyboard':'pen','mac':'laptop','movies':'film','tv-series':'tv','music':'music','biking':'bike','caution':'info','important':'spark','info':'info','idea':'bulb','warning':'info','home':'home','nav-first':'back','nav-last':'arrow','nav-next':'arrow','nav-previous':'back'}
    for name in ICONS:
        (ROOT/'assets/icons'/f'{name}.svg').write_text(svg(name),encoding='utf-8')
    for name,target in mapping.items():
        (ROOT/'assets/icons'/f'{name}.svg').write_text(svg(target),encoding='utf-8')
    (ROOT/'assets/icons/book.svg').write_text(svg('book'),encoding='utf-8')
    (ROOT/'favicon.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="18" fill="#edc76b"/><path d="M19 53c-13-12 33-10 28-23S9 30 23 17c3-3 14-4 19-6" fill="none" stroke="#332d24" stroke-width="3.4" stroke-linecap="round"/></svg>',encoding='utf-8')


def create_covers(posts):
    for idx,p in enumerate(posts):
        if 'media' not in p: continue
        m=p['media']; name=m['title']; author=m['creator']
        bg=m.get('color','#344c45'); ink=m.get('ink','#f4ecd9')
        lines=textwrap.wrap(name,18)
        tx=''.join(f'<tspan x="32" dy="{0 if i==0 else 30}">{html.escape(line)}</tspan>' for i,line in enumerate(lines))
        circles=''.join(f'<circle cx="{150+40*((i%3)-1)}" cy="{250+18*i}" r="{95-14*i}" fill="none" stroke="{ink}" stroke-opacity="{0.5-i*.05}" stroke-width="1.3"/>' for i in range(5))
        if p['category']=='music':
            art=f'<circle cx="150" cy="263" r="108" fill="{ink}" opacity=".06"/>'+''.join(f'<circle cx="150" cy="263" r="{r}" fill="none" stroke="{ink}" stroke-opacity=".25"/>' for r in [96,84,72,60,48])+f'<circle cx="150" cy="263" r="30" fill="{ink}" opacity=".8"/><circle cx="150" cy="263" r="5" fill="{bg}"/>'
        elif p['category'] in ['movies','tvseries']:
            art=f'<path d="M0 315 95 156l72 85 59-90 74 164v85H0z" fill="{ink}" opacity=".11"/><circle cx="195" cy="190" r="50" fill="{ink}" opacity=".15"/><path d="m-15 340 117-124 62 88 73-62 80 98" fill="none" stroke="{ink}" opacity=".45" stroke-width="2"/>'
        else:art=circles
        y=62
        out=f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 450" role="img" aria-label="Cubierta ilustrada: {html.escape(name,quote=True)}"><rect width="300" height="450" fill="{bg}"/><rect x="10" width="2" height="450" fill="black" opacity=".15"/><text x="32" y="30" font-family="Arial,sans-serif" font-size="8" fill="{ink}" letter-spacing="3">BIBLIOTECA PERSONAL</text><text x="32" y="{y}" font-family="Georgia,serif" font-size="25" fill="{ink}">{tx}</text>{art}<path d="M32 398h236" stroke="{ink}" opacity=".4"/><text x="32" y="424" font-family="Arial,sans-serif" font-size="12" fill="{ink}">{html.escape(author[:34])}</text><text x="269" y="382" font-family="Arial,sans-serif" font-size="9" fill="{ink}" transform="rotate(-90 269 382)" letter-spacing="2">A PASO LENTO · {m.get('year','')}</text></svg>'''
        (ROOT/'assets/covers'/f'{p["slug"]}.svg').write_text(out,encoding='utf-8')

if __name__=='__main__':
    create_icons()
    path=ROOT/'content/posts.json'
    if path.exists():create_covers(json.loads(path.read_text(encoding='utf-8')))
