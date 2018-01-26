#!/usr/bin/python
#
# Escucha paquetes SSDP en la red para 
# atender encendidos o apagados de equipos
# compatibles con UPnP
#
from socket import socket, inet_aton, IPPROTO_IP, IP_ADD_MEMBERSHIP
from socket import AF_INET, SOCK_DGRAM, SOL_SOCKET, SO_REUSEADDR, INADDR_ANY
import struct


MCAST_GRP   = '239.255.255.250'
MCAST_PORT  = 1900
BUFFER_SIZE = 1024
ENCENDIDO   = "ssdp:alive"
APAGADO     = "ssdp:byebye"

OPENHAB     = '192.168.1.5'

valid_keys = {
        'host:':               None,
        'server:':             None,
        'nt:':                 None,
        'nts:':                None,
        'location:':           None,
        'cache-control:':      None,    # Atento, indica cuando va a morir
        'usn:':                None,
        'content-length:':     None,
        'mx:':                 None,
        'man:':                None,
        'st:':                 None,
        'user-agent:':         None
}

def Mostrar(*args):
    print(*args)

# Comienzo del bucle principal

sock = socket(AF_INET, SOCK_DGRAM)
sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
sock.bind(('', MCAST_PORT))

mreq = struct.pack('=4s4s', inet_aton(MCAST_GRP), inet_aton(OPENHAB)) # pack MCAST_GRP correctly
sock.setsockopt(IPPROTO_IP, IP_ADD_MEMBERSHIP, mreq)         # Request MCAST_GRP

#sock.bind(('', MCAST_PORT))                           # Bind to all intfs

# HOST: SERVER: NT: NTS: LOCATION: CACHE-CONTROL: USN: Content-Length:
# NTS (Notification Sub Type) puede tener el valor "ssdp:alive" para registrarse o "ssdp:byebye" para anular el registro del dispositivo.
# USN (Unique Service Name) contiene una identificación única.
# LOCATION contiene la URL de la descripción

while True:
    respuesta, host = sock.recvfrom(BUFFER_SIZE)
    respuesta = respuesta.split(b'\r\n')
#
# Respuesta es una colección de objetos
#
    estado  = ""
    paquete = {}
    tipo    = 0
    for item in respuesta:
        linea = item.decode("utf-8")

        tokens = linea.split()

        if len(tokens) == 0:
            continue

        key = tokens[0].lower()

        if key == "m-search":
            tipo = 1
        elif key == "notify":
            tipo = 2
        elif key in valid_keys:
            paquete[key] = tokens[1:]
        else:
            paquete["Error " + key] = tokens[1:]
            # Enviar una copia a un fichero

    print("Conexión desde:", host)
    if tipo == 1:
        print("\tEra una búsqueda")
    elif tipo == 2:
        print("\tEra un anuncio")
    if tipo == 0:
        print('=' * 20)
        print("Comando desconocido")
        print('=' * 20)

    if tipo == 2 and 'nts:' in paquete:
        for item in paquete:
            Mostrar("Clave: ", item, "==>", paquete[item])

        if paquete['nts:'] == [ENCENDIDO]:
            estado = 'ON'
        elif paquete['nts:'] == [APAGADO]:
            estado = 'OFF'
        else:
            print("Subopción NTS Desconocida", paquete['nts:'])
        if estado != '':
            if estado == 'ON':
                print("<=== Cacharro encendiendose ===>")
            else:
                print("<=== Cacharro apagandose ===>")

# Una vez que encuentro que se enciende o se apaga
# Buscar un lease de DHCP para la dirección IP del emisor
# Obtener la dirección MAC
# Buscar en el fichero si la MAC aparece
# Si la MAC aparece, sacar el nombre del objeto
# Obtener por REST el estado del objeto
# Actualizarlo si procede
#