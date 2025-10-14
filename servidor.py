# servidor.py
import socket
import json
import os
import threading
from datetime import datetime

# --- Configuração Inicial ---
PASTA_DADOS = "dados"
PASTA_LOGS = "logs"
ARQUIVO_CONTAS = os.path.join(PASTA_DADOS, "contas.json")
ARQUIVO_LOG = os.path.join(PASTA_LOGS, "transacoes.log")

# Formato: {"num_conta": 
#          {"saldo": float,    
#          "senha": str}}

contas = {}

contas_lock = threading.Lock()

def carregar_contas():
    global contas
    with contas_lock:
        if os.path.exists(ARQUIVO_CONTAS):
            try:
                with open(ARQUIVO_CONTAS, 'r') as f:
                    contas = json.load(f)
                    print(f"Contas carregadas de {ARQUIVO_CONTAS}")
            except json.JSONDecodeError:
                print(f"Aviso: O arquivo {ARQUIVO_CONTAS} esta vazio ou corrompido.")
                contas = {}

def salvar_contas():
    with open(ARQUIVO_CONTAS, 'w') as f:
        json.dump(contas, f, indent=4)

def log_transacao(mensagem):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(ARQUIVO_LOG, 'a') as f:
        f.write(f"[{timestamp}] {mensagem}\n")

def processar_comando(comando):
    partes = comando.strip().split()
    operacao = partes[0].upper()

    try:
        with contas_lock:
            if operacao == "CRIAR":
                if len(partes) != 2:
                    return "[FALHA] Uso: CRIAR <senha>"
                senha = partes[1]
                num_conta = str(len(contas) + 100)
                contas[num_conta] = {"saldo": 0.0, "senha": senha}
                log_transacao(f"CRIAR_CONTA: Sucesso - Conta {num_conta} criada.")
                salvar_contas()
                return f"[SUCESSO] Conta {num_conta} criada com sucesso."

            elif operacao == "SALDO":
                if len(partes) != 2:
                    return "[FALHA] Uso: SALDO <numero_da_conta>"
                num_conta = partes[1]
                if num_conta in contas:
                    saldo = contas[num_conta]["saldo"]
                    return f"[SUCESSO] Saldo da conta {num_conta}: R$ {saldo:.2f}"
                else:
                    return f"[FALHA] Conta {num_conta} nao encontrada."

            elif operacao == "DEPOSITAR":
                if len(partes) != 3:
                    return "[FALHA] Uso: DEPOSITAR <numero_da_conta> <valor>"
                num_conta, valor_str = partes[1], partes[2]
                valor = float(valor_str)
                if num_conta in contas:
                    if valor > 0:
                        contas[num_conta]["saldo"] += valor
                        log_transacao(f"DEPOSITO: Sucesso - Conta {num_conta}, Valor: {valor:.2f}")
                        salvar_contas()
                        return f"[SUCESSO] Deposito de R$ {valor:.2f} realizado na conta {num_conta}."
                    else:
                        return "[FALHA] O valor do deposito deve ser positivo."
                else:
                    return f"[FALHA] Conta {num_conta} nao encontrada."

            elif operacao == "SACAR":
                if len(partes) != 4:
                     return "[FALHA] Uso: SACAR <numero_da_conta> <valor> <senha>"
                num_conta, valor_str, senha = partes[1], partes[2], partes[3]
                valor = float(valor_str)
                if num_conta in contas:
                    if contas[num_conta]["senha"] != senha:
                        return "[FALHA] Senha incorreta."
                    if valor <= 0:
                        return "[FALHA] O valor do saque deve ser positivo."
                    if contas[num_conta]["saldo"] >= valor:
                        contas[num_conta]["saldo"] -= valor
                        log_transacao(f"SAQUE: Sucesso - Conta {num_conta}, Valor: {valor:.2f}")
                        salvar_contas()
                        return f"[SUCESSO] Saque de R$ {valor:.2f} realizado."
                    else:
                        log_transacao(f"SAQUE: Falha - Saldo insuficiente na conta {num_conta}.")
                        return "[FALHA] Saldo insuficiente."
                else:
                    return f"[FALHA] Conta {num_conta} nao encontrada."

            elif operacao == "TRANSFERIR":
                if len(partes) != 5:
                    return "[FALHA] Uso: TRANSFERIR <origem> <destino> <valor> <senha>"
                c_origem, c_destino, valor_str, senha = partes[1], partes[2], partes[3], partes[4]
                valor = float(valor_str)

                if c_origem not in contas: return f"[FALHA] Conta de origem {c_origem} nao existe."
                if c_destino not in contas: return f"[FALHA] Conta de destino {c_destino} nao existe."
                if c_origem == c_destino: return "[FALHA] Conta de origem e destino nao podem ser a mesma."
                if contas[c_origem]["senha"] != senha: return "[FALHA] Senha da conta de origem incorreta."
                if valor <= 0: return "[FALHA] O valor da transferencia deve ser positivo."
                if contas[c_origem]["saldo"] < valor: return "[FALHA] Saldo insuficiente na conta de origem."

                contas[c_origem]["saldo"] -= valor
                contas[c_destino]["saldo"] += valor
                log_transacao(f"TRANSFERENCIA: Sucesso - {valor:.2f} da conta {c_origem} para {c_destino}.")
                salvar_contas()
                return f"[SUCESSO] Transferencia de R$ {valor:.2f} para a conta {c_destino} realizada."

            else:
                return "[FALHA] Comando desconhecido."

    except (IndexError, ValueError):
        return "[FALHA] Comando invalido ou mal formatado. Verifique os argumentos."
    except Exception as e:
        return f"[FALHA] Erro inesperado no servidor: {e}"

# --- Gerenciador de Clientes ---
def handle_client(conn, addr):
    print(f"[NOVA CONEXAO] {addr} conectado.")
    try:
        while True:
            data = conn.recv(1024).decode('utf-8')
            if not data:
                break
            print(f"[{addr}] Comando recebido: {data}")
            resposta = processar_comando(data)
            conn.sendall(resposta.encode('utf-8'))
    except ConnectionResetError:
        print(f"[{addr}] Conexao perdida abruptamente.")
    finally:
        conn.close()
        print(f"[CONEXAO FECHADA] {addr} desconectado.")

def main():
    os.makedirs(PASTA_DADOS, exist_ok=True)
    os.makedirs(PASTA_LOGS, exist_ok=True)
    carregar_contas()

    host = input("Digite o endereco IP do servidor: ")
    port = int(input("Digite a porta do servidor: "))

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen()

    print(f"[OUVINDO] Servidor ouvindo em {host}:{port}")

    try:
        while True:
            conn, addr = server_socket.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.start()
            print(f"[CONEXOES ATIVAS] {threading.active_count() - 1}")
    except KeyboardInterrupt:
        print("\n[ENCERRANDO] Servidor sendo desligado...")
    finally:
        print("[SALVANDO] Salvando estado final das contas...")
        salvar_contas()
        server_socket.close()
        print("[DESLIGADO] Servidor desligado.")

if __name__ == "__main__":
    main()