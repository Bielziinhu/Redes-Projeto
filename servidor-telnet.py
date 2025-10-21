# servidor.py / Arquivo do servidor, utilizando telnet para comunicação com o cliente
import socket
import json
import os
import threading
from datetime import datetime

# Toda criação de pastas e arquivos deve ser feita na inicialização do servidor
PASTA_DADOS = "dados"
PASTA_LOGS = "logs"
ARQUIVO_CONTAS = os.path.join(PASTA_DADOS, "contas.json")
ARQUIVO_LOG = os.path.join(PASTA_LOGS, "transacoes.log")

#Estrutura base
contas = {}
cpf_para_conta = {}
conexoes_ativas = {}

contas_lock = threading.Lock()
conexoes_lock = threading.Lock()

#Faz a criação e carregamento dos dados das contas, caso as pastas não existam, vai ser criada
def carregar_contas():
    global contas, cpf_para_conta
    with contas_lock:
        if os.path.exists(ARQUIVO_CONTAS):
            try:
                with open(ARQUIVO_CONTAS, 'r') as f:
                    dados = json.load(f)
                    contas = dados.get("contas", {})
                    cpf_para_conta = dados.get("cpf_salvos", {}) 
                print(f"[IFBANK] Contas carregadas de {ARQUIVO_CONTAS}")
            except json.JSONDecodeError:
                print(f"[IFBANK] Arquivo {ARQUIVO_CONTAS} corrompido ou vazio.")
                contas, cpf_para_conta = {}, {}
        else:
            print("[IFBANK] Arquivo de contas não encontrado. Começando do zero.")
            contas, cpf_para_conta = {}, {}

#Salva as contas no json, função é chamada várias vezes, para permitir uma boa persistência de dados
def salvar_contas():
    try:
        with open(ARQUIVO_CONTAS, 'w') as f:
            dados = {"contas": contas, "cpf_salvos": cpf_para_conta}
            json.dump(dados, f, indent=4)
    except Exception as e:
        print(f"[IFBANK] Falha ao salvar contas: {e}")

def log_transacao(mensagem):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(ARQUIVO_LOG, 'a') as f:
            f.write(f"[{timestamp}] {mensagem}\n")
    except Exception as e:
        print(f"[LOGS] Falha ao escrever no log: {e}")

def enviar_notificacao(num_conta_destino, mensagem):
    with conexoes_lock:
        if num_conta_destino in conexoes_ativas:
            conn_destino = conexoes_ativas[num_conta_destino]
            try:
                conn_destino.sendall(f"\r\n{mensagem}\r\n".encode('utf-8'))
                print(f"[LOGS] Alerta enviado para conta {num_conta_destino}.")
            except Exception as e:
                print(f"[LOGS] Falha ao enviar notificação para {num_conta_destino}: {e}")

def processar_comando(comando, num_conta_logada):
    partes = comando.strip().split('|')
    operacao = partes[0].upper()
    estado_retorno = ("NO_CHANGE", None, None)
    notificacao = None

    with contas_lock:
        if operacao == "CRIAR":
            try:
                if len(partes) != 4:
                    return ("[IFBANK] Formato incorreto. Use: CRIAR|Nome Completo|CPF|Senha", estado_retorno, notificacao)
                
                nome, cpf, senha = partes[1], partes[2], partes[3]

                #Validações - Adicionar mais até o final do projeto
                #Coloquei apenas 3 números para facilitar os testes, mas o numero original é 11
                if not cpf.isdigit() or len(cpf) != 3:
                    return ("[IFBANK] CPF inválido. Deve conter 11 números.", estado_retorno, notificacao)
                if not nome or '|' in nome:
                    return ("[IFBANK] Nome inválido. Não pode estar vazio ou conter '|'.", estado_retorno, notificacao)
                if not senha or '|' in senha:
                     return ("[IFBANK] Senha inválida. Não pode estar vazia ou conter '|'.", estado_retorno, notificacao)

                if cpf in cpf_para_conta:
                    #Verificar remoção do dado de CPF na mensagem de retorno
                    print(f"[IFBANK] CPF {cpf} já cadastrado.")
                    return ("[IFBANK] CPF já cadastrado.", estado_retorno, notificacao)
                
                num_conta = str(len(contas) + 100)
                contas[num_conta] = {"nome": nome, "cpf": cpf, "senha": senha, "saldo": 0.0}
                cpf_para_conta[cpf] = num_conta
                salvar_contas()
                
                print(f"[IFBANK] Conta {num_conta} criada para {nome} (CPF: {cpf[:3]}.***.{cpf[-3:]})")
                log_transacao(f"CONTA_CRIADA: Conta {num_conta}, Nome: {nome}, CPF: {cpf[:3]}.***.{cpf[-3:]}")
                return (f"[IFBANK] Conta {num_conta} criada para {nome}.", estado_retorno, notificacao)
            
            except IndexError: #Caso falte algum campo no comando
                return ("[IFBANK] Formato: CRIAR|Nome Completo|CPF|Senha", estado_retorno, notificacao)

        elif operacao == "LOGIN":
            try:
                if len(partes) != 3:
                     return ("[IFBANK] Formato: LOGIN|CPF|Senha", estado_retorno, notificacao)
                
                cpf, senha = partes[1], partes[2]

                #Faz uma verificação para passar apenas numeros
                if not cpf.isdigit():
                    return ("[IFBANK] Formato de CPF inválido. Use apenas números.", estado_retorno, notificacao)

                if cpf not in cpf_para_conta:
                    print(f"[IFBANK] CPF não encontrado: {cpf[:3]}.***")
                    return ("[IFBANK] CPF ou senha incorretos.", estado_retorno, notificacao)
                
                num_conta = cpf_para_conta[cpf]

                #Verifica se a conta ja foi logada, para evitar duplicar a conexão
                with conexoes_lock:
                    if num_conta in conexoes_ativas:
                        print(f"[IFBANK] Conta {num_conta} já está logada.")
                        return ("[IFBANK] Essa conta já foi acessada em outra sessão.", estado_retorno, notificacao)

                if contas[num_conta]["senha"] == senha:
                    nome = contas[num_conta]["nome"]
                    estado_retorno = ("LOGIN", num_conta, nome)
                    print(f"[IFBANK] Usuário {nome} (Conta: {num_conta}) logou.")
                    return (f"[IFBANK]|{nome}|{num_conta}", estado_retorno, notificacao)
                else:
                    #Faz uma pequena modificação para mostrar que o CPF está sendo censurado
                    print(f"[IFBANK] Senha incorreta para CPF {cpf[:3]}.***")
                    return ("[IFBANK] CPF ou senha incorretos.", estado_retorno, notificacao)
            except IndexError:
                return ("[IFBANK] Formato: LOGIN|CPF|Senha", estado_retorno, notificacao)

        if num_conta_logada is None:
            return ("[IFBANK] Você precisa estar logado para esta operação.", estado_retorno, notificacao)

        try:
            if operacao == "SALDO":
                saldo = contas[num_conta_logada]["saldo"]
                return (f"[IFBANK] Saldo: R$ {saldo:.2f}", estado_retorno, notificacao)
            
            elif operacao == "DEPOSITAR":
                #Pequena verificação para evitar erros de índice
                try:
                    valor = float(partes[1])
                except (ValueError, IndexError):
                    return ("[IFBANK] Valor inválido. Formato: DEPOSITAR|Valor", estado_retorno, notificacao)
                
                if valor <= 0:
                    return ("[IFBANK] O valor deve ser positivo.", estado_retorno, notificacao)
                
                contas[num_conta_logada]["saldo"] += valor
                saldo_atual = contas[num_conta_logada]["saldo"]
                salvar_contas()
                log_transacao(f"DEPOSITO: Sucesso - Conta {num_conta_logada}, Valor: {valor:.2f}, Saldo Novo: {saldo_atual:.2f}")
                print(f"[IFBANK] Conta {num_conta_logada} depositou R$ {valor:.2f}.")
                return (f"[IFBANK] Depósito de R$ {valor:.2f} realizado. Novo saldo: R$ {saldo_atual:.2f}", estado_retorno, notificacao)
            
            elif operacao == "SACAR":
                #Validações na senha e valor
                try:
                    valor_str, senha = partes[1], partes[2]
                    valor = float(valor_str)
                except ValueError:
                    return ("[IFBANK] Valor inválido. Use apenas números para o valor.", estado_retorno, notificacao)
                except IndexError:
                    return ("[IFBANK] Formato incorreto. Use: SACAR|Valor|Senha", estado_retorno, notificacao)

                if contas[num_conta_logada]["senha"] != senha:
                    return ("[IFBANK] Senha incorreta.", estado_retorno, notificacao)
                if valor <= 0:
                    return ("[IFBANK] O valor deve ser positivo.", estado_retorno, notificacao)
                if contas[num_conta_logada]["saldo"] < valor:
                    print(f"[IFBANK] Saldo insuficiente para C:{num_conta_logada} (Tenta: {valor:.2f}, Tem: {contas[num_conta_logada]['saldo']:.2f})")
                    return ("[IFBANK] Saldo insuficiente.", estado_retorno, notificacao)
                
                contas[num_conta_logada]["saldo"] -= valor
                saldo_atual = contas[num_conta_logada]["saldo"]
                salvar_contas()
                log_transacao(f"SAQUE: Sucesso - Conta {num_conta_logada}, Valor: {valor:.2f}, Saldo Novo: {saldo_atual:.2f}")
                print(f"[IFBANK] Conta {num_conta_logada} sacou R$ {valor:.2f}.")
                return (f"[SUCIFBANKESSO] Saque de R$ {valor:.2f} realizado. Novo saldo: R$ {saldo_atual:.2f}", estado_retorno, notificacao)
            
            elif operacao == "TRANSFERIR":
                #Validações da senha também são feitas aqui, junto com numeros validos
                try:
                    c_destino, valor_str, senha = partes[1], partes[2], partes[3]
                    valor = float(valor_str)
                except ValueError:
                    return ("[IFBANK] Valor inválido. Use apenas números para o valor.", estado_retorno, notificacao)
                except IndexError:
                    return ("[IFBANK] Formato incorreto. Use: TRANSFERIR|ContaDestino|Valor|Senha", estado_retorno, notificacao)
                
                if not c_destino.isdigit():
                     return ("[IFBANK] Número da conta de destino deve ser numérico.", estado_retorno, notificacao)
                
                if c_destino not in contas:
                    return ("[IFBANK] Conta de destino não existe.", estado_retorno, notificacao)
                if c_destino == num_conta_logada:
                    return ("[IFBANK] Não pode transferir para si mesmo.", estado_retorno, notificacao)
                if contas[num_conta_logada]["senha"] != senha:
                    return ("[IFBANK] Senha incorreta.", estado_retorno, notificacao)
                if valor <= 0:
                    return ("[IFBANK] O valor deve ser positivo.", estado_retorno, notificacao)
                if contas[num_conta_logada]["saldo"] < valor:
                    print(f"[IFBANK] Saldo insuficiente para C:{num_conta_logada} (Tenta: {valor:.2f}, Tem: {contas[num_conta_logada]['saldo']:.2f})")
                    return ("[IFBANK] Saldo insuficiente.", estado_retorno, notificacao)
                
                contas[num_conta_logada]["saldo"] -= valor
                contas[c_destino]["saldo"] += valor
                nome_origem = contas[num_conta_logada]["nome"]
                nome_destino = contas[c_destino]["nome"]

                #Salvar alterações após a transferência no arquivo
                salvar_contas()
                ##
                
                print(f"[IFBANK] {nome_origem} (C:{num_conta_logada}) -> {nome_destino} (C:{c_destino}), Valor: R$ {valor:.2f}")
                log_transacao(f"TRANSFERENCIA: Sucesso - R$ {valor:.2f} de C:{num_conta_logada} ({nome_origem}) para C:{c_destino} ({nome_destino})")

                #Alerta que será enviado na tela do usuario
                mensagem_notificacao = f"[IFBANK] Você recebeu uma transferência de {nome_origem} (Conta: {num_conta_logada}) no valor de R$ {valor:.2f}."
                notificacao = (c_destino, mensagem_notificacao)
                
                return (f"[IFBANK] Transferência de R$ {valor:.2f} para {nome_destino} (Conta: {c_destino}) realizada.", estado_retorno, notificacao)
            
            elif operacao == "LOGOUT":
                estado_retorno = ("LOGOUT", None, None)
                print(f"[IFBANK] Usuário {contas[num_conta_logada]['nome']} (Conta: {num_conta_logada}) deslogou.")
                return ("[IFBANK] Você saiu da sua conta.", estado_retorno, notificacao)

            else:
                return ("[IFBANK] Comando desconhecido.", estado_retorno, notificacao)
        
        except Exception as e:
            print(f"[ERRO] {e}")
            return (f"[FALHA] Erro inesperado no servidor: {e}", estado_retorno, notificacao)

#Funcao de comunicação do telnet - Modificado para utilizar outro sistema telnet
def receber_input(conn, prompt_text=""):
    try:
        conn.sendall(f"\r\n{prompt_text}> ".encode('utf-8'))
        
        while True:
            raw_data = conn.recv(1024)
            if not raw_data:
                return None

            IAC = b'\xff'
            if IAC not in raw_data:
                try:
                    data_str = raw_data.decode('utf-8').strip()
                    if data_str: 
                        return data_str
                except UnicodeDecodeError:
                    print("[AVISO] Recebido dado não-UTF8, ignorando.")
                    conn.sendall(f"\r\n{prompt_text}> ".encode('utf-8'))
                    continue
            
            clean_data = bytearray()
            i = 0
            while i < len(raw_data):
                byte = raw_data[i:i+1]
                if byte == IAC:
                    i += 3
                else:
                    clean_data.extend(byte)
                    i += 1
            
            if clean_data:
                try:
                    data_str = clean_data.decode('utf-8').strip()
                    if data_str:
                        return data_str
                except UnicodeDecodeError:
                    print("[AVISO] Dado não-UTF8 recebido após limpeza, ignorando.")
                    conn.sendall(f"\r\n{prompt_text}> ".encode('utf-8'))
                    continue
            
            conn.sendall(f"\r\n{prompt_text}> ".encode('utf-8'))
            
    except (ConnectionResetError, BrokenPipeError):
        return None

#Funcao para lidar com o cliente já conectado
def handle_client(conn, addr):
    print(f"[NOVA CONEXAO] {addr} conectado.")
    num_conta_logada = None
    nome_logado = None
    
    try:
        while True:
            menu_principal_texto = (
                "\r\n" + "="*40 +
                "\r\n--- Bem-vindo ao IFBank ---" +
                "\r\n Transferências rápidas e sem taxas." +
                "\r\n Crie sua conta e aproveite!" +
                "\r\n" + "="*40 +
                "\r\n1. Acessar minha Conta" +
                "\r\n2. Criar nova Conta" +
                "\r\n3. Sair do Aplicativo"
            )
            escolha = receber_input(conn, menu_principal_texto)

            if escolha is None: break

            if escolha == '1':
                cpf = receber_input(conn, "Digite seu CPF: ")
                if cpf is None: break
                senha = receber_input(conn, "Digite sua senha: ")
                if senha is None: break
                
                comando = f"LOGIN|{cpf}|{senha}"
                resposta, novo_estado, _ = processar_comando(comando, None)
                conn.sendall(f"\r\n{resposta}\r\n".encode('utf-8'))
                
                if novo_estado[0] == "LOGIN":
                    num_conta_logada, nome_logado = novo_estado[1], novo_estado[2]
                    with conexoes_lock:
                        conexoes_ativas[num_conta_logada] = conn

                    while True:
                        menu_logado_texto = (
                            f"\r\n--- IFBank | Olá, {nome_logado} (Conta: {num_conta_logada}) ---" +
                            "\r\n1. Ver Saldo" +
                            "\r\n2. Depositar" +
                            "\r\n3. Sacar" +
                            "\r\n4. Transferir" +
                            "\r\n5. Sair da Conta (Logout)"
                        )
                        escolha_logado = receber_input(conn, menu_logado_texto)
                        
                        if escolha_logado is None: break

                        if escolha_logado == '1':
                            comando_logado = "SALDO"
                            resposta, _, _ = processar_comando(comando_logado, num_conta_logada)
                        
                        elif escolha_logado == '2':
                            valor_str = receber_input(conn, "Digite o valor para depositar: R$ ")
                            if valor_str is None: break
                            comando_logado = f"DEPOSITAR|{valor_str}"
                            resposta, _, _ = processar_comando(comando_logado, num_conta_logada)
                        
                        elif escolha_logado == '3':
                            valor_str = receber_input(conn, "Digite o valor para sacar: R$ ")
                            if valor_str is None: break
                            senha_saque = receber_input(conn, "Digite sua senha para confirmar: ")
                            if senha_saque is None: break
                            comando_logado = f"SACAR|{valor_str}|{senha_saque}"
                            resposta, _, _ = processar_comando(comando_logado, num_conta_logada)

                        elif escolha_logado == '4':
                            c_destino = receber_input(conn, "Digite o número da conta de destino: ")
                            if c_destino is None: break
                            valor_str = receber_input(conn, "Digite o valor para transferir: R$ ")
                            if valor_str is None: break
                            senha_transf = receber_input(conn, "Digite sua senha para confirmar: ")
                            if senha_transf is None: break
                            comando_logado = f"TRANSFERIR|{c_destino}|{valor_str}|{senha_transf}"
                            resposta, _, notificacao = processar_comando(comando_logado, num_conta_logada)
                            if notificacao:
                                enviar_notificacao(notificacao[0], notificacao[1])

                        elif escolha_logado == '5':
                            comando_logado = "LOGOUT"
                            resposta, _, _ = processar_comando(comando_logado, num_conta_logada)
                            conn.sendall(f"\r\n{resposta}\r\n".encode('utf-8'))
                            break
                        
                        else:
                            resposta = "[IFBANK] Opção inválida, tente novamente."
                        
                        conn.sendall(f"\r\n{resposta}\r\n".encode('utf-8'))
                    
                    if num_conta_logada:
                        with conexoes_lock:
                            if num_conta_logada in conexoes_ativas:
                                del conexoes_ativas[num_conta_logada]
                        print(f"[IFBANK] Conexão ativa de {nome_logado} (C:{num_conta_logada}) removida.")
                        num_conta_logada, nome_logado = None, None

            elif escolha == '2':
                nome = receber_input(conn, "Digite seu nome completo: ")
                if nome is None: break
                cpf = receber_input(conn, "Digite seu CPF: ")
                if cpf is None: break
                senha = receber_input(conn, "Crie uma senha: ")
                if senha is None: break
                senha_conf = receber_input(conn, "Confirme sua senha: ")
                if senha_conf is None: break
                
                if senha != senha_conf:
                    conn.sendall("\r\n[ERRO] As senhas não coincidem.\r\n".encode('utf-8'))
                    continue
                
                comando = f"CRIAR|{nome}|{cpf}|{senha}"
                resposta, _, _ = processar_comando(comando, None)
                conn.sendall(f"\r\n{resposta}\r\n".encode('utf-8'))

            elif escolha == '3':
                conn.sendall("\r\nObrigado por usar o IFBank!\r\n".encode('utf-8'))
                break
            
            else:
                conn.sendall("\r\n[IFBANK] Opção inválida.\r\n".encode('utf-8'))
        
    except (ConnectionResetError, BrokenPipeError, EOFError):
        print(f"[IFBANK] {addr} desconectou.")
    finally:
        if num_conta_logada:
            with conexoes_lock:
                if num_conta_logada in conexoes_ativas:
                    del conexoes_ativas[num_conta_logada]
                    print(f"[IFBANK] Conexão ativa de {nome_logado} (C:{num_conta_logada}) removida.")
        conn.close()
        print(f"Encerrando {addr}.")

def main():
    os.makedirs(PASTA_DADOS, exist_ok=True)
    os.makedirs(PASTA_LOGS, exist_ok=True)
    carregar_contas()

    host = input("Digite o endereco IP do servidor: ")
    port = int(input("Digite a porta do servidor: "))

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.bind((host, port))
        server_socket.listen()
        print(f"[IFBANK] Servidor IFBank ativo em {host}:{port}")
    except Exception as e:
        print(f"[IFBANK] Falha ao iniciar o servidor: {e}")
        return

    try:
        while True:
            conn, addr = server_socket.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.start()
    except KeyboardInterrupt:
        print("\n[IFBANK] Servidor encerrando atividades...")
    finally:
        print("[IFBANK] Salvando contas...")
        with contas_lock:
            salvar_contas()
        server_socket.close()
        print("[IFBANK] Servidor desligado.")

if __name__ == "__main__":
    main()