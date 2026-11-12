#!/usr/bin/env python3
"""
decrypt_binary.py — Descifra el binario de TikTok usando Frida
Requiere: frida-tools, dispositivo iOS conectado con Frida server

Uso:
    python3 decrypt_binary.py

El script inyecta código en el proceso de TikTok para descifrar
el binario en memoria y extraerlo descifrado.

Proceso:
1. Conecta al dispositivo iOS vía USB
2. Adjunta al proceso de TikTok (o lo lanza)
3. Lee el header Mach-O para encontrar información de cifrado
4. Extrae el binario descifrado de la memoria del proceso
5. Guarda el binario descifrado en _work/ipa/decrypted/
"""

import frida
import sys
import os
import struct
import time

# Configuración
BUNDLE_ID = 'com.zhiliaoapp.musically'
MODULE_NAME = 'MusicallyCore'
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '_work', 'ipa', 'decrypted')

def on_message(message, data):
    if message['type'] == 'error':
        print(f"[!] Error: {message['description']}")
    elif message['type'] == 'send':
        print(f"[+] {message['payload']}")

def ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"[*] Directorio de salida: {OUTPUT_DIR}")

def get_device():
    """Conectar al dispositivo iOS"""
    print("[*] Buscando dispositivo iOS...")
    try:
        device = frida.get_usb_device(timeout=10)
        print(f"✓ Dispositivo conectado: {device.name}")
        print(f"  ID: {device.identifier}")
        return device
    except frida.ServerNotRunningError:
        print("[!] Frida server no está corriendo en el dispositivo")
        print("[*] Instala frida-server:")
        print("  1. Descarga: https://github.com/frida/frida/releases")
        print("  2. Copia al dispositivo: scp frida-server /tmp/")
        print("  3. Ejecuta: ssh root@device 'chmod +x /tmp/frida-server && /tmp/frida-server &'")
        sys.exit(1)
    except frida.TimedOutError:
        print("[!] No se encontró un dispositivo iOS conectado")
        print("[*] Conecta el dispositivo vía USB y asegúrate de confiar en esta computadora")
        sys.exit(1)
    except Exception as e:
        print(f"[!] Error al conectar: {e}")
        sys.exit(1)

def attach_to_tiktok(device):
    """Adjuntar al proceso de TikTok"""
    print(f"\n[*] Buscando proceso {BUNDLE_ID}...")
    
    # Verificar si TikTok está corriendo
    try:
        pid = device.get_frontmost_application().identifier
        if pid == BUNDLE_ID:
            print("✓ TikTok está en primer plano")
    except:
        pass
    
    # Intentar adjuntar
    try:
        app = device.get_application(BUNDLE_ID)
        print(f"✓ TikTok encontrado en el dispositivo")
        
        # Verificar si está corriendo
        try:
            session = device.attach(app.pid)
            print(f"✓ Adjuntado al proceso (PID: {app.pid})")
            return session
        except frida.InvalidOperationError:
            pass
        
        # Si no está corriendo, lanzarlo
        print("[*] TikTok no está corriendo. Lanzando...")
        session = device.attach(device.spawn(BUNDLE_ID))
        device.resume(session.identifier)
        print("✓ TikTok lanzado y adjuntado")
        return session
        
    except Exception as e:
        print(f"[!] Error al adjuntar a TikTok: {e}")
        print("[*] Asegúrate de que TikTok esté instalado en el dispositivo")
        sys.exit(1)

def analyze_encryption(session):
    """Analizar el estado de cifrado del binario"""
    
    script_code = """
    // Encontrar el módulo MusicallyCore
    var moduleName = 'MusicallyCore';
    var targetModule = null;
    
    var modules = Process.enumerateModules();
    for (var i = 0; i < modules.length; i++) {
        if (modules[i].name === moduleName) {
            targetModule = modules[i];
            break;
        }
    }
    
    if (!targetModule) {
        send('Módulo ' + moduleName + ' no encontrado');
        send('Módulos disponibles:');
        for (var i = 0; i < Math.min(modules.length, 50); i++) {
            send('  ' + modules[i].name + ' @ ' + modules[i].base);
        }
        return;
    }
    
    send('Módulo: ' + targetModule.name);
    send('Base: ' + targetModule.base.toString());
    send('Size: ' + targetModule.size.toString());
    send('Path: ' + targetModule.path);
    
    // Leer el header Mach-O
    var header = targetModule.base;
    var magic = header.readUInt32();
    send('Magic: 0x' + magic.toString(16));
    
    var is64Bit = (magic === 0xfeedfacf || magic === 0xcffaedfe);
    var isFat = (magic === 0xcafebabe || magic === 0xbebafeca);
    
    if (isFat) {
        send('⚠ Fat binary detectado (universal binary)');
        return;
    }
    
    if (!is64Bit) {
        send('⚠ No es un Mach-O 64-bit válido');
        return;
    }
    
    send('✓ Mach-O 64-bit detectado');
    
    // Leer campos del header
    var cpuType = header.add(4).readInt32();
    var cpuSubtype = header.add(8).readInt32();
    var filetype = header.add(12).readUInt32();
    var ncmds = header.add(16).readUInt32();
    var sizeofcmds = header.add(20).readUInt32();
    var flags = header.add(24).readUInt32();
    
    send('CPU Type: 0x' + cpuType.toString(16));
    send('CPU Subtype: 0x' + cpuSubtype.toString(16));
    send('File Type: 0x' + filetype.toString(16));
    send('NCMDs: ' + ncmds);
    send('Sizeofcmds: ' + sizeofcmds);
    send('Flags: 0x' + flags.toString(16));
    
    // Buscar LC_ENCRYPTION_INFO y LC_SEGMENT_64
    var cmdOffset = header.add(32);
    var encryptionInfo = null;
    var textSegment = null;
    
    for (var i = 0; i < ncmds; i++) {
        var cmd = cmdOffset.readUInt32();
        var cmdsize = cmdOffset.add(4).readUInt32();
        
        if (cmd === 0x21 || cmd === 0x2C) {
            // LC_ENCRYPTION_INFO (0x21) o LC_ENCRYPTION_INFO_64 (0x2C)
            var cryptoff = cmdOffset.add(8).readUInt32();
            var cryptsize = cmdOffset.add(12).readUInt32();
            var cryptid = cmdOffset.add(16).readUInt32();
            
            encryptionInfo = {
                cryptoff: cryptoff,
                cryptsize: cryptsize,
                cryptid: cryptid
            };
            
            send('');
            send('=== ENCRYPTION INFO ===');
            send('CryptID: ' + cryptid);
            send('CryptOff: 0x' + cryptoff.toString(16));
            send('CryptSize: 0x' + cryptsize.toString(16) + ' (' + (cryptsize / 1024 / 1024).toFixed(2) + ' MB)');
            
            if (cryptid === 0) {
                send('Estado: NO CIFRADO');
            } else if (cryptid === 1) {
                send('Estado: CIFRADO (AES-128)');
            } else if (cryptid === 2) {
                send('Estado: CIFRADO (AES-192)');
            } else if (cryptid === 3) {
                send('Estado: CIFRADO (AES-256)');
            } else if (cryptid === 4) {
                send('Estado: CIFRADO (AES-128 con key diferente)');
            } else {
                send('Estado: CIFRADO (unknown cryptid: ' + cryptid + ')');
            }
        }
        
        if (cmd === 0x19 || cmd === 0x25) {
            // LC_SEGMENT_64
            var segname = cmdOffset.add(8).readUtf8String(16).replace(/\\u0000/g, '');
            if (segname === '__TEXT') {
                var vmaddr = cmdOffset.add(24).readPointer();
                var vmsize = cmdOffset.add(32).readUInt64();
                var fileoff = cmdOffset.add(40).readUInt64();
                var filesize = cmdOffset.add(48).readUInt64();
                
                textSegment = {
                    vmaddr: vmaddr,
                    vmsize: vmsize,
                    fileoff: fileoff,
                    filesize: filesize
                };
                
                send('');
                send('=== __TEXT SEGMENT ===');
                send('VMAddr: 0x' + vmaddr.toString(16));
                send('VMSize: 0x' + vmsize.toString(16));
                send('FileOff: 0x' + fileoff.toString(16));
                send('FileSize: 0x' + filesize.toString(16));
            }
        }
        
        cmdOffset = cmdOffset.add(cmdsize);
    }
    
    if (!encryptionInfo) {
        send('');
        send('⚠ No se encontró LC_ENCRYPTION_INFO');
    }
    
    // Enviar info para descifrado
    if (encryptionInfo && encryptionInfo.cryptid > 0) {
        send('');
        send('=== PARA DESCIFRADO ===');
        send('El binario está cifrado en memoria.');
        send('iOS descifra el binario al cargarlo en memoria.');
        send('Para extraer el binario descifrado, hay que leerlo de la memoria del proceso.');
    }
    """
    
    print("\n[*] Analizando cifrado del binario...")
    script = session.create_script(script_code)
    script.on('message', on_message)
    script.load()
    
    # Esperar a que termine
    time.sleep(5)
    
    return script

def decrypt_binary(session, device):
    """Extraer el binario descifrado de la memoria"""
    
    script_code = f"""
    var moduleName = '{MODULE_NAME}';
    var targetModule = null;
    
    var modules = Process.enumerateModules();
    for (var i = 0; i < modules.length; i++) {{
        if (modules[i].name === moduleName) {{
            targetModule = modules[i];
            break;
        }}
    }}
    
    if (!targetModule) {{
        send('Módulo no encontrado');
        return;
    }}
    
    send('Extrayendo binario de memoria...');
    send('Tamaño: ' + targetModule.size + ' bytes');
    
    // Leer el binario completo de la memoria (ya descifrado por iOS)
    var chunkSize = 0x100000; // 1MB por chunk
    var offset = 0;
    var totalSize = targetModule.size;
    
    while (offset < totalSize) {{
        var size = Math.min(chunkSize, totalSize - offset);
        var ptr = targetModule.base.add(offset);
        var data = ptr.readByteArray(size);
        
        send('Progreso: ' + Math.round((offset + size) / totalSize * 100) + '%');
        
        // Enviar datos al Python
        send(data);
        
        offset += size;
    }}
    
    send('DESCRYPION_COMPLETE');
    """
    
    print("\n[*] Extrayendo binario descifrado de la memoria...")
    print(f"  Esto puede tardar varios minutos ({MODULE_NAME} es ~866 MB)")
    
    script = session.create_script(script_code)
    
    received_data = bytearray()
    
    def on_message(message, data):
        if message['type'] == 'error':
            print(f"[!] Error: {message['description']}")
        elif message['type'] == 'send':
            payload = message['payload']
            if isinstance(payload, bytes):
                received_data.extend(payload)
                size_mb = len(received_data) / 1024 / 1024
                print(f"  Recibido: {size_mb:.1f} MB")
            elif 'DESCRYPION_COMPLETE' in str(payload):
                print("✓ Extracción completada")
            else:
                print(f"  {payload}")
    
    script.on('message', on_message)
    script.load()
    
    # Esperar a que termine
    try:
        sys.stdin.read()
    except KeyboardInterrupt:
        pass
    
    if received_data:
        output_path = os.path.join(OUTPUT_DIR, MODULE_NAME)
        with open(output_path, 'wb') as f:
            f.write(received_data)
        print(f"\n✓ Binario descifrado guardado: {output_path}")
        print(f"  Tamaño: {len(received_data) / 1024 / 1024:.1f} MB")
    else:
        print("[!] No se recibieron datos")

def main():
    print("=" * 50)
    print("  TikTok iOS — Descifrado de binario con Frida")
    print("=" * 50)
    print()
    
    ensure_output_dir()
    device = get_device()
    session = attach_to_tiktok(device)
    
    print("\n[*] ¿Qué deseas hacer?")
    print("  1. Analizar cifrado del binario")
    print("  2. Extraer binario descifrado de memoria")
    print("  3. Ambos")
    print()
    
    choice = input("[*] Elige (1-3): ").strip()
    
    if choice in ('1', '3'):
        analyze_encryption(session)
    
    if choice == '2':
        decrypt_binary(session, device)
    elif choice == '3':
        print("\n[*] Ahora extrayendo binario descifrado...")
        decrypt_binary(session, device)
    
    print("\n✓ Proceso completado")
    print(f"  Binario descifrado: {OUTPUT_DIR}/{MODULE_NAME}")
    print()
    print("  Siguiente paso:")
    print("  1. Mueve el binario a _work/ipa/TikTok_extracted/Payload/TikTok.app/Frameworks/MusicallyCore.framework/")
    print("  2. Ejecuta: bash scripts/run_analysis.sh")

if __name__ == '__main__':
    main()
