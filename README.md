# Sistema Básico de Operações Financeiras (Banco Redes)

Este projeto implementa um sistema bancário cliente-servidor utilizando sockets TCP em Python, conforme proposto na atividade de Redes de Computadores.

## Funcionalidades

* **Servidor**: Gerencia contas bancárias (criar, consultar saldo, depositar, sacar).
* **Cliente**: Interface de linha de comando para interagir com o servidor.
* **Protocolo TCP**: Garante a comunicação confiável entre cliente e servidor.
* **Persistência de Dados**: O estado das contas é salvo em `contas.json` quando o servidor é encerrado e carregado na inicialização.
* **Log de Transações**: Todas as operações de depósito e saque são registradas em `transacoes.log` com data e hora.

REDES-PROJETO/

|-- dados/contas.json

|-- logs/transacoes.log

|-- README.md

|-- servidor.py

|-- cliente.py

## Como Compilar e Executar

O projeto foi desenvolvido em Python 3. Não são necessárias bibliotecas externas.

### Pré-requisitos

* Python 3
* Duas ou mais máquinas (físicas ou virtuais) na mesma rede.

### 1. Executando o Servidor

1.  Clone este repositório para a máquina que será o servidor.
2.  Abra um terminal e navegue até a pasta do projeto.
3.  Execute o script do servidor:
    ```bash
    python3 servidor.py
    ```
4.  O programa solicitará o endereço IP e a porta que o servidor deve usar. Forneça o IP da própria máquina servidora.

### 2. Executando o Cliente

1.  Clone este repositório para a máquina cliente.
2.  Abra um terminal e navegue até a pasta do projeto.
3.  Execute o script do cliente:
    ```bash
    python3 cliente.py
    ```
4.  O programa solicitará o endereço IP e a porta do **servidor** ao qual deseja se conectar.

### 3. Utilizando o Servidor com Telnet

1. Logo depois de executar o **servidor-telnet.py** utilizando o mesmo processo do arquivo **servidor.py** anteriormente.

2. Execute o seguinte comando no console da máquina virtual:
```bash
   telnet <IP> <PORTA>
```
OBS: Para executar o Telnet no Windows, é necessário utilizar o software PuTTY Terminal.

### Comandos Disponíveis

**Menu Principal**

**​1. Acessar minha Conta:** Requer CPF e Senha para logar.
**​2. Criar nova Conta:** Inicia o processo de criação de conta (requer Nome, CPF e Senha).
**​3. Sair do Aplicativo:** Encerra a conexão.

**​Menu Logado**

**​1. Ver Saldo:** Exibe o saldo atual da conta.
**​2. Depositar:** Permite depositar um valor na própria conta.
**​3. Sacar:** Permite sacar um valor da própria conta (requer confirmação de senha).
**​4. Transferir:** Permite transferir um valor para outra conta (requer conta de destino, valor e confirmação de senha).
**​5. Sair da Conta:** Desloga o usuário e retorna ao Menu Principal.