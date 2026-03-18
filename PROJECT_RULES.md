# Regras do Projeto — Realtec Vision Buddmeyer

## 1. Stack e padrões

- **UI:** PySide6 (Qt Widgets). Não usar Tkinter.
- **Arquitetura:** feature-based, com camadas internas por feature.
- **Logs:** dois trilhos — `system.log` (app/infra/erros) e `process_trace.log` (eventos/transições).
- **Integrações:** GigE/GenICam e CLP encapsulados por ports/adapters.

## 2. Estrutura por feature

Cada feature deve ter, no mínimo:

- `ui_qt/` — widgets PySide6 sem lógica de infra
- `state/` — viewmodels/controllers (QObject + signals)
- `application/` — casos de uso (orquestração)
- `domain/` — modelos e regras
- `infrastructure/` — adapters (GigE/CLP/files); não conhece Qt

**Regras de dependência:**

- `ui_qt → state → application → domain`
- `infrastructure` implementa ports e não depende de Qt
- `shared` apenas para logging, errors, config

## 3. Threading (PySide6)

- GUI thread deve permanecer livre.
- Stream de câmera e polling CLP em workers (QThread/QRunnable).
- Atualização da UI via signals/slots.

## 4. UI enxuta (ISA-101 / alarm banner)

- Operação: modo/estado, alarmes (banner + resumo), conexões, receita/job, ciclo.
- Remover elementos que não ajudam a operar ou diagnosticar.
- Alarmes com banner e resumo (prática industrial).

## 5. Logs estruturados

Campos obrigatórios: `ts`, `level`, `logger`, `feature`, `use_case`, `cycle_id` (quando houver), `frame_id` (quando aplicável), `error_code` (quando houver), `message`.

## 6. Placeholders futuros

- Integração com robô: via `control/robot_controller.py` e `communication/cip_client.py`.
