"""Disabled-by-default candidate adapters; no claim of evaluated voice quality."""
import hashlib
import json
import os
import re
from dataclasses import dataclass, field
from decimal import Decimal
from html import escape
from urllib.request import Request, build_opener, HTTPRedirectHandler

PROFILES = {'report':'Informe', 'narrative':'Narración', 'neutral':'Lectura neutra'}

@dataclass
class Configuration:
    enabled: bool = False
    provider: str = ''
    key: str = field(default='', repr=False)
    region: str = ''
    model: str = ''
    voices: list = field(default_factory=list)
    daily_chars: int = 0
    user_chars: int = 0
    daily_micro_usd: int = 0
    price_per_million: str = '0'
    cache_bytes: int = 64 * 1024 * 1024
    cache_seconds: int = 86400
    reason: str = 'La narración neuronal aún no está configurada. No se usará una voz del dispositivo.'

    @classmethod
    def environment(cls):
        c=cls()
        if os.getenv('MARGEN_NARRATION_ENABLED')!='1':return c
        def require(value):
            if not value:raise ValueError('Invalid narration configuration')
        try:
            c.provider=os.getenv('MARGEN_NARRATION_PROVIDER','')
            c.key=os.getenv('MARGEN_NARRATION_KEY','')
            c.region=os.getenv('MARGEN_NARRATION_AZURE_REGION','')
            c.model=os.getenv('MARGEN_NARRATION_MODEL','')
            c.daily_chars=int(os.getenv('MARGEN_NARRATION_DAILY_CHARS','0'))
            c.user_chars=int(os.getenv('MARGEN_NARRATION_USER_CHARS','0'))
            c.daily_micro_usd=int(os.getenv('MARGEN_NARRATION_DAILY_MICRO_USD','0'))
            c.price_per_million=os.getenv('MARGEN_NARRATION_USD_PER_MILLION_CHARS','0')
            require(os.getenv('MARGEN_NARRATION_BILLING_APPROVED')=='1' and c.daily_micro_usd>0 and Decimal(c.price_per_million).is_finite() and Decimal(c.price_per_million)>0)
            c.voices=json.loads(os.getenv('MARGEN_NARRATION_VOICES','[]'))
            require(c.provider in ('azure','elevenlabs') and c.key and 0<c.user_chars<=c.daily_chars<=10000000)
            require(isinstance(c.voices,list) and 1<=len(c.voices)<=12)
            require(len({v['id'] for v in c.voices})==len(c.voices))
            for v in c.voices:
                require(set(v)<= {'id','label','voice','styles'})
                require(re.fullmatch(r'[a-z0-9-]{1,40}',v['id']) and isinstance(v['label'],str) and 1<=len(v['label'])<=80)
                require(re.fullmatch(r'[A-Za-z0-9:-]{1,100}',v['voice']))
                require(isinstance(v.get('styles',{}),dict))
                require(all(k in PROFILES and re.fullmatch(r'[a-z-]{1,50}',value) for k,value in v.get('styles',{}).items()))
            if c.provider=='azure':
                require(re.fullmatch(r'[a-z0-9]{2,30}',c.region))
                require(all('MultilingualNeural' in v['voice'] for v in c.voices))
                c.model='azure-multilingual-neural'
            else:require(c.model=='eleven_multilingual_v2')
            c.enabled=True;c.reason=''
        except (ValueError,TypeError,KeyError,ArithmeticError,AttributeError):
            c.enabled=False;c.reason='La configuración de narración está incompleta. El administrador debe revisar proveedor, voces y límites.'
        return c

    def public(self):
        return {'enabled':self.enabled,'reason':self.reason,'provider':{'azure':'Azure Speech','elevenlabs':'ElevenLabs'}.get(self.provider,''),
                'voices':[{'id':v['id'],'label':v['label']} for v in self.voices] if self.enabled else [],
                'profiles':[{'id':k,'label':v} for k,v in PROFILES.items()], 'external':True, 'quality_validated':False}

    def fingerprint(self):
        # Key material never enters the hash, cache, logs or responses.
        value=[self.provider,self.region,self.model,self.voices,'prosody-v1','mp3']
        return hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()


def prosody(block,profile):
    heading=block['kind'].startswith('h') and block['kind'][1:].isdigit()
    table=block['kind'] in ('td','th','caption')
    return {'pause_ms':450 if heading else 220 if table else 300,
            'rate':'-6%' if profile=='report' or table else '-2%' if profile=='narrative' else '0%',
            'pitch':'+2%' if heading else '0%'}


def request_data(config,block,voice,profile):
    """No document text is interpolated into instructions; SSML text is escaped."""
    p=prosody(block,profile)
    if config.provider=='azure':
        text=''.join(f'<lang xml:lang="{escape(r["lang"],quote=True)}">{escape(r["text"])}</lang>' if r['lang'] else escape(r['text']) for r in block['runs'])
        text=f'<prosody rate="{p["rate"]}" pitch="{p["pitch"]}">{text}</prosody>'
        style=voice.get('styles',{}).get(profile)
        if style:text=f'<mstts:express-as style="{escape(style,quote=True)}">{text}</mstts:express-as>'
        body=(f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="es-ES"><voice name="{escape(voice["voice"],quote=True)}">{text}</voice></speak>').encode()
        return (f'https://{config.region}.tts.speech.microsoft.com/cognitiveservices/v1',body,
                {'Ocp-Apim-Subscription-Key':config.key,'Content-Type':'application/ssml+xml','X-Microsoft-OutputFormat':'audio-24khz-96kbitrate-mono-mp3','User-Agent':'MargenReader'})
    if config.provider=='elevenlabs':
        body=json.dumps({'text':block['text'],'model_id':config.model,
                         'voice_settings':{'stability':.7 if profile=='report' else .5,'similarity_boost':.75,'style':.2 if profile=='narrative' else 0,'use_speaker_boost':True,'speed':.94 if profile=='report' else 1.0}}).encode()
        return (f'https://api.elevenlabs.io/v1/text-to-speech/{voice["voice"]}/stream?output_format=mp3_44100_128',body,
                {'xi-api-key':config.key,'Content-Type':'application/json'})
    raise ValueError('Proveedor no implementado.')


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None


class Provider:
    def __init__(self,config):self.config=config
    def open(self,block,voice,profile):
        url,body,headers=request_data(self.config,block,voice,profile)
        response=build_opener(NoRedirect()).open(Request(url,data=body,headers=headers,method='POST'),timeout=15)
        if response.headers.get_content_type() not in ('audio/mpeg','audio/mp3','application/octet-stream'):
            response.close();raise ValueError('Respuesta de audio inválida.')
        return response
