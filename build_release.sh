#!/bin/bash
# Script automatizado para criar release

VERSION="2.0.0"
PLATFORM="linux-x64"

echo "🔨 Building DetectorNudez v${VERSION} for ${PLATFORM}"

# Limpar builds anteriores
rm -rf build dist

# Criar executável
echo "📦 Criando executável..."
pyinstaller detector_nudez.spec

# Testar executável
echo "🧪 Testando executável..."
if [ -f "dist/DetectorNudez" ]; then
    echo "✓ Executável criado com sucesso!"
else
    echo "❌ Erro ao criar executável!"
    exit 1
fi

# Criar release
echo "📦 Criando pacote de release..."
mkdir -p releases/v${VERSION}/${PLATFORM}
cd dist
tar -czf ../releases/v${VERSION}/${PLATFORM}/DetectorNudez-${PLATFORM}-v${VERSION}.tar.gz DetectorNudez
cd ..

echo "✅ Release criado em: releases/v${VERSION}/${PLATFORM}/"
echo "📊 Tamanho: $(du -h releases/v${VERSION}/${PLATFORM}/*.tar.gz | cut -f1)"