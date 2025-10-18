# cliente.py
import socket
import sys
import getpass

client_socket = None

def conectar_servidor():
    global client_socket
    host = input("Digite o endereco IP do servidor: ")
    port = int(input("Digite a porta do servidor: "))

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((host, port))
        print(f"Conectado ao IFBank em {host}:{port}")
        return True
    except ConnectionRefusedError:
        print("[ERRO] Servidor offline ou recusou a conexão.")
        return False
    except Exception as e:
        print(f"[ERRO] Ocorreu um erro ao conectar: {e}")
        return False

def enviar_comando_e_receber(comando):
    """Envia um comando e espera (bloqueado) pela resposta."""
    try:
        client_socket.settimeout(None)
        client_socket.sendall(comando.encode('utf-8'))
        resposta = client_socket.recv(1024).decode('utf-8')
        return resposta
    except (ConnectionResetError, BrokenPipeError):
        print("\n[ERRO] Conexão com o servidor perdida.")
        sys.exit()

def verificar_notificacoes():
    try:
        client_socket.settimeout(0.1)
        notificacao = client_socket.recv(1024).decode('utf-8')
        
        if notificacao.startswith("[ALERTA]"):
            print("\n" + "="*50)
            print(f" {notificacao} ")
            print("="*50)
            print("Digite sua opção: ", end='', flush=True)
            
    except socket.timeout:
        pass
    except (ConnectionResetError, BrokenPipeError):
        print("\n[ERRO] Conexão com o servidor perdida.")
        sys.exit()
    finally:
        client_socket.settimeout(None)

def menu_logado(nome, num_conta):
    print(f"\n--- Login bem-sucedido! ---")
    
    while True:
        verificar_notificacoes()

        print(f"\n--- IFBank | Olá, {nome} (Conta: {num_conta}) ---")
        print("1. Ver Saldo")
        print("2. Depositar")
        print("3. Sacar")
        print("4. Transferir")
        print("5. Sair da Conta (Logout)")
        
        escolha = input("Digite sua opção: ")
        
        if escolha == '1':
            resposta = enviar_comando_e_receber("SALDO")
            print(f"Resposta do Servidor: {resposta}")
        
        elif escolha == '2':
            try:
                valor = float(input("Digite o valor para depositar: R$ "))
                comando = f"DEPOSITAR|{valor}"
                resposta = enviar_comando_e_receber(comando)
                print(f"Resposta do Servidor: {resposta}")
            except ValueError:
                print("[ERRO] Valor inválido.")
        
        elif escolha == '3':
            try:
                valor = float(input("Digite o valor para sacar: R$ "))
                senha = getpass.getpass("Digite sua senha para confirmar: ")
                comando = f"SACAR|{valor}|{senha}"
                resposta = enviar_comando_e_receber(comando)
                print(f"Resposta do Servidor: {resposta}")
            except ValueError:
                print("[ERRO] Valor inválido.")
                
        elif escolha == '4':
            try:
                c_destino = input("Digite o número da conta de destino: ")
                valor = float(input("Digite o valor para transferir: R$ "))
                senha = getpass.getpass("Digite sua senha para confirmar: ")
                comando = f"TRANSFERIR|{c_destino}|{valor}|{senha}"
                resposta = enviar_comando_e_receber(comando)
                print(f"Resposta do Servidor: {resposta}")
            except ValueError:
                print("[ERRO] Valor inválido.")
                
        elif escolha == '5':
            resposta = enviar_comando_e_receber("LOGOUT")
            print(f"Resposta do Servidor: {resposta}")
            break
        
        else:
            print("[AVISO] Opção inválida, tente novamente.")

def menu_principal():
    while True:
        print("\n--- Bem-vindo ao IFBank ---")
        print("Transferências rápidas e sem taxas. Crie sua conta!")
        print("1. Acessar minha Conta")
        print("2. Criar nova Conta")
        print("3. Sair do Aplicativo")
        
        escolha = input("Digite sua opção: ")
        
        if escolha == '1':
            # Acessar Conta (Login)
            cpf = input("Digite seu CPF: ")
            senha = getpass.getpass("Digite sua senha: ")
            comando = f"LOGIN|{cpf}|{senha}"
            resposta = enviar_comando_e_receber(comando)
            
            if resposta.startswith("[SUCESSO]"):
                try:
                    _, nome, num_conta = resposta.split('|')
                    menu_logado(nome, num_conta)
                except ValueError:
                    print(f"[ERRO-CLIENTE] Resposta de login inesperada: {resposta}")
            else:
                print(f"Resposta do Servidor: {resposta}")
                
        elif escolha == '2':
            print("\n--- Criação de Conta ---")
            nome = input("Digite seu nome completo: ")
            cpf = input("Digite seu CPF (apenas números): ")
            senha = getpass.getpass("Crie uma senha: ")
            senha_conf = getpass.getpass("Confirme sua senha: ")
            
            if senha != senha_conf:
                print("[ERRO] As senhas não coincidem.")
                continue
            
            comando = f"CRIAR|{nome}|{cpf}|{senha}"
            resposta = enviar_comando_e_receber(comando)
            print(f"Resposta do Servidor: {resposta}")

        elif escolha == '3':
            print("Obrigado por usar o IFBank. Até logo!")
            break
        
        else:
            print("[AVISO] Opção inválida, tente novamente.")

def main():
    if conectar_servidor():
        menu_principal()
    
    if client_socket:
        client_socket.close()
    print("Programa encerrado.")

if __name__ == "__main__":
    main()