import { beforeEach, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
beforeEach(()=>{ document.body.innerHTML='<section></section><pre></pre>';window.eval(readFileSync('portal/static/install-command.js','utf8')); });
it('switches shell commands without mixing Bash with native PowerShell',()=>{
 const api=(window as any).MargenInstall;
 const root=document.querySelector('section')!, code=document.querySelector('pre')!;
 const select=api.selector(root,code);
 select.value='windows';select.dispatchEvent(new Event('change'));
 expect(code.textContent).toContain('Invoke-WebRequest');expect(code.textContent).toContain('Join-Path $env:TEMP');expect(code.textContent).not.toContain('| bash');
 select.value='unix';select.dispatchEvent(new Event('change'));expect(code.textContent).toContain('/install.sh | bash');
 expect(api.command('windows','https://self.example')).toContain('https://self.example/install.ps1');
});
