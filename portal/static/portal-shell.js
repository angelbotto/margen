/* Portal navigation owns chrome only. Artifact readers keep their own controls. */
window.MargenPortalShell = (() => {
  const $ = (selector) => document.querySelector(selector);
  const sidebar = $('#portal-sidebar');
  if (!sidebar) return {updateIdentity() {}};
  const toggle = $('#sidebar-toggle'), close = $('#sidebar-close');
  const trigger = $('#profile-trigger'), menu = $('#profile-menu');
  const mobile = matchMedia('(max-width: 850px)');
  const background = [$('.shell-topbar'), $('#main'), $('#footer')];
  let drawerOpen = false, collapsed = false, wasMobile = mobile.matches;
  try { collapsed = localStorage.getItem('margen-sidebar-collapsed') === 'true'; } catch { /* optional preference */ }
  const visible = (root) => [...root.querySelectorAll('a[href],button,input,select,summary,[tabindex="0"]')]
    .filter((node) => !node.disabled && !node.closest('[hidden]') && node.getClientRects().length);
  function closeProfile(restore = false) {
    menu.hidden = true;
    trigger.setAttribute('aria-expanded', 'false');
    if (restore) trigger.focus();
  }
  function sync() {
    document.body.classList.toggle('sidebar-collapsed', collapsed && !mobile.matches);
    document.body.classList.toggle('sidebar-open', drawerOpen && mobile.matches);
    sidebar.inert = mobile.matches && !drawerOpen;
    $('#sidebar-backdrop').hidden = !drawerOpen;
    for (const node of background) if (node) node.inert = drawerOpen;
    if (drawerOpen) {
      sidebar.setAttribute('role', 'dialog');
      sidebar.setAttribute('aria-modal', 'true');
    } else {
      sidebar.removeAttribute('role');
      sidebar.removeAttribute('aria-modal');
    }
    toggle.setAttribute('aria-expanded', String(mobile.matches ? drawerOpen : !collapsed));
    toggle.setAttribute('aria-label', mobile.matches ? 'Abrir navegación' : collapsed ? 'Expandir navegación' : 'Contraer navegación');
  }
  function setDrawer(open, restore = true) {
    drawerOpen = open;
    closeProfile();
    sync();
    if (open) close.focus();
    else if (restore) toggle.focus();
  }
  toggle.addEventListener('click', () => {
    if (mobile.matches) return setDrawer(true);
    collapsed = !collapsed;
    closeProfile();
    try { localStorage.setItem('margen-sidebar-collapsed', String(collapsed)); } catch { /* optional preference */ }
    sync();
  });
  close.addEventListener('click', () => setDrawer(false));
  $('#sidebar-backdrop').addEventListener('click', () => setDrawer(false));
  mobile.addEventListener('change', (event) => {
    if (event.matches !== mobile.matches || event.matches === wasMobile) return;
    wasMobile = event.matches;
    const hadFocus = sidebar.contains(document.activeElement);
    setDrawer(false, mobile.matches && hadFocus);
  });
  trigger.addEventListener('click', () => {
    menu.hidden = !menu.hidden;
    trigger.setAttribute('aria-expanded', String(!menu.hidden));
    if (!menu.hidden) visible(menu)[0]?.focus();
  });
  menu.addEventListener('click', (event) => {
    if (event.target.closest('[role="menuitem"]')) closeProfile(true);
  });
  document.addEventListener('click', (event) => {
    if (!event.target.closest('.sidebar-account')) closeProfile();
  });
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
      if (!menu.hidden) { event.preventDefault(); event.stopPropagation(); closeProfile(true); }
      else if (drawerOpen) { event.preventDefault(); setDrawer(false); }
      return;
    }
    if (!menu.hidden && ['ArrowDown', 'ArrowUp', 'Home', 'End'].includes(event.key)) {
      const items = visible(menu), current = items.indexOf(document.activeElement);
      const next = event.key === 'Home' ? 0 : event.key === 'End' ? items.length - 1 :
        (current + (event.key === 'ArrowUp' ? -1 : 1) + items.length) % items.length;
      event.preventDefault(); items[next]?.focus();
    }
    if (drawerOpen && event.key === 'Tab') {
      const items = visible(sidebar), first = items[0], last = items.at(-1);
      if (event.shiftKey && (document.activeElement === first || document.activeElement === sidebar)) {
        event.preventDefault(); last?.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault(); first?.focus();
      }
    }
  });
  document.addEventListener('focusin', (event) => {
    if (!menu.hidden && !event.target.closest('.sidebar-account')) closeProfile();
  });
  sidebar.addEventListener('click', (event) => {
    if (event.target.closest('button[data-view]') && drawerOpen) setDrawer(false);
  });
  function updateLocation() {
    const view = document.body.dataset.view || 'mine';
    const selected = sidebar.querySelector('[data-view="' + view + '"]');
    if (!selected) return;
    $('#shell-current').textContent = selected.textContent.trim();
    $('#shell-group').textContent = selected.closest('.nav-group')?.getAttribute('aria-label') || 'Biblioteca';
    for (const button of sidebar.querySelectorAll('[data-view]')) {
      button.title = button.textContent.trim();
      button.setAttribute('aria-label', button.textContent.trim());
    }
  }
  new MutationObserver(updateLocation).observe(document.body, {attributes:true, attributeFilter:['data-view']});
  function updateIdentity(user) {
    const name = user?.name || user?.email || 'Tu cuenta';
    $('#profile-name').textContent = name;
    $('#profile-role').textContent = user?.admin ? 'Administrador' : user?.verified ? 'Cuenta personal' : user ? 'Invitado' : 'Explorar Margen';
    $('#profile-avatar').textContent = user ? name.slice(0, 2).toUpperCase() : 'M';
    trigger.setAttribute('aria-label', 'Menú de cuenta: ' + name);
    updateLocation();
  }
  sync();
  return {updateIdentity};
})();
