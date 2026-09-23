/* Organize existing navigation nodes without replacing handlers or state. */
window.MargenSidebar = (() => {
  const el = (tag, text, cls) => {
    const node = document.createElement(tag);
    if (text != null) node.textContent = text;
    if (cls) node.className = cls;
    return node;
  };
  const normalized = (value) => value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  function init(nav) {
    if (nav.dataset.organized) return;
    nav.dataset.organized = 'true';
    for (const [id, label, views] of [
      ['library', 'Biblioteca', ['mine', 'shared', 'inbox']],
      ['knowledge', 'Conocimiento', ['brain', 'work', 'insights']],
      ['account', 'Más herramientas', ['notifications', 'public', 'archived', 'connections', 'all', 'admin']],
    ]) {
      const group = el(id === 'account' ? 'details' : 'section', null, 'nav-group nav-' + id);
      group.setAttribute('aria-label', label);
      group.append(el(id === 'account' ? 'summary' : 'h2', label));
      for (const view of views) {
        const button = nav.querySelector('[data-view="' + view + '"]');
        if (!button) continue;
        group.append(button);
        if (id === 'account' && button.classList.contains('active')) group.open = true;
      }
      nav.append(group);
    }
  }
  function facets(nav, {id, label, values, selected, onSelect, open = false}) {
    let group = nav.querySelector('#' + id);
    if (!group) {
      group = el('details', null, 'category-nav sidebar-facets ' + (id === 'company-nav' ? 'company-nav' : ''));
      group.id = id;
      group.open = open;
      const summary = el('summary');
      summary.append(el('span', label), el('span', '', 'nav-count'));
      const search = el('input');
      search.type = 'search';
      search.placeholder = 'Buscar ' + label.toLowerCase();
      search.setAttribute('aria-label', search.placeholder);
      const list = el('div', null, 'sidebar-facet-list');
      const empty = el('p', 'Sin coincidencias.', 'sidebar-no-matches');
      empty.setAttribute('role', 'status');
      empty.hidden = true;
      group.append(summary, search, list, empty);
      search.addEventListener('input', () => {
        let count = 0;
        for (const button of list.children) {
          button.hidden = !normalized(button.dataset.value).includes(normalized(search.value.trim()));
          if (!button.hidden) count++;
        }
        empty.hidden = count > 0;
      });
      nav.insertBefore(group, nav.querySelector('.nav-account'));
    }
    group.hidden = !values.length;
    group.querySelector('.nav-count').textContent = String(values.length);
    const key = JSON.stringify(values);
    const list = group.querySelector('.sidebar-facet-list');
    group.onSelect = onSelect;
    if (group.dataset.values !== key) {
      group.dataset.values = key;
      list.replaceChildren();
      for (const value of values) {
        const button = el('button');
        button.type = 'button';
        button.dataset.value = value;
        button.title = value;
        if (id === 'company-nav') {
          const initial = el('span', value.slice(0, 2), 'company-initial');
          initial.setAttribute('aria-hidden', 'true');
          button.append(initial);
        }
        button.append(el('span', value, 'nav-label'));
        button.addEventListener('click', () => group.onSelect(button.getAttribute('aria-pressed') === 'true' ? '' : value));
        list.append(button);
      }
      group.querySelector('input').dispatchEvent(new Event('input'));
    }
    group.querySelector('input').hidden = values.length < 7;
    for (const button of list.children) {
      const chosen = button.dataset.value === selected;
      button.classList.toggle('chosen', chosen);
      button.setAttribute('aria-pressed', String(chosen));
    }
    if (selected) group.open = true;
  }
  return {init, facets};
})();
