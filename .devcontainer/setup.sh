#!/usr/bin/env bash
set -e
echo "⚙️ Configurando entorno..."
# NvChad
git clone https://github.com/NvChad/starter ~/.config/nvim
nvim --headless "+Lazy sync" +qa 2>/dev/null || true
# Config clangd para C++20
echo "clangd.compilationDatabasePath: /workspace/build" >> ~/.config/nvim/lua/plugins/clangd.lua 2>/dev/null || true
echo "Entorno listo."
