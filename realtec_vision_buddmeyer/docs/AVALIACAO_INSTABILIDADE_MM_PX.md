# Avaliação da instabilidade mm/px em operação

## Resumo

A instabilidade relacionada a **mm/px em operação** foi corrigida ao expor o parâmetro de calibração **na própria aba Operação**, com efeito imediato e uso de uma única fonte de verdade em memória. Abaixo está a análise da causa raiz e do que foi alterado.

---

## 1. Sintoma da instabilidade

- Coordenadas (centroide) enviadas ao CLP em mm podiam não refletir o valor de calibração que o operador esperava.
- O valor efetivo podia parecer “atrasado” ou exigir reinício do sistema para passar a valer após mudança em Configuração.

---

## 2. Causa raiz identificada

### 2.1 Duas fontes de verdade e falta de controle em operação

- **Onde se configurava:** apenas em **Configuração → Pré-processamento** (campo “Calibração mm/px”).
- **Onde se usava:** na **Operação**, em vários pontos que leem `get_settings().preprocess.mm_per_pixel`:
  - `OperationPage._communicate_centroid_to_plc()` (envio periódico ao CLP)
  - `RobotController` ao processar detecção e ao enviar dados ao CLP
  - `VideoWidget` e `StatusPanel` para exibir coordenadas em mm

Ou seja: o valor era definido longe do contexto de operação e não havia controle visível na tela de Operação.

### 2.2 Risco de referência “stale” (antes da correção)

- `get_settings()` retorna um **singleton** em cache. A `ConfigurationPage` e a `OperationPage` usam a mesma instância quando não há `reload=True`.
- Se em algum fluxo o “Salvar” em Configuração chamasse `get_settings(reload=True)`, o singleton seria **substituído**. A `OperationPage` guarda `self._settings = get_settings()` no `__init__`: continuaria apontando para a **instância antiga**. Os componentes que leem `get_settings()` a cada chamada passariam a ver o novo valor; o fluxo de envio na Operação que dependesse de `self._settings` poderia continuar usando o **mm/px antigo** até reinício da aplicação.
- Mesmo sem `reload`, o operador não via na tela de Operação qual valor estava em uso e tinha que ir a Configuração para alterar, o que favorecia erro e sensação de “instabilidade”.

### 2.3 Documentação de oportunidades de melhoria

O próprio **OPORTUNIDADES_DE_MELHORIA.md** (item 3) já apontava:

- *“Recarregamento de mm_per_pixel em tempo real: get_settings() retorna instância em cache. Quando o usuário altera mm/px na UI e salva, os widgets que leem get_settings().preprocess.mm_per_pixel passam a ver o novo valor. Porém, se a UI de configuração não chama get_settings(reload=True) ou atualiza o objeto em memória, pode haver inconsistência.”*

Ou seja: a causa raiz está alinhada a **uma única instância em memória** e ao **fluxo de atualização** (Config vs Operação), não a um bug matemático da conversão pixel→mm.

---

## 3. Correção implementada

1. **Controle mm/px na aba Operação**
   - Spinbox **“mm/px”** na barra de controles da Operação.
   - Valor inicial vindo de `get_settings().preprocess.mm_per_pixel`.
   - Ao alterar: `_on_mm_per_pixel_changed(value)` faz `self._settings.preprocess.mm_per_pixel = value` (atualiza o singleton em tempo real).

2. **Uma única fonte em memória**
   - Operação e Configuração trabalham sobre o **mesmo** objeto `Settings` (singleton). Não há `reload=True` no fluxo de salvar Configuração; o salvamento apenas persiste o estado atual em YAML.
   - `_communicate_centroid_to_plc()` e o `RobotController` passam a usar sempre o valor atual de `get_settings().preprocess.mm_per_pixel` (ou, na Operação, `self._settings.preprocess.mm_per_pixel`, que é o mesmo objeto).

3. **Sincronização da UI**
   - `_sync_combo_to_settings()` na Operação atualiza o spinbox mm/px a partir do settings (ex.: ao voltar da Configuração após salvar).
   - Na Configuração, o `showEvent` chama `_load_settings()`, de modo que ao abrir a aba o valor exibido (incluindo mm/px) reflete o estado atual em memória.

4. **Efeito imediato**
   - Alterar mm/px na Operação aplica na hora para envio ao CLP e para exibição (centroide em mm), sem precisar reiniciar o sistema.

---

## 4. Conclusão

| Aspecto | Antes | Depois |
|--------|--------|--------|
| Onde configurar mm/px | Só em Configuração → Pré-processamento | Configuração **e** Operação (spinbox na barra) |
| Visibilidade em operação | Nenhuma | Valor visível e editável na tela de Operação |
| Efeito da alteração | Dependia de fluxo (salvar Config / possível reload) | Imediato na Operação; consistente em toda a aplicação |
| Risco de valor “stale” | Possível se singleton fosse recriado | Mitigado: uma instância, atualizada in-place na Operação e na Config |

A **instabilidade** tinha como causa raiz a **combinação** de: (i) ausência de controle mm/px na tela de Operação, (ii) possível inconsistência entre instância em memória e valor usado no envio ao CLP, e (iii) falta de feedback imediato para o operador. A solução unifica a fonte de verdade, expõe e atualiza mm/px diretamente na Operação e elimina a necessidade de reinício para a calibração passar a valer.
