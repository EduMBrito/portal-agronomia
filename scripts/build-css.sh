#!/usr/bin/env bash
#
# Compila assets/css/input.css -> static/css/tailwind.css
#
#   ./scripts/build-css.sh           # build minificado — rode antes de commitar
#   ./scripts/build-css.sh --watch    # recompila sozinho ao salvar um template
#
# Usa o binário standalone do Tailwind: não precisa de Node nem npm, nem aqui
# nem no servidor do campus. O binário é baixado uma vez em .bin/ (ignorado
# pelo Git) e reaproveitado nas execuções seguintes.
#
set -euo pipefail

TAILWIND_VERSION="v4.3.3"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN_DIR="$ROOT/.bin"
BIN="$BIN_DIR/tailwindcss-$TAILWIND_VERSION"
INPUT="$ROOT/assets/css/input.css"
OUTPUT="$ROOT/static/css/tailwind.css"

case "$(uname -s)-$(uname -m)" in
  Darwin-arm64)   TARGET="macos-arm64" ;;
  Darwin-x86_64)  TARGET="macos-x64"   ;;
  Linux-aarch64)  TARGET="linux-arm64" ;;
  Linux-x86_64)   TARGET="linux-x64"   ;;
  *)
    echo "Plataforma não suportada: $(uname -s)-$(uname -m)" >&2
    echo "Baixe o binário manualmente em:" >&2
    echo "  https://github.com/tailwindlabs/tailwindcss/releases/tag/$TAILWIND_VERSION" >&2
    exit 1
    ;;
esac

if [ ! -x "$BIN" ]; then
  echo "==> Baixando Tailwind CLI $TAILWIND_VERSION ($TARGET)..."
  mkdir -p "$BIN_DIR"
  curl -sSL --fail \
    -o "$BIN" \
    "https://github.com/tailwindlabs/tailwindcss/releases/download/$TAILWIND_VERSION/tailwindcss-$TARGET"
  chmod +x "$BIN"
fi

mkdir -p "$(dirname "$OUTPUT")"

if [ "${1:-}" = "--watch" ]; then
  echo "==> Observando templates/ e apps/ — Ctrl+C para sair"
  exec "$BIN" -i "$INPUT" -o "$OUTPUT" --watch
fi

echo "==> Compilando static/css/tailwind.css..."
"$BIN" -i "$INPUT" -o "$OUTPUT" --minify
echo "==> Pronto: $(du -h "$OUTPUT" | cut -f1) em static/css/tailwind.css"
