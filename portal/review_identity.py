"""Presentation of recorded review identities; never changes event ownership."""
import re

CONTROLS = re.compile(r'[\x00-\x1f\x7f-\x9f\u061c\u200e\u200f\u202a-\u202e\u2066-\u2069]')


def identity_text(value, fallback='Sin nombre'):
    if not isinstance(value, str):
        return fallback
    return ' '.join(CONTROLS.sub(' ', value).split()) or fallback


def identity_metadata(event):
    agent = identity_text(event.get('agent'), '')
    verified = event.get('verified')
    kind = 'agente' if agent else 'cuenta verificada' if verified is True else 'invitado' if verified is False else 'histórico sin verificación registrada'
    return {'tipo': kind, 'nombre': identity_text(event.get('author')), 'agente': agent or None,
            'correo_verificado': verified if isinstance(verified, bool) else None}


def byline(event):
    info = identity_metadata(event)
    return info['agente'] + ' (agente de ' + info['nombre'] + ')' if info['agente'] else info['nombre']
