/* Shared, keyboard-accessible install choices. No identity or token is embedded. */
window.MargenInstall = (() => {
  const agents = {codex: ['Codex', '.agents'], claude: ['Claude Code', '.claude'], hermes: ['Hermes', '.hermes']};
  const icons = {
    mac: '<path fill="currentColor" stroke="none" d="M17.2 6.2c1.1-1.3 1-2.7 1-3.2-1.1.1-2.4.8-3.1 1.7-.8.8-1.2 1.9-1.1 3 1.2.1 2.4-.6 3.2-1.5ZM20.1 17.8c-.5 1.2-.8 1.7-1.5 2.7-1 1.4-2.3 3.1-3.9 3.1-1.4 0-1.8-.9-3.7-.9-1.8 0-2.3.9-3.7.9-1.6 0-2.8-1.5-3.8-3-2.7-3.9-3-8.5-1.3-11 1.2-1.8 3.1-2.8 4.9-2.8 1.5 0 2.5.9 3.8.9 1.3 0 2.1-.9 3.8-.9 1.5 0 3 .8 4.1 2-3.6 2-3 7.3 1.3 9Z" transform="translate(2 -1) scale(.91)"/>',
    windows: '<path fill="currentColor" stroke="none" d="m3 5 8-1v7H3zm10-1.2L22 2.5V11h-9zM3 13h8v7l-8-1zm10 0h9v8.5l-9-1.3z"/>',
    linux: '<path fill="currentColor" stroke="none" d="M12 2c-3.8 0-4.9 3-4.8 6.7C7.3 11 4 13.9 4 18c0 3 3.4 4 8 4s8-1 8-4c0-4.1-3.3-7-3.2-9.3C16.9 5 15.8 2 12 2Z"/><ellipse cx="12" cy="15" rx="4.8" ry="5.7" fill="var(--panel)" stroke="none"/><ellipse cx="10" cy="7.5" rx="1.2" ry="1.8" fill="var(--panel)" stroke="none"/><ellipse cx="14" cy="7.5" rx="1.2" ry="1.8" fill="var(--panel)" stroke="none"/><path d="m9 10 3-1 3 1-3 2Z" fill="var(--muted)" stroke="none"/><path d="m7 19-3 2 5 1m8-3 3 2-5 1"/>',
    codex: '<path d="m8 6-6 6 6 6m8-12 6 6-6 6M14 3l-4 18"/>',
    claude: '<path d="M12 2v20M2 12h20M5 5l14 14M5 19 19 5M8 3l8 18M3 8l18 8M3 16l18-8M8 21l8-18"/>',
    hermes: '<path d="M5 19h14M9 19l3-8 3 8M12 11C5 13 3 8 3 4l9 5 9-5c0 4-2 9-9 7ZM4 8l5 2m11-2-5 2"/>',
    check: '<path d="m5 12 4 4L19 6"/>',
    copy: '<rect x="8" y="8" width="12" height="12" rx="2"/><path d="M16 8V4a1 1 0 0 0-1-1H4a1 1 0 0 0-1 1v11a1 1 0 0 0 1 1h4"/>',
    arrow: '<path d="M4 12h16m-6-6 6 6-6 6"/>',
    terminal: '<path d="m4 6 6 6-6 6m9 0h7"/>',
    user: '<circle cx="12" cy="8" r="3"/><path d="M5 21v-3a7 7 0 0 1 14 0v3"/>',
    key: '<circle cx="8" cy="8" r="5"/><path d="m12 12 9 9m-3-3 3-3m-6 0 3-3"/>',
  };
  let sequence = 0;
  function icon(name) {
    const wrap = document.createElement('span'); wrap.className = 'install-icon';
    wrap.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + (icons[name] || icons.terminal) + '</svg>';
    return wrap;
  }
  function node(tag, text, className) {
    const el = document.createElement(tag); if (text) el.textContent = text; if (className) el.className = className; return el;
  }
  function command(platform, origin = location.origin, selected = Object.keys(agents)) {
    if (!selected.length) return '';
    if (selected.some(id => !Object.hasOwn(agents, id))) throw new Error('Unknown agent');
    const names = selected.join(',');
    if (platform === 'windows') return "$installer = Join-Path $env:TEMP 'margen-install.ps1'\nInvoke-WebRequest -UseBasicParsing '" + origin + "/install.ps1' -OutFile $installer\npowershell.exe -NoProfile -ExecutionPolicy Bypass -File $installer -Agents '" + names + "'";
    return 'curl -fsSL ' + origin + '/install.sh | bash -s -- --agents ' + names;
  }
  function connectionCommand(platform, origin = location.origin, email = '') {
    const quotedEmail = platform === 'windows' ? "'" + email.replaceAll("'", "''") + "'" : "'" + email.replaceAll("'", "'\"'\"'") + "'";
    return (platform === 'windows' ? '& "$HOME\\.local\\bin\\margen.cmd"' : '"$HOME/.local/bin/margen"') + ' connect --server ' + origin + (email ? ' --email ' + quotedEmail : '');
  }
  function selector(target, code, onChange = () => {}) {
    const id = 'install-' + (++sequence), root = node('div', '', 'install-picker');
    const system = node('fieldset'), legend = node('legend', '01 · Tu sistema'); system.append(legend);
    const grid = node('div', '', 'install-platforms');
    const initial = /Windows/i.test(navigator.userAgent) ? 'windows' : /Mac/i.test(navigator.userAgent) ? 'mac' : 'linux';
    for (const [value, title] of [['mac','macOS'],['linux','Linux'],['windows','Windows']]) {
      const label = node('label', '', 'install-option'), input = node('input');
      input.type = 'radio'; input.name = id + '-os'; input.value = value; input.checked = value === initial;
      const face = node('span', '', 'install-option-face'); face.append(icon(value), node('span',title));
      label.append(input,face); grid.append(label);
    }
    system.append(grid);
    const wsl = node('label', '', 'install-wsl'), wslInput = node('input'); wslInput.type = 'checkbox'; wslInput.name = id + '-wsl';
    wsl.append(wslInput, node('span','Mi agente corre dentro de WSL')); system.append(wsl);
    const platformHelp = node('p', '', 'install-help'); system.append(platformHelp);
    const agentSet = node('fieldset'); agentSet.append(node('legend','02 · Tus agentes'), node('p','Elige uno o varios. Instalaremos el skill en cada uno.', 'install-help'));
    const agentGrid = node('div', '', 'install-agents');
    for (const [value, [title]] of Object.entries(agents)) {
      const label = node('label', '', 'install-option'), input = node('input');
      input.type = 'checkbox'; input.name = id + '-agent'; input.value = value;
      const face = node('span', '', 'install-option-face'), tick = icon('check'); tick.classList.add('install-tick');
      face.append(icon(value),node('span',title),tick); label.append(input,face); agentGrid.append(label);
    }
    agentSet.append(agentGrid, node('p','Necesitas tener instalado el agente. Margen añade la biblioteca y sus instrucciones.', 'install-help'));
    root.append(system, agentSet); target.append(root);
    let state;
    const update = () => {
      const os = root.querySelector('input[type=radio]:checked').value;
      wsl.hidden = os !== 'windows';
      const platform = os === 'windows' && wslInput.checked ? 'wsl' : os;
      const selected = Array.from(agentGrid.querySelectorAll('input:checked'), el => el.value);
      platformHelp.textContent = platform === 'windows' ? 'PowerShell · Python 3.10+. Sin Bash ni permisos de administrador.' : platform === 'wsl' ? 'Bash dentro de WSL. El skill se instala en tu usuario de Linux, separado de Windows.' : 'Bash · Python 3.10+, curl y OpenSSL.';
      code.textContent = command(platform, location.origin, selected) || 'Elige al menos un agente para preparar tu comando.';
      state = {platform, agents:selected, valid:!!selected.length, names:selected.map(id=>agents[id][0]), paths:selected.map(id=>(platform==='windows'?'$HOME\\':'~/')+agents[id][1]+(platform==='windows'?'\\skills\\margen':'/skills/margen')), shell:platform==='windows'?'PowerShell':'Bash'};
      onChange(platform, state);
    };
    root.addEventListener('change',update); update();
    return {element:root, get state(){ return state; }};
  }
  async function copyText(text, status, source) {
    try { await navigator.clipboard.writeText(text); status.textContent = 'Copiado. Pégalo en tu terminal.'; }
    catch {
      const range = document.createRange(); range.selectNodeContents(source); const selection = getSelection(); selection.removeAllRanges(); selection.addRange(range);
      status.textContent = 'Seleccionado. Usa Copiar en tu navegador.';
    }
  }
  return {command, connectionCommand, selector, icon, copyText};
})();
