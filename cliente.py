# cliente.py // necessário inserir o ip e porta do servidor na rede que esta rodando o sistema
import socket

def main():
    host = input("Digite o endereco IP do servidor: ")
    port = int(input("Digite a porta do servidor: "))

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        client_socket.connect((host, port))
        print(f"Conectado ao servidor em {host}:{port}")
        print("\n--- Bem-vindo ao Banco Distribuido ---")
        print("Comandos disponiveis:")
        print("  CRIAR <senha>")
        print("  SALDO <numero_da_conta>")
        print("  DEPOSITAR <numero_da_conta> <valor>")
        print("  SACAR <numero_da_conta> <valor> <senha>")
        print("  TRANSFERIR <conta_origem> <conta_destino> <valor> <senha_origem>")
        print("  /sair para encerrar")
        
        while True:
            comando = input("\nDigite o comando: ")

            if comando.strip().lower() == '/sair':
                break

            if not comando:
                continue
            client_socket.sendall(comando.encode('utf-8'))

            resposta = client_socket.recv(1024).decode('utf-8')
            print(f"Resposta do Servidor: {resposta}")

    except ConnectionRefusedError:
        print("[ERRO] Nao foi possivel se conectar ao servidor. Verifique o IP/Porta e se o servidor esta rodando.")
    except Exception as e:
        print(f"Ocorreu um erro: {e}")
    finally:
        client_socket.close()
        print("Conexao encerrada.")

if __name__ == "__main__":
    main()