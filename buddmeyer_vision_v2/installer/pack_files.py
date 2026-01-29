#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para empacotar arquivos do projeto para o instalador.
"""

import shutil
import zipfile
from pathlib import Path

def pack_project():
    """Empacota o projeto em um arquivo ZIP."""
    
    installer_dir = Path(__file__).parent
    project_root = installer_dir.parent.parent
    project_dir = project_root / "buddmeyer_vision_v2"
    
    output_file = installer_dir / "buddmeyer_vision_v2.zip"
    
    print("Empacotando projeto...")
    
    # Remove arquivo ZIP anterior se existir
    if output_file.exists():
        output_file.unlink()
    
    # Cria arquivo ZIP
    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in project_dir.rglob('*'):
            if file_path.is_file():
                # Ignora arquivos temporários e cache
                if any(part in str(file_path) for part in ['__pycache__', '.pyc', '.pyo', '.pyd']):
                    continue
                
                arcname = file_path.relative_to(project_root)
                zipf.write(file_path, arcname)
                print(f"  Adicionado: {arcname}")
    
    print(f"\n✓ Projeto empacotado: {output_file}")
    print(f"  Tamanho: {output_file.stat().st_size / 1024 / 1024:.2f} MB")
    
    return output_file

if __name__ == "__main__":
    pack_project()
