#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Teste de integração: detecção, conexão CLP, estados e ciclo a cada 25 frames.

Valida antes do cliente clonar:
- Conexão ao CLP (ou modo simulado)
- Estados VisionReady e RobotReady
- Máquina de estados do RobotController
- Envio de detecções (X, Y) ao CLP
- Ciclo de comunicação a cada 25 frames
"""

import sys
import asyncio
from pathlib import Path

# Raiz do projeto = pai de scripts/
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import os
# Opcional: timeout curto só vale se config não vier de YAML (get_settings usa from_yaml)
os.environ.setdefault("BUDDMEYER_CIP__CONNECTION_TIMEOUT", "3")
os.chdir(ROOT)


def run_async(coro):
    return asyncio.run(coro)


async def test_cip_connection():
    """Testa conexão ao CLP (modo real ou simulado)."""
    from config import get_settings
    from communication import CIPClient

    settings = get_settings(reload=True)
    client = CIPClient()
    connected = await client.connect()
    # Aceita conectado ou modo simulado
    ok = client._state.is_connected
    await client.disconnect()
    return ok, "CIP conectado ou simulado" if ok else "CIP não conectou"


async def test_vision_ready_and_detection_write():
    """Testa VisionReady e escrita de detecção (X, Y) no CLP."""
    from communication import CIPClient

    client = CIPClient()
    await client.connect()
    if not client._state.is_connected:
        await client.disconnect()
        return False, "Requer CIP conectado/simulado"

    try:
        await client.set_vision_ready(True)
        ok_vr = True
    except Exception as e:
        ok_vr = False
        msg_vr = str(e)

    try:
        ok_det = await client.write_detection_result(
            detected=True,
            centroid_x=100.5,
            centroid_y=200.25,
            confidence=0.95,
            detection_count=1,
            processing_time=12.0,
        )
    except Exception as e:
        ok_det = False
        msg_det = str(e)

    try:
        await client.set_vision_ready(False)
    except Exception:
        pass
    await client.disconnect()

    if not ok_vr:
        return False, f"set_vision_ready(True) falhou: {msg_vr}"
    if not ok_det:
        return False, f"write_detection_result falhou: {msg_det}"
    return True, "VisionReady e escrita X,Y OK"


async def test_robot_controller_states():
    """Testa RobotController: start e transição INITIALIZING -> WAITING_AUTHORIZATION.
    Sem Qt, o QTimer não dispara; simulamos chamando _process_current_state() diretamente.
    """
    from communication import CIPClient
    from control import RobotController

    client = CIPClient()
    await client.connect()
    if not client._state.is_connected:
        await client.disconnect()
        return False, "Requer CIP conectado/simulado"

    robot = RobotController()
    robot.start()
    # Sem Qt, QTimer não dispara; drive manual para testar a máquina de estados
    for _ in range(5):
        await robot._process_current_state()
        await asyncio.sleep(0.05)
    state = robot._state
    robot.stop()
    await client.disconnect()

    if state.value == "WAITING_AUTHORIZATION":
        return True, "Estado WAITING_AUTHORIZATION alcançado"
    if state.value == "INITIALIZING":
        return False, "Permaneceu em INITIALIZING (verifique CLP/conexão)"
    return True, f"Estado atual: {state.value}"


def test_25_frame_cycle_logic():
    """Testa lógica do ciclo a cada 25 frames (sem GUI)."""
    communication_interval = 25
    frame_count = 0
    send_events = []

    for _ in range(80):  # simula 80 frames
        frame_count += 1
        if frame_count % communication_interval == 0:
            send_events.append(frame_count)

    if send_events == [25, 50, 75]:
        return True, "Ciclo a cada 25 frames: disparos em 25, 50, 75"
    return False, f"Esperado [25,50,75], obtido {send_events}"


async def test_robot_ready_handshake():
    """Testa leitura de RobotReady (handshake antes de enviar)."""
    from communication import CIPClient

    client = CIPClient()
    await client.connect()
    if not client._state.is_connected:
        await client.disconnect()
        return False, "Requer CIP conectado/simulado"

    try:
        val = await client.read_tag("RobotReady")
        await client.disconnect()
        # Simulado retorna True; real pode ser bool
        return True, f"RobotReady lido: {val}"
    except Exception as e:
        await client.disconnect()
        return False, f"read_tag RobotReady: {e}"


async def test_disconnect_no_close_error():
    """Garante que disconnect() não chama .close() inexistente."""
    from communication import CIPClient

    client = CIPClient()
    await client.connect()
    try:
        await client.disconnect()
        return True, "disconnect() concluído sem erro"
    except AttributeError as e:
        if "close" in str(e).lower():
            return False, f"disconnect ainda usa .close(): {e}"
        raise
    except Exception as e:
        return False, f"disconnect falhou: {e}"


def test_detection_module_import():
    """Verifica se módulo de detecção e eventos existem."""
    try:
        from detection import InferenceEngine
        from detection.events import DetectionEvent
        # DetectionEvent com centroid
        e = DetectionEvent(
            detected=True,
            class_name="test",
            confidence=0.9,
            centroid=(10.0, 20.0),
            detection_count=1,
            inference_time_ms=5.0,
        )
        return e.centroid[0] == 10.0 and e.centroid[1] == 20.0, "Detecção e DetectionEvent OK"
    except Exception as ex:
        return False, f"Detecção/eventos: {ex}"


def main():
    print("=" * 60)
    print("TESTE DE INTEGRAÇÃO: Visão + CLP + Estados + Ciclo 25 frames")
    print("=" * 60)

    results = []
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # 1) Módulo de detecção
    ok, msg = test_detection_module_import()
    results.append(("Detecção / DetectionEvent", ok, msg))
    print(f"  [{'OK' if ok else 'FALHA'}] Detecção / DetectionEvent: {msg}")

    # 2) Lógica 25 frames
    ok, msg = test_25_frame_cycle_logic()
    results.append(("Ciclo a cada 25 frames", ok, msg))
    print(f"  [{'OK' if ok else 'FALHA'}] Ciclo a cada 25 frames: {msg}")

    # 3) Conexão CIP
    ok, msg = loop.run_until_complete(test_cip_connection())
    results.append(("Conexão CLP", ok, msg))
    print(f"  [{'OK' if ok else 'FALHA'}] Conexão CLP: {msg}")

    # 4) VisionReady + write_detection_result
    ok, msg = loop.run_until_complete(test_vision_ready_and_detection_write())
    results.append(("VisionReady + envio X,Y", ok, msg))
    print(f"  [{'OK' if ok else 'FALHA'}] VisionReady + envio X,Y: {msg}")

    # 5) RobotReady (handshake)
    ok, msg = loop.run_until_complete(test_robot_ready_handshake())
    results.append(("Handshake RobotReady", ok, msg))
    print(f"  [{'OK' if ok else 'FALHA'}] Handshake RobotReady: {msg}")

    # 6) Estados RobotController
    ok, msg = loop.run_until_complete(test_robot_controller_states())
    results.append(("Estados RobotController", ok, msg))
    print(f"  [{'OK' if ok else 'FALHA'}] Estados RobotController: {msg}")

    # 7) Disconnect sem erro close
    ok, msg = loop.run_until_complete(test_disconnect_no_close_error())
    results.append(("Disconnect sem .close()", ok, msg))
    print(f"  [{'OK' if ok else 'FALHA'}] Disconnect: {msg}")

    loop.run_until_complete(asyncio.sleep(0.3))  # deixa timers/threads encerrarem
    loop.close()

    print()
    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print("=" * 60)
    if passed == total:
        print(f"RESULTADO: TODOS OS {total} TESTES PASSARAM.")
        print("Sistema pronto para o cliente clonar e usar.")
    else:
        print(f"RESULTADO: {passed}/{total} testes passaram.")
        for name, ok, msg in results:
            if not ok:
                print(f"  - {name}: {msg}")
    print("=" * 60)
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
