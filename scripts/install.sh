#!/usr/bin/env bash
# Shell entrypoint; verified installer and generator require Python 3.10+.
set -euo pipefail
main() {
  printf '\nMargen · instalar o actualizar\n\n'
  printf 'Se preparará el skill para los agentes seleccionados.\nLa actualización conserva tu selección anterior.\n\n'
  printf 'Agentes disponibles: Codex, Claude Code y Hermes.\n'
  printf 'Este instalador configura agentes locales; no instala extensiones en la web de ChatGPT.\n'
  printf 'Se instala para tu usuario del sistema. No incluye una cuenta ni un token.\n'
  printf 'Cada persona debe entrar al portal con su correo y crear su propia conexión.\n'
  printf 'Las actualizaciones conservan tus credenciales; publicar requiere confirmar su cuenta.\n\n'
  if ! command -v curl >/dev/null 2>&1; then
    printf 'Falta curl. Instálalo con el gestor de paquetes de tu sistema.\n' >&2; return 1
  fi
  local bottifact_python='' candidate bottifact_tmp
  for candidate in python3 /opt/homebrew/bin/python3 /usr/local/bin/python3 python3.13 python3.12 python3.11 python3.10; do
    if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import sys; raise SystemExit(sys.version_info < (3,10))' >/dev/null 2>&1; then
      bottifact_python="$candidate"; break
    fi
  done
  if [ -z "$bottifact_python" ]; then
    printf 'El generador necesita Python 3.10+.\n' >&2
    if command -v brew >/dev/null 2>&1; then printf 'Ejecuta: brew install python\n' >&2
    else printf 'Instala Python desde https://www.python.org/downloads/ y repite este comando.\n' >&2; fi
    return 1
  fi
  bottifact_tmp="$(mktemp -d "${TMPDIR:-/tmp}/bottifact-install.XXXXXX")"
  trap "rm -rf -- $(printf '%q' "$bottifact_tmp")" EXIT
  printf 'Descargando y verificando la versión publicada…\n'
  curl --proto '=https' --tlsv1.2 -fsS --max-time 60 https://artifacts.botto.is/install.py -o "$bottifact_tmp/install.py"
  "$bottifact_python" "$bottifact_tmp/install.py" --servidor https://artifacts.botto.is "$@"
  rm -rf -- "$bottifact_tmp"
  trap - EXIT
  printf '\nPara futuras actualizaciones: margen update\n'
  printf 'ChatGPT: https://artifacts.botto.is/downloads/bottifact-portable.zip\n'
  printf 'Abre una conversación nueva y pide: «Usa el skill margen».\n'
}
main "$@"
