#!/usr/bin/env python3
"""
jtool2_linux.py — Alternativa a jtool2 para Linux usando LIEF.
Inspecciona binarios Mach-O: entitlements, dylibs, cifrado, firma, secciones, etc.

Uso:
    python3 jtool2_linux.py <ruta_al_binario_Mach-O> [opciones]

Opciones:
    --all          Ejecutar todos los análisis (por defecto)
    --ent          Solo entitlements
    --dylib        Solo dynamic libraries
    --encrypt      Solo info de cifrado
    --sections     Solo secciones
    --symbols      Solo símbolos
    --sign         Solo firma de código
    --uuid         Solo UUID
    --lcs          Solo load commands
    --output FILE  Escribir resultados en archivo
"""

import sys
import os
import lief
import struct
import hashlib
import subprocess
from datetime import datetime

def get_binary_info(binary):
    """Get general binary information."""
    info = []
    info.append("=" * 60)
    info.append("  Información general del binario")
    info.append("=" * 60)
    
    # Header
    if hasattr(binary, 'header'):
        header = binary.header
        info.append(f"Arquitectura: {header.arch}")
        info.append(f"Tipo: {header.type}")
        info.append(f"Flags: {hex(header.flags) if hasattr(header, 'flags') else 'N/A'}")
    
    # File size
    file_size = os.path.getsize(binary.name if hasattr(binary, 'name') else '')
    info.append(f"Tamaño del archivo: {file_size / (1024*1024):.1f} MB")
    
    # Hashes
    info.append(f"\nHashes:")
    with open(binary.name if hasattr(binary, 'name') else '', 'rb') as f:
        data = f.read(1024*1024)  # First 1MB for hash
        info.append(f"  SHA256 (primer 1MB): {hashlib.sha256(data).hexdigest()[:32]}...")
    
    return "\n".join(info)

def get_load_commands(binary):
    """Get load commands (equivalent to jtool2 --lcs)."""
    info = []
    info.append("=" * 60)
    info.append("  Load Commands (jtool2 --lcs)")
    info.append("=" * 60)
    
    if hasattr(binary, 'commands'):
        for cmd in binary.commands:
            cmd_type = type(cmd).__name__
            info.append(f"\n[{cmd_type}]")
            
            if hasattr(cmd, 'name'):
                info.append(f"  Nombre: {cmd.name}")
            if hasattr(cmd, 'path'):
                info.append(f"  Path: {cmd.path}")
            if hasattr(cmd, 'address'):
                info.append(f"  Dirección: {hex(cmd.address)}")
            if hasattr(cmd, 'size'):
                info.append(f"  Tamaño: {cmd.size}")
            if hasattr(cmd, 'cmdsize'):
                info.append(f"  CmdSize: {cmd.cmdsize}")
    
    return "\n".join(info)

def get_dynamic_libraries(binary):
    """Get dynamic libraries (equivalent to jtool2 --dylib)."""
    info = []
    info.append("=" * 60)
    info.append("  Dynamic Libraries (jtool2 --dylib)")
    info.append("=" * 60)
    
    if hasattr(binary, 'imported_libraries'):
        libs = binary.imported_libraries
        info.append(f"\nLibrerías importadas: {len(libs)}")
        info.append("-" * 40)
        for lib in sorted(libs):
            info.append(f"  {lib}")
    
    if hasattr(binary, 'reexported_libraries'):
        info.append(f"\nLibrerías re-exportadas: {len(binary.reexported_libraries)}")
        for lib in binary.reexported_libraries:
            info.append(f"  {lib}")
    
    return "\n".join(info)

def get_encryption_info(binary):
    """Get encryption info (equivalent to jtool2 --encrypt)."""
    info = []
    info.append("=" * 60)
    info.append("  Encryption Info (jtool2 --encrypt)")
    info.append("=" * 60)
    
    if hasattr(binary, 'encryption_info'):
        enc = binary.encryption_info
        info.append(f"Crypt ID: {enc.crypt_id if hasattr(enc, 'crypt_id') else 'N/A'}")
        info.append(f"Crypt Offset: {enc.crypt_offset if hasattr(enc, 'crypt_offset') else 'N/A'}")
        info.append(f"Crypt Size: {enc.crypt_size if hasattr(enc, 'crypt_size') else 'N/A'}")
        
        crypt_id = enc.crypt_id if hasattr(enc, 'crypt_id') else 0
        if crypt_id == 0:
            info.append("\nEstado: NO CIFRADO (cryptid=0)")
            info.append("El binario está completamente descifrado.")
        elif crypt_id == 1:
            info.append("\nEstado: CIFRADO con FairPlay 128-bit")
        elif crypt_id == 2:
            info.append("\nEstado: CIFRADO con FairPlay 128-bit (v2)")
        elif crypt_id == 3:
            info.append("\nEstado: CIFRADO con FairPlay 256-bit")
        else:
            info.append(f"\nEstado: cifrado desconocido (cryptid={crypt_id})")
    else:
        info.append("No se encontró información de cifrado en el binario.")
        info.append("Esto puede indicar que el binario NO está cifrado.")
    
    return "\n".join(info)

def get_entitlements(binary):
    """Get entitlements (equivalent to jtool2 --ent)."""
    info = []
    info.append("=" * 60)
    info.append("  Entitlements (jtool2 --ent)")
    info.append("=" * 60)
    
    # Try to get from binary
    if hasattr(binary, 'entitlements'):
        ents = binary.entitlements
        if ents:
            info.append("\nEntitlements encontrados en el binario:")
            for key, value in ents.items():
                info.append(f"  {key}: {value}")
        else:
            info.append("\nNo se encontraron entitlements en el binario.")
    else:
        info.append("\nLIEF no encontró entitlements directamente.")
        info.append("Buscando en archivos .xcent...")
    
    # Try to read from embedded entitlements file
    binary_path = binary.name if hasattr(binary, 'name') else ''
    app_dir = os.path.dirname(binary_path)
    
    xcent_file = os.path.join(app_dir, 'embedded.mobileprovision')
    xcent_file2 = os.path.join(app_dir, 'archived-expanded-entitlements.xcent')
    
    if os.path.exists(xcent_file2):
        info.append(f"\nEntitlements de {xcent_file2}:")
        try:
            with open(xcent_file2, 'r') as f:
                content = f.read()
                # Parse plist XML
                if '<dict>' in content:
                    # Simple XML parsing for entitlements
                    import re
                    keys = re.findall(r'<key>(.*?)</key>', content)
                    values = re.findall(r'<string>(.*?)</string>|<true/>|<false/>|<integer>(.*?)</integer>', content)
                    for i, key in enumerate(keys):
                        val = values[i] if i < len(values) else '?'
                        info.append(f"  {key}: {val}")
        except Exception as e:
            info.append(f"  Error al leer: {e}")
    
    return "\n".join(info)

def get_code_signature(binary):
    """Get code signature info (equivalent to jtool2 --sign)."""
    info = []
    info.append("=" * 60)
    info.append("  Code Signature (jtool2 --sign)")
    info.append("=" * 60)
    
    if hasattr(binary, 'signature'):
        sig = binary.signature
        info.append(f"Tipo de firma: {type(sig).__name__}")
        
        if hasattr(sig, 'teams_id'):
            info.append(f"Team ID: {sig.teams_id}")
        if hasattr(sig, 'identifier'):
            info.append(f"Identifier: {sig.identifier}")
        if hasattr(sig, 'info_plist'):
            info.append(f"Info.plist hash: {sig.info_plist}")
        
        # Signature slots
        if hasattr(sig, 'slots'):
            info.append(f"\nSlots de firma: {len(sig.slots)}")
            for slot in sig.slots:
                info.append(f"  - {type(slot).__name__}")
    else:
        info.append("No se encontró información de firma de código.")
    
    return "\n".join(info)

def get_sections(binary):
    """Get sections info."""
    info = []
    info.append("=" * 60)
    info.append("  Secciones del binario")
    info.append("=" * 60)
    
    if hasattr(binary, 'sections'):
        info.append(f"\nTotal secciones: {len(binary.sections)}")
        info.append(f"{'Nombre':<25} {'Tamaño':>12} {'Dirección':>15} {'Flags':<10}")
        info.append("-" * 65)
        
        for section in binary.sections:
            name = section.name if hasattr(section, 'name') else 'unknown'
            size = section.size if hasattr(section, 'size') else 0
            addr = hex(section.address) if hasattr(section, 'address') else 'N/A'
            flags = str(section.type) if hasattr(section, 'type') else ''
            
            # Highlight interesting sections
            marker = ""
            if 'objc' in name.lower():
                marker = " ← Objective-C"
            elif 'swift' in name.lower():
                marker = " ← Swift"
            elif '__text' in name or '__text' in name:
                marker = " ← Código"
            elif 'cstring' in name:
                marker = " ← Strings"
            
            info.append(f"  {name:<23} {size:>12,} {addr:>15} {flags:<10}{marker}")
    
    return "\n".join(info)

def get_symbols(binary):
    """Get symbols info (equivalent to jtool2 --sym)."""
    info = []
    info.append("=" * 60)
    info.append("  Símbolos (jtool2 --sym)")
    info.append("=" * 60)
    
    # Use nm for comprehensive symbol listing
    binary_path = binary.name if hasattr(binary, 'name') else ''
    
    try:
        result = subprocess.run(
            ['nm', '-g', '--defined-only', binary_path],
            capture_output=True, text=True, timeout=120
        )
        defined_symbols = result.stdout.strip().split('\n')
        defined_count = len([s for s in defined_symbols if s.strip()])
        
        result = subprocess.run(
            ['nm', '-u', binary_path],
            capture_output=True, text=True, timeout=120
        )
        undefined_symbols = result.stdout.strip().split('\n')
        undefined_count = len([s for s in undefined_symbols if s.strip()])
        
        info.append(f"\nSímbolos definidos: {defined_count}")
        info.append(f"Símbolos indefinidos (externos): {undefined_count}")
        
        # Count ObjC symbols
        objc_classes = 0
        objc_methods = 0
        objc_protocols = 0
        swift_symbols = 0
        
        for line in defined_symbols:
            if '_OBJC_CLASS_$_' in line:
                objc_classes += 1
            elif '_OBJC_$_INSTANCE_METHOD' in line or '_OBJC_$_CLASS_METHOD' in line:
                objc_methods += 1
            elif '_OBJC_PROTOCOL_$_' in line:
                objc_protocols += 1
            elif '$s' in line or 'Swift.' in line:
                swift_symbols += 1
        
        info.append(f"\nDesglose:")
        info.append(f"  Clases Objective-C: {objc_classes}")
        info.append(f"  Métodos Objective-C: {objc_methods}")
        info.append(f"  Protocolos Objective-C: {objc_protocols}")
        info.append(f"  Símbolos Swift: {swift_symbols}")
        
    except Exception as e:
        info.append(f"Error al ejecutar nm: {e}")
    
    return "\n".join(info)

def get_uuid(binary):
    """Get UUID (equivalent to jtool2 --uuid)."""
    info = []
    info.append("=" * 60)
    info.append("  UUID (jtool2 --uuid)")
    info.append("=" * 60)
    
    if hasattr(binary, 'uuid'):
        info.append(f"UUID: {binary.uuid}")
    else:
        info.append("No se encontró UUID en el binario.")
    
    return "\n".join(info)

def get_fileinfo(binary):
    """Get file info."""
    info = []
    info.append("=" * 60)
    info.append("  File Info")
    info.append("=" * 60)
    
    binary_path = binary.name if hasattr(binary, 'name') else ''
    
    # Use 'file' command
    try:
        result = subprocess.run(['file', binary_path], capture_output=True, text=True)
        info.append(result.stdout.strip())
    except:
        pass
    
    # Entry point
    if hasattr(binary, 'entrypoint'):
        info.append(f"\nEntry point: {hex(binary.entrypoint)}")
    
    return "\n".join(info)

def analyze_binary(binary_path, options=None, output_file=None):
    """Main analysis function."""
    
    print(f"[*] Cargando binario: {binary_path}")
    
    try:
        binary = lief.parse(binary_path)
    except Exception as e:
        print(f"[!] Error al cargar: {e}")
        return False
    
    if binary is None:
        print("[!] No se pudo parsear el binario")
        return False
    
    print(f"[*] Binario cargado: {type(binary).__name__}")
    
    results = []
    
    # Determine which analyses to run
    if options is None or 'all' in options:
        results.append(get_fileinfo(binary))
        results.append(get_binary_info(binary))
        results.append(get_uuid(binary))
        results.append(get_encryption_info(binary))
        results.append(get_entitlements(binary))
        results.append(get_dynamic_libraries(binary))
        results.append(get_code_signature(binary))
        results.append(get_sections(binary))
        results.append(get_symbols(binary))
        results.append(get_load_commands(binary))
    else:
        if 'ent' in options:
            results.append(get_entitlements(binary))
        if 'dylib' in options:
            results.append(get_dynamic_libraries(binary))
        if 'encrypt' in options:
            results.append(get_encryption_info(binary))
        if 'sections' in options:
            results.append(get_sections(binary))
        if 'symbols' in options:
            results.append(get_symbols(binary))
        if 'sign' in options:
            results.append(get_code_signature(binary))
        if 'uuid' in options:
            results.append(get_uuid(binary))
        if 'lcs' in options:
            results.append(get_load_commands(binary))
    
    output = "\n\n".join(results)
    
    # Add header
    header = f"""
============================================
  jtool2 — Análisis Mach-O (Linux/LIEF)
  Binario: {os.path.basename(binary_path)}
  Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
============================================
"""
    output = header + "\n" + output
    
    # Output
    if output_file:
        with open(output_file, 'w') as f:
            f.write(output)
        print(f"[✓] Resultados escritos en: {output_file}")
    else:
        print(output)
    
    return True

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"Uso: {sys.argv[0]} <binario_Mach-O> [opciones]")
        print("Opciones: --all --ent --dylib --encrypt --sections --symbols --sign --uuid --lcs")
        sys.exit(1)
    
    binary_path = sys.argv[1]
    options = sys.argv[2:] if len(sys.argv) > 2 else ['all']
    
    output_file = None
    if '--output' in options:
        idx = options.index('--output')
        if idx + 1 < len(options):
            output_file = options[idx + 1]
            options = [o for o in options if o != '--output' and o != output_file]
    
    if not os.path.exists(binary_path):
        print(f"[!] Binario no encontrado: {binary_path}")
        sys.exit(1)
    
    success = analyze_binary(binary_path, options, output_file)
    sys.exit(0 if success else 1)
