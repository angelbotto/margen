"""Render pipeline probe: an author custom element whose name starts with html- ahead of any script/style/body."""
import sys, tempfile
from pathlib import Path
REPO = Path(sys.argv[1]).resolve(); sys.path.insert(0, str(REPO))
from fastapi.testclient import TestClient
from portal.app import create_app, COOKIE
O = 'https://portal.test'; tmp = tempfile.TemporaryDirectory()
app = create_app(tmp.name, origin=O, issuer='https://identity.test', audience='our-app'); st = app.state.store
c = TestClient(app, base_url=O, headers={'Origin': O}); u = st.user('o@example.com', 'P'); c.cookies.set(COOKIE, st.session(u['id']))
reg = '<script>/* REGISTRO TEMAS */ const themeRegistry = {"familias":[{"id":"editorial","light":"light","dark":"dark"}]};</script>'
html = '<meta name="nota-documento" content="probe-ce"><meta name="nota-tema-inicial" content="editorial"><meta name="nota-modo-inicial" content="dark"><html-include src="x"></html-include><p>Hola</p>' + reg
r = c.post('/api/artifacts', json={'title': 'ce', 'html': html}); r.raise_for_status(); aid = r.json()['id']
out = c.get('/api/artifacts/' + aid + '/render').text
i = out.find('html-include'); print(sys.argv[2], repr(out[max(0, i - 40):i + 30]))
