# DOCUMENTO DE CONTEXTO TÉCNICO
## Projeto de Migração de Telemetria — Estação de Pedro Osório/RS

**Data de referência:** 27 de outubro de 2026  
**Visita técnica prevista:** 28 de outubro de 2026  
**Equipamento principal:** Modem de telemetria ABS CEL S  
**Sistema atual:** Dualbase / PCDWeb  
**Objetivo:** Migrar a recepção e o armazenamento dos dados da estação para infraestrutura própria, preferencialmente sem substituir o hardware existente.

---

# 1. Visão geral do projeto

Estamos desenvolvendo uma solução para migrar a infraestrutura de recebimento e armazenamento de dados de uma estação de telemetria localizada em Pedro Osório, no Rio Grande do Sul.

Atualmente, a estação possui um modem de telemetria ABS CEL S, que transmite dados para a infraestrutura da empresa Dualbase, utilizando sua plataforma PCDWeb.

Nossa equipe passou a dispor de um servidor próprio e pretende deixar de depender da infraestrutura da Dualbase para receber e armazenar essas medições.

Entretanto, existe uma dificuldade técnica importante: **o modem ABS CEL S instalado na estação utiliza um firmware modificado/customizado para o ambiente da Dualbase**.

Não sabemos ainda se o endereço do servidor remoto pode ser alterado por configuração, se está embutido no firmware ou se a comunicação utiliza um protocolo específico da Dualbase.

Queremos investigar o equipamento de maneira estruturada para determinar a estratégia mais segura de migração.

Existem dois caminhos possíveis:

**Plano A — Preservar o modem instalado em Pedro Osório.**

Investigar o firmware e a configuração atual, identificar como os dados são transmitidos à Dualbase e descobrir se é possível modificar o destino para o servidor próprio sem prejudicar o funcionamento do equipamento.

**Plano B — Utilizar um segundo modem ABS CEL S.**

Possuímos outro modem do mesmo modelo, mas com firmware diferente. Caso não seja viável adaptar o equipamento instalado, pretendemos configurar esse segundo modem e utilizá-lo como substituto.

A preferência é pelo Plano A, desde que seja tecnicamente viável e seguro.

---

# 2. Arquitetura atual da estação

A arquitetura operacional informada é:

```text
SENSORES / INSTRUMENTOS DE MEDIÇÃO
              |
              v
   DATALOGGER / CONTROLADOR
     (a confirmar em campo)
              |
              v
       MODEM ABS CEL S
    Firmware customizado
         para Dualbase
              |
              v
       REDE CELULAR
         3G / 4G
    (tecnologia a confirmar)
              |
              v
    INFRAESTRUTURA DUALBASE
              |
              v
           PCDWEB
              |
              v
   ARMAZENAMENTO / CONSULTA
      DAS MEDIÇÕES ATUAIS
```

O usuário confirmou que o equipamento de Pedro Osório transmite para o ecossistema Dualbase/PCDWeb.

Entretanto, não conhecemos todos os detalhes internos da arquitetura. Por exemplo, não sabemos se o modem:

- Comunica-se diretamente com um servidor do PCDWeb.
- Envia mensagens a um receptor intermediário da Dualbase.
- Utiliza uma API HTTP/HTTPS.
- Utiliza TCP ou UDP com protocolo próprio.
- Utiliza algum mecanismo de provisionamento remoto.
- Possui autenticação e confirmações específicas de recebimento.

**Não devemos assumir que o PCDWeb é acessado diretamente por uma API REST.**

O modem pode transmitir dados em um protocolo de telemetria, enquanto outro serviço da Dualbase realiza a interpretação e a persistência das medições.

Também não sabemos ainda o modelo dos sensores, o protocolo do datalogger, a frequência das medições ou o formato exato dos pacotes.

Essas informações precisam ser coletadas.

---

# 3. Equipamentos disponíveis

## 3.1. Modem principal — Pedro Osório

**Modelo:** ABS CEL S.

**Localização:** instalado na estação de telemetria em Pedro Osório/RS.

**Situação:** em operação, transmitindo dados para a Dualbase/PCDWeb.

**Firmware:** customizado ou modificado para a integração com a Dualbase, conforme informação do usuário.

### O que sabemos

- O modelo do modem é ABS CEL S.
- O equipamento está instalado na estação.
- O ambiente receptor atual é Dualbase/PCDWeb.
- Nossa intenção é preservar esse equipamento, se possível.
- Ainda não realizamos testes seriais no modem instalado.
- Uma visita técnica está prevista para 28/10/2026.

### O que não sabemos

- Versão exata do firmware.
- Revisão de hardware.
- Fabricante ou responsável pela customização efetiva.
- Se possui interface de configuração acessível.
- Se aceita o configurador original da ABS.
- Se aceita comandos AT.
- Se o destino remoto é configurável.
- Se existe proteção contra leitura ou atualização do firmware.
- Se o protocolo de transmissão é proprietário.
- Se existe alguma possibilidade oficial de exportar sua configuração.
- Quais consequências teria uma tentativa de atualização ou substituição de firmware.

**Importante:** até este momento, não temos uma cópia binária do firmware de Pedro Osório.

Consequentemente, ainda não foi realizada engenharia reversa efetiva de seu código.

## 3.2. Modem alternativo — Equipamento de bancada

**Modelo:** ABS CEL S.

**Situação:** equipamento disponível fisicamente para investigação e eventual substituição.

**Firmware:** diferente daquele instalado no modem de Pedro Osório.

Não foi confirmado se esse firmware é o original do fabricante ou outra versão customizada.

### O que já fizemos

Tentamos conectar esse modem a um notebook Windows utilizando um adaptador USB para serial DB9.

Inicialmente, houve dúvida porque o conector foi confundido com VGA.

Posteriormente, identificamos que se trata de uma conexão serial DB9, associada à comunicação RS-232 do equipamento.

O Windows reconheceu o adaptador como:

```text
Prolific USB-to-Serial Comm Port (COM8)
```

Isso representa uma descoberta confirmada:

**O adaptador USB-serial foi reconhecido corretamente pelo Windows.**

Não há evidência, nessa etapa, de um problema de driver do conversor.

Entretanto, precisamos distinguir a interface USB do modem propriamente dito.

O Windows reconhecer COM8 significa apenas que o conversor USB/RS-232 está disponível.

Não significa que o computador conseguiu comunicar-se com o firmware do ABS CEL S.

### Problema de alimentação

O modem alternativo não estava conectado à sua alimentação externa.

Pela especificação discutida da família ABS CEL S, o equipamento utiliza alimentação de aproximadamente 10 a 30 V em corrente contínua, mas devemos conferir os dados na etiqueta e no manual da revisão exata.

A conexão USB/DB9 não foi projetada para alimentar esse modem.

Assim, o cenário observado foi:

```text
NOTEBOOK
   |
   | USB
   v
CONVERSOR PROLIFIC
   |
   | RS-232
   v
ABS CEL S
   |
   X Sem alimentação externa confirmada
```

O usuário informou que não tinha o cabo ou conjunto de alimentação apropriado naquele momento.

Por isso, **a comunicação serial com o modem alternativo ainda não foi efetivamente testada**.

Também não foi confirmada a polaridade dos terminais de alimentação.

Não devemos energizar os bornes sem identificar com segurança os terminais positivos e negativos.

### Outra observação importante

Quando o adaptador é conectado ao modem, é normal que o Windows não apresente um novo dispositivo.

O RS-232 não possui o mecanismo de enumeração USB.

O esperado é continuar vendo a mesma porta COM.

A comunicação com o equipamento precisa ser testada por software.

---

# 4. Objetivo técnico da migração

A nova arquitetura desejada é:

```text
SENSORES / DATALOGGER
          |
          v
      ABS CEL S
          |
          v
     REDE CELULAR
          |
          v
   SERVIDOR PRÓPRIO
          |
          v
 RECEPÇÃO DAS MENSAGENS
          |
          v
 DECODIFICAÇÃO / VALIDAÇÃO
          |
          v
   BANCO DE DADOS
          |
          v
API / CONSULTA / APLICAÇÕES
```

Não estamos tentando simplesmente mudar o local onde os arquivos do modem são gravados.

Nosso objetivo real é **alterar o destino das transmissões e implementar um serviço receptor compatível com os dados enviados pela estação**.

Precisaremos identificar:

1. Como os dados são produzidos pelo datalogger.
2. Como são entregues ao modem.
3. Qual protocolo é utilizado pelo modem para transmissão.
4. Qual servidor recebe atualmente as mensagens.
5. Como as mensagens são autenticadas e interpretadas.
6. Como o servidor confirma o recebimento.
7. Como o modem reage à perda de conectividade.
8. Como os dados serão transformados e armazenados na infraestrutura própria.

Dependendo do protocolo, não será suficiente criar uma API REST tradicional.

Poderemos precisar implementar um receptor TCP, UDP, HTTP, HTTPS ou outro protocolo específico.

---

# 5. Principais hipóteses sobre o firmware

A customização da Dualbase ainda não foi analisada. Trabalhamos com quatro hipóteses.

## Hipótese A — Destino configurável

O firmware possui parâmetros de comunicação armazenados em memória persistente.

Exemplos:

```text
SERVER_HOST
SERVER_IP
SERVER_PORT
APN
PROTOCOL
DEVICE_ID
```

Nesse caso, nossa tarefa pode ser relativamente simples.

Precisaremos localizar o mecanismo de leitura e alteração desses parâmetros e configurar um novo destino.

**Teste:** verificar se o configurador oficial da ABS reconhece o equipamento e permite consultar parâmetros de comunicação.

**Risco:** o firmware customizado pode utilizar outro formato de configuração, e o configurador original pode não ser compatível.

## Hipótese B — Destino embutido no firmware

O endereço da Dualbase pode ter sido incluído diretamente no binário do firmware.

Nesse cenário, precisamos investigar uma imagem binária do firmware, caso ela possa ser obtida de maneira autorizada e segura.

O objetivo inicial seria encontrar indicadores como:

```text
dualbase
pcdweb
http://
https://
server
host
endpoint
tcp
```

A presença dessas strings não comprova que sejam utilizadas em execução.

Também existe a possibilidade de que o firmware esteja comprimido, cifrado ou represente as informações em formato binário.

**Importante:** ainda não temos essa imagem binária.

## Hipótese C — Protocolo proprietário da Dualbase

O modem pode utilizar um protocolo próprio para comunicação com a infraestrutura da Dualbase.

Nesse cenário, o endereço do servidor é apenas parte do problema.

Também seria necessário compreender:

- Estrutura dos pacotes.
- Identificação do equipamento.
- Codificação das medições.
- Checksum ou CRC.
- Sequenciamento de mensagens.
- Confirmação de recebimento.
- Autenticação.
- Reconexão.
- Retransmissão de dados não entregues.

O novo servidor precisaria reproduzir o comportamento do receptor esperado pelo firmware.

## Hipótese D — Provisionamento externo

O modem pode obter o endereço do servidor e outros parâmetros a partir de um processo de provisionamento remoto.

Nesse caso, mesmo que modifiquemos um endereço localmente, o equipamento pode receber novamente a configuração original.

Precisamos investigar se existe gerenciamento remoto, mas não temos evidências de que ele esteja presente.

---

# 6. Ferramentas e scripts discutidos

Durante a conversa, foram planejados scripts de diagnóstico em Python.

A principal biblioteca é:

```powershell
py -m pip install pyserial
```

## Script 01 — Inventário de portas seriais

**Objetivo:** identificar interfaces seriais presentes no Windows.

Informações coletadas:

- Porta COM.
- Descrição.
- Fabricante.
- VID/PID do conversor USB.
- Disponibilidade da interface.

Já identificamos anteriormente uma porta COM8 associada ao conversor Prolific.

Entretanto, o número COM pode mudar dependendo da porta USB ou do computador utilizado.

## Script 02 — Captura serial

**Objetivo:** registrar os bytes recebidos pela interface serial sem enviar comandos de aplicação ao modem.

Parâmetros inicialmente considerados:

```text
Porta: COM8
Baud rate inicial: 9600
Bits de dados: 8
Paridade: nenhuma
Stop bits: 1
```

Esses parâmetros são apenas uma configuração de teste, não uma confirmação da configuração real do firmware.

O resultado pode ser armazenado em um arquivo JSON Lines, com timestamp, representação hexadecimal e representação textual dos bytes.

Exemplos de resultados:

**Caso 1: texto legível.**

```text
MODEM READY
CONNECT OK
```

Poderia indicar mensagens de diagnóstico.

**Caso 2: bytes binários.**

```text
F0 3A 00 2B 11 7F
```

Poderia indicar protocolo binário ou parâmetros seriais incorretos.

**Caso 3: nenhuma resposta.**

Pode indicar interface silenciosa, ausência de alimentação, pinagem incompatível, baud rate incorreto ou necessidade de comandos específicos.

Nenhum desses cenários deve ser interpretado isoladamente.

Abrir uma porta serial também pode modificar sinais de controle elétrico. O teste exige cuidado, especialmente em equipamento de produção.

## Script 03 — Identificação por comandos AT

Foram discutidos comandos como:

```text
AT
ATI
AT+CGMI
AT+CGMM
AT+CGMR
```

Esses comandos podem identificar fabricantes, modelos e versões de módulos celulares que disponibilizam interfaces AT.

Entretanto, **não sabemos se o firmware customizado expõe uma interface AT pelo conector DB9**.

Portanto, esses comandos não devem ser enviados automaticamente ao equipamento de produção.

Primeiro é necessário confirmar suporte e compatibilidade.

## Script 04 — Análise estática do firmware

Foi proposto um script para procurar strings relevantes em uma imagem binária de firmware.

Por exemplo:

```text
dualbase
pcdweb
api
server
mqtt
http
https
```

Também pode procurar domínios e endereços IP.

Esse script trabalha somente em arquivos, sem alterar o hardware.

Entretanto, ainda não temos um arquivo `.bin` ou `.img` do firmware.

Precisamos primeiro descobrir se existe uma forma oficial de obtê-lo ou identificar sua versão.

**Não devemos realizar procedimentos invasivos de extração ou reflashing durante a primeira visita.**

## Script 05 — Receptor HTTP de teste

Também foi proposto um servidor local em Python capaz de receber requisições HTTP e armazenar o corpo das mensagens.

Seu objetivo é validar a arquitetura do futuro receptor.

Contudo, ainda não sabemos se o modem realmente usa HTTP.

Esse script só será aplicável diretamente se o protocolo de transmissão for compatível.

Além disso, um serviço em `127.0.0.1` é acessível apenas localmente. Um modem remoto conectado pela rede celular precisará de um endpoint acessível na rede apropriada.

## Kit de diagnóstico

Durante a conversa anterior foi disponibilizado um pacote chamado:

```text
kit_pedro_osorio.zip
```

Ele foi apresentado como contendo scripts de inventário serial, captura, análise offline de firmware e instruções de campo.

É importante verificar seu conteúdo e funcionamento antes da visita. Até o momento, os scripts não foram executados no modem de Pedro Osório.

---

# 7. Acessos disponíveis e pendentes

Precisamos diferenciar o acesso físico ao hardware do acesso aos sistemas externos.

| Recurso | Situação atual |
|---|---|
| Modem ABS CEL S alternativo | Disponível fisicamente |
| Conversor USB/RS-232 | Disponível e reconhecido pelo Windows |
| Porta COM8 | Observada anteriormente |
| Alimentação do modem alternativo | Não disponível/confirmada no teste anterior |
| Modem principal em Pedro Osório | Acesso físico previsto para 28/10 |
| Firmware binário do modem principal | Não obtido |
| Configuração interna do modem principal | Não lida |
| PCDWeb | Sabemos que é utilizado; nível de acesso não esclarecido |
| Credenciais administrativas do PCDWeb | Não confirmadas |
| Logs de recebimento na Dualbase | Acesso não confirmado |
| Servidor próprio | Existência informada; configuração do receptor pendente |
| Código-fonte do firmware customizado | Não disponível |
| Documentação específica da customização | Não disponível |
| Dados de configuração da rede celular | Não coletados |

A existência de acesso ao PCDWeb para visualizar medições não implica automaticamente permissão para visualizar ou modificar configurações do modem.

Também não devemos assumir acesso aos logs internos dos servidores da Dualbase.

---

# 8. Novas problemáticas identificadas

## 8.1. Firmware customizado

Essa é a principal dificuldade.

Mesmo utilizando o hardware ABS CEL S, o modem pode ter sido programado especificamente para a infraestrutura Dualbase.

Não sabemos quais funcionalidades originais foram mantidas.

O firmware pode incorporar comunicação própria, regras de transmissão, tratamento de medições e controle remoto.

## 8.2. Mesmo hardware não significa mesmo comportamento

Temos dois modems do mesmo modelo, mas com firmwares diferentes.

Isso não garante que sejam intercambiáveis.

Antes de utilizar o alternativo, precisamos verificar:

- Revisão da placa.
- Compatibilidade elétrica.
- Interfaces e pinagem.
- Comunicação com o datalogger.
- Protocolo das medições.
- Configurações da rede celular.
- Funcionalidades de armazenamento temporário.
- Procedimentos de inicialização.
- Compatibilidade com os sensores e controladores existentes.

Não devemos copiar firmware de um equipamento para outro sem confirmar compatibilidade, autorização e possibilidade de recuperação.

## 8.3. Comunicação serial não é comunicação celular

O adaptador Prolific permite acesso à interface RS-232.

Isso não significa que teremos visibilidade de todas as transmissões realizadas pelo modem na rede celular.

É possível que o firmware receba dados pela serial e envie mensagens por outra interface interna.

Portanto, não devemos presumir que capturar a serial revelará diretamente o endereço do servidor remoto.

## 8.4. Protocolo de transmissão desconhecido

Não sabemos se o equipamento utiliza:

- TCP.
- UDP.
- HTTP/HTTPS.
- FTP.
- MQTT.
- Protocolo binário proprietário.

A escolha do protocolo afeta completamente a implementação do novo receptor.

## 8.5. Persistência e retransmissão

O modem ou datalogger pode armazenar medições temporariamente quando perde conectividade.

Precisamos investigar se existe:

- Fila de transmissão.
- Buffer local.
- Reenvio automático.
- Confirmação do servidor.
- Identificação única das mensagens.
- Tratamento de duplicatas.
- Recuperação após reinicialização.

Uma migração que ignore esses mecanismos pode resultar em perda ou duplicação de medições.

## 8.6. Autenticação e segurança

O destino atual pode exigir credenciais, identificadores, certificados ou algum mecanismo próprio de autenticação.

A migração deverá considerar como o equipamento será autenticado no novo servidor.

Não devemos compartilhar publicamente tokens, senhas, SIM/ICCID, identificadores sensíveis ou configurações privadas extraídas durante os testes.

## 8.7. Risco operacional

A estação de Pedro Osório está funcionando.

Uma alteração incorreta pode interromper a transmissão das medições.

Por isso, a primeira visita deve priorizar diagnóstico e coleta de evidências.

Devemos preservar o funcionamento atual e evitar:

- Reset de fábrica.
- Atualização de firmware.
- Escrita em memória.
- Alteração não planejada do servidor remoto.
- Interrupção desnecessária da alimentação.
- Remoção de cabos sem registro de pinagem.
- Envio indiscriminado de comandos de configuração.

## 8.8. Possíveis restrições contratuais

É necessário verificar se a equipe tem autorização para modificar a integração, utilizar protocolos ou alterar o firmware customizado da Dualbase.

A intenção é migrar equipamento e dados sob nossa responsabilidade, preservando a operação e respeitando os direitos envolvidos.

---

# 9. Planejamento da visita de 28/10/2026

## Objetivo principal

Coletar evidências técnicas suficientes para escolher entre manter o firmware atual ou substituir o modem.

A visita não precisa terminar com a migração concluída.

## Preparação

Levar:

- Notebook Windows.
- Python e PySerial instalados.
- Conversor USB–RS-232 Prolific.
- Cabos e adaptadores DB9 adequados.
- Multímetro.
- Documentação da ABS disponível offline.
- Configurador Celular da ABS.
- Scripts de diagnóstico.
- Ferramenta para registrar capturas e arquivos de configuração.
- Informações de acesso autorizado ao PCDWeb, caso disponíveis.
- Contato da pessoa responsável pela estação.

Se houver intenção de testar o modem alternativo, também precisaremos providenciar uma alimentação apropriada, compatível com a revisão e pinagem do equipamento.

## Procedimento proposto

### Etapa 1 — Inspeção física

Antes de qualquer alteração:

1. Fotografar o modem instalado.
2. Registrar sua etiqueta e identificação.
3. Fotografar conectores e cabeamento.
4. Identificar alimentação.
5. Identificar a ligação com o datalogger.
6. Registrar o estado dos LEDs.
7. Registrar data e hora da última medição no PCDWeb.

**Resultado esperado:** documentação básica da instalação.

### Etapa 2 — Identificação da comunicação

Verificar:

1. Tipo de interface física disponível.
2. Pinagem.
3. Compatibilidade com o adaptador USB/RS-232.
4. Disponibilidade de porta serial no Windows.
5. Parâmetros seriais conhecidos.

Não desconectar uma ligação de produção sem autorização e conhecimento de sua função.

**Resultado esperado:** determinar se é possível acessar uma interface de diagnóstico com segurança.

### Etapa 3 — Leitura de configuração

Caso haja uma interface apropriada:

1. Abrir o configurador oficial da ABS.
2. Verificar se identifica o modem.
3. Consultar modelo e versão.
4. Investigar opções de leitura.
5. Exportar ou registrar as configurações, se permitido.

Não alterar parâmetros neste primeiro momento.

**Resultado esperado:** verificar se existe uma forma documentada de acessar parâmetros de comunicação.

### Etapa 4 — Registro de comunicação

Se a interface permitir, capturar mensagens seriais e registrar os resultados.

Precisamos distinguir mensagens do firmware, dados provenientes do datalogger e respostas de comandos.

Se não houver resposta, investigar as condições da interface antes de assumir que existe bloqueio.

**Resultado esperado:** evidências sobre o comportamento serial do equipamento.

### Etapa 5 — Conferência da operação

Ao terminar:

1. Confirmar que a estação continua energizada.
2. Verificar o estado dos LEDs.
3. Confirmar que os cabos permanecem corretamente conectados.
4. Conferir a chegada de novas medições ao PCDWeb.
5. Registrar qualquer comportamento anormal.

**Resultado esperado:** encerrar a visita sem comprometer o funcionamento da telemetria.

---

# 10. Interpretação dos possíveis resultados

| Resultado | Interpretação inicial | Próxima ação |
|---|---|---|
| Configurador reconhece o modem | Existe alguma compatibilidade de comunicação | Investigar parâmetros de leitura |
| Configurador lê IP/domínio de destino | Há indícios de configuração acessível | Avaliar migração por configuração |
| Configurador não reconhece o modem | Pode existir incompatibilidade de protocolo | Investigar versão e interface específica |
| Serial retorna mensagens legíveis | Há canal de comunicação observável | Registrar mensagens e eventos |
| Serial retorna dados binários | Pode existir protocolo binário ou parâmetros incorretos | Analisar capturas e configuração serial |
| Serial permanece silenciosa | Resultado inconclusivo | Verificar interface, alimentação e modo de operação |
| Encontramos endpoint no firmware | Possível destino embutido | Correlacionar com funcionamento real |
| Não encontramos endpoint | Não comprova ausência | Investigar configuração externa |
| Encontramos protocolo proprietário | Receptor possivelmente especializado | Investigar estrutura e confirmação das mensagens |
| Não conseguimos modificar o firmware | Plano A pode ser inviável | Avaliar adaptação do modem alternativo |

---

# 11. Estratégias de migração

## Estratégia A — Alterar somente a configuração

É o melhor cenário operacional.

Se conseguirmos identificar o host e a porta de transmissão e houver mecanismo suportado para modificá-los, poderemos manter o firmware existente.

O servidor próprio precisará implementar o protocolo esperado.

## Estratégia B — Implementar receptor compatível

Se o firmware utilizar um protocolo da Dualbase, mas permitir redirecionamento, podemos estudar a compatibilidade do receptor.

Nesse caso, precisaremos entender o formato das mensagens e as confirmações esperadas.

## Estratégia C — Substituir o modem

Caso a customização impossibilite a migração, utilizaremos o segundo ABS CEL S, desde que ele possa receber as medições do datalogger e transmiti-las ao novo servidor.

Essa alternativa exige testes de integração.

## Estratégia D — Integração com o sistema atual

Também devemos investigar se o PCDWeb oferece mecanismos autorizados de exportação, integração ou encaminhamento dos dados.

Se existir essa opção, pode ser possível obter as medições sem modificar inicialmente o firmware.

Essa estratégia pode funcionar como solução intermediária, embora não necessariamente elimine a dependência da Dualbase.

---

# 12. Requisitos do futuro servidor

Depois de descobrir o protocolo, o servidor próprio deverá contemplar:

**Recepção**
- Endpoint ou serviço de rede compatível.
- Autenticação de equipamentos.
- Validação dos dados recebidos.
- Tratamento de mensagens incompletas.
- Respostas e confirmações compatíveis.

**Processamento**
- Identificação da estação.
- Identificação dos sensores.
- Decodificação das medições.
- Tratamento de timestamps.
- Validação de valores.
- Tratamento de duplicatas.

**Persistência**
- Banco de dados estruturado.
- Histórico das medições.
- Rastreabilidade das mensagens.
- Controle de falhas.
- Possibilidade de reprocessamento.

**Operação**
- Logs.
- Monitoramento da última transmissão.
- Alertas de estação offline.
- Tratamento de reconexões.
- Segurança da comunicação.
- Backups.
- Procedimento de recuperação.

O modelo de dados definitivo ainda depende da identificação dos sensores e do formato das mensagens.

---

# 13. Estado real do projeto

**Confirmado até agora:**

- Existe uma estação de telemetria em Pedro Osório/RS.
- O modem instalado é ABS CEL S.
- O firmware desse modem foi customizado para o ambiente Dualbase, conforme informação do usuário.
- As medições são encaminhadas ao ecossistema Dualbase/PCDWeb.
- Queremos migrar a recepção e o armazenamento para um servidor próprio.
- Existe um segundo modem ABS CEL S com firmware diferente.
- O conversor USB/RS-232 Prolific foi reconhecido no Windows como COM8.
- O modem alternativo não teve sua comunicação testada de forma conclusiva, principalmente pela falta de alimentação externa.
- Uma visita física à estação está prevista para 28/10/2026.

**Ainda não confirmado:**

- Protocolo utilizado entre o modem e a Dualbase.
- Formato dos pacotes.
- Endereço IP ou domínio de destino.
- Porta de comunicação.
- Parâmetros seriais do modem instalado.
- Versão do firmware customizado.
- Existência de proteção contra leitura.
- Possibilidade de alterar o servidor por configuração.
- Existência de API ou exportação utilizável no PCDWeb.
- Compatibilidade operacional do modem alternativo.
- Viabilidade de migração sem alterar o firmware.
- Capacidade do servidor próprio para reproduzir o protocolo exigido.

**Ainda não realizado:**

- Leitura da configuração do modem de Pedro Osório.
- Captura de tráfego do equipamento principal.
- Extração autorizada de firmware.
- Análise de binário real.
- Testes de comandos AT no equipamento principal.
- Implementação de um receptor compatível com o protocolo real.
- Teste de transmissão do modem para o novo servidor.
- Alteração do destino de produção.

---

# 14. Próximas entregas desejadas

Depois da visita, queremos produzir:

1. **Inventário técnico da estação:** hardware, conexões, versões e interfaces.
2. **Relatório de diagnóstico:** procedimentos executados, saídas dos scripts, evidências e limitações.
3. **Análise do firmware/protocolo:** mecanismo de configuração e transmissão.
4. **Decisão arquitetural:** manter o modem atual ou utilizar o alternativo.
5. **Especificação do novo receptor:** protocolo, mensagens, validações, autenticação e armazenamento.
6. **Plano de migração:** testes, rollback, monitoramento e critérios de sucesso.
7. **Implementação e validação:** recepção real das medições no servidor próprio.

---

# 15. Orientações para o próximo agente de IA

Ao continuar este projeto:

- Considere todo o contexto acima como histórico da investigação.
- Não confunda o modem de Pedro Osório com o modem alternativo de bancada.
- Ambos são ABS CEL S, mas utilizam firmwares diferentes.
- Não assuma que o firmware instalado é original da ABS.
- Não assuma que a Dualbase utiliza uma API REST convencional.
- Não assuma que o endereço do servidor é configurável até obtermos evidências.
- Não considere que a COM8 confirma comunicação com o firmware.
- Não confunda captura serial com captura do tráfego 4G.
- Não recomende comandos de escrita ou atualização de firmware antes de identificar a interface e preservar a configuração atual.
- Diferencie fatos confirmados, hipóteses e resultados ainda pendentes.
- Priorize procedimentos de leitura, documentação, capturas e testes reversíveis.
- Antes de sugerir compra de equipamento, verifique compatibilidade com o que já possuímos.
- Ao analisar cada resultado de teste, explique o significado técnico, os limites da evidência e qual próximo experimento permitirá confirmar ou refutar a hipótese.
- Sempre considere que a estação de Pedro Osório está em operação e a continuidade das medições é prioritária.

## Pergunta central do projeto

**Como fazer um modem ABS CEL S, atualmente operando com firmware customizado para transmitir dados à infraestrutura Dualbase/PCDWeb, enviar suas medições para um servidor próprio, preservando a confiabilidade da telemetria e evitando a substituição desnecessária do hardware?**

O próximo avanço depende principalmente dos resultados da inspeção física e dos testes de diagnóstico previstos para 28 de outubro de 2026.