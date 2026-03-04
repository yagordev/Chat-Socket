"""
crypto.py — Módulo de criptografia AES (modo CBC)

A chave compartilhada (SECRET_KEY) deve ser conhecida tanto pelo
cliente quanto pelo servidor. Em produção ela seria trocada de forma
segura; aqui ela fica fixa para fins didáticos.
"""

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64
import os

# ─── Chave secreta compartilhada ─────────────────────────────────────────────
# Deve ter exatamente 16, 24 ou 32 bytes (128, 192 ou 256 bits)
SECRET_KEY = b"MinhaChaveSecreta32BytesAqui1234"  # 32 bytes = AES-256

def encrypt(message: str) -> str:
    """
    Recebe uma string, criptografa com AES-CBC e retorna
    a mensagem em Base64 (IV + dados cifrados).
    """
    iv = os.urandom(16)                          # Vetor de inicialização aleatório
    cipher = AES.new(SECRET_KEY, AES.MODE_CBC, iv)
    encrypted = cipher.encrypt(pad(message.encode("utf-8"), AES.block_size))
    # Concatena IV + dados e converte para Base64 para trafegar como texto
    return base64.b64encode(iv + encrypted).decode("utf-8")

def decrypt(encoded: str) -> str:
    """
    Recebe uma string em Base64, descriptografa com AES-CBC
    e retorna a mensagem original.
    """
    raw = base64.b64decode(encoded)
    iv = raw[:16]                                # Extrai o IV dos primeiros 16 bytes
    cipher = AES.new(SECRET_KEY, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(raw[16:]), AES.block_size).decode("utf-8")
