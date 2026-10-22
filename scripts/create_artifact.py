#!/usr/bin/env python3
"""Compone una o varias páginas con los controles obligatorios. Sin instalaciones ni red."""
import argparse,json
from pathlib import Path
from contract_artifact import build,THEMES,STYLES,MODES,composition_warnings
from brands import BRANDS
from project_profile import resolve, FORMATS

def main():
 p=argparse.ArgumentParser(description=__doc__);group=p.add_mutually_exclusive_group(required=True);group.add_argument('--content','--contenido',dest='contenido',type=Path);group.add_argument('--config',type=Path)
 p.add_argument('--theme','--tema',dest='tema',choices=THEMES);p.add_argument('--mode','--modo',dest='modo',choices=MODES);p.add_argument('--typography','--estilo',dest='estilo',choices=STYLES)
 p.add_argument('--brand','--marca',dest='marca',choices=[*BRANDS,'bottifact','margen'],help='Identidad y logo del documento; por defecto se infiere de un tema de marca.')
 p.add_argument('--project-root',type=Path,help='Discover .margen.json or an exact Git remote identity here. Defaults to the content/config directory.')
 p.add_argument('--project-profile',type=Path,help='Explicit project profile, with local logo paths relative to it.')
 p.add_argument('--no-project',action='store_true',help='Disable project discovery.')
 p.add_argument('--format',choices=FORMATS,help='Document, chapters or presentation; default follows page count.')
 p.add_argument('--theme-policy',choices=['project','reader'],help='Project defaults or saved reader appearance.')
 p.add_argument('--date','--fecha',dest='fecha',help='Explicit publication date, YYYY-MM-DD. Never inferred.');p.add_argument('--document-id','--documento-id',dest='documento_id');p.add_argument('--title','--titulo',dest='titulo');p.add_argument('--description','--descripcion',dest='descripcion',default='');p.add_argument('--output','--salida',dest='salida',required=True,type=Path);args=p.parse_args()
 try:
  config={}
  if args.config:
   config=json.loads(args.config.read_text());title=config.get('title',config.get('titulo'));description=config.get('description',config.get('descripcion',''));page_configs=config.get('pages',config.get('paginas',[]));pages=[{**page,'titulo':page.get('title',page.get('titulo')),'html':(args.config.parent/page.get('content',page.get('contenido'))).read_text()} for page in page_configs]
  else:
   if not args.titulo:p.error('--titulo es obligatorio con --contenido')
   title=args.titulo;description=args.descripcion;pages=[{'id':'contenido','titulo':title,'html':args.contenido.read_text()}]
  sources=([args.config]+[args.config.parent/page.get('content',page.get('contenido')) for page in page_configs]) if args.config else [args.contenido]
  if args.salida.resolve() in [path.resolve() for path in sources]:raise ValueError('La salida no puede sobrescribir las fuentes de contenido.')
  if args.no_project and (args.project_profile or args.project_root):raise ValueError('--no-project cannot be combined with a project root/profile.')
  project={} if args.no_project else resolve(args.project_root or (args.config or args.contenido).resolve().parent,args.project_profile)
  prefs=project.get('preferences',{})
  def option(cli,key,legacy=None):return cli if cli is not None else config.get(key,config.get(legacy)) if key in config or legacy in config else prefs.get(key)
  result=build(title,pages,description,mode=option(args.modo,'mode','modo'),theme=option(args.tema,'theme','tema'),style=option(args.estilo,'typography','estilo'),document_id=option(args.documento_id,'document_id','documento_id'),marca=option(args.marca,'brand','marca'),project=project,format=option(args.format,'format'),theme_policy=option(args.theme_policy,'themePolicy'),date=args.fecha if args.fecha is not None else config.get('date',config.get('fecha')),footer=config.get('footer',config.get('pie')),reactions=config.get('reactions',config.get('reacciones',False)))

  for warning in composition_warnings(result):print('COMPOSITION: '+warning)
  args.salida.parent.mkdir(parents=True,exist_ok=True);args.salida.write_text(result)
  print(str(args.salida)+': base estándar verificada; '+str(len(pages))+' página(s). Probar a 320/390 px y en navegador antes de compartir.')
 except (ValueError,KeyError,TypeError,OSError) as error:p.exit(1,str(error)+'\n')
if __name__=='__main__':main()
