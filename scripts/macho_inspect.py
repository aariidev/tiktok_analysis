#!/usr/bin/env python3
"""
macho_inspect.py — Inspección ligera de binarios Mach-O sin cargar todo en memoria.
Lee solo los headers y load commands para obtener info clave.

Uso:
    python3 macho_inspect.py <binario_Mach-O> [output_file]
"""

import struct
import sys
import os
import re
from datetime import datetime

def format_uuid(b):
    return f'{b[0]:02x}{b[1]:02x}{b[2]:02x}{b[3]:02x}-{b[4]:02x}{b[5]:02x}-{b[6]:02x}{b[7]:02x}-{b[8]:02x}{b[9]:02x}-{b[10]:02x}{b[11]:02x}{b[12]:02x}{b[13]:02x}{b[14]:02x}{b[15]:02x}'

def parse_macho(binary_path):
    results = []
    
    file_size = os.path.getsize(binary_path)
    
    with open(binary_path, 'rb') as f:
        magic = struct.unpack('<I', f.read(4))[0]
        
        if magic != 0xfeedfacf:
            # Try fat binary
            fat_magic = struct.unpack('>I', f.read(4))[0] if magic != 0xcafebabe else magic
            if fat_magic == 0xcafebabe:
                results.append("Fat binary detected, using first architecture")
                nfat_arch = struct.unpack('>I', f.read(4))[0]
                # Find first 64-bit arm64 arch
                for _ in range(nfat_arch):
                    cputype, cpusubtype, offset, size, align = struct.unpack('<IIIII', f.read(20))
                    if cputype == 0x0100000C:  # arm64
                        f.seek(offset)
                        magic = struct.unpack('<I', f.read(4))[0]
                        break
            
        cputype, cpusubtype, filetype, ncmds, sizeofcmds, flags = struct.unpack('<IIIII I', f.read(24))
        
        header_size = 32
        load_commands_start = header_size
        f.seek(load_commands_start)
        
        dylibs = []
        encryption_info = None
        uuid_val = None
        segments = []
        code_sig_size = 0
        entry_point = None
        
        for i in range(ncmds):
            pos = f.tell()
            cmd, cmdsize = struct.unpack('<II', f.read(8))
            
            if cmd == 0x21:  # LC_ENCRYPTION_INFO_64
                cryptoff, cryptsize, cryptid, pad = struct.unpack('<IIII', f.read(16))
                encryption_info = {'crypt_id': cryptid, 'crypt_offset': cryptoff, 'crypt_size': cryptsize}
            elif cmd == 0x25:  # LC_ENCRYPTION_INFO
                cryptoff, cryptsize, cryptid = struct.unpack('<III', f.read(12))
                encryption_info = {'crypt_id': cryptid, 'crypt_offset': cryptoff, 'crypt_size': cryptsize}
            elif cmd == 0x1A:  # LC_UUID
                uuid_bytes = f.read(16)
                uuid_val = format_uuid(uuid_bytes)
            elif cmd in (0xC, 0xD, 0xE, 0x39):  # LC_LOAD_DYLIB, LC_LOAD_WEAK_DYLIB, etc.
                name_offset = struct.unpack('<I', f.read(4))[0]
                f.seek(load_commands_start + name_offset)
                name_bytes = b''
                while True:
                    b = f.read(1)
                    if b == b'\x00' or len(name_bytes) > 512:
                        break
                    name_bytes += b
                name = name_bytes.decode('utf-8', errors='replace')
                if name:
                    dylibs.append(name)
                f.seek(pos + cmdsize)
                continue
            elif cmd == 0x6:  # LC_SEGMENT_64
                seg_name_raw = f.read(16)
                seg_name = seg_name_raw.split(b'\x00')[0].decode('utf-8', errors='replace')
                vmaddr, vmsize, fileoff, filesize = struct.unpack('<QQQQ', f.read(32))
                maxprot, initprot, nsects, flags_seg = struct.unpack('<iiII', f.read(16))
                segments.append({
                    'name': seg_name, 'nsects': nsects,
                    'fileoff': fileoff, 'filesize': filesize, 'vmsize': vmsize
                })
                f.seek(pos + cmdsize)
                continue
            elif cmd == 0x1E:  # LC_CODE_SIGNATURE
                dataoff, datalen = struct.unpack('<II', f.read(8))
                code_sig_size = datalen
            elif cmd == 0x22:  # LC_MAIN (entry point)
                entryoff = struct.unpack('<I', f.read(4))[0]
                entry_point = entryoff
            elif cmd == 0x23:  # LC_DATA_IN_CODE
                pass
            
            f.seek(pos + cmdsize)
    
    # Build output
    output = []
    output.append("=" * 60)
    output.append("  jtool2 — Análisis Mach-O de TikTok iOS (MusicallyCore)")
    output.append(f"  Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    output.append("=" * 60)
    output.append("")
    
    output.append("--- Información general ---")
    output.append(f"  Archivo: {os.path.basename(binary_path)}")
    output.append(f"  Tamaño: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")
    output.append(f"  Arquitectura: arm64")
    output.append(f"  File type: {hex(filetype)}")
    output.append(f"  Load commands: {ncmds}")
    output.append(f"  Flags: {hex(flags)}")
    output.append("")
    
    output.append("--- UUID ---")
    output.append(f"  {uuid_val if uuid_val else 'No encontrado'}")
    output.append("")
    
    output.append("--- Encryption Info ---")
    if encryption_info:
        cid = encryption_info['crypt_id']
        output.append(f"  Crypt ID: {cid}")
        output.append(f"  Crypt Offset: {hex(encryption_info['crypt_offset'])} ({encryption_info['crypt_offset']})")
        output.append(f"  Crypt Size: {hex(encryption_info['crypt_size'])} ({encryption_info['crypt_size']:,} bytes)")
        if cid == 0:
            output.append(f"  Estado: NO CIFRADO (binario descifrado por TTKiller Plus)")
        elif cid == 1:
            output.append(f"  Estado: CIFRADO FairPlay 128-bit")
        elif cid == 2:
            output.append(f"  Estado: CIFRADO FairPlay 128-bit v2")
        elif cid == 3:
            output.append(f"  Estado: CIFRADO FairPlay 256-bit")
    else:
        output.append(f"  No se encontró LC_ENCRYPTION_INFO en el binario")
        output.append(f"  Estado: NO CIFRADO (sin comando de cifrado = binario ya descifrado)")
    output.append("")
    
    output.append(f"--- Dynamic Libraries ({len(dylibs)}) ---")
    system_libs = []
    third_party_libs = []
    for lib in sorted(dylibs):
        if lib.startswith('/System/') or lib.startswith('/usr/lib/'):
            system_libs.append(lib)
        else:
            third_party_libs.append(lib)
    
    output.append(f"\n  Sistema ({len(system_libs)}):")
    for lib in system_libs:
        output.append(f"    {lib}")
    
    if third_party_libs:
        output.append(f"\n  Terceros ({len(third_party_libs)}):")
        for lib in third_party_libs:
            output.append(f"    {lib}")
    output.append("")
    
    output.append(f"--- Segments ({len(segments)}) ---")
    output.append(f"  {'Segment':<20} {'Secciones':>10} {'Tamaño':>15} {'Descripción'}")
    output.append(f"  {'-'*20} {'-'*10} {'-'*15} {'-'*20}")
    for seg in segments:
        marker = ''
        sname = seg['name']
        if 'OBJC' in sname or 'objc' in sname:
            marker = ' ← Objective-C metadata'
        elif 'text' in sname:
            marker = ' ← Código ejecutable'
        elif 'cstring' in sname or 'const' in sname:
            marker = ' ← Strings y constantes'
        elif 'swift' in sname:
            marker = ' ← Swift metadata'
        elif 'data' in sname or 'bss' in sname:
            marker = ' ← Datos mutables'
        elif 'info' in sname or 'debug' in sname:
            marker = ' ← Debug/Info'
        elif 'linkedit' in sname:
            marker = ' ← Symbol table, strings'
        output.append(f"  {sname:<20} {seg['nsects']:>10} {seg['filesize']:>15,} {marker}")
    output.append("")
    
    output.append("--- Code Signature ---")
    if code_sig_size:
        output.append(f"  Code signature size: {code_sig_size:,} bytes ({code_sig_size/1024/1024:.1f} MB)")
    else:
        output.append(f"  No code signature found")
    output.append("")
    
    # Entitlements
    output.append("--- Entitlements ---")
    app_dir = os.path.dirname(os.path.dirname(binary_path))
    xcent = os.path.join(app_dir, 'archived-expanded-entitlements.xcent')
    if os.path.exists(xcent):
        with open(xcent, 'r') as ef:
            content = ef.read()
            # Parse keys and values
            keys = re.findall(r'<key>(.*?)</key>', content)
            strings = re.findall(r'<string>(.*?)</string>', content)
            trues = content.count('<true/>')
            falses = content.count('<false/>')
            
            for i, key in enumerate(keys):
                val = strings[i] if i < len(strings) else '?'
                output.append(f"  {key}: {val}")
    else:
        output.append("  No entitlements file found")
    output.append("")
    
    return "\n".join(output)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"Uso: {sys.argv[0]} <binario_Mach-O> [output_file]")
        sys.exit(1)
    
    binary_path = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not os.path.exists(binary_path):
        print(f"[!] Binario no encontrado: {binary_path}")
        sys.exit(1)
    
    print(f"[*] Analizando: {binary_path}")
    result = parse_macho(binary_path)
    
    if output_file:
        os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
        with open(output_file, 'w') as f:
            f.write(result)
        print(f"[✓] Resultados escritos en: {output_file}")
    else:
        print(result)
    
    print("[✓] Análisis completado")
