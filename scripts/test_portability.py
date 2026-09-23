"""Instalación real en temporal, actualización, integridad y generación fuera del skill."""
import tempfile,zipfile,json,subprocess,unittest,sys
from pathlib import Path
from package import package
from install import install
from verify_package import verify
from contract_artifact import build,validate

class PortableTests(unittest.TestCase):
 def test_bundle_install_update_and_generate(self):
  archive=package()
  with tempfile.TemporaryDirectory(prefix='nota-portable-') as tmp:
   root=Path(tmp)
   with zipfile.ZipFile(archive) as z:z.extractall(root/'descarga')
   source=root/'descarga/bottifact';dest=root/'hermes/skills/bottifact'
   install(source,dest);verify(dest)
   with self.assertRaises(ValueError):install(source,dest)
   (dest/'marca-usuario.txt').write_text('conservar')
   _,backup=install(source,dest,True)
   self.assertEqual((backup/'marca-usuario.txt').read_text(),'conservar');self.assertFalse((dest/'marca-usuario.txt').exists())
   output=root/'examples/generated/report.html'
   subprocess.run([sys.executable,'-X','utf8',str(dest/'scripts/create_artifact.py'),'--contenido',str(dest/'examples/content/standard-content.html'),'--titulo','Prueba portable','--tema','blueprint','--estilo','tecnico','--salida',str(output)],cwd=root,check=True,capture_output=True)
   subprocess.run([sys.executable,'-X','utf8',str(dest/'scripts/validate_artifact.py'),str(output)],cwd=root,check=True,capture_output=True)
   self.assertIn('nota-tema-inicial',output.read_text())
   self.assertIn('Margen',output.read_text())
   self.assertIn('name: margen', (dest/'SKILL.md').read_text())
   self.assertEqual(dest.name,'bottifact')
   from new_component import scaffold
   scaffold(dest, 'test-release-brief', 'Release brief', 'reports')
   subprocess.run([sys.executable,'-X','utf8',str(dest/'scripts/build.py')],cwd=root,check=True,capture_output=True)
   registry=json.loads((dest/'packages/core/registry/registry.json').read_text())['componentes']
   added=next(item for item in registry if item['id']=='test-release-brief')
   self.assertEqual(added['nombre'],'Release brief')
   self.assertEqual(added['capitulo'],'reportes')
   (source/'SKILL.md').write_text('alterado')
   with self.assertRaises(ValueError):install(source,root/'otra-copia')
   self.assertFalse((root/'otra-copia').exists())
 def test_invalid_preferences(self):
  pages=[{'id':'contenido','titulo':'Título','html':'<section id="intro"><h2>Inicio</h2><p>Texto</p></section>'}]
  for kwargs in [{'theme':'desconocido'},{'style':'fuente-remota'}]:
   with self.assertRaises(ValueError):build('Prueba',pages,**kwargs)
  result=build('Prueba',pages,theme='hacker',style='tecnico');self.assertEqual(validate(result),[])
  self.assertTrue(validate(result.replace('content="hacker"','content="desconocido"')))
if __name__=='__main__':unittest.main()
