# Oportunidades de Melhoria — Buddmeyer Vision Supervisório Pick-and-Place

Este documento lista oportunidades de aprimoramento identificadas após a execução dos testes unitários e análise do código, com foco em **robustez**, **estabilidade** e **boas práticas** para um sistema supervisório industrial.

---

## 1. Resultados dos Testes Unitários

**73 testes passando** em:
- `config.settings` — validação, defaults, carga YAML
- `core.exceptions` — hierarquia de exceções
- `detection.events` — BoundingBox, Detection, DetectionResult, DetectionEvent
- `detection.postprocess` — NMS, setters
- `preprocessing.transforms` — pixel_to_mm, ImageTransforms
- `preprocessing.roi_manager` — ROI (geometria)
- `streaming.frame_buffer` — FrameBuffer, FrameInfo
- `communication.connection_state` — ConnectionState, ConnectionStatus
- `output.mjpeg_stream` — StreamFrameProvider, MjpegStreamServer

**Executar testes:** `python -m pytest buddmeyer_vision_v2/tests/unit -v`

---

## 2. Oportunidades de Melhoria (Priorizadas)

### 2.1 Robustez e Estabilidade

| # | Oportunidade | Descrição | Prioridade |
|---|-------------|-----------|------------|
| 1 | **Validação de transições de estado no RobotController** | O dicionário `VALID_TRANSITIONS` existe, mas não está claro se toda transição passa por validação antes de executar. Adicionar assert/check explícito em `_transition_to()` para garantir que apenas transições válidas ocorram. | Alta |
| 2 | **Tratamento de exceção no MJPEG quando cliente desconecta** | O handler `_serve_mjpeg` captura BrokenPipe/ConnectionReset, mas outras exceções podem derrubar o thread. Envolver o loop em try/except genérico e log para evitar crash do servidor. | Alta |
| 3 | **Recarregamento de mm_per_pixel em tempo real** | `get_settings()` retorna instância em cache. Quando o usuário altera mm/px na UI e salva, os widgets que leem `get_settings().preprocess.mm_per_pixel` passam a ver o novo valor. Porém, se a UI de configuração não chama `get_settings(reload=True)` ou atualiza o objeto em memória, pode haver inconsistência. Validar fluxo de "Salvar" → atualização em memória. | Média |
| 4 | **Timeout e retry no FrameBuffer.get()** | `get(timeout=X)` espera indefinidamente se `_new_frame_event` nunca for setado (ex.: stream travado). Avaliar timeout máximo e comportamento em caso de "no frames". | Média |
| 5 | **Integração do PreprocessPipeline** | O `PreprocessPipeline` existe mas não é usado no fluxo principal (StreamManager → InferenceEngine direto). Avaliar se ROI, brilho e contraste devem ser aplicados antes da inferência. | Média |

### 2.2 Segurança e Confiabilidade Industrial

| # | Oportunidade | Descrição | Prioridade |
|---|-------------|-----------|------------|
| 6 | **Confirmação explícita de Parada de Emergência** | O estado `SAFETY_BLOCKED` e `PlcEmergencyStop` existem. Verificar se há UI ou fluxo claro para o operador confirmar parada de emergência e recuperação. | Alta |
| 7 | **Log de auditoria para decisões críticas** | Registrar em log estruturado: envio de coordenadas ao CLP, autorização de envio (modo manual), transições de estado do robô. Facilita rastreabilidade em caso de incidente. | Média |
| 8 | **Validação de range de coordenadas antes de enviar ao CLP** | Se mm_per_pixel estiver mal configurado ou houver bug, coordenadas podem ser negativas ou fora do range esperado pelo CLP. Adicionar validação (min/max) antes de `write_detection_result`. | Média |

### 2.3 Observabilidade e Operação

| # | Oportunidade | Descrição | Prioridade |
|---|-------------|-----------|------------|
| 9 | **Métricas Prometheus/export** | O `MetricsCollector` existe. Avaliar export para Prometheus ou endpoint `/metrics` (formato Prometheus) para integração com monitoramento industrial. | Baixa |
| 10 | **Health check agregado** | Já existe `/health` no MJPEG. Adicionar endpoint que verifica: stream ativo, inferência ativa, CLP conectado. Útil para load balancer ou monitoramento externo. | Média |
| 11 | **Dashboard de diagnóstico em tempo real** | A aba Diagnósticos tem métricas. Considerar gráficos de tendência (ex.: FPS, latência CIP) com histórico para análise pós-incidente. | Baixa |

### 2.4 Testes e Qualidade

| # | Oportunidade | Descrição | Prioridade |
|---|-------------|-----------|------------|
| 12 | **Testes de integração com pytest** | Os scripts em `scripts/test_*.py` são manuais. Migrar para `tests/integration/` com pytest, usando mocks para CLP, câmera e modelo. | Média |
| 13 | **Testes do RobotController (máquina de estados)** | Criar testes que simulam sinais do CLP e verificam transições de estado esperadas. Essencial para pick-and-place. | Alta |
| 14 | **CI/CD com testes automáticos** | Configurar GitHub Actions ou similar para rodar `pytest tests/` em todo push/PR. | Média |

### 2.5 Configuração e Manutenção

| # | Oportunidade | Descrição | Prioridade |
|---|-------------|-----------|------------|
| 15 | **Documentação de TAGs e contrato CLP** | O `TAG_CONTRACT.md` existe. Manter sincronizado com alterações em `tag_map.py` e garantir que toda nova TAG seja documentada. | Média |
| 16 | **Versionamento de config** | Adicionar campo `config_version` no YAML para migrações automáticas quando o schema mudar (ex.: novos campos obrigatórios). | Baixa |
| 17 | **Backup automático de config** | Antes de sobrescrever `config.yaml`, fazer backup com timestamp. Facilita rollback em caso de corrupção. | Baixa |

### 2.6 Performance e Escalabilidade

| # | Oportunidade | Descrição | Prioridade |
|---|-------------|-----------|------------|
| 18 | **Otimização de encode JPEG no MJPEG** | Usar `cv2.imencode` com parâmetro de qualidade configurável para balancear latência vs. banda. Ex.: `cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 85])`. | Baixa |
| 19 | **Limite de clientes MJPEG simultâneos** | Se muitos clientes conectarem ao `/stream`, o servidor pode ficar sobrecarregado. Considerar limite (ex.: 5 conexões) ou fila. | Baixa |

---

## 3. Resumo Executivo

| Categoria | Alta | Média | Baixa |
|-----------|------|-------|-------|
| Robustez | 2 | 3 | 0 |
| Segurança Industrial | 1 | 2 | 0 |
| Observabilidade | 0 | 2 | 1 |
| Testes | 1 | 2 | 0 |
| Config/Manutenção | 0 | 1 | 2 |
| Performance | 0 | 0 | 2 |
| **Total** | **4** | **10** | **5** |

**Top 5 recomendadas para próximas iterações:**
1. Validação de transições no RobotController (segurança do ciclo)
2. Tratamento robusto de exceções no MJPEG
3. Testes da máquina de estados do RobotController
4. Confirmação e fluxo de parada de emergência
5. Validação de range de coordenadas antes do envio ao CLP

---

## 4. Referências

- Testes unitários: `buddmeyer_vision_v2/tests/unit/`
- Documentação: `buddmeyer_vision_v2/docs/`
- Contrato de TAGs: `buddmeyer_vision_v2/docs/TAG_CONTRACT.md`
