# Manual – Câmera GenTL (Omron Sentech) e melhorias de desempenho

Documento que descreve tudo o que foi implementado e alterado para suporte à câmera **GenTL (Harvester / Omron Sentech)**, correções de travamento da UI e carregamento do modelo em segundo plano.

---

## Índice

1. [Visão geral do que foi feito](#1-visão-geral-do-que-foi-feito)
2. [Onde está a conexão de cada tipo de câmera](#2-onde-está-a-conexão-de-cada-tipo-de-câmera)
3. [Câmera GenTL (Omron Sentech)](#3-câmera-gentl-omron-sentech)
4. [Configuração e uso na interface](#4-configuração-e-uso-na-interface)
5. [Proteções e desempenho (evitar travamentos)](#5-proteções-e-desempenho-evitar-travamentos)
6. [Carregamento do modelo em segundo plano](#6-carregamento-do-modelo-em-segundo-plano)
7. [FPS e gargalos](#7-fps-e-gargalos)
8. [Referência rápida de arquivos](#8-referência-rápida-de-arquivos)

---

## 1. Visão geral do que foi feito

| Item | Descrição |
|------|-----------|
| **Nova fonte GenTL** | Tipo de fonte "Câmera GenTL (Omron Sentech)" usando a biblioteca **Harvester** (GenICam/GenTL) e arquivo CTI do fabricante. |
| **Configuração GenTL** | CTI path, índice da câmera, **dimensão máxima** (redimensionamento) e **FPS alvo** configuráveis na aba Configuração e na Operação ("Selecionar CTI..."). |
| **Proteção na abertura** | Remoção do `fetch()` em `open()` do adaptador GenTL para não travar a UI ao obter um frame 20MP na thread principal. Dimensões passam a ser obtidas no primeiro `read()` na thread do worker. |
| **Redimensionamento** | Frames grandes (ex.: 5472×3648) são redimensionados para um máximo configurável (ex.: 1920 px no lado maior) para não travar exibição e inferência. Limite de segurança mesmo com "Sem limite" (0). |
| **Cache no widget de vídeo** | Conversão numpy → QImage → QPixmap e escala passam a ser cacheadas; só recalculadas quando o frame ou o tamanho do widget mudam, reduzindo trabalho na thread principal. |
| **Carregamento do modelo em background** | Carregamento do modelo RT-DETR em uma **QThread**; botão "Carregando modelo..." e UI responsiva durante o carregamento. |
| **Logger** | Uso de `datetime.now(timezone.utc)` em vez de `datetime.utcnow()` para evitar DeprecationWarning. |
| **Dependência** | Inclusão de **harvesters** em `requirements.txt` para suporte GenTL. |

---

## 2. Onde está a conexão de cada tipo de câmera

### 2.1 Implementação da conexão (backend)

**Arquivo:** `buddmeyer_vision_v2/streaming/source_adapters.py`

Cada tipo de câmera tem um **adaptador** que implementa `open()` e `read()`:

| Tipo | Classe | Como conecta |
|------|--------|---------------|
| **Arquivo de vídeo** | `VideoFileAdapter` | `cv2.VideoCapture(caminho_do_arquivo)` |
| **USB** | `USBCameraAdapter` | `cv2.VideoCapture(índice, cv2.CAP_DSHOW)` (Windows) ou fallback sem CAP_DSHOW |
| **RTSP** | `RTSPAdapter` | `cv2.VideoCapture(url, cv2.CAP_FFMPEG)` |
| **GigE (genérico)** | `GigECameraAdapter` | Pipeline GStreamer (UDP/RTP/JPEG) ou `cv2.VideoCapture("gige://ip:porta")` |
| **GenTL (Omron Sentech)** | `GenTLHarvesterAdapter` | Harvester: `add_file(cti)`, `update()`, `create(índice)`, `start()`; frames via `fetch()` |

A **factory** que escolhe o adaptador é a função **`create_adapter()`** no mesmo arquivo (parâmetros: `source_type`, `video_path`, `camera_index`, `rtsp_url`, `gige_ip`, `gige_port`, `gentl_cti_path`, `gentl_device_index`, `gentl_max_dimension`, `gentl_target_fps`, `loop_video`).

### 2.2 Quem abre a fonte e roda o stream

**Arquivo:** `buddmeyer_vision_v2/streaming/stream_manager.py`

- **`_start_with_current_settings()`**: chama `create_adapter(...)` com os parâmetros de `settings.streaming`, depois `adapter.open()` e cria o **StreamWorker** (QThread) que em loop chama `adapter.read()` e emite os frames.
- **`change_source(...)`**: atualiza tipo e parâmetros da fonte em memória; se o stream estava rodando, para e reinicia com as novas configurações.

### 2.3 Configuração (valores padrão e persistência)

**Arquivo:** `buddmeyer_vision_v2/config/settings.py`

- **`StreamingSettings`**: `source_type`, `video_path`, `usb_camera_index`, `rtsp_url`, `gige_ip`, `gige_port`, `gentl_cti_path`, `gentl_device_index`, `gentl_max_dimension`, `gentl_target_fps`, `max_frame_buffer_size`, `loop_video`.
- Validação de `source_type` inclui `"gentl"`.

---

## 3. Câmera GenTL (Omron Sentech)

### 3.1 Conceito

- **GenTL** é o padrão GenICam para transporte (GigE Vision, USB3 Vision, etc.).
- A **Omron Sentech** fornece um driver (CTI) que o Harvester usa para falar com a câmera.
- O usuário informa o **caminho do arquivo .cti** (ex.: `C:\Program Files\Common Files\OMRON_SENTECH\GenTL\v1_5\StGenTL_MD_VC141_v1_5_x64.cti`) e o **índice** da câmera (0 = primeira).

### 3.2 Fluxo no código

1. **`GenTLHarvesterAdapter.open()`**  
   - Carrega Harvester, `add_file(cti_path)`, `update()`, `create(device_index)`, `start()`.  
   - **Não** faz `fetch()` aqui (evita travar a UI com um frame 20MP na thread principal).

2. **`GenTLHarvesterAdapter.read()`** (rodando na **StreamWorker**)  
   - `fetch(timeout)` → buffer do Harvester.  
   - `reshape` + `cvtColor` (mono → BGR se necessário).  
   - **`_resize_if_needed()`**: se o frame exceder `max_dimension` (ou o limite de segurança 1920), redimensiona mantendo proporção.  
   - Retorna `FrameInfo` com o frame já redimensionado.

3. **Logs**  
   - `gentl_opened`: apenas `cti_path` e `device_index`.  
   - `gentl_first_frame`: uma vez, com `native=(largura, altura)` e `output=(largura, altura)` após o resize.

### 3.3 Parâmetros configuráveis

| Parâmetro | Config / UI | Efeito |
|-----------|-------------|--------|
| **gentl_cti_path** | Caminho do arquivo .cti | Driver GenTL usado pelo Harvester. |
| **gentl_device_index** | Índice 0, 1, … | Qual câmera na lista do Harvester. |
| **gentl_max_dimension** | 0–4096 px (0 = “Sem limite”) | Lado maior do frame após resize; 0 ainda aplica limite de segurança 1920. |
| **gentl_target_fps** | 1–60 (ex.: 10 ou 15) | FPS alvo do StreamWorker; o FPS real pode ser menor se o processamento por frame for lento. |

---

## 4. Configuração e uso na interface

### 4.1 Aba Configuração → Fonte de Vídeo

- **Tipo de Fonte:** inclui "Câmera GenTL (Omron Sentech)".
- Com GenTL selecionado aparecem:
  - **Arquivo CTI:** campo somente leitura + botão **"Procurar..."** para escolher o .cti.
  - **Índice da câmera:** 0–10.
  - **Dimensão máx. (px):** 0–4096 (0 exibido como "Sem limite").
  - **FPS alvo:** 1,0–60,0.
- **Salvar Configurações** grava no `config.yaml` (incluindo `gentl_cti_path`, `gentl_device_index`, `gentl_max_dimension`, `gentl_target_fps`).

### 4.2 Aba Operação

- **Fonte:** combo com "Câmera GenTL (Omron Sentech)".
- Com GenTL selecionado aparece o botão **"Selecionar CTI..."** para escolher o .cti **sem** ir à aba Configuração (valor fica em memória na sessão).
- Legenda abaixo do vídeo:
  - Com CTI selecionado: `Fonte: Câmera GenTL — nome_do_arquivo.cti`
  - Sem CTI: `Fonte: Câmera GenTL (Omron Sentech) — use 'Selecionar CTI...'`
- Ao clicar **Iniciar** com GenTL:
  - Se não houver CTI configurado, é exibida mensagem pedindo para usar "Selecionar CTI..." ou a Configuração.
  - Se o arquivo não existir, mensagem de erro orientando a selecionar de novo.

### 4.3 Uso típico

1. Instalar dependência: `pip install harvesters` (já em `requirements.txt`).
2. **Configuração** (opcional, para persistir): Tipo "Câmera GenTL (Omron Sentech)", Procurar… → escolher o .cti, ajustar dimensão máx. e FPS alvo, Salvar.
3. **Operação**: Fonte "Câmera GenTL (Omron Sentech)", se necessário "Selecionar CTI...", depois **Iniciar**.

---

## 5. Proteções e desempenho (evitar travamentos)

### 5.1 Nenhum fetch no `open()` GenTL

- **Problema:** Fazer `fetch()` em `open()` (na thread principal) para ler dimensões trazia um frame 5472×3648 e travava a UI.
- **Solução:** Em `open()` só se faz `create()`, `start()` e log. As dimensões são definidas no primeiro `read()` (na thread do worker). Log `gentl_first_frame` mostra resolução nativa e de saída.

### 5.2 Redimensionamento e limite de segurança

- Frames com lado maior que **max_dimension** (ou que 1920 quando max_dimension é 0) são redimensionados com `cv2.resize(..., INTER_AREA)`.
- **Limite de segurança:** mesmo com "Dimensão máx. = 0", o lado maior não ultrapassa 1920 px (constante `_SAFETY_MAX_DIMENSION` em `GenTLHarvesterAdapter`).

### 5.3 Cache no widget de vídeo

**Arquivo:** `buddmeyer_vision_v2/ui/widgets/video_widget.py`

- **Problema:** Em cada `paintEvent` o frame era copiado (BGR→RGB), convertido para QImage e escalado para o tamanho do widget, sobrecarregando a thread principal.
- **Solução:** Cache de `QPixmap` (e tamanho do widget / shape do frame). A conversão e o escalonamento só são refeitos quando o frame ou o tamanho do widget mudam. Em `resizeEvent` o cache de tamanho é invalidado.

---

## 6. Carregamento do modelo em segundo plano

### 6.1 Objetivo

- Evitar que a UI trave durante o carregamento do modelo RT-DETR (pesos e pré-processador).

### 6.2 Implementação

**Arquivo:** `buddmeyer_vision_v2/ui/pages/operation_page.py`

- **`_ModelLoaderWorker`** (QObject): em `run()` chama `inference_engine.load_model()` e emite **`finished(bool)`** (True = sucesso).
- O worker é movido para uma **QThread**; o thread é iniciado ao precisar carregar o modelo.

**Fluxo ao clicar Iniciar:**

1. Validações e início do **stream** (vídeo já aparece).
2. Se o modelo **já está carregado**: chama **`_finish_start_system_after_model(source_label)`** (inicia inferência, CLP, atualiza UI).
3. Se o modelo **não está carregado**:
   - Mensagem no console: "Carregando modelo de detecção... (aguarde)".
   - Botão "▶ Iniciar" vira **"Carregando modelo..."** e fica desabilitado.
   - Inicia a thread do worker e retorna (UI continua responsiva).
4. Quando o worker termina (**`_on_model_load_finished(success)`**):
   - Restaura o botão para "▶ Iniciar" e reabilita.
   - Se falhou: mensagem de erro e para o stream.
   - Se sucesso: "Modelo carregado." e **`_finish_start_system_after_model(source_label)`**.

**`_finish_start_system_after_model(source_label)`** concentra o que antes vinha depois do `load_model`: iniciar inferência, modo de ciclo, `_connect_plc_and_start_robot()`, `_is_running = True`, `_update_ui_state()` e mensagem de sucesso.

---

## 7. FPS e gargalos

### 7.1 Por que o FPS real pode ser ~4 com GenTL

- **gentl_target_fps** (ex.: 10) define o **máximo** desejado (intervalo entre capturas no StreamWorker).
- Cada frame exige: **fetch** (5472×3648) + **reshape** + **cvtColor** + **resize** para 1920 (ou menor). O **resize** de ~20 MP por frame é pesado na CPU.
- Se o tempo total por frame for ~250 ms, o FPS real fica ~4, independente do target_fps.

### 7.2 O que ajustar para aumentar FPS

1. **Dimensão máx. (px):** reduzir (ex.: 960 ou 640) para menos pixels no resize e mais FPS.
2. **Resolução nativa da câmera:** se a câmera permitir modo de menor resolução, menos dados por frame.
3. **(Opcional) Interpolação:** trocar `INTER_AREA` por `INTER_LINEAR` no `cv2.resize` do adaptador GenTL deixa o resize mais rápido, com pequena perda de qualidade.

---

## 8. Referência rápida de arquivos

| Arquivo | Alterações / conteúdo |
|---------|------------------------|
| **streaming/source_adapters.py** | `SourceType.GENTL`, `GenTLHarvesterAdapter` (open sem fetch, read com resize e log `gentl_first_frame`), `create_adapter` com parâmetros GenTL, limite de segurança 1920. |
| **streaming/stream_manager.py** | `change_source` e `_start_with_current_settings` com `gentl_*`, validação de CTI para GenTL, `create_adapter(..., gentl_max_dimension, gentl_target_fps)`. |
| **config/settings.py** | `StreamingSettings`: `gentl_cti_path`, `gentl_device_index`, `gentl_max_dimension`, `gentl_target_fps`; `source_type` válido inclui `"gentl"`. |
| **ui/pages/configuration_page.py** | Combo com "Câmera GenTL (Omron Sentech)", grupo GenTL (CTI, índice, dimensão máx., FPS alvo), load/save e `_browse_gentl_cti`. |
| **ui/pages/operation_page.py** | Combo e legenda GenTL, botão "Selecionar CTI...", validação de CTI ao iniciar, `_ModelLoaderWorker`, carregamento do modelo em QThread, `_on_model_load_finished`, `_finish_start_system_after_model`. |
| **ui/widgets/video_widget.py** | Cache de QPixmap/tamanho/shape; `_ensure_cached_pixmap()`, `resizeEvent` invalidando cache. |
| **core/logger.py** | Timestamp com `datetime.now(timezone.utc)` em vez de `utcnow()`. |
| **requirements.txt** | Entrada `harvesters>=2.3.0`. |

---

*Documento gerado com base nas alterações realizadas no sistema Buddmeyer Vision v2 para suporte GenTL (Omron Sentech) e melhorias de estabilidade e desempenho.*
