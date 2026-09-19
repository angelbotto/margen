#!/usr/bin/env python3
"""Local adapter tests do not launch an agent or contact a server."""
import io,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import agent_connector as connector

class AdapterTests(unittest.TestCase):
 def test_fixed_commands_and_invalid_sessions(self):
  self.assertEqual(connector.command('Codex','actual-session','prompt'),['codex','exec','resume','actual-session','prompt'])
  self.assertEqual(connector.command('Claude','','prompt'),['claude','--print','prompt'])
  self.assertEqual(connector.command('Hermes','actual-session','prompt'),['hermes','--resume','actual-session','-z','prompt'])
  with self.assertRaises(ValueError):connector.command('Codex','--dangerous','prompt')
 def test_stdio_tool_failure_is_a_tool_result(self):
  requests=[{'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2025-11-25'}},{'jsonrpc':'2.0','id':2,'method':'tools/list'},{'jsonrpc':'2.0','id':3,'method':'tools/call','params':{'name':'margen_assignment','arguments':{'job':'a'*32}}}]
  output=io.StringIO()
  with patch.object(connector.sys,'stdin',io.StringIO('\n'.join(json.dumps(r) for r in requests))),patch.object(connector.sys,'stdout',output),patch.object(connector,'api',side_effect=ValueError('Revoked')):connector.mcp({})
  responses=[json.loads(line) for line in output.getvalue().splitlines()]
  self.assertEqual(len(responses[1]['result']['tools']),3);self.assertTrue(responses[2]['result']['isError'])
 def test_private_config_permissions(self):
  with tempfile.TemporaryDirectory() as folder:
   p=Path(folder)/'config';connector.private(p,'{}');self.assertEqual(p.stat().st_mode&0o777,0o600)
if __name__=='__main__':unittest.main()
