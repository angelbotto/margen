/* File bytes stay outside the account DOM. Inspection never publishes. */
window.MargenUpload = (() => {
  const MiB = 1024 * 1024;
  const size = bytes => bytes < MiB ? `${Math.ceil(bytes / 1024)} KB` : `${(bytes / MiB).toFixed(1)} MB`;
  function create({api, navigate = url => location.assign(url)}) {
    const dialog = document.querySelector('#upload-dialog'), form = dialog.querySelector('form');
    const input = form.elements.file, drop = form.querySelector('[data-upload-drop]');
    const report = form.querySelector('[data-upload-report]'), status = form.querySelector('[data-upload-status]');
    const error = form.querySelector('.form-error'), submit = form.querySelector('[type=submit]');
    let selected = null, inspection = null, encoded = null, revision = null, generation = 0, busy = false;
    const node = (tag, text, cls) => { const el = document.createElement(tag); el.textContent = text; if(cls) el.className = cls; return el; };
    const base64 = file => new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(String(reader.result).split(',')[1]);
      reader.onerror = () => reject(Error('No se pudo leer el archivo. Vuelve a seleccionarlo.'));
      reader.readAsDataURL(file);
    });
    function state(message, working = false) {
      status.textContent = message;
      form.setAttribute('aria-busy', String(working));
      submit.disabled = working || !inspection;
      submit.textContent = working && busy ? 'Guardando…' : revision ? 'Guardar revisión privada' : 'Crear artefacto privado';
    }
    async function choose(files) {
      if (busy) return;
      const ticket = ++generation;
      selected = null; inspection = null; encoded = null; report.hidden = true; error.textContent = '';
      state('');
      if (!files?.length) return;
      if (files.length !== 1) { error.textContent = 'Selecciona un archivo. Para incluir imágenes y estilos, agrúpalos en un ZIP.'; return; }
      const file = files[0], extension = file.name.split('.').pop().toLowerCase();
      if (!['html', 'htm', 'pdf', 'zip'].includes(extension)) { error.textContent = 'Elige un HTML, un PDF o un ZIP con tu página y sus recursos.'; return; }
      if (!file.size || file.size > (extension === 'pdf' ? 12 : 15) * MiB) { error.textContent = extension === 'pdf' ? 'El PDF debe ocupar entre 1 byte y 12 MB.' : 'El HTML o ZIP debe ocupar entre 1 byte y 15 MB.'; return; }
      selected = file;
      state(`Revisando ${file.name} · ${size(file.size)}…`, true);
      try {
        const data = await base64(file);
        if (ticket !== generation) return;
        const result = await api('/api/uploads/inspect', {method: 'POST', body: JSON.stringify({name: file.name, data})});
        if (ticket !== generation) return;
        inspection = result; encoded = data;
        if (!form.elements.title.value.trim()) form.elements.title.value = result.title || file.name.replace(/\.[^.]+$/, '');
        report.replaceChildren();
        const heading = node('div', '', 'upload-file-heading');
        heading.append(node('strong', file.name), node('span', `${result.kind.toUpperCase()} · ${size(file.size)}`, 'upload-file-meta'));
        report.append(heading);
        const details = [];
        if (result.entry) details.push(`Página inicial: ${result.entry}`);
        if (result.pages) details.push(`${result.pages} páginas · vista previa visual`);
        details.push(result.kind === 'html' ? 'Tu diseño se conserva. Puedes subir HTML sin usar la biblioteca.' : result.kind === 'zip' ? 'Página estática con sus recursos locales.' : 'Se conserva el original para descargarlo.');
        report.append(node('p', details.join(' ')));
        if (result.files?.length > 1) {
          const list = node('details', ''); list.append(node('summary', `${result.files.length} archivos revisados`));
          const ul = node('ul', '', 'upload-file-list');
          for (const f of result.files) { const li = node('li', ''); li.append(node('span', f.path), node('small', size(f.size))); ul.append(li); }
          list.append(ul); report.append(list);
        }
        if (result.warnings?.length) {
          const box = node('div', '', 'upload-warnings'); box.append(node('strong', 'Antes de continuar'));
          const ul = node('ul', ''); result.warnings.forEach(warning => ul.append(node('li', warning))); box.append(ul); report.append(box);
        }
        report.hidden = false;
        state('Archivo revisado. Aún no se ha creado ningún artefacto.');
      } catch (e) { if (ticket === generation) { inspection = null; error.textContent = e.message; state('No se pudo preparar el archivo.'); } }
    }
    input.addEventListener('change', () => choose(input.files));
    drop.addEventListener('dragover', e => { e.preventDefault(); if (!busy) drop.dataset.dragging = ''; });
    drop.addEventListener('dragleave', e => { if (!drop.contains(e.relatedTarget)) delete drop.dataset.dragging; });
    drop.addEventListener('drop', e => { e.preventDefault(); delete drop.dataset.dragging; choose(e.dataTransfer.files); });
    form.addEventListener('submit', async e => {
      e.preventDefault();
      if (busy || !inspection || !selected || !encoded || !form.reportValidity()) return;
      busy = true; error.textContent = ''; state('Guardando tu artefacto privado…', true);
      for (const el of form.querySelectorAll('[data-close],input,select')) el.disabled = true;
      try {
        const body = {name:selected.name, data:encoded, title:form.elements.title.value, space:form.elements.space.value,
          ...(revision ? {artifact:revision.id, expected_current:revision.current_version, mode:'draft'} : {}),
          source:{agent:form.elements.agent.value, device:form.elements.device.value, session:form.elements.session.value}};
        if (inspection.entry) body.entry = inspection.entry;
        const original = form.elements.original.files[0];
        if (original) {
          if (original.size > 12 * MiB) throw Error('El original debe ocupar menos de 12 MB.');
          body.attachments = [{name:'original.' + original.name.split('.').pop().toLowerCase(), data:await base64(original)}];
        }
        const result = await api('/api/uploads', {method:'POST', body:JSON.stringify(body)});
        navigate('/a/' + encodeURIComponent(result.id) + (result.state === 'draft' ? '?version=' + encodeURIComponent(result.version) : ''));
      } catch (e) { error.textContent = e.message; }
      finally { busy = false; for (const el of form.querySelectorAll('[data-close],input,select')) el.disabled = false; state(inspection ? 'Archivo preparado para guardar.' : ''); }
    });
    dialog.addEventListener('cancel', e => { if (busy) e.preventDefault(); });
    dialog.addEventListener('close', () => { ++generation; selected = inspection = encoded = null; });
    return {open(artifact = null) {
      if (busy) return;
      ++generation; revision = artifact ? {id:artifact.id, current_version:artifact.current_version} : null;
      selected = inspection = encoded = null; form.reset(); error.textContent = ''; report.hidden = true;
      form.elements.title.value = artifact?.title || ''; form.elements.space.value = artifact?.space || 'Personal';
      form.querySelector('#upload-heading').textContent = artifact ? 'Subir una revisión' : 'Un archivo. Un enlace.';
      form.querySelector('[data-upload-intro]').textContent = artifact ? 'Revisa una nueva versión antes de cambiar lo que ven tus lectores. El enlace y los comentarios se conservan.' : 'Arrastra tu documento y compártelo cuando esté listo. Empieza privado, con tu diseño y tu contenido.';
      state(''); dialog.showModal();
    }};
  }
  return {create};
})();
