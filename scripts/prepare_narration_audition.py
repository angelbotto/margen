#!/usr/bin/env python3
"""Prepare a synthetic private audition locally. No network or synthesis calls."""
import hashlib
import json
from pathlib import Path
from contract_artifact import build

ROOT=Path(__file__).resolve().parents[1]

def main():
    source=(ROOT/'examples/content/narration-audition.html').read_text()
    folder=ROOT/'tests/artifacts/narration-audition';folder.mkdir(parents=True,exist_ok=True)
    source_sha=hashlib.sha256(source.encode()).hexdigest()
    scorecard=folder/'scorecard.pending.json'
    if scorecard.exists() and json.loads(scorecard.read_text()).get('source_sha256')!=source_sha:
        raise SystemExit('Corpus changed. Preserve the previous audition folder before preparing a new scorecard.')
    html=build('Narración · Corpus sintético ES / EN', [{'id':'audition','titulo':'Prueba de escucha','html':source}],document_id='margen-neural-audition',theme='kaira',mode='light')
    (folder/'audition.html').write_text(html)
    card={'status':'pending_real_listening','provider':None,'model':None,'stock_voice':None,'region':None,'budget_approved':None,'actual_cost':None,'timestamp':None,'browser':None,'listener':None,'source_sha256':source_sha,'conditions':[]}
    for section in ('es-report','es-narrative','en-report','en-narrative','mixed-report','mixed-narrative'):
        for profile in ('report','narrative'):
            card['conditions'].append({'section':section,'profile':profile,'pronunciation_es':None,'pronunciation_en':None,'language_switching':None,'naturalness':None,'pauses_rhythm':None,'document_fit':None,'fragment_continuity':None,'time_to_first_audio_ms':None,'fidelity_errors':[],'listened':False,'accepted':False})
    if not scorecard.exists():scorecard.write_text(json.dumps(card,ensure_ascii=False,indent=2)+'\n')
    print('Prepared synthetic HTML and pending scorecard in tests/artifacts/narration-audition/. No provider called.')

if __name__=='__main__':main()
