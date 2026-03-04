# 💬 Chat Cliente-Servidor com Sockets e Criptografia AES

Aplicação de chat em tempo real desenvolvida em **Python**, utilizando **sockets TCP nativos** e **criptografia AES-256** para proteger as mensagens trafegadas na rede.

---

## 🛠️ Linguagem e Tecnologias

- **Python 3.8+**
- `socket` — comunicação via rede (biblioteca nativa do Python)
- `threading` — múltiplos clientes simultâneos (biblioteca nativa do Python)
- `pycryptodome` — criptografia AES

---

## 📁 Estrutura do Projeto

```
chat-socket/
├── server.py     # Servidor TCP que aceita múltiplos clientes
├── client.py     # Cliente que envia e recebe mensagens
├── crypto.py     # Módulo de criptografia e descriptografia AES
├── README.md     # Documentação do projeto
└── .gitignore    # Arquivos ignorados pelo Git
```

---

## 🔐 Criptografia Utilizada

### Algoritmo: AES-256 no modo CBC

O **AES (Advanced Encryption Standard)** é um algoritmo de **criptografia simétrica**, ou seja, a mesma chave é usada para criptografar e descriptografar as mensagens.

### Como funciona no projeto:

1. Antes de enviar qualquer mensagem, o cliente (ou servidor) chama a função `encrypt()`
2. A função gera um **IV (Vetor de Inicialização)** aleatório de 16 bytes a cada mensagem
3. A mensagem é criptografada com AES-256 no modo CBC usando a `SECRET_KEY` + IV
4. O resultado é convertido para **Base64** para trafegar como texto
5. Ao receber, a função `decrypt()` extrai o IV, descriptografa e retorna o texto original

### Chave utilizada:

```python
SECRET_KEY = b"MinhaChaveSecreta32BytesAqui1234"  # 32 bytes = AES-256
```

A chave está definida em `crypto.py` e é compartilhada entre cliente e servidor. Em um sistema real, ela seria trocada de forma segura usando criptografia assimétrica (RSA), mas para fins didáticos ela fica fixa no código.

### Por que AES-CBC?

- **AES** é o padrão de criptografia mais utilizado no mundo
- **Modo CBC** garante que mensagens iguais gerem resultados diferentes (por causa do IV aleatório)
- **256 bits** oferece o mais alto nível de segurança do AES

---

## ▶️ Como Executar

### 1. Pré-requisitos

Certifique-se de ter o **Python 3.8+** instalado:

```bash
python --version
```

### 2. Instalar dependências

```bash
pip install pycryptodome
```

### 3. Iniciar o Servidor

Abra um terminal e execute:

```bash
python server.py
```

Você verá:
```
✅ Servidor de chat rodando em 0.0.0.0:5000
Aguardando conexões...
```

### 4. Iniciar o(s) Cliente(s)

Abra um **novo terminal** para cada cliente e execute:

```bash
python client.py
```

Você verá:
```
✅ Conectado ao servidor 127.0.0.1:5000
Digite seu apelido: 
```

> Repita esse passo em quantos terminais quiser para simular múltiplos usuários conversando.

---

## 🏗️ Arquitetura da Solução

```
[Cliente A]                    [Servidor]                   [Cliente B]
    |                              |                              |
    |-- conecta via TCP ---------->|                              |
    |-- envia apelido (cifrado) -->|                              |
    |<- boas-vindas (cifrado) -----|                              |
    |                              |<-- conecta via TCP ----------|
    |                              |<-- envia apelido (cifrado) --|
    |<- "B entrou no chat" --------|                              |
    |                              |                              |
    |-- "Olá!" (cifrado) --------->|                              |
    |                              |-- "A: Olá!" (cifrado) ------>|
    |                              |                              |
```

### Fluxo de uma mensagem:

```
Usuário digita "Olá!"
        ↓
encrypt("Olá!") → texto cifrado em Base64
        ↓
socket.sendall() → enviado pelo TCP
        ↓
Servidor recebe o texto cifrado
        ↓
decrypt() → "Olá!" (texto original)
        ↓
Exibe no console do servidor
        ↓
encrypt("A: Olá!") → cifra novamente
        ↓
Retransmite para todos os outros clientes (broadcast)
        ↓
Cada cliente recebe e descriptografa
        ↓
Exibe "A: Olá!" na tela
```

---

## 🧪 Testando a Criptografia

Para verificar que as mensagens realmente trafegam criptografadas, você pode rodar o seguinte teste no terminal:

```python
python -c "
from crypto import encrypt, decrypt
msg = 'Olá, mundo!'
cifrada = encrypt(msg)
print('Cifrada:', cifrada)
print('Original:', decrypt(cifrada))
"
```

---

## ⚙️ Configurações

Para conectar clientes em máquinas diferentes na mesma rede, edite o `client.py`:

```python
HOST = "192.168.x.x"  # Substitua pelo IP da máquina do servidor
```
