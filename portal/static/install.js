(() => {
  const $ = s => document.querySelector(s), ui = window.MargenInstall;
  try { document.documentElement.toggleAttribute('data-dark', localStorage.getItem('bottifact-portal-dark') === 'true' || (!localStorage.getItem('bottifact-portal-dark') && matchMedia('(prefers-color-scheme:dark)').matches)); } catch {}
  $('#install-theme').onclick = () => { const dark = document.documentElement.toggleAttribute('data-dark'); try { localStorage.setItem('bottifact-portal-dark', String(dark)); } catch {} };
  $('#copy-install').prepend(ui.icon('copy')); $('#copy-connect').append(ui.icon('copy'));
  document.querySelectorAll('[data-install-icon]').forEach(el => el.append(ui.icon(el.dataset.installIcon)));
  const picker = ui.selector($('#install-platform'), $('#command'), (platform, state) => {
    $('#shell-label').replaceChildren(ui.icon('terminal'), document.createTextNode(state.shell));
    $('#installer-source').href = platform === 'windows' ? '/install.ps1' : '/install.sh';
    $('#copy-install').disabled = !state.valid;
    $('.install-terminal').classList.toggle('is-empty', !state.valid);
    $('#install-summary').textContent = state.valid ? state.names.join(' + ') : 'Elige tus agentes';
    $('#copy-status').textContent = ''; $('#connect-status').textContent = '';
    const paths = state.paths.map((path, i) => { const li = document.createElement('li'), code = document.createElement('code'); code.textContent = path; li.append(document.createTextNode(state.names[i] + ' · '), code); return li; });
    $('#install-path-list').replaceChildren(...(paths.length ? paths : [document.createTextNode('Selecciona al menos un agente.') ]));
    $('#connect-command').textContent = ui.connectionCommand(platform);
    $('#restart-help').textContent = (platform === 'windows' ? 'Reabre tu terminal al terminar. ' : '') + 'Abre una conversación nueva en tu agente y pide: «Usa el skill margen».';
  });
  $('#copy-install').onclick = () => { if (picker.state.valid) ui.copyText($('#command').textContent, $('#copy-status'), $('#command')); };
  $('#copy-connect').onclick = () => ui.copyText($('#connect-command').textContent, $('#connect-status'), $('#connect-command'));
})();
