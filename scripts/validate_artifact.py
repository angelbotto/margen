#!/usr/bin/env python3
"""Verifica un archivo final contra el contrato estándar; no prueba su navegador."""
import argparse
from pathlib import Path
from contract_artifact import validate,composition_warnings

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('archivo',type=Path);p.add_argument('--strict-composition',action='store_true',help='Fail on custom prose wrappers without a spacing contract.');args=p.parse_args()
 try:
  html=args.archivo.read_text();errors=validate(html);warnings=composition_warnings(html)
 except OSError as e:p.exit(1,str(e)+'\n')
 for warning in warnings:print('COMPOSITION: '+warning)
 if args.strict_composition:errors+=warnings
 if errors:p.exit(1,'\n'.join('ERROR: '+e for e in errors)+'\n')
 print('Contrato estándar correcto: apariencia, audio con silencio/prueba/volumen, comentarios, lectura, dependencias, fuentes y referencias. Falta comprobar comportamiento en navegador.')
if __name__=='__main__':main()
