window.MargenInstall = (() => {
  function command(platform, origin = location.origin) {
    if (platform === 'windows') return "$installer = Join-Path $env:TEMP 'margen-install.ps1'\nInvoke-WebRequest -UseBasicParsing '" + origin + "/install.ps1' -OutFile $installer\npowershell.exe -NoProfile -ExecutionPolicy Bypass -File $installer";
    return 'curl -fsSL ' + origin + '/install.sh | bash';
  }
  function selector(target, code, onChange = () => {}) {
    const label = document.createElement('label'); label.textContent = 'Tu terminal '; 
    const select = document.createElement('select'); select.setAttribute('aria-label', 'Sistema de instalación');
    for (const [value, text] of [['unix','macOS / Linux / WSL · Bash'],['windows','Windows · PowerShell']]) {
      const option = document.createElement('option'); option.value=value; option.textContent=text; select.append(option);
    }
    select.value = /Windows/i.test(navigator.userAgent) ? 'windows' : 'unix';
    const update = () => { code.textContent=command(select.value); onChange(select.value); };
    select.addEventListener('change',update); label.append(select); target.append(label); update();
    return select;
  }
  return {command, selector};
})();
