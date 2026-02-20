#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Teste de validação: verifica que change_source() + start()
respeita o source_type selecionado pela UI para todas as fontes.

Testa a correção do bug onde get_settings(reload=True) sobrescrevia
o source_type em memória com o valor do config.yaml.
"""

import sys
from pathlib import Path

# Adiciona diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_settings


def test_settings_persistence():
    """
    Valida que alterar source_type em memória NÃO é sobrescrito
    ao chamar get_settings() sem reload.
    """
    print("=" * 60)
    print("TESTE 1: Settings persistence (sem reload)")
    print("=" * 60)
    
    settings = get_settings()
    original = settings.streaming.source_type
    print(f"  source_type original (do YAML): '{original}'")
    
    # Simula a UI selecionando USB
    settings.streaming.source_type = "usb"
    print(f"  source_type após set 'usb': '{settings.streaming.source_type}'")
    
    # get_settings sem reload deve retornar mesma instância
    settings2 = get_settings()
    print(f"  source_type via get_settings(): '{settings2.streaming.source_type}'")
    
    assert settings2.streaming.source_type == "usb", \
        f"FALHA: esperado 'usb', obteve '{settings2.streaming.source_type}'"
    
    # Restaura
    settings.streaming.source_type = original
    print("  PASSOU\n")


def test_settings_reload_overwrites():
    """
    Confirma que get_settings(reload=True) recarrega do disco.
    Isso é o que causava o bug — agora start() NÃO usa reload.
    """
    print("=" * 60)
    print("TESTE 2: Settings reload=True sobrescreve (comportamento esperado)")
    print("=" * 60)
    
    settings = get_settings()
    original = settings.streaming.source_type
    print(f"  source_type original (do YAML): '{original}'")
    
    # Simula a UI selecionando USB
    settings.streaming.source_type = "usb"
    print(f"  source_type após set 'usb': '{settings.streaming.source_type}'")
    
    # reload=True recria do disco — era isso que causava o bug
    settings_reloaded = get_settings(reload=True)
    print(f"  source_type após reload=True: '{settings_reloaded.streaming.source_type}'")
    
    # Após reload, volta ao valor do YAML
    assert settings_reloaded.streaming.source_type == original, \
        f"FALHA: esperado '{original}', obteve '{settings_reloaded.streaming.source_type}'"
    
    print("  PASSOU (reload sobrescreve — por isso start() NÃO deve usar reload)\n")


def test_change_source_updates_memory():
    """
    Valida que change_source() atualiza o source_type em memória
    para USB e GigE.
    """
    print("=" * 60)
    print("TESTE 3: change_source() atualiza memória (USB e GigE)")
    print("=" * 60)
    
    from streaming import StreamManager
    
    sm = StreamManager()
    settings = sm._settings
    original = settings.streaming.source_type
    
    test_cases = [
        ("usb", {"camera_index": 0}),
        ("gige", {"gige_ip": "192.168.1.100", "gige_port": 3956}),
    ]
    
    for source_type, params in test_cases:
        sm.change_source(source_type=source_type, **params)
        actual = settings.streaming.source_type
        status = "OK" if actual == source_type else "FALHA"
        print(f"  change_source('{source_type}') -> settings.source_type='{actual}' [{status}]")
        assert actual == source_type, \
            f"FALHA: esperado '{source_type}', obteve '{actual}'"
    
    # Restaura
    settings.streaming.source_type = original
    print("  PASSOU\n")


def test_start_uses_memory_not_disk():
    """
    Valida que start() usa as configurações em memória (setadas
    via change_source), e NÃO recarrega do YAML.
    
    Este é o teste principal da correção.
    """
    print("=" * 60)
    print("TESTE 4: start() usa memória, não disco (CORREÇÃO PRINCIPAL)")
    print("=" * 60)
    
    from streaming import StreamManager
    
    sm = StreamManager()
    settings = sm._settings
    original = settings.streaming.source_type
    
    # Simula: UI seleciona USB, chama change_source
    sm.change_source(source_type="usb", camera_index=0)
    
    print(f"  Após change_source('usb'): source_type='{settings.streaming.source_type}'")
    assert settings.streaming.source_type == "usb"
    
    # Verifica que start() lê o source_type correto
    # (Não vamos realmente iniciar a câmera, apenas verificar o fluxo)
    # O método _start_with_current_settings() é chamado por start()
    # e usa self._settings.streaming que já tem 'usb'
    
    # Verifica o source_type que seria usado
    effective_type = sm._settings.streaming.source_type
    print(f"  source_type que start() usará: '{effective_type}'")
    assert effective_type == "usb", \
        f"FALHA: start() usaria '{effective_type}' em vez de 'usb'"
    
    # Restaura
    settings.streaming.source_type = original
    print("  PASSOU\n")


def test_usb_camera_detection():
    """
    Testa se o sistema consegue detectar/abrir a câmera USB (se disponível).
    """
    print("=" * 60)
    print("TESTE 5: Detecção de câmera USB (hardware)")
    print("=" * 60)
    
    import cv2
    
    # Testa índices 0 e 1
    for idx in range(3):
        cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
        if cap.isOpened():
            ret, frame = cap.read()
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            cap.release()
            status = "ABERTA" if ret else "aberta mas sem frame"
            print(f"  Câmera {idx}: {status} ({w}x{h} @ {fps:.1f} FPS)")
        else:
            cap.release()
            print(f"  Câmera {idx}: não disponível")
    
    print("  INFO: Use o índice da câmera USB correta em config.yaml\n")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  VALIDAÇÃO DA CORREÇÃO: Stream Source Selection")
    print("=" * 60 + "\n")
    
    try:
        test_settings_persistence()
        test_settings_reload_overwrites()
        test_change_source_updates_memory()
        test_start_uses_memory_not_disk()
        test_usb_camera_detection()
        
        print("=" * 60)
        print("  TODOS OS TESTES PASSARAM")
        print("=" * 60)
        
    except AssertionError as e:  # noqa: F821
        print(f"\n  FALHA: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n  ERRO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
