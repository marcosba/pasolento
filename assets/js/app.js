/* Mejora progresiva. El contenido y la navegación no dependen de este archivo. */
(() => {
  'use strict';
  const D = window.BLOG_DATA;
  if (!D) return;
  const postsById = new Map(D.posts.map(p => [p.slug, p]));
  const categories = new Map(D.site.categories.map(c => [c.slug, c]));
  const memory = Object.create(null);
  let canStore = true, storageWarned = false, toastTimeout, noteTimeout, timerInterval, dailyInterval;
  const $ = (s, root = document) => root.querySelector(s);
  const $$ = (s, root = document) => [...root.querySelectorAll(s)];
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const normal = s => String(s ?? '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  const searchMeta = p => [p.category_name,p.media?.title,p.media?.creator,...(p.tags||[]),...(p.people||[]),...(p.countries||[]),...(p.genres||[]),...(p.collections||[]),...(p.parks||[]),...(p.trails||[]),(p.date||'').slice(0,4)].join(' ');
  const paths = {
    bookmark:'<path d="M6 3h12v18l-6-4-6 4z"/>', check:'<path d="m4 12 5 5L20 6"/>',
    arrow:'<path d="M4 12h16m-6-6 6 6-6 6"/>', back:'<path d="M20 12H4m6-6-6 6 6 6"/>',
    search:'<circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/>',
    sun:'<circle cx="12" cy="12" r="4"/><path d="M12 1v2M12 21v2M1 12h2M21 12h2M4 4l2 2M18 18l2 2M4 20l2-2M18 6l2-2"/>',
    moon:'<path d="M21 13A9 9 0 1 1 11 3a7 7 0 0 0 10 10z"/>',
    copy:'<rect x="8" y="8" width="13" height="13" rx="2"/><path d="M16 8V3H3v13h5"/>',
    clock:'<circle cx="12" cy="12" r="9"/><path d="M12 6v6l4 2"/>',
    book:'<path d="M12 5c-3-2-6-2-10-1v15c4-1 7-1 10 1 3-2 6-2 10-1V4c-4-1-7-1-10 1zM12 5v15"/>',
    mountain:'<path d="m2 20 8-16 5 10 3-5 4 11zM7 10l3 2 3-2"/>',
    pen:'<path d="m15 4 5 5M3 21l5-1L21 7a2 2 0 0 0-5-5L3 15zM3 15l5 5"/>',
    music:'<path d="M9 18V5l12-2v13M9 8l12-2"/><ellipse cx="6" cy="18" rx="3" ry="3"/><ellipse cx="18" cy="16" rx="3" ry="3"/>',
    film:'<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M7 3v18M17 3v18M3 8h4M3 16h4M17 8h4M17 16h4M7 12h10"/>',
    leaf:'<path d="M20 3C11 2 3 8 5 15c2 8 16 5 15-12zM4 21l11-12"/>',
    x:'<path d="m6 6 12 12M6 18 18 6"/>'
  };
  const icon = name => `<svg class="ui-icon" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths[name] || paths.leaf}</svg>`;
  const rootURL = () => new URL(window.PREVIEW_ROOT || document.body.dataset.base || './', document.baseURI);
  const url = path => new URL(path, rootURL()).href;
  const asset = path => window.PREVIEW_ASSETS?.[path] || url(path);
  const formatNumber = n => new Intl.NumberFormat('es-AR',{maximumFractionDigits:1}).format(n);
  const formatDate = date => new Intl.DateTimeFormat('es-AR',{day:'numeric',month:'short',year:'numeric',timeZone:'UTC'}).format(new Date(date+'T12:00:00Z'));
  const currentURL = () => window.PREVIEW_ROOT ? location.href.split('#')[0]+'#/'+(document.body.dataset.route || '') : url(document.body.dataset.route || '');

  try { localStorage.setItem('paso-test','1'); localStorage.removeItem('paso-test'); } catch (_) { canStore = false; }
  function get(key, fallback = null) {
    if (canStore) { try { return localStorage.getItem(key) ?? fallback; } catch (_) { canStore = false; } }
    return memory[key] ?? fallback;
  }
  function set(key, value, announce = true) {
    memory[key] = value;
    if (canStore) { try { localStorage.setItem(key, value); return true; } catch (_) { canStore = false; } }
    if (announce && !storageWarned) { storageWarned = true; toast('El almacenamiento está bloqueado. Los cambios durarán esta visita.'); }
    return false;
  }
  function remove(key) { delete memory[key]; if (canStore) { try { localStorage.removeItem(key); } catch (_) { canStore = false; } } }
  function readSaved() {
    try { const ids = JSON.parse(get('paso-saved','[]')); return new Set(Array.isArray(ids) ? ids.filter(id => postsById.has(id)) : []); }
    catch (_) { return new Set(); }
  }
  let saved = readSaved();
  function toast(text) {
    const el = $('#toast'); if (!el) return;
    clearTimeout(toastTimeout); el.textContent = text; el.classList.add('visible');
    toastTimeout = setTimeout(() => el.classList.remove('visible'), 4300);
  }
  function openDialog(el) {
    if (!el || el.open) return;
    if (typeof el.showModal === 'function') el.showModal(); else el.setAttribute('open','');
    document.body.classList.add('modal-open');
  }
  function closeDialog(el) { if (el?.open) { el.close(); document.body.classList.remove('modal-open'); } }
  function confirmAction(title, message) {
    return new Promise(resolve => {
      const dialog = document.createElement('dialog');
      dialog.setAttribute('aria-label',title);
      dialog.innerHTML = `<div class="dialog-head"><h2>${esc(title)}</h2></div><div style="padding:24px"><p style="font-size:14px;color:var(--muted);margin-bottom:23px">${esc(message)}</p><div class="button-row"><button class="button" data-confirm-no>Cancelar</button><button class="button primary" data-confirm-yes>Confirmar</button></div></div>`;
      document.body.append(dialog);
      let finished = false;
      const done = result => { if (finished) return; finished = true; closeDialog(dialog); dialog.remove(); resolve(result); };
      $('[data-confirm-no]',dialog).onclick = () => done(false);
      $('[data-confirm-yes]',dialog).onclick = () => done(true);
      dialog.addEventListener('cancel', e => { e.preventDefault(); done(false); });
      openDialog(dialog); $('[data-confirm-no]',dialog).focus();
    });
  }
  async function copy(text, message = 'Copiado al portapapeles.') {
    try {
      if (navigator.clipboard?.writeText && window.isSecureContext) await navigator.clipboard.writeText(text);
      else {
        const input = document.createElement('textarea'); input.value = text;
        input.style.cssText = 'position:fixed;left:-9999px;top:0'; document.body.append(input); input.select();
        const ok = document.execCommand('copy'); input.remove(); if (!ok) throw new Error('clipboard');
      }
      toast(message);
    } catch (_) {
      const dialog = document.createElement('dialog'); dialog.setAttribute('aria-label','Copiar texto');
      dialog.innerHTML = `<div class="dialog-head"><h2>Copiar texto</h2><button class="icon-button" data-close-dialog aria-label="Cerrar">${icon('x')}</button></div><div style="padding:24px"><p style="font-size:12px;color:var(--muted)">Tu navegador no habilitó el portapapeles. Seleccioná el texto y copialo manualmente.</p><textarea style="width:100%;min-height:120px;padding:12px;border:1px solid var(--line);border-radius:6px" readonly></textarea></div>`;
      $('textarea',dialog).value = text; document.body.append(dialog);
      dialog.addEventListener('close',() => { document.body.classList.remove('modal-open'); dialog.remove(); });
      openDialog(dialog); $('textarea',dialog).select();
    }
  }
  function download(name, contents, type = 'text/plain;charset=utf-8') {
    const blob = new Blob([contents],{type}); const href = URL.createObjectURL(blob);
    const link = document.createElement('a'); link.href = href; link.download = name; document.body.append(link); link.click(); link.remove();
    setTimeout(() => URL.revokeObjectURL(href),1500);
  }

  function updateTheme() {
    const dark = document.documentElement.dataset.theme === 'dark';
    $$('[data-theme-toggle]').forEach(button => { button.innerHTML = icon(dark ? 'moon':'sun'); button.setAttribute('aria-label',dark ? 'Activar tema claro':'Activar tema oscuro'); button.title = dark ? 'Tema oscuro · cambiar a claro':'Tema claro · cambiar a oscuro'; });
    $('meta[name="theme-color"]')?.setAttribute('content',dark ? '#1d211d':'#faf9f6');
  }
  function syncSaved() {
    $$('[data-save]').forEach(button => {
      const yes = saved.has(button.dataset.save); button.classList.toggle('saved',yes); button.setAttribute('aria-pressed',String(yes));
      const title = postsById.get(button.dataset.save)?.title || 'nota'; button.setAttribute('aria-label',(yes?'Quitar de guardados: ':'Guardar: ')+title); button.title = yes ? 'Quitar de guardados':'Guardar nota';
      const label = $('[data-save-label]',button); if (label) label.textContent = yes ? 'Nota guardada':'Guardar nota';
    });
    $$('[data-save-count]').forEach(el => { el.textContent = saved.size; el.hidden = !saved.size; });
    const grid = $('[data-saved-grid]');
    if (grid) {
      $$('[data-card]',grid).forEach(card => card.hidden = !saved.has(card.dataset.card));
      $('[data-empty]',grid).hidden = saved.size > 0;
      $('[data-saved-status]').textContent = saved.size ? `${saved.size} ${saved.size===1?'nota guardada':'notas guardadas'} en este navegador.` : 'Podés empezar desde cualquier entrada del archivo.';
    }
  }
  function persistSaved() { set('paso-saved',JSON.stringify([...saved])); syncSaved(); }

  function renderSearch(q = '') {
    const words = normal(q.trim()).split(/\s+/).filter(Boolean);
    const items = [...D.posts,...D.pages];
    const score = item => {
      const title = normal(item.title), tags = normal(searchMeta(item)), description = normal(item.excerpt), full = normal(item.text);
      if (!words.every(w => (title+' '+tags+' '+description+' '+full).includes(w))) return 0;
      return words.reduce((n,w) => n+(title.includes(w)?14:0)+(tags.includes(w)?7:0)+(description.includes(w)?4:0)+(full.includes(w)?1:0),0);
    };
    const matches = words.length ? items.map(item=>({item,score:score(item)})).filter(x=>x.score>0).sort((a,b)=>b.score-a.score||String(b.item.date).localeCompare(String(a.item.date))).map(x=>x.item) : D.posts.slice(0,8);
    const results = $('#search-results'); if (!results) return;
    results.innerHTML = matches.slice(0,18).map(item=>`<a class="search-result" href="${esc(url(item.url))}"><span class="result-category">${esc(item.category_name)}${item.date?' · '+esc(formatDate(item.date)):''}</span><strong>${esc(item.title)}</strong><small>${esc(item.excerpt)}</small></a>`).join('') || `<div class="empty-state" style="border:0"><h3>No encontré esa combinación.</h3><p>Probá con «libro», «Patagonia» o «atención».</p></div>`;
    $('#search-status').textContent = words.length ? `${matches.length} ${matches.length===1?'resultado':'resultados'}${matches.length>18?' · mostrando los primeros 18':''}` : 'Ocho notas recientes para empezar.';
  }
  function openSearch() { const dialog = $('#search-dialog'); renderSearch($('#global-search')?.value||''); openDialog(dialog); setTimeout(()=>$('#global-search')?.focus(),10); }

  function matchesPost(p,q) { const words=normal(q.trim()).split(/\s+/).filter(Boolean); const haystack=normal([p.title,p.excerpt,p.text,searchMeta(p)].join(' ')); return words.every(w=>haystack.includes(w)); }
  function writeQuery(state, initialPage = 1) {
    if (window.PREVIEW_ROOT || location.protocol==='file:') return;
    const query = new URLSearchParams();
    if(state.q)query.set('q',state.q); if(state.category)query.set('category',state.category); if(state.year)query.set('year',state.year); if(state.rating)query.set('rating',state.rating);
    if(state.sort && state.sort!==state.defaultSort)query.set('sort',state.sort); if(state.view==='list')query.set('view','list'); if(state.page && (state.page!==1||initialPage!==1))query.set('page',state.page);
    history.replaceState(null,'',location.pathname+(query.toString()?'?'+query:'')+location.hash);
  }
  function setView(grid,view) {
    grid.classList.toggle('list-view',view==='list');
    $$('[data-view]').forEach(btn=>{const yes=btn.dataset.view===view;btn.classList.toggle('active',yes);btn.setAttribute('aria-pressed',String(yes));});
  }
  function initArchive() {
    const grid=$('[data-post-grid][data-mode="archive"]') || $('[data-shelf-grid]'); if(!grid)return;
    const shelf=grid.hasAttribute('data-shelf-grid'), query = new URLSearchParams(window.PREVIEW_ROOT ? (window.PREVIEW_QUERY||'') : location.search);
    const initialPage=Number(grid.dataset.page||1), defaultSort=shelf?'title':'recent';
    const qInput=$('[data-filter-search]'), cInput=$('[data-filter-category]'), yInput=$('[data-filter-year]'), rInput=$('[data-filter-rating]'), sortInput=$('[data-filter-sort]');
    const state={q:query.get('q')||'',category:query.get('category')||'',year:query.get('year')||'',rating:query.get('rating')||'',sort:query.get('sort')||defaultSort,defaultSort,view:query.get('view')||get(shelf?'paso-view-shelf':'paso-view-blog','grid'),page:Math.max(1,Number(query.get('page')||initialPage)||1)};
    const inputValue=(input,value)=>{if(!input)return '';input.value=value;return input.value;};
    state.q=inputValue(qInput,state.q);state.category=inputValue(cInput,state.category);state.year=inputValue(yInput,state.year);state.rating=inputValue(rInput,state.rating);state.sort=inputValue(sortInput,state.sort)||defaultSort;
    const cards=$$(shelf?'[data-shelf-item]':'[data-card]',grid), empty=$('[data-empty]',grid), perPage=shelf?1000:Number(grid.dataset.perPage||9);
    const basePosts=shelf?D.posts.filter(p=>p.category===grid.dataset.category&&p.media):D.posts;
    function render(updateURL=true) {
      let found=basePosts.filter(p=>matchesPost(p,state.q)&&(!state.category||p.category===state.category)&&(!state.year||p.date.startsWith(state.year))&&(!state.rating||(p.media?.rating||0)>=Number(state.rating)));
      found.sort((a,b)=>state.sort==='title'?normal(shelf?a.media.title:a.title).localeCompare(normal(shelf?b.media.title:b.title),'es'):state.sort==='oldest'?a.date.localeCompare(b.date):state.sort==='rating'?(b.media.rating-a.media.rating)||normal(a.media.title).localeCompare(normal(b.media.title),'es'):b.date.localeCompare(a.date));
      const pages=Math.max(1,Math.ceil(found.length/perPage));state.page=Math.min(state.page,pages);
      const shown=new Set(found.slice((state.page-1)*perPage,state.page*perPage).map(p=>p.slug));
      const cardMap=new Map(cards.map(el=>[shelf?el.dataset.shelfItem:el.dataset.card,el]));
      found.forEach(p=>grid.append(cardMap.get(p.slug))); cards.forEach(el=>el.hidden=!shown.has(shelf?el.dataset.shelfItem:el.dataset.card)); grid.append(empty);empty.hidden=found.length>0;
      const status=$('[data-result-status]');if(status)status.textContent=shelf?`${found.length} ${found.length===1?'título':'títulos'}`:`${found.length} ${found.length===1?'nota':'notas'}${found.length?' · página '+state.page+' de '+pages:''}`;
      setView(grid,state.view);
      const pagination=$('[data-pagination]');
      if(pagination) {
        pagination.hidden=pages===1;
        pagination.innerHTML=Array.from({length:pages},(_,i)=>i+1).map(n=>{const qs=new URLSearchParams();if(state.q)qs.set('q',state.q);if(state.category)qs.set('category',state.category);if(state.year)qs.set('year',state.year);if(state.sort!==defaultSort)qs.set('sort',state.sort);if(state.view==='list')qs.set('view','list');const href=url(n===1?'blog/':`blog/page/${n}/`)+(qs.size?'?'+qs:'');return `<a href="${esc(href)}" data-page-link="${n}" ${n===state.page?'class="active" aria-current="page"':''}>${n}</a>`;}).join('');
      }
      if(updateURL)writeQuery(state,initialPage);
    }
    const apply=()=>{state.q=qInput.value;state.category=cInput?.value||'';state.year=yInput.value;state.rating=rInput?.value||'';state.sort=sortInput.value;state.page=1;render();};
    qInput.addEventListener('input',apply);[cInput,yInput,rInput,sortInput].filter(Boolean).forEach(el=>el.addEventListener('change',apply));
    $$('[data-view]').forEach(btn=>btn.addEventListener('click',()=>{state.view=btn.dataset.view;set(shelf?'paso-view-shelf':'paso-view-blog',state.view,false);render();}));
    $$('[data-reset-filters]').forEach(btn=>btn.addEventListener('click',()=>{qInput.value='';if(cInput)cInput.value='';yInput.value='';if(rInput)rInput.value='';sortInput.value=defaultSort;apply();qInput.focus();}));
    $('[data-pagination]')?.addEventListener('click',e=>{const link=e.target.closest('[data-page-link]');if(!link||e.ctrlKey||e.metaKey||e.shiftKey||e.altKey)return;e.preventDefault();state.page=Number(link.dataset.pageLink);render();grid.scrollIntoView({block:'start',behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});});
    render(false);
  }

  function initHome() {
    const grid=$('[data-post-grid][data-mode="home"]');if(!grid)return;
    const cards=$$('[data-card]',grid),empty=$('[data-empty]',grid);
    const render=category=>{
      const found=D.posts.filter(p=>category?p.category===category:p.slug!==grid.dataset.exclude);const shown=new Set(found.slice(0,6).map(p=>p.slug));
      cards.forEach(card=>card.hidden=!shown.has(card.dataset.card));empty.hidden=found.length>0;
      $$('[data-home-filter]').forEach(button=>{const yes=button.dataset.homeFilter===category;button.classList.toggle('active',yes);button.setAttribute('aria-pressed',String(yes));});
      $('[data-home-status]').textContent=category?`Mostrando ${Math.min(found.length,6)} de ${found.length} notas de ${categories.get(category).name.toLowerCase()}.`:`Seis notas para empezar. El archivo tiene ${D.posts.length}.`;
    };
    $$('[data-home-filter]').forEach(button=>button.addEventListener('click',()=>render(button.dataset.homeFilter)));
    $('[data-reset-filters]',grid)?.addEventListener('click',()=>render(''));render('');
  }
  function initTerms() {
    const grid=$('[data-term-grid]');if(!grid)return;
    const terms=$$('[data-term]',grid),empty=$('[data-empty]',grid),search=$('[data-term-search]'),sort=$('[data-term-sort]');
    const render=()=>{const q=normal(search.value);let count=0;terms.forEach(el=>{el.hidden=!normal(el.dataset.term).includes(q);if(!el.hidden)count++;});const ordered=[...terms].sort((a,b)=>sort.value==='count'?Number(b.dataset.count)-Number(a.dataset.count):grid.dataset.taxonomy==='years'?b.dataset.term.localeCompare(a.dataset.term):normal(a.dataset.term).localeCompare(normal(b.dataset.term),'es'));ordered.forEach(el=>grid.append(el));grid.append(empty);empty.hidden=count>0;};
    search.addEventListener('input',render);sort.addEventListener('change',render);render();
  }
  function initNumbers() {
    const select=$('[data-numbers-year]');if(!select)return;
    select.value=new URLSearchParams(window.PREVIEW_ROOT ? (window.PREVIEW_QUERY||'') : location.search).get('year')||'';
    const render=(updateURL=true)=>{
      const metrics=D.metrics[select.value]||D.metrics.all;
      $$('[data-stat]').forEach(el=>el.textContent=formatNumber(metrics[el.dataset.stat]||0));
      $$('[data-year-row]').forEach(row=>row.hidden=!!select.value&&row.dataset.yearRow!==select.value);
      $$('[data-bar-year]').forEach(bar=>bar.classList.toggle('dimmed',!!select.value&&bar.dataset.barYear!==select.value));
      $('[data-stats-total-label]').textContent=select.value||'Total';
      if(updateURL&&!window.PREVIEW_ROOT&&location.protocol!=='file:')history.replaceState(null,'',location.pathname+(select.value?'?year='+select.value:''));
    };
    select.addEventListener('change',()=>render());render(false);
  }

  function cardHTML(p) {
    const c=categories.get(p.category);let art;
    if(p.image)art=`<img src="${esc(asset('assets/images/'+p.image))}" alt="Ilustración de demostración" loading="lazy">`;
    else if(p.media)art=`<div class="card-art"><img class="art-cover" src="${esc(asset('assets/covers/'+p.slug+'.svg'))}" alt="Cubierta ilustrada de ${esc(p.media.title)}"><span class="art-icon">${icon(c.icon)}</span></div>`;
    else art=`<div class="card-art"><span class="card-text-art">Mirar<br>más despacio.</span></div>`;
    return `<article class="post-card" data-card="${esc(p.slug)}" style="--cat-color:${c.color};--cat-pale:${c.pale}"><a class="card-image-link" href="${esc(url(p.url))}" aria-label="Leer ${esc(p.title)}">${art}</a><div class="card-body"><div class="card-topline"><a class="category-label" href="${esc(url('categories/'+p.category+'/'))}">${icon(c.icon)}${esc(c.name)}</a><time datetime="${p.date}">${esc(formatDate(p.date))}</time></div><h3><a href="${esc(url(p.url))}">${esc(p.title)}</a></h3><p class="excerpt">${esc(p.excerpt)}</p><div class="card-footer"><span class="reading-time">${icon('clock')}${p.minutes} min de lectura</span><button type="button" class="card-save" data-save="${esc(p.slug)}" aria-label="Guardar nota" aria-pressed="false">${icon('bookmark')}</button></div></div></article>`;
  }
  function initToday() {
    if(!$('.page-today'))return;
    const render=()=>{
      const now=new Date();let parts;
      try{parts=new Intl.DateTimeFormat('en-CA',{year:'numeric',month:'2-digit',day:'2-digit',timeZone:D.site.timezone}).formatToParts(now);}catch(_){parts=new Intl.DateTimeFormat('en-CA',{year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(now);}
      const getPart=t=>parts.find(p=>p.type===t).value;const y=Number(getPart('year')),m=Number(getPart('month')),d=Number(getPart('day'));
      const date=`${y}-${String(m).padStart(2,'0')}-${String(d).padStart(2,'0')}`;const ordinal=Math.floor((Date.UTC(y,m-1,d)-Date.UTC(y,0,0))/86400000);
      const quote=D.quotes[ordinal%D.quotes.length],post=D.posts[ordinal%D.posts.length];
      $('[data-today-date]').textContent=new Intl.DateTimeFormat('es-AR',{weekday:'long',day:'numeric',month:'long',year:'numeric',timeZone:'UTC'}).format(new Date(date+'T12:00:00Z'));
      $('[data-daily-quote]').textContent=quote.text;$('[data-daily-quote-link]').href=url(postsById.get(quote.post).url);
      $('[data-daily-post-title]').textContent=post.title;$('[data-daily-post-excerpt]').textContent=post.excerpt;$('[data-daily-post-link]').href=url(post.url);
      const anniversary=D.posts.filter(p=>p.date.slice(5)===date.slice(5)&&Number(p.date.slice(0,4))<y);
      $('[data-anniversary-posts]').innerHTML=anniversary.length?anniversary.map(cardHTML).join(''):'<div class="empty-state"><h3>Hoy el archivo no tiene un aniversario.</h3><p>Hay otras historias esperando una lectura.</p></div>';syncSaved();
    };render();dailyInterval=setInterval(render,60000);
  }

  function initBlank() {
    const textarea=$('[data-blank-text]');if(!textarea)return;
    textarea.value=get('paso-note','');
    const words=()=>{$('[data-note-words]').textContent=(textarea.value.trim()?textarea.value.trim().split(/\s+/).length:0)+' palabras';};words();
    textarea.addEventListener('input',()=>{clearTimeout(noteTimeout);$('[data-note-status]').textContent='Guardando…';words();noteTimeout=setTimeout(()=>{const persisted=set('paso-note',textarea.value);$('[data-note-status]').textContent=persisted?'Guardado en este navegador.':'En memoria temporal: descargá el texto para conservarlo.';},300);});
    let remaining=Number($('#timer-duration').value),end=0,running=false;
    const display=()=>{$('[data-timer-display]').textContent=`${String(Math.floor(remaining/60)).padStart(2,'0')}:${String(remaining%60).padStart(2,'0')}`;$('[data-timer-toggle]').innerHTML=icon('clock')+(running?'Pausar':'Empezar');$('#timer-duration').disabled=running;};
    $('#timer-duration').addEventListener('change',()=>{remaining=Number($('#timer-duration').value);display();});
    $('[data-timer-toggle]').addEventListener('click',()=>{if(running){clearInterval(timerInterval);running=false;display();return;}if(remaining<=0)remaining=Number($('#timer-duration').value);running=true;end=Date.now()+remaining*1000;display();timerInterval=setInterval(()=>{remaining=Math.max(0,Math.ceil((end-Date.now())/1000));if(!remaining){clearInterval(timerInterval);running=false;toast('Terminó el tiempo. Podés seguir escribiendo, sin apuro.');}display();},250);});
    $('[data-timer-reset]').addEventListener('click',()=>{clearInterval(timerInterval);running=false;remaining=Number($('#timer-duration').value);display();});display();
  }

  function initImages() {
    $$('.photo-grid img').forEach(img=>{img.classList.add('lightbox-trigger');img.setAttribute('data-lightbox','');img.setAttribute('role','button');img.tabIndex=0;img.setAttribute('aria-label','Ampliar: '+img.alt);});
  }
  function initCode() {
    $$('.prose pre').forEach(pre=>{if($('.code-copy',pre))return;const button=document.createElement('button');button.type='button';button.className='code-copy';button.setAttribute('aria-label','Copiar código');button.innerHTML=icon('copy');button.addEventListener('click',()=>copy($('code',pre)?.textContent||'','Código copiado.'));pre.append(button);});
  }
  function updateReading() {
    const progress=$('.reading-progress');if(!progress)return;
    const body=$('.article-prose');if(!body)return;
    const top=body.getBoundingClientRect().top+window.scrollY, bottom=top+body.offsetHeight,viewport=window.innerHeight;
    progress.style.width=Math.max(0,Math.min(100,(window.scrollY-top+viewport*.45)/Math.max(1,bottom-top-viewport*.55)*100))+'%';
    const headings=$$('.article-prose h2,.article-prose h3');let current=headings[0];headings.forEach(h=>{if(h.getBoundingClientRect().top<160)current=h;});
    $$('.article-toc a').forEach(link=>{const yes=current&&decodeURIComponent(link.getAttribute('href').slice(1))===current.id;link.classList.toggle('current',!!yes);if(yes)link.setAttribute('aria-current','location');else link.removeAttribute('aria-current');});
  }
  let scrollScheduled=false;
  window.addEventListener('scroll',()=>{if(scrollScheduled)return;scrollScheduled=true;requestAnimationFrame(()=>{scrollScheduled=false;updateReading();});},{passive:true});
  window.addEventListener('resize',updateReading,{passive:true});

  document.addEventListener('click',async e=>{
    const button=e.target.closest('button,a,[data-lightbox]');if(!button)return;
    if(button.hasAttribute('data-open-search')){e.preventDefault();openSearch();}
    else if(button.hasAttribute('data-close-dialog'))closeDialog(button.closest('dialog'));
    else if(button.hasAttribute('data-theme-toggle')){const theme=document.documentElement.dataset.theme==='dark'?'light':'dark';document.documentElement.dataset.theme=theme;set('paso-theme',theme);updateTheme();}
    else if(button.hasAttribute('data-save')){const id=button.dataset.save;if(!postsById.has(id))return;const was=saved.has(id);was?saved.delete(id):saved.add(id);persistSaved();if(canStore)toast(was?'Nota quitada de tu selección.':'Nota guardada para volver.');}
    else if(button.hasAttribute('data-copy-text'))copy(button.dataset.copyText,'Cita copiada.');
    else if(button.hasAttribute('data-copy-url'))copy(window.PREVIEW_ROOT ? location.href.split('#')[0]+'#/'+button.dataset.copyUrl : url(button.dataset.copyUrl),window.PREVIEW_ROOT ? 'Ruta de demostración copiada. El feed real está en el proyecto.':'Enlace del feed copiado.');
    else if(button.hasAttribute('data-copy-page'))copy(currentURL(),'Enlace de la nota copiado.');
    else if(button.hasAttribute('data-share-page')){const data={title:postsById.get(document.body.dataset.post)?.title||document.title,url:currentURL()};if(navigator.share&&!window.PREVIEW_ROOT){try{await navigator.share(data);}catch(err){if(err.name!=='AbortError')copy(data.url);}}else copy(data.url,'Enlace listo para compartir.');}
    else if(button.hasAttribute('data-reader-size')){let scale=Number(get('paso-reader-scale','1'))||1;const step=Number(button.dataset.readerSize);scale=step===0?1:Math.min(1.4,Math.max(.9,Math.round((scale+.1*step)*10)/10));document.documentElement.style.setProperty('--reader-scale',scale);set('paso-reader-scale',String(scale));toast('Tamaño de lectura: '+Math.round(scale*100)+' %.');updateReading();}
    else if(button.hasAttribute('data-reader-focus')){document.body.classList.add('reading-mode');updateReading();}
    else if(button.hasAttribute('data-exit-focus')){document.body.classList.remove('reading-mode','quiet-mode');updateReading();}
    else if(button.hasAttribute('data-lightbox')){const img=$('#lightbox-image');img.src=button.currentSrc||button.src;img.alt=button.alt;$('#lightbox-caption').textContent=button.alt+' · Ilustración de demostración';openDialog($('#lightbox-dialog'));}
    else if(button.hasAttribute('data-export-saved')){download('a-paso-lento-guardados.json',JSON.stringify({version:1,site:'a-paso-lento',exported_at:new Date().toISOString(),saved:[...saved],notes:[...saved].map(id=>({id,title:postsById.get(id).title}))},null,2),'application/json');toast('Selección exportada.');}
    else if(button.hasAttribute('data-import-saved'))$('#import-saved-file')?.click();
    else if(button.hasAttribute('data-clear-saved')){if(!saved.size){toast('Tu selección ya está vacía.');return;}if(await confirmAction('¿Vaciar tus guardados?','Se quitará la selección de este navegador. Las entradas del blog no se borrarán.')){saved.clear();persistSaved();toast('Selección vaciada.');}}
    else if(button.hasAttribute('data-copy-message')){const form=$('[data-contact-form]');copy('Asunto: '+form.elements.subject.value+'\n\n'+form.elements.message.value,'Mensaje copiado. No se envió ningún dato.');}
    else if(button.hasAttribute('data-reset-local')){if(await confirmAction('¿Borrar los datos locales?','Se borrarán el tema, las preferencias de lectura, la selección de notas y el texto privado de este navegador.')){['paso-saved','paso-theme','paso-reader-scale','paso-note','paso-view-blog','paso-view-shelf'].forEach(remove);saved.clear();document.documentElement.dataset.theme='light';document.documentElement.style.setProperty('--reader-scale','1');syncSaved();updateTheme();toast('Datos locales eliminados.');}}
    else if(button.hasAttribute('data-quiet-mode')){document.body.classList.add('quiet-mode');$('[data-blank-text]')?.focus();}
    else if(button.hasAttribute('data-download-note')){const value=$('[data-blank-text]').value;download('mi-pagina-en-blanco.txt',value);toast('Texto descargado.');}
    else if(button.hasAttribute('data-clear-note')){if(!$('[data-blank-text]').value)return;if(await confirmAction('¿Limpiar esta página?','El texto privado se quitará del navegador. Descargalo antes si querés conservarlo.')){clearTimeout(noteTimeout);$('[data-blank-text]').value='';set('paso-note','');$('[data-note-words]').textContent='0 palabras';$('[data-note-status]').textContent='Página vacía, guardada localmente.';}}
  });
  document.addEventListener('keydown',e=>{
    const editing=e.target.matches('input,textarea,select,[contenteditable="true"]');
    if((e.key==='/'&&!editing)||((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='k')){e.preventDefault();openSearch();return;}
    if(e.key==='Escape'){
      const opened=$('dialog[open]');
      if(opened){e.preventDefault();const cancel=new Event('cancel',{cancelable:true});if(opened.dispatchEvent(cancel))closeDialog(opened);return;}
      document.body.classList.remove('reading-mode','quiet-mode');
    }
    if(e.target.hasAttribute('data-lightbox')&&['Enter',' '].includes(e.key)){e.preventDefault();e.target.click();}
    const dialog=$('#search-dialog');if(!dialog?.open)return;
    const links=$$('.search-result',dialog),index=links.indexOf(document.activeElement);
    if(e.key==='ArrowDown'){e.preventDefault();links[Math.min(index+1,links.length-1)]?.focus();}
    else if(e.key==='ArrowUp'){e.preventDefault();if(index<=0)$('#global-search').focus();else links[index-1]?.focus();}
    else if(e.key==='Enter'&&e.target.id==='global-search'&&links.length){e.preventDefault();links[0].click();}
  });
  window.addEventListener('storage',e=>{if(e.key==='paso-saved'){saved=readSaved();syncSaved();}if(e.key==='paso-theme'){document.documentElement.dataset.theme=get('paso-theme','light');updateTheme();}});

  function init() {
    clearInterval(timerInterval);clearInterval(dailyInterval);clearTimeout(noteTimeout);clearTimeout(toastTimeout);
    document.documentElement.dataset.theme=get('paso-theme','light');document.documentElement.style.setProperty('--reader-scale',get('paso-reader-scale','1'));
    updateTheme();syncSaved();initHome();initArchive();initTerms();initNumbers();initToday();initBlank();initCode();initImages();updateReading();
    $('#global-search')?.addEventListener('input',e=>renderSearch(e.target.value));
    $$('dialog').forEach(dialog=>{
      dialog.addEventListener('close',()=>document.body.classList.remove('modal-open'));
      dialog.addEventListener('click',e=>{if(e.target!==dialog)return;const rect=dialog.getBoundingClientRect();if(e.clientX<rect.left||e.clientX>rect.right||e.clientY<rect.top||e.clientY>rect.bottom)closeDialog(dialog);});
    });
    $('#import-saved-file')?.addEventListener('change',async e=>{
      const file=e.target.files[0];if(!file)return;
      try{if(file.size>1000000)throw new Error('size');const parsed=JSON.parse(await file.text());const ids=Array.isArray(parsed)?parsed:parsed.saved;if(!Array.isArray(ids)||ids.length>10000)throw new Error('format');let added=0,unknown=0;ids.forEach(id=>{if(typeof id==='string'&&postsById.has(id)){if(!saved.has(id))added++;saved.add(id);}else unknown++;});persistSaved();toast(`${added} ${added===1?'nota importada':'notas importadas'}.${unknown?' '+unknown+' identificadores no pertenecen a este cuaderno.':''}`);}catch(_){toast('No pude leer la selección. Usá un JSON exportado por este blog.');}e.target.value='';
    });
    $('[data-contact-form]')?.addEventListener('submit',e=>{
      e.preventDefault();if(!D.site.email){toast('Configurá un email propio para activar esta función.');return;}const form=e.target;const href='mailto:'+D.site.email+'?subject='+encodeURIComponent(form.elements.subject.value)+'&body='+encodeURIComponent(form.elements.message.value);location.href=href;toast('Se abrirá tu correo. El blog no envió el mensaje.');
    });
    $$('a[href^="http"]').forEach(link=>{try{const dest=new URL(link.href);if(dest.origin!==rootURL().origin){link.target='_blank';link.rel='noopener noreferrer';}}catch(_){} });
    // Decorative and expanded images remain in the current site; no CDN calls.
  }
  window.initBlog=init;
  window.blogAsset=asset;
  window.flushBlogNote=()=>{const note=$('[data-blank-text]');if(note){clearTimeout(noteTimeout);set('paso-note',note.value,false);}};
  window.addEventListener('beforeunload',()=>window.flushBlogNote());
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
