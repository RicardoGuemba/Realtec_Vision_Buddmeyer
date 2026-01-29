# Correcao: Centroide e Comunicacao Periodica

## Objetivo

1. Exibir apenas o centroide da deteccao de maior confianca
2. Comunicar coordenadas do centroide ao CLP a cada 25 frames (simulacao)

## Alteracoes Implementadas

### 1. **VideoWidget - Exibicao do Centroide**

**Arquivo:** `ui/widgets/video_widget.py`

Modificado o metodo `_draw_detections()` para:
- Encontrar a deteccao de maior confianca
- Desenhar apenas o bounding box desta deteccao
- Desenhar centroide destacado (circulo maior com cruz)
- Exibir coordenadas do centroide abaixo do bbox

**Caracteristicas visuais:**
- Bounding box com linha mais grossa (3px)
- Centroide com circulo de 20px preenchido
- Cruz preta no centro do centroide
- Label com coordenadas (X, Y) abaixo do objeto

### 2. **OperationPage - Comunicacao Periodica**

**Arquivo:** `ui/pages/operation_page.py`

Adicionadas variaveis de controle:
```python
self._frame_count = 0
self._communication_interval = 25  # A cada 25 frames
self._last_best_detection = None
```

Modificado `_on_frame_available()` para:
- Incrementar contador de frames
- Chamar `_communicate_centroid_to_plc()` a cada 25 frames

Modificado `_on_detection()` para:
- Armazenar ultima melhor deteccao

Adicionado metodo `_communicate_centroid_to_plc()`:
- Verifica se ha deteccao
- Verifica conexao com CLP
- Loga a comunicacao
- Exibe mensagem no console de eventos
- Chama `_send_detection_to_plc()` assincronamente

Adicionado metodo `_send_detection_to_plc()`:
- Usa TAGs definidas no CIPClient
- Envia: PRODUCT_DETECTED, CENTROID_X, CENTROID_Y, CONFIDENCE, etc.

## TAGs Utilizadas (Script Logico)

| TAG | Tipo | Descricao |
|-----|------|-----------|
| PRODUCT_DETECTED | BOOL | Produto detectado |
| CENTROID_X | REAL | Coordenada X do centroide |
| CENTROID_Y | REAL | Coordenada Y do centroide |
| CONFIDENCE | REAL | Confianca (0-1) |
| DETECTION_COUNT | INT | Numero de deteccoes no frame |
| PROCESSING_TIME | REAL | Tempo de processamento (ms) |

## Comportamento

1. **A cada frame:**
   - Inferencia processa o frame
   - Deteccoes sao exibidas (apenas melhor centroide)

2. **A cada 25 frames:**
   - Coordenadas do centroide sao enviadas ao CLP
   - Log eh registrado
   - Mensagem aparece no console de eventos

3. **Visualizacao:**
   - Apenas a deteccao de maior confianca eh destacada
   - Centroide marcado com circulo grande e cruz
   - Coordenadas exibidas abaixo do objeto

## Teste

1. Execute o aplicativo
2. Selecione um video e inicie o sistema
3. Observe:
   - Apenas o centroide da melhor deteccao eh mostrado
   - A cada 25 frames, mensagem de comunicacao aparece no console
   - Coordenadas sao exibidas no formato (X, Y)

## Status

- Exibicao de centroide unico funcionando
- Comunicacao periodica implementada
- TAGs do CLP respeitadas

**PRONTO PARA USO!**
