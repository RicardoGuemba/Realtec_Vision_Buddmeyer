# Perguntas e Respostas — Realtec Vision Buddmeyer

Sistema de visão computacional para automação pick-and-place. Este documento responde dúvidas frequentes sobre uso, visão computacional, FPS, streaming, CLP e interface.

---

## Visão computacional e FPS

### Posso alterar o FPS em tempo real?

**Não.** O FPS do stream vem da câmera (taxa nativa). O FPS de inferência e do stream MJPEG são configurados em **Configuração** e exigem **Salvar + reinício** (Parar → Iniciar) para aplicar.

### O streaming tem quantos FPS?

O **streaming** (captura) usa o FPS **nativo da câmera**. Câmeras USB costumam reportar 15–30 FPS; GigE pode ser maior. O valor é exibido na **barra de status** ("FPS: X.X") e em **Diagnósticos → Visão Geral → Stream FPS**. Se a câmera reportar 0, o sistema usa 30 FPS como padrão.

### Qual a diferença entre FPS do stream e FPS de inferência?

| Parâmetro | Significado |
|-----------|-------------|
| **FPS do stream** | Taxa de captura da câmera (ex.: 30 FPS). Quantos frames/segundo são enviados ao buffer. |
| **FPS de inferência** | Taxa de processamento pelo modelo RT-DETR (ex.: 10 FPS). Quantos frames/segundo são enviados ao modelo. Frames excedentes são descartados. |

Se o stream tem 30 FPS e a inferência 10 FPS, o modelo processa 1 a cada 3 frames (sempre o mais recente).

### Onde configuro o FPS de inferência?

Em **Configuração → Modelo RT-DETR → FPS de inferência** (1–60). Padrão: 10. Após alterar, clique em **Salvar Configurações** e **Parar → Iniciar** na aba Operação.

### O que é o FPS do stream MJPEG?

É o ritmo de envio de frames para clientes web (supervisório). Configurável em **Configuração → Output → FPS** (1–30). Padrão: 10. Controla o consumo de CPU e rede. Não afeta a captura nem a inferência.

---

## ROI e confinamento

### O que é a ROI de confinamento?

A ROI (Region of Interest) de confinamento define uma área retangular centrada na imagem. Centroides detectados **fora** dessa área são projetados para o ponto mais próximo **dentro** dela antes de serem enviados ao CLP. Evita que a placa de ventosas colida com as paredes do contêiner.

### Posso alterar a ROI em tempo real?

A **exibição** do retângulo (Ligado/Desligado) sim — combo **ROI** na aba Operação. Os **limites** (X±, Y± em mm) são alterados em Configuração → Pré-processamento e exigem **Salvar + reinício** para aplicar no processamento.

### Como dimensiono a ROI?

Em **Configuração → Pré-processamento → ROI para Confinamento** defina X- (esquerda), X+ (direita), Y+ (acima), Y- (abaixo) em mm relativos ao centro da imagem. Use a calibração mm/px para conversão.

---

## Calibração e coordenadas

### O que é mm/px?

Relação **milímetros por pixel**. 1 = coordenadas em pixels; outro valor = coordenadas em mm. Usado para exibir e enviar ao CLP. **Alteração em tempo real** na aba Operação.

### O centroide é em pixels ou mm?

Depende do mm/px. Se mm/px = 1, as coordenadas são em pixels. Se mm/px ≠ 1, são convertidas para mm. O valor exibido na UI e enviado ao CLP segue essa configuração.

---

## Stream e câmera

### Quantos FPS a câmera USB suporta?

Depende do modelo. O sistema usa o valor reportado pela câmera (OpenCV). Se a câmera reportar 0, o padrão é 30 FPS.

### O buffer de frames afeta o FPS?

Não. O buffer (`streaming.max_frame_buffer_size`, padrão 30) armazena frames. Quando cheio, o mais antigo é descartado. O FPS do stream é determinado pela câmera e pelo StreamWorker.

### Posso usar câmera GigE e USB ao mesmo tempo?

Não. Apenas uma fonte por vez. Selecione no combo **Fonte** na aba Operação antes de iniciar.

---

## Inferência e detecção

### Qual modelo de detecção é usado?

RT-DETR (Real-Time Detection Transformer). Configurável em **Configuração → Modelo RT-DETR**. Padrão: PekingU/rtdetr_r50vd.

### O que é a confiança mínima?

Threshold (0–100%). Detecções abaixo são descartadas. Ajuste em Configuração → Modelo RT-DETR. Valores baixos aumentam detecções mas podem gerar falsos positivos.

### O que é "máx. detecções"?

Número máximo de caixas por frame após NMS (Non-Maximum Suppression). Configurável em Configuração → Modelo RT-DETR.

---

## CLP e comunicação

### O que é modo simulado?

Quando ativo, o sistema não conecta ao CLP real. Usa um simulador interno com delays (ACK ~1s, Pick ~2s, Place ~2s). Útil para testes sem CLP.

### Como forço modo simulado?

Em **Configuração → Controle (CLP)** marque **Modo simulado** e salve.

### O sistema tenta conectar ao CLP ao iniciar?

Sim. Se a conexão falhar, o sistema cai automaticamente para **modo simulado** e exibe no console: "CLP real não alcançável — operando em modo SIMULADO".

---

## Interface e operação

### O que é Modo Contínuo?

Quando marcado, o ciclo pick-and-place segue automaticamente após cada detecção. Quando desmarcado, após uma detecção o sistema aguarda o botão **Autorizar envio ao CLP**.

### Onde vejo o status do CLP?

Na **barra de status** (inferior): "CLP: Conectado" (verde), "CLP: Simulado" (azul) ou "CLP: Desconectado" (vermelho).

### O que o botão Parar faz?

Para stream, inferência, controlador e encerra a conexão CLP (VisionReady = False). A parada é executada em segundo plano para não bloquear a interface.

### Posso alterar a fonte com o sistema rodando?

Não. Pare o sistema, altere a fonte no combo e clique em Iniciar.

---

## Stream MJPEG (supervisório web)

### Como acesso o stream via navegador?

Em **Configuração → Output** copie a **URL (acesso web)** (ex.: `http://<IP>:8765/stream`) e abra no navegador. O stream MJPEG exibe o vídeo com overlay de detecções.

### Qual a porta padrão do stream MJPEG?

8765. Configurável em Configuração → Output → Porta.

---

## Diagnósticos e logs

### Onde vejo o FPS em tempo real?

- **Barra de status:** FPS do stream.
- **Aba Diagnósticos → Visão Geral:** Stream FPS e Inferência FPS.
- **Aba Diagnósticos → Métricas:** Gráfico de FPS do stream ao longo do tempo.

### Onde ficam os logs?

Arquivo definido em `config.yaml` → `log_file` (padrão: `logs/realtec_vision_buddmeyer.log`). Visualizável em **Aba Diagnósticos → Logs**.

---

## Configuração e persistência

### Quais alterações exigem reinício?

Fonte (tipo, índice, IP, porta), FPS de inferência, modelo, device, confiança, máx. detecções, limites da ROI, stream MJPEG (habilitar, porta, FPS), IP/porta do CLP, modo simulado. **Salvar Configurações** e **Parar → Iniciar**.

### Quais alterações têm efeito imediato?

mm/px, ROI (exibição Ligado/Desligado), Modo Contínuo/Manual.

### Onde está o arquivo de configuração?

`config/config.yaml` dentro do pacote (ex.: `realtec_vision_buddmeyer/config/config.yaml`).
