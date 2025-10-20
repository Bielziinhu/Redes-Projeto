# servidor.py / Arquivo que será alocado na máquina virtual - tentar iniciar em uma VM depois
import socket
import json
import os
import threading # multiplas conexões
from datetime import datetime # Para log de transações

PASTA_DADOS = "dados"
PASTA_LOGS = "logs"
ARQUIVO_CONTAS = os.path.join(PASTA_DADOS, "contas.json")
ARQUIVO_LOG = os.path.join(PASTA_LOGS, "transacoes.log")

# # Estruturas
contas = {}
cpf_para_conta = {}
conexoes_ativas = {}

# Aloca as threads no sistema
contas_lock = threading.Lock()
conexoes_lock = threading.Lock()

# Funções para carregar e salvar contas
def carregar_contas():
    global contas, cpf_para_conta
    with contas_lock:
        if os.path.exists(ARQUIVO_CONTAS):
            try:
                with open(ARQUIVO_CONTAS, 'r') as f:
                    dados = json.load(f)
                    contas = dados.get("contas", {})
                    cpf_para_conta = dados.get("cpf_salvos", {})
                print(f"[INFO] Contas carregadas de {ARQUIVO_CONTAS}")
            except json.JSONDecodeError:
                print(f"[AVISO] Arquivo {ARQUIVO_CONTAS} corrompido ou vazio.")
                contas, cpf_para_conta = {}, {}
        else:
            print("[INFO] Arquivo de contas não encontrado. Começando do zero.")
            contas, cpf_para_conta = {}, {}

# Função para salvar contas
def salvar_contas():
    try:
        with open(ARQUIVO_CONTAS, 'w') as f:
            dados = {"contas": contas, "cpf_salvos": cpf_para_conta}
            json.dump(dados, f, indent=4)
    except Exception as e:
        print(f"[ERRO FATAL] Falha ao salvar contas: {e}")

#Função para logar transações
def log_transacao(mensagem):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(ARQUIVO_LOG, 'a') as f:
            f.write(f"[{timestamp}] {mensagem}\n")
    except Exception as e:
        print(f"[ERRO] Falha ao escrever no log: {e}")

# Função para enviar notificações a clientes conectados (necessário recarregar a página ativa)
def enviar_notificacao(num_conta_destino, mensagem):
    with conexoes_lock:
        if num_conta_destino in conexoes_ativas:
            conn_destino = conexoes_ativas[num_conta_destino]
            try:
                #Envia a log que a notificação foi enviada
                conn_destino.sendall(mensagem.encode('utf-8'))
                print(f"[NOTIFICACAO] Alerta enviado para conta {num_conta_destino}.")
            except Exception as e:
                print(f"[ERRO] Falha ao enviar notificação para {num_conta_destino}: {e}")

#Função para processar comandos dos clientes
def processar_comando(comando, num_conta_logada):
    partes = comando.strip().split('|')
    operacao = partes[0].upper()
    estado_retorno = ("NO_CHANGE", None, None)
    notificacao = None

#Toda lógica de operações e leitura dos comandos inseridos
    with contas_lock:
        if operacao == "CRIAR":
            try:
                nome, cpf, senha = partes[1], partes[2], partes[3]
                if cpf in cpf_para_conta:
                    print(f"[FALHA-CRIAR] CPF {cpf} já cadastrado.")
                    return ("[FALHA] CPF já cadastrado.", estado_retorno, notificacao)
                
                num_conta = str(len(contas) + 100)
                contas[num_conta] = {"nome": nome, "cpf": cpf, "senha": senha, "saldo": 0.0}
                cpf_para_conta[cpf] = num_conta
                salvar_contas()
                
                print(f"[CONTAS] Conta {num_conta} criada para {nome} (CPF: {cpf[:3]}.***.{cpf[-3:]})")
                log_transacao(f"CONTA_CRIADA: Conta {num_conta}, Nome: {nome}, CPF: {cpf[:3]}.***.{cpf[-3:]}")
                return (f"[CONTAS] Conta {num_conta} criada para {nome}.", estado_retorno, notificacao)
            except IndexError:
                return ("[CONTAS] Formato: CRIAR|Nome Completo|CPF|Senha", estado_retorno, notificacao)

# # LEMBRETE - Fazer lógica para não conseguir logar na conta que já está em outra sessão # #
        elif operacao == "LOGIN":
            try:
                cpf, senha = partes[1], partes[2]
                if cpf not in cpf_para_conta:
                    print(f"[LOGIN] CPF não encontrado: {cpf[:3]}.***")
                    return ("[LOGIN] CPF ou senha incorretos.", estado_retorno, notificacao)
                
                num_conta = cpf_para_conta[cpf]
                if contas[num_conta]["senha"] == senha:
                    nome = contas[num_conta]["nome"]
                    estado_retorno = ("LOGIN", num_conta, nome)
                    print(f"[LOGIN] Usuário {nome} (Conta: {num_conta}) logou.")
                    return (f"[LOGIN]|{nome}|{num_conta}", estado_retorno, notificacao)
                else:
                    print(f"[LOGIN] Senha incorreta para CPF {cpf[:3]}.***")
                    return ("[LOGIN] CPF ou senha incorretos.", estado_retorno, notificacao)
            except IndexError:
                return ("[LOGIN] Formato: LOGIN|CPF|Senha", estado_retorno, notificacao)

        if num_conta_logada is None:
            return ("[LOGIN] Você precisa estar logado para esta operação.", estado_retorno, notificacao)

        try:
            if operacao == "SALDO":
                saldo = contas[num_conta_logada]["saldo"]
                return (f"[SALDO] Saldo: R$ {saldo:.2f}", estado_retorno, notificacao)
            elif operacao == "DEPOSITAR":
                valor = float(partes[1])
                if valor <= 0:
                    return ("[DEPOSITO] O valor deve ser positivo.", estado_retorno, notificacao)
                contas[num_conta_logada]["saldo"] += valor
                saldo_atual = contas[num_conta_logada]["saldo"]
                salvar_contas()
                log_transacao(f"DEPOSITO: Sucesso - Conta {num_conta_logada}, Valor: {valor:.2f}, Saldo Novo: {saldo_atual:.2f}")
                print(f"[DEPOSITO] Conta {num_conta_logada} depositou R$ {valor:.2f}.")
                return (f"[DEPOSITO] Depósito de R$ {valor:.2f} realizado. Novo saldo: R$ {saldo_atual:.2f}", estado_retorno, notificacao)
            
            elif operacao == "SACAR":
                valor, senha = float(partes[1]), partes[2]
                if contas[num_conta_logada]["senha"] != senha:
                    return ("[SACAR] Senha incorreta.", estado_retorno, notificacao)
                if valor <= 0:
                    return ("[SACAR] O valor deve ser positivo.", estado_retorno, notificacao)
                if contas[num_conta_logada]["saldo"] < valor:
                    print(f"[SACAR] Saldo insuficiente para C:{num_conta_logada} (Tenta: {valor:.2f}, Tem: {contas[num_conta_logada]['saldo']:.2f})")
                    return ("[SACAR] Saldo insuficiente.", estado_retorno, notificacao)
                contas[num_conta_logada]["saldo"] -= valor
                saldo_atual = contas[num_conta_logada]["saldo"]
                salvar_contas()
                log_transacao(f"SAQUE: Sucesso - Conta {num_conta_logada}, Valor: {valor:.2f}, Saldo Novo: {saldo_atual:.2f}")
                print(f"[SACAR] Conta {num_conta_logada} sacou R$ {valor:.2f}.")
                return (f"[SUCESSO] Saque de R$ {valor:.2f} realizado. Novo saldo: R$ {saldo_atual:.2f}", estado_retorno, notificacao)
            
            elif operacao == "TRANSFERIR":
                c_destino, valor, senha = partes[1], float(partes[2]), partes[3]
                
                if c_destino not in contas:
                    return ("[TRANSFERÊNCIA] Conta de destino não existe.", estado_retorno, notificacao)
                if c_destino == num_conta_logada:
                    return ("[TRANSFERÊNCIA] Não pode transferir para si mesmo.", estado_retorno, notificacao)
                if contas[num_conta_logada]["senha"] != senha:
                    return ("[TRANSFERÊNCIA] Senha incorreta.", estado_retorno, notificacao)
                if valor <= 0:
                    return ("[TRANSFERÊNCIA] O valor deve ser positivo.", estado_retorno, notificacao)
                if contas[num_conta_logada]["saldo"] < valor:
                    print(f"[TRANSFERÊNCIA] Saldo insuficiente para C:{num_conta_logada} (Tenta: {valor:.2f}, Tem: {contas[num_conta_logada]['saldo']:.2f})")
                    return ("[TRANSFERÊNCIA] Saldo insuficiente.", estado_retorno, notificacao)
                
                contas[num_conta_logada]["saldo"] -= valor
                contas[c_destino]["saldo"] += valor
                nome_origem = contas[num_conta_logada]["nome"]
                nome_destino = contas[c_destino]["nome"]
                salvar_contas()
                
                print(f"[TRANSFERÊNCIA] {nome_origem} (C:{num_conta_logada}) -> {nome_destino} (C:{c_destino}), Valor: R$ {valor:.2f}")
                log_transacao(f"TRANSFERENCIA: Sucesso - R$ {valor:.2f} de C:{num_conta_logada} ({nome_origem}) para C:{c_destino} ({nome_destino})")

                mensagem_notificacao = f"[ALERTA] Você recebeu uma transferência de {nome_origem} (Conta: {num_conta_logada}) no valor de R$ {valor:.2f}."
                notificacao = (c_destino, mensagem_notificacao)
                
                return (f"[TRANSFERÊNCIA] Transferência de R$ {valor:.2f} para {nome_destino} (Conta: {c_destino}) realizada.", estado_retorno, notificacao)
            
            elif operacao == "LOGOUT":
                estado_retorno = ("LOGOUT", None, None)
                print(f"[DESLOGAR] Usuário {contas[num_conta_logada]['nome']} (Conta: {num_conta_logada}) deslogou.")
                return ("[DESLOGAR] Você saiu da sua conta.", estado_retorno, notificacao)

            else:
                return ("[FALHA] Comando desconhecido.", estado_retorno, notificacao)
        
        except (IndexError, ValueError):
            return ("[FALHA] Comando mal formatado ou valor inválido.", estado_retorno, notificacao)
        except Exception as e:
            print(f"[ERRO] {e}")
            return (f"[FALHA] Erro inesperado no servidor: {e}", estado_retorno, notificacao)

#Função para lidar com cada cliente conectado
def handle_client(conn, addr):
    print(f"[NOVA CONEXAO] {addr} conectado.")
    num_conta_logada = None
    nome_logado = None
    
    try:
        while True:
            data = conn.recv(1024).decode('utf-8')
            if not data:
                print(f"[CONEXAO PERDIDA] {addr} desconectou.")
                break
            
            print(f"[{addr} | C:{num_conta_logada or 'N/A'}] Comando: {data}")
            
            resposta, novo_estado, notificacao = processar_comando(data, num_conta_logada)
            
            if novo_estado[0] == "LOGIN":
                num_conta_logada, nome_logado = novo_estado[1], novo_estado[2]
                with conexoes_lock:
                    conexoes_ativas[num_conta_logada] = conn
            elif novo_estado[0] == "LOGOUT":
                with conexoes_lock:
                    if num_conta_logada in conexoes_ativas:
                        del conexoes_ativas[num_conta_logada]
                num_conta_logada, nome_logado = None, None
            
            conn.sendall(resposta.encode('utf-8'))
            
            if notificacao:
                enviar_notificacao(notificacao[0], notificacao[1])

    except (ConnectionResetError, BrokenPipeError):
        print(f"[CONEXAO FECHADA] {addr} desconectou.")
    finally:
        if num_conta_logada:
            with conexoes_lock:
                if num_conta_logada in conexoes_ativas:
                    del conexoes_ativas[num_conta_logada]
                    print(f"[LIMPEZA] Conexão ativa de {nome_logado} (C:{num_conta_logada}) removida.")
        conn.close()

#Principal, onde é iniciado o servidor e determinado o IP e porta, caso queira alocar no ip que a máquina estar, use: 0.0.0.0 como IP.
def main():
    os.makedirs(PASTA_DADOS, exist_ok=True)
    os.makedirs(PASTA_LOGS, exist_ok=True)
    carregar_contas()

#
    host = input("Digite o endereco IP do servidor: ")
    port = int(input("Digite a porta do servidor: "))
# #
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.bind((host, port))
        server_socket.listen()
        print(f"[CONEXÃO] Servidor IFBank ativo em {host}:{port}")
    except Exception as e:
        print(f"[FALHA] Falha ao iniciar o servidor: {e}")
        return

    try:
        while True:
            conn, addr = server_socket.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.start()
    except KeyboardInterrupt:
        print("\n[ENCERRANDO] Servidor encerrando atividades...")
    finally:
        print("[SALVANDO] Salvando contas...")
        with contas_lock:
            salvar_contas()
        server_socket.close()
        print("[DESLIGADO] Servidor desligado.")

if __name__ == "__main__":
    main()