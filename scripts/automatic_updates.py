"""Opt-in per-user background updates for managed Margen libraries."""
import hashlib
import json
import os
from pathlib import Path
import plistlib
import subprocess
import sys


def configure(action, destination, home=None, platform=None, run=subprocess.run):
    home=Path(home or Path.home());platform=platform or sys.platform
    destination=Path(destination).absolute()
    label='is.botto.bottifact.updates.'+hashlib.sha256(str(destination).encode()).hexdigest()[:10]
    command=[sys.executable,str(destination/'scripts/update.py'),'--destination',str(destination),'--if-changed']
    logs=home/'.local/state/bottifact';logs.mkdir(parents=True,exist_ok=True);logs.chmod(0o700)
    if platform == 'win32':
        import datetime
        import xml.etree.ElementTree as ET
        directory = home/'.local/state/bottifact'; path = directory/(label+'.xml')
        task_name = 'Margen-' + label.rsplit('.',1)[-1]
        if action == 'status':
            result = run(['schtasks.exe','/Query','/TN',task_name],capture_output=True,text=True,check=False)
            return {'configured':result.returncode == 0,'scheduler':'windows-task-scheduler','interval_hours':6,'definition':str(path)}
        if action == 'disable':
            result = run(['schtasks.exe','/Delete','/TN',task_name,'/F'],capture_output=True,text=True,check=False)
            if result.returncode:
                present = run(['schtasks.exe','/Query','/TN',task_name],capture_output=True,text=True,check=False)
                if present.returncode == 0: raise ValueError('Could not disable the Windows update task.')
            path.unlink(missing_ok=True)
            return {'configured':False,'scheduler':'windows-task-scheduler'}
        identity = run(['powershell.exe','-NoProfile','-NonInteractive','-Command','[System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value'],capture_output=True,text=True,check=True).stdout.strip()
        import re
        if not re.fullmatch(r'S-1-[0-9-]+',identity): raise ValueError('Could not identify the current Windows user.')
        task = ET.Element('Task',{'version':'1.2','xmlns':'http://schemas.microsoft.com/windows/2004/02/mit/task'})
        triggers = ET.SubElement(task,'Triggers'); trigger = ET.SubElement(triggers,'TimeTrigger')
        repetition = ET.SubElement(trigger,'Repetition'); ET.SubElement(repetition,'Interval').text = 'PT6H'
        ET.SubElement(trigger,'StartBoundary').text = (datetime.datetime.now()+datetime.timedelta(minutes=5)).isoformat(timespec='seconds')
        ET.SubElement(trigger,'Enabled').text = 'true'
        principal = ET.SubElement(ET.SubElement(task,'Principals'),'Principal',{'id':'Author'})
        for key,value in [('UserId',identity),('LogonType','InteractiveToken'),('RunLevel','LeastPrivilege')]: ET.SubElement(principal,key).text = value
        settings = ET.SubElement(task,'Settings')
        for key,value in [('MultipleInstancesPolicy','IgnoreNew'),('DisallowStartIfOnBatteries','false'),('StopIfGoingOnBatteries','false'),('StartWhenAvailable','true')]: ET.SubElement(settings,key).text = value
        execute = ET.SubElement(ET.SubElement(task,'Actions',{'Context':'Author'}),'Exec')
        ET.SubElement(execute,'Command').text = sys.executable
        ET.SubElement(execute,'Arguments').text = subprocess.list2cmdline(['-X','utf8',*command[1:]])
        path.write_bytes(ET.tostring(task,encoding='utf-16',xml_declaration=True))
        result = run(['schtasks.exe','/Create','/TN',task_name,'/XML',str(path),'/F'],capture_output=True,text=True,check=False)
        if result.returncode: raise ValueError('Windows could not register the per-user task. Use margen update manually. '+result.stderr.strip())
        return {'configured':True,'scheduler':'windows-task-scheduler','interval_hours':6,'definition':str(path)}
    if platform=='darwin':
        directory=home/'Library/LaunchAgents';path=directory/(label+'.plist')
        if action=='status':return {'configured':path.exists(),'scheduler':'launchd','interval_hours':6,'definition':str(path)}
        run(['launchctl','bootout','gui/'+str(os.getuid())+'/'+label],capture_output=True,check=False)
        if action=='disable':path.unlink(missing_ok=True);return {'configured':False,'scheduler':'launchd'}
        directory.mkdir(parents=True,exist_ok=True)
        for name in ['updates.log','updates-error.log']:
            log=logs/name;log.touch(exist_ok=True);log.chmod(0o600)
        data={'Label':label,'ProgramArguments':command,'RunAtLoad':True,'StartInterval':21600,
              'StandardOutPath':str(logs/'updates.log'),'StandardErrorPath':str(logs/'updates-error.log')}
        path.write_bytes(plistlib.dumps(data));path.chmod(0o600)
        result=run(['launchctl','bootstrap','gui/'+str(os.getuid()),str(path)],capture_output=True,text=True,check=False)
        if result.returncode:raise ValueError('La tarea está escrita, pero launchd no la activó. Ejecuta el comando desde una sesión de usuario abierta. '+result.stderr.strip())
        return {'configured':True,'scheduler':'launchd','interval_hours':6,'definition':str(path)}
    if platform.startswith('linux'):
        directory=home/'.config/systemd/user';service=directory/(label+'.service');timer=directory/(label+'.timer')
        if action=='status':return {'configured':timer.exists(),'scheduler':'systemd-user','interval_hours':6,'definition':str(timer)}
        if action=='disable':
            run(['systemctl','--user','disable','--now',label+'.timer'],capture_output=True,check=False)
            timer.unlink(missing_ok=True);service.unlink(missing_ok=True)
            run(['systemctl','--user','daemon-reload'],check=True);return {'configured':False,'scheduler':'systemd-user'}
        directory.mkdir(parents=True,exist_ok=True)
        if any('\n' in arg or '\r' in arg for arg in command):raise ValueError('Ruta de comando no válida.')
        quoted=' '.join('"'+arg.replace('\\','\\\\').replace('"','\\"').replace('%','%%').replace('$','$$')+'"' for arg in command)
        service.write_text('[Unit]\nDescription=Update the managed Margen skill\n[Service]\nType=oneshot\nExecStart='+quoted+'\n')
        timer.write_text('[Unit]\nDescription=Check Margen every six hours\n[Timer]\nOnStartupSec=5m\nOnUnitActiveSec=6h\nRandomizedDelaySec=5m\n[Install]\nWantedBy=timers.target\n')
        run(['systemctl','--user','daemon-reload'],check=True);run(['systemctl','--user','enable','--now',label+'.timer'],check=True)
        return {'configured':True,'scheduler':'systemd-user','interval_hours':6,'definition':str(timer)}
    raise ValueError('Automatic scheduling supports macOS, Linux user systemd and Windows Task Scheduler. Usa update manualmente en otros entornos.')
