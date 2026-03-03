# v2.1.0: Sair, ROI confinamento e overlay, docs variáveis UI, branding Realtec, Stop, higienização

## Resumo

Release 2.1.0 com novas funcionalidades de operação, confinamento de centroide, overlay da ROI na imagem, documentação completa das variáveis da UI, rebranding para Realtec Vision Buddmeyer, botão Stop e higienização de código não utilizado.

## Alterações principais

### Adicionado
- **Menu Sair (Arquivo → Sair / Ctrl+Q):** Encerra todos os processos (stream, inferência, CLP, robô, MJPEG) e fecha a aplicação de forma ordenada.
- **Confinamento de centroide (ROI em mm):** Configuração → Pré-processamento — área retangular definida a partir do centro da imagem (X+, X-, Y+, Y- em mm). Centroides fora da área são projetados para o ponto mais próximo dentro da ROI; evita colisão da placa de ventosas com as paredes do contêiner.
- **Overlay da ROI na imagem:** Checkbox **ROI** na aba Operação liga/desliga o desenho do retângulo da área de confinamento sobre o vídeo (traço amarelo fino).
- **Referência das variáveis da UI:** Nova seção em `docs/USO_E_ABAS.md` listando todas as variáveis/controles (tipo, localização, significado) das abas Operação, Configuração e Diagnósticos.
- **Pré-carregamento do modelo:** Carregamento do modelo em background após abrir a janela (reduz travamento ao clicar Iniciar).

### Removido
- `preprocessing/preprocess_pipeline.py` e `preprocessing/roi_manager.py` (não utilizados pelo fluxo principal).
- `tests/unit/test_preprocessing_roi.py`.
- `core/application.py`, `control/cycle_processor.py` (já removidos em trabalho anterior).

### Alterado
- **Branding:** Nome do produto e instaladores atualizados para **Realtec Vision Buddmeyer** (título, log, instalador, scripts de inicialização, documentação). Exceção: classe `BuddmeyerVisionError` mantida por compatibilidade.
- **Botão "Novo Ciclo" → "Stop":** Interrompe ciclo e comandos ao robô; detecções continuam; apenas envio ao CLP e comandos ao robô são parados.
- **Versão:** 2.1.0 em `main.py`, título da janela e CHANGELOG.

## Documentação
- CHANGELOG atualizado com seção [2.1.0].
- USO_E_ABAS, DOCUMENTACAO_SISTEMA_COMPLETA, DOCUMENTACAO_PARA_CLIENTE, DOCUMENTACAO_AVALIACAO_CLIENTE_TI, instalador e PRD atualizados.

## Testes
- 83 testes passando (testes de `roi_manager` removidos com o módulo).
