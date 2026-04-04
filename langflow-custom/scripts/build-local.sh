#!/usr/bin/env bash
# Build local do frontend Langflow customizado (sem Docker).
# Útil para iterar rapidamente na customização sem esperar pelo pipeline Docker.
#
# Uso:
#   bash scripts/build-local.sh           # usa versão 1.8.3 (default)
#   bash scripts/build-local.sh 1.9.0     # usa versão específica
#
# Requer: node 20+, git
# Output: /tmp/langflow-rid-build/dist/

set -euo pipefail

LANGFLOW_VERSION="${1:-1.8.3}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CUSTOMIZATION_DIR="$(cd "$SCRIPT_DIR/../customization" && pwd)"
WORK_DIR="/tmp/langflow-rid-build"

echo "→ Langflow v${LANGFLOW_VERSION} — build customizado RID"
echo "→ Customization: $CUSTOMIZATION_DIR"
echo "→ Output: $WORK_DIR/dist/"
echo ""

# Limpar build anterior
rm -rf "$WORK_DIR"
mkdir -p "$WORK_DIR"

echo "[1/4] Clonando Langflow v${LANGFLOW_VERSION} (sparse checkout)..."
git clone \
  --filter=blob:none \
  --no-checkout \
  --depth=1 \
  --branch "v${LANGFLOW_VERSION}" \
  https://github.com/langflow-ai/langflow.git "$WORK_DIR"

cd "$WORK_DIR"
git sparse-checkout init --cone
git sparse-checkout set src/frontend
git checkout

cd src/frontend

echo "[2/4] Instalando dependências npm..."
npm ci --prefer-offline

echo "[3/4] Copiando overrides RID..."
cp -r "$CUSTOMIZATION_DIR/" src/customization/

echo "[4/4] Build..."
npm run build

echo ""
echo "✓ Build concluído: $WORK_DIR/src/frontend/dist/"
echo ""
echo "Para inspecionar: open $WORK_DIR/src/frontend/dist/index.html"
