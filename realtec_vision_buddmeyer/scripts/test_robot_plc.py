#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de teste para verificar conexão do robô com CLP.
"""

import sys
from pathlib import Path

# Adiciona diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from config import get_settings
from communication import CIPClient
from control import RobotController

async def test_robot_plc():
    """Testa conexão do robô com CLP."""
    print("=" * 60)
    print("TESTE DE CONEXAO ROBO-CLP")
    print("=" * 60)
    print()
    
    # Obtém configurações
    settings = get_settings(reload=True)
    print(f"CLP IP: {settings.cip.ip}")
    print(f"CLP Port: {settings.cip.port}")
    print(f"Modo simulado: {settings.cip.simulated}")
    print()
    
    # Cria cliente CIP
    print("Criando cliente CIP...")
    cip_client = CIPClient()
    print("OK: Cliente CIP criado")
    print()
    
    # Tenta conectar
    print("Conectando ao CLP...")
    try:
        connected = await cip_client.connect()
        if connected:
            print("OK: Conectado ao CLP")
        else:
            print("AVISO: Modo simulado ativado")
        
        print(f"Status: {cip_client._state.status.value}")
        print(f"Conectado: {cip_client._state.is_connected}")
        print()
        
        # Testa leitura de TAG
        if cip_client._state.is_connected:
            print("Testando leitura de TAG...")
            try:
                value = await cip_client.read_tag("PlcAuthorizeDetection")
                print(f"OK: TAG lido: {value}")
            except Exception as e:
                print(f"ERRO ao ler TAG: {e}")
            print()
        
        # Cria controlador de robô
        print("Criando controlador de robô...")
        robot_controller = RobotController()
        print("OK: Controlador criado")
        print()
        
        # Verifica se pode iniciar
        if cip_client._state.is_connected:
            print("Iniciando controlador de robô...")
            robot_controller.start()
            print("OK: Controlador iniciado")
            
            # Aguarda um pouco
            await asyncio.sleep(1)
            
            print(f"Estado do robô: {robot_controller._state.value}")
        else:
            print("AVISO: Robô não iniciado - CLP não conectado")
        
    except Exception as e:
        print(f"ERRO: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=" * 60)
    print("TESTE CONCLUÍDO")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_robot_plc())
