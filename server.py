"""
server.py — Servidor de chat com sockets TCP, criptografia AES e sistema de salas

Como funciona:
  1. O servidor inicia e fica aguardando conexões na porta 5000
  2. Cada cliente escolhe um apelido e uma sala ao conectar
  3. As mensagens são retransmitidas apenas para clientes da mesma sala
"""

import socket
import threading
from crypto import encrypt, decrypt

# ─── Configurações ────────────────────────────────────────────────────────────
HOST = "0.0.0.0"
PORT = 5000

# ─── Salas disponíveis ────────────────────────────────────────────────────────
ROOMS = ["geral", "jogos", "tecnologia"]

# ─── Estado global ────────────────────────────────────────────────────────────
# Dicionário: { nome_da_sala: [(socket, apelido), ...] }
rooms = {room: [] for room in ROOMS}
lock = threading.Lock()

def broadcast_room(room: str, message: str, sender_socket=None):
    """Envia mensagem criptografada para todos na sala, exceto o remetente."""
    encrypted = encrypt(message)
    with lock:
        for client_socket, _ in rooms[room]:
            if client_socket != sender_socket:
                try:
                    client_socket.sendall((encrypted + "\n").encode("utf-8"))
                except:
                    pass

def send(client_socket, message: str):
    """Envia uma mensagem criptografada para um cliente específico."""
    try:
        client_socket.sendall((encrypt(message) + "\n").encode("utf-8"))
    except:
        pass

def list_users_in_room(room: str) -> str:
    """Retorna uma string com os apelidos de todos na sala."""
    with lock:
        users = [nick for _, nick in rooms[room]]
    return ", ".join(users) if users else "Ninguém"

def handle_client(client_socket: socket.socket, address: tuple):
    """Thread dedicada para cada cliente conectado."""
    nickname = ""
    current_room = ""

    try:
        # ── Solicita apelido ──────────────────────────────────────────────────
        send(client_socket, "APELIDO:")
        nickname = decrypt(client_socket.recv(1024).decode("utf-8").strip())

        # ── Envia lista de salas e solicita escolha ───────────────────────────
        rooms_list = "\n".join([f"{i+1}. #{room}" for i, room in enumerate(ROOMS)])
        send(client_socket, f"SALAS:{rooms_list}")
        choice_raw = decrypt(client_socket.recv(1024).decode("utf-8").strip())

        try:
            idx = int(choice_raw) - 1
            current_room = ROOMS[idx] if 0 <= idx < len(ROOMS) else ROOMS[0]
        except ValueError:
            current_room = choice_raw if choice_raw in ROOMS else ROOMS[0]

        # ── Adiciona cliente à sala ───────────────────────────────────────────
        with lock:
            rooms[current_room].append((client_socket, nickname))

        print(f"[+] {nickname} entrou em #{current_room} ({address})")
        send(client_socket, f"SALA_OK:{current_room}")
        send(client_socket, f"[Servidor] Bem-vindo à sala #{current_room}, {nickname}!")
        broadcast_room(current_room, f"[Servidor] {nickname} entrou na sala.", sender_socket=client_socket)

        # ── Loop de mensagens ─────────────────────────────────────────────────
        while True:
            data = client_socket.recv(4096).decode("utf-8").strip()
            if not data:
                break

            message = decrypt(data)

            if message.strip() == "/usuarios":
                users = list_users_in_room(current_room)
                send(client_socket, f"[Servidor] Usuários em #{current_room}: {users}")
                continue

            if message.startswith("/sala "):
                new_room = message.split(" ", 1)[1].strip()
                if new_room not in ROOMS:
                    send(client_socket, f"[Servidor] Sala '#{new_room}' não existe. Salas: {', '.join(ROOMS)}")
                    continue

                broadcast_room(current_room, f"[Servidor] {nickname} saiu da sala.", sender_socket=client_socket)
                with lock:
                    rooms[current_room] = [(s, n) for s, n in rooms[current_room] if s != client_socket]

                current_room = new_room
                with lock:
                    rooms[current_room].append((client_socket, nickname))

                send(client_socket, f"SALA_OK:{current_room}")
                send(client_socket, f"[Servidor] Você entrou em #{current_room}!")
                broadcast_room(current_room, f"[Servidor] {nickname} entrou na sala.", sender_socket=client_socket)
                print(f"[~] {nickname} mudou para #{current_room}")
                continue

            print(f"[#{current_room}] [{nickname}] {message}")
            broadcast_room(current_room, f"[{nickname}]: {message}", sender_socket=client_socket)

    except Exception as e:
        print(f"[!] Erro com {nickname or address}: {e}")

    finally:
        with lock:
            if current_room and current_room in rooms:
                rooms[current_room] = [(s, n) for s, n in rooms[current_room] if s != client_socket]
        client_socket.close()
        print(f"[-] {nickname or address} desconectou")
        if nickname and current_room:
            broadcast_room(current_room, f"[Servidor] {nickname} saiu do chat.")

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()

    print(f"✅ Servidor de chat rodando em {HOST}:{PORT}")
    print(f"📋 Salas disponíveis: {', '.join(['#' + r for r in ROOMS])}")
    print("Aguardando conexões...\n")

    try:
        while True:
            client_socket, address = server.accept()
            thread = threading.Thread(target=handle_client, args=(client_socket, address))
            thread.daemon = True
            thread.start()
    except KeyboardInterrupt:
        print("\n[!] Servidor encerrado.")
    finally:
        server.close()

if __name__ == "__main__":
    start_server()
