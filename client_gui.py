"""
client_gui.py — Cliente de chat com interface gráfica (Tkinter) e salas

Como funciona:
  1. Abre uma janela pedindo apelido e sala
  2. Conecta ao servidor via socket TCP
  3. Exibe mensagens em tempo real na janela
  4. Permite trocar de sala pelo botão ou digitando /sala <nome>
"""

import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog
from crypto import encrypt, decrypt

# ─── Configurações ────────────────────────────────────────────────────────────
HOST = "127.0.0.1"
PORT = 5000

class ChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("💬 Chat")
        self.root.configure(bg="#1a1a2e")
        self.root.resizable(True, True)
        self.root.minsize(500, 400)

        self.client = None
        self.nickname = ""
        self.current_room = ""
        self.running = False
        self.buffer = ""

        self._build_ui()
        self.root.after(100, self._connect)

    # ─── Interface ────────────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Cabeçalho ──────────────────────────────────────────────────────────
        self.header = tk.Frame(self.root, bg="#16213e", pady=10)
        self.header.pack(fill="x")

        self.title_label = tk.Label(
            self.header, text="💬 Chat", font=("Segoe UI", 16, "bold"),
            fg="white", bg="#16213e"
        )
        self.title_label.pack(side="left", padx=16)

        self.room_label = tk.Label(
            self.header, text="", font=("Segoe UI", 11),
            fg="#4ade80", bg="#16213e"
        )
        self.room_label.pack(side="left")

        # Botões de sala no cabeçalho
        self.rooms_frame = tk.Frame(self.header, bg="#16213e")
        self.rooms_frame.pack(side="right", padx=10)

        self.room_buttons = {}
        for room in ["geral", "jogos", "tecnologia"]:
            btn = tk.Button(
                self.rooms_frame, text=f"#{room}",
                font=("Segoe UI", 9), bg="#0f3460", fg="white",
                relief="flat", padx=8, pady=4, cursor="hand2",
                command=lambda r=room: self._change_room(r)
            )
            btn.pack(side="left", padx=4)
            self.room_buttons[room] = btn

        # ── Área de mensagens ──────────────────────────────────────────────────
        self.chat_area = scrolledtext.ScrolledText(
            self.root, state="disabled", wrap="word",
            bg="#0f3460", fg="white", font=("Segoe UI", 11),
            relief="flat", padx=12, pady=10,
            insertbackground="white"
        )
        self.chat_area.pack(fill="both", expand=True, padx=12, pady=(8, 4))

        # Cores por tipo de mensagem
        self.chat_area.tag_config("server", foreground="#facc15")
        self.chat_area.tag_config("self",   foreground="#4ade80")
        self.chat_area.tag_config("other",  foreground="#e2e8f0")

        # ── Barra de entrada ──────────────────────────────────────────────────
        input_frame = tk.Frame(self.root, bg="#1a1a2e", pady=8)
        input_frame.pack(fill="x", padx=12, pady=(0, 10))

        self.input_field = tk.Entry(
            input_frame, font=("Segoe UI", 12),
            bg="#16213e", fg="white", relief="flat",
            insertbackground="white"
        )
        self.input_field.pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 8))
        self.input_field.bind("<Return>", self._send_message)

        send_btn = tk.Button(
            input_frame, text="Enviar", font=("Segoe UI", 11, "bold"),
            bg="#4ade80", fg="#0f3460", relief="flat",
            padx=16, pady=6, cursor="hand2",
            command=self._send_message
        )
        send_btn.pack(side="right")

        # ── Rodapé com dica de comandos ────────────────────────────────────────
        footer = tk.Label(
            self.root,
            text="Comandos: /usuarios  |  /sala <nome>",
            font=("Segoe UI", 8), fg="#4b5563", bg="#1a1a2e"
        )
        footer.pack(pady=(0, 6))

    # ─── Conexão ──────────────────────────────────────────────────────────────

    def _connect(self):
        self.nickname = simpledialog.askstring("Apelido", "Digite seu apelido:", parent=self.root)
        if not self.nickname:
            self.root.destroy()
            return

        try:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.connect((HOST, PORT))
        except:
            messagebox.showerror("Erro", f"Não foi possível conectar ao servidor {HOST}:{PORT}\nCertifique-se de que o servidor está rodando.")
            self.root.destroy()
            return

        self.running = True
        thread = threading.Thread(target=self._receive_loop, daemon=True)
        thread.start()

    def _receive_loop(self):
        """Fica em segundo plano recebendo mensagens do servidor."""
        while self.running:
            try:
                data = self.client.recv(4096).decode("utf-8")
                if not data:
                    break

                self.buffer += data
                while "\n" in self.buffer:
                    line, self.buffer = self.buffer.split("\n", 1)
                    line = line.strip()
                    if line:
                        message = decrypt(line)
                        self.root.after(0, self._handle_server_message, message)
            except:
                break

    def _handle_server_message(self, message: str):
        """Processa mensagens recebidas do servidor."""

        # Servidor pedindo apelido
        if message == "APELIDO:":
            self.client.sendall((encrypt(self.nickname) + "\n").encode("utf-8"))
            return

        # Servidor enviando lista de salas
        if message.startswith("SALAS:"):
            self._ask_room(message[6:])
            return

        # Confirmação de entrada na sala
        if message.startswith("SALA_OK:"):
            self.current_room = message[8:]
            self.room_label.config(text=f"  •  #{self.current_room}")
            self.root.title(f"💬 Chat — #{self.current_room}")
            self._highlight_room_button()
            return

        # Mensagem normal
        tag = "server" if message.startswith("[Servidor]") else "other"
        self._append_message(message, tag)

    def _ask_room(self, rooms_text: str):
        """Abre janela para escolher a sala."""
        rooms = [line.split(". #")[1] for line in rooms_text.strip().split("\n") if ". #" in line]
        choice = simpledialog.askstring(
            "Escolha a sala",
            f"Salas disponíveis:\n{rooms_text}\n\nDigite o número ou nome da sala:",
            parent=self.root
        )
        if not choice:
            choice = "1"
        self.client.sendall((encrypt(choice) + "\n").encode("utf-8"))

    # ─── Mensagens ────────────────────────────────────────────────────────────

    def _send_message(self, event=None):
        message = self.input_field.get().strip()
        if not message or not self.client:
            return

        try:
            self.client.sendall((encrypt(message) + "\n").encode("utf-8"))
        except:
            self._append_message("[Erro] Falha ao enviar mensagem.", "server")
            return

        # Exibe a própria mensagem localmente
        if not message.startswith("/"):
            self._append_message(f"[Você]: {message}", "self")

        self.input_field.delete(0, tk.END)

    def _append_message(self, message: str, tag: str = "other"):
        """Adiciona uma mensagem na área de chat."""
        self.chat_area.config(state="normal")
        self.chat_area.insert(tk.END, message + "\n", tag)
        self.chat_area.config(state="disabled")
        self.chat_area.see(tk.END)

    # ─── Salas ────────────────────────────────────────────────────────────────

    def _change_room(self, room: str):
        """Troca de sala pelo botão do cabeçalho."""
        if room == self.current_room:
            return
        try:
            self.client.sendall((encrypt(f"/sala {room}") + "\n").encode("utf-8"))
        except:
            pass

    def _highlight_room_button(self):
        """Destaca o botão da sala atual."""
        for room, btn in self.room_buttons.items():
            if room == self.current_room:
                btn.config(bg="#4ade80", fg="#0f3460", font=("Segoe UI", 9, "bold"))
            else:
                btn.config(bg="#0f3460", fg="white", font=("Segoe UI", 9))

# ─── Inicialização ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    app = ChatApp(root)
    root.mainloop()
