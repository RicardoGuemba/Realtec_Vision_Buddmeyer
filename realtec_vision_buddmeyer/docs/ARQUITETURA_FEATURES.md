# Arquitetura por Features — Por que cada recurso

Documento que explica as decisões arquiteturais do Realtec Vision Buddmeyer.

---

## 1. PySide6 (não Tkinter)

**Por que:** PySide6 (Qt for Python) oferece threading robusto (QThread, signals/slots), widgets industriais e suporte multiplataforma (Windows, macOS, Linux). Tkinter tem limitações em workers e atualização de UI a partir de threads. Para um sistema de visão em tempo real com stream de câmera e polling CLP, Qt é a escolha adequada.

---

## 2. Dois logs (system + process_trace)

**Por que:** Separar "por que quebrou" (infra, exceções, reconexões) de "em qual passo quebrou" (transições de estado, eventos por ciclo) reduz ruído e acelera diagnóstico. O `process_trace.log` não registra por frame, apenas eventos e transições, evitando explosão de volume. Correlação via `cycle_id`, `frame_id`, `feature`, `use_case` permite rastrear falhas entre os dois trilhos.

---

## 3. UI enxuta (ISA-101 / alarm banner)

**Por que:** Em HMIs industriais, menos elementos visuais reduz carga cognitiva e destaca o anormal. Contadores (detecções, ciclos, erros) foram removidos da Operação; alarmes e estado do sistema permanecem em destaque. ROI foi movido para Operação para ajuste rápido durante a produção.

---

## 4. Configuração sem "Tipo" e sem "Ajustes de Imagem"

**Por que:** O tipo de fonte é definido na aba Operação (combo Fonte), onde o operador escolhe a fonte ativa. A Configuração mantém apenas os parâmetros de cada fonte (caminho, IP, etc.). Ajustes de Imagem (brilho/contraste) foram removidos da UI; parâmetros GenICam (gain/exposição) permanecem no adapter quando necessário.

---

## 5. Ports/Adapters (GigE, CLP)

**Por que:** Isolar integrações em adapters permite trocar implementação (ex.: outro driver GigE ou outro protocolo CLP) sem alterar o core. A infraestrutura não conhece Qt; a orquestração usa interfaces (ports).

---

## 6. Threading (workers para stream e CLP)

**Por que:** A GUI thread do Qt não deve bloquear. Stream de câmera GigE e polling CLP rodam em QThread/QRunnable; a UI é atualizada via signals/slots. Isso evita travamentos e mantém a interface responsiva.
