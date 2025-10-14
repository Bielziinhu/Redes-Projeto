`# Sistema Básico de Operações Financeiras (Banco Redes)

Este projeto implementa um sistema bancário cliente-servidor utilizando sockets TCP em Python, conforme proposto na atividade de Redes de Computadores.

## Funcionalidades

* **Servidor**: Gerencia contas bancárias (criar, consultar saldo, depositar, sacar).
* **Cliente**: Interface de linha de comando para interagir com o servidor.
* **Protocolo TCP**: Garante a comunicação confiável entre cliente e servidor.
* **Persistência de Dados**: O estado das contas é salvo em `contas.json` quando o servidor é encerrado e carregado na inicialização.
* **Log de Transações**: Todas as operações de depósito e saque são registradas em `transacoes.log` com data e hora.

`REDES-PROJETO/

|-- dados/contas.json

|-- logs/transacoes.log

|-- README.md

|-- servidor.py

|-- cliente.py`

## Como Compilar e Executar

O projeto foi desenvolvido em Python 3. Não são necessárias bibliotecas externas.

### Pré-requisitos

* Python 3
* Duas ou mais máquinas (físicas ou virtuais) na mesma rede. O projeto foi testado com duas VMs Debian no VirtualBox em modo de rede "Bridge".

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

### Comandos Disponíveis no Cliente

* `CRIAR <senha>`: Cria uma nova conta com saldo zero.
* `SALDO <numero_da_conta>`: Verifica o saldo de uma conta existente.
* `DEPOSITAR <numero_da_conta> <valor>`: Adiciona um valor ao saldo da conta.
* `TRANSFERIR <conta_origem> <conta_destino> <valor> <senha_origem>`: Transfere um valor de uma conta para outra
* `SACAR <numero_da_conta> <valor> <senha>`: Retira um valor do saldo da conta.
* `/sair`: Encerra a conexão e fecha o cliente.`