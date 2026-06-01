#!/usr/bin/env bash
set -euo pipefail

if command -v audiveris >/dev/null 2>&1; then
  echo "Audiveris encontrado: $(command -v audiveris)"
  exit 0
fi

cat <<'MSG'
Audiveris não foi encontrado no PATH.

Opções:
1. Instale pelo release oficial:
   https://github.com/Audiveris/audiveris/releases

2. Depois rode o app apontando para o executável:
   AUDIVERIS_CMD=/caminho/para/audiveris uvicorn app.main:app --reload

3. Se criar um symlink chamado audiveris no PATH, o app detecta automaticamente.
MSG

exit 1
