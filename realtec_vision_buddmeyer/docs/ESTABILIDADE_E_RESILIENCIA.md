# Estabilidade e resiliência — Supervisório Pick-and-Place

Este documento descreve as causas de instabilidade identificadas no sistema e as práticas aplicadas para garantir estabilidade e resiliência em ambiente industrial (supervisório de visão + CLP + robô).

---

## 1. Contexto

O Realtec Vision Buddmeyer atua como **supervisório**: aquisição de imagem, detecção, conversão pixel→mm e comunicação com o CLP para ciclo pick-and-place. A falha ou instabilidade pode causar parada de linha, coordenadas erradas ou perda de sincronia com o CLP.

**Objetivos:**

- Estado consistente entre UI, controlador de robô e CIP.
- Recuperação limitada e previsível (sem loops infinitos).
- Encerramento limpo (sem crash ao fechar a aplicação).
- Uma única fonte de verdade para parâmetros críticos (ex.: mm/px).

---

## 2. Causas de instabilidade identificadas

### 2.1 Calibração mm/px (detalhes em [AVALIACAO_INSTABILIDADE_MM_PX.md](AVALIACAO_INSTABILIDADE_MM_PX.md))

- **Sintoma:** Coordenadas em mm enviadas ao CLP não refletiam o valor configurado; parecia necessário reiniciar para “pegar” o novo valor.
- **Causa:** Configuração apenas em Configuração → Pré-processamento; risco de referência “stale” ao singleton de settings; ausência de controle visível na Operação.
- **Correção:** Spinbox mm/px na aba Operação, atualização in-place no singleton, sincronização entre abas, efeito imediato sem reinício.

### 2.2 Máquina de estados do robô

- **Risco:** Loop infinito ERROR → recuperação → ERROR sem intervenção do operador.
- **Correção:** Limite de tentativas de recuperação (`_max_recovery_attempts = 3`). Após exaustão, o controlador permanece em ERROR até reset/reinício pelo operador.
- **Benefício:** Comportamento previsível e auditável em ambiente industrial.

### 2.3 Estado sujo entre partidas

- **Risco:** Ao parar e reiniciar, detecção anterior, etapas de ciclo ou flags de autorização permaneciam, podendo influenciar a próxima partida.
- **Correção:** Em `RobotController.stop()`: limpeza de `_current_detection`, `_cycle_steps`, `_user_cycle_authorized`, `_user_send_authorized` e `_recovery_attempts`.
- **Benefício:** Cada “Iniciar” começa com estado limpo e reproduzível.

### 2.4 Conexão CIP após falhas

- **Risco:** Contadores de erro e `last_error` permaneciam altos após reconexão bem-sucedida, levando a nova marcação como DEGRADED com poucos erros.
- **Correção:** Em conexão bem-sucedida (real ou simulado) e após reconexão automática: `error_count = 0`, `last_error = None`, `reconnect_attempts = 0`.
- **Benefício:** Estado de conexão reflete a sessão atual; reconexão restaura operação normal.

### 2.5 Encerramento da aplicação (Qt + asyncio)

- **Risco:** Durante o fechamento da janela, o event loop pode estar fechando; `asyncio.create_task()` nesse momento gera `RuntimeError` e pode derrubar o processo.
- **Correção:** Uso de `safe_create_task()` (`core/async_utils.py`): só agenda a coroutine se o loop existir, estiver rodando e não estiver fechado; em caso contrário, registra em log e não agenda.
- **Benefício:** Encerramento limpo sem crash ao parar o sistema ou fechar a aplicação.

### 2.6 Serialização de status

- **Risco:** `get_status()` do controlador usava `current_detection.to_dict()`, que podia incluir objetos não serializáveis (ex.: bbox) e falhar em log ou API.
- **Correção:** `get_status()` monta um dicionário apenas com campos serializáveis da detecção atual (detected, class_name, confidence, centroid); em falha, retorna fallback seguro.
- **Benefício:** Logs e diagnósticos estáveis; sem exceção em código de status.

### 2.7 Instabilidade com objeto muito perto da câmera

- **Sintoma:** Sistema instável quando o objeto é aproximado muito perto da câmera.
- **Causas:** (1) NMS com divisão por zero ou bboxes degeneradas; (2) comunicação periódica ao CLP sobrescrevendo coordenadas durante ciclo do robô; (3) flood de envios quando há detecção contínua.
- **Correção:** Post-process com proteção numérica (área mínima, denom não zero, clip de boxes); comunicação periódica só quando robô aceita novas coordenadas; throttle de 500 ms entre envios.
- **Benefício:** Comportamento estável mesmo com objeto muito próximo.

---

## 3. Práticas aplicadas (resumo)

| Prática | Onde | Objetivo |
|--------|------|----------|
| **Uma fonte de verdade para mm/px** | Settings singleton; spinbox na Operação atualiza in-place | Evitar valor “stale” e inconsistência entre exibição e envio ao CLP |
| **Validação de transições** | `RobotController._transition_to()` + `VALID_TRANSITIONS` | Apenas transições permitidas; log de tentativas inválidas |
| **Limite de recuperação** | `_handle_error()` com `_max_recovery_attempts` | Evitar loop ERROR → INIT → ERROR; exigir intervenção após N falhas |
| **Limpeza em stop()** | `RobotController.stop()` | Estado limpo a cada nova partida |
| **Reset de estado CIP em conexão OK** | `CIPClient.connect()` e `_try_reconnect()` | Contadores e last_error zerados após conexão/reconexão bem-sucedida |
| **safe_create_task()** | OperationPage, RobotController, CIPClient | Não agendar tarefas async quando o loop está fechando |
| **get_status() serializável** | `RobotController.get_status()` | Status sempre serializável para log e API |

---

## 4. Arquivos alterados (referência)

- **control/robot_controller.py:** Limpeza em `stop()`, limite de recuperação em `_handle_error()`, `get_status()` seguro, uso de `safe_create_task`.
- **communication/cip_client.py:** Reset de `error_count`/`last_error`/`reconnect_attempts` em conexão e reconexão; uso de `safe_create_task` para reconnect e heartbeat.
- **ui/pages/operation_page.py:** Uso de `safe_create_task` para conexão PLC, envio de detecção e shutdown.
- **core/async_utils.py:** Novo módulo com `safe_create_task()`.
- **core/__init__.py:** Export de `safe_create_task`.

---

## 5. Documentos relacionados

- [AVALIACAO_INSTABILIDADE_MM_PX.md](AVALIACAO_INSTABILIDADE_MM_PX.md) — Causa raiz e correção da instabilidade mm/px.
- [OPORTUNIDADES_DE_MELHORIA.md](OPORTUNIDADES_DE_MELHORIA.md) — Backlog de melhorias (robustez, segurança, testes).
