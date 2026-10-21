import { beforeEach, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
beforeEach(() => { document.body.innerHTML = '<section></section><pre></pre>'; window.eval(readFileSync('portal/static/install-command.js', 'utf8')); });
const change = (selector: string, checked = true) => { const input = document.querySelector<HTMLInputElement>(selector)!; input.checked = checked; input.dispatchEvent(new Event('change', {bubbles:true})); };
it('requires an agent and generates commands for the chosen shell and selected agents only', () => {
  const api = (window as any).MargenInstall;
  const picker = api.selector(document.querySelector('section')!, document.querySelector('pre')!);
  expect(picker.state.valid).toBe(false);
  change('input[value=windows]'); change('input[value=hermes]');
  let code = document.querySelector('pre')!.textContent!;
  expect(code).toContain('Invoke-WebRequest'); expect(code).toContain("-Agents 'hermes'"); expect(code).not.toContain('| bash');
  expect(picker.state.paths).toEqual(['$HOME\\.hermes\\skills\\margen']);
  change('input[value=codex]'); change('.install-wsl input');
  code = document.querySelector('pre')!.textContent!;
  expect(code).toContain('| bash -s -- --agents codex,hermes'); expect(code).not.toContain('Invoke-WebRequest');
  expect(picker.state.platform).toBe('wsl');
  change('input[value=mac]'); expect(picker.state.platform).toBe('mac');
  expect(document.querySelector<HTMLElement>('.install-wsl')!.hidden).toBe(true);
  change('input[value=codex]',false); change('input[value=hermes]',false);
  expect(picker.state.valid).toBe(false); expect(api.command('windows', 'https://self.example', [])).toBe('');
});
it('uses the self-host origin and correctly quotes an account email in both shells', () => {
  const api=(window as any).MargenInstall;
  expect(api.command('windows','https://self.example',['claude'])).toContain('https://self.example/install.ps1');
  expect(api.command('linux','https://self.example',['claude'])).toContain('--agents claude');
  expect(api.connectionCommand('windows','https://self.example',"o'neil@example.org")).toContain("--email 'o''neil@example.org'");
  expect(api.connectionCommand('mac','https://self.example',"o'neil@example.org")).toContain("--email 'o'\"'\"'neil@example.org'");
  expect(api.connectionCommand('windows')).toContain('& "$HOME\\.local\\bin\\margen.cmd"');
  expect(() => api.command('mac','https://self.example',['unknown;bad'])).toThrow();
});
it('keeps two picker instances independent with labeled native inputs', () => {
  const api=(window as any).MargenInstall;
  const a=api.selector(document.querySelector('section'),document.querySelector('pre'));
  const target=document.createElement('section'),code=document.createElement('pre'); document.body.append(target,code);
  const b=api.selector(target,code);
  expect(a.element.querySelector('input').name).not.toBe(b.element.querySelector('input').name);
  expect(a.element.querySelectorAll('fieldset')).toHaveLength(2);
  expect(a.element.querySelectorAll('label input')).toHaveLength(7);
});
