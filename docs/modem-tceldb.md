# Modem de Pedro Osório: comandos e troca do destino

Registro de 28/10/2026 (horários em UTC; local = UTC−03:00). O modem `pedro-osorio`
é um ABS CEL S com módulo Cinterion EHS6 rodando o app Java da dualBASE
`TCelDB_V2.0`. O manual da ABS vale para hardware, LEDs e pinagem; a configuração
segue o protocolo da dualBASE, descrito abaixo. Ensaio por ensaio em
[registro-investigacao.md](registro-investigacao.md).

## Resultado

O destino dos dados é trocado com:

```text
!CMD->urldados:<URL terminada no parâmetro que recebe a linha>%
```

Às 17:42 UTC o modem entregou ao `nimbus` três mensagens de teste e duas de `BOOT`,
todas com `Status envio: true`, usando:

```text
!CMD->urldados:http://nimbus.nucleodeprevisao.com/teste-dispositivo/receber?cmd=%
```

Às 17:58 UTC o canal remoto e o DDNS também saíram da dualBASE:

```text
!CMD->ddns:http://nimbus.nucleodeprevisao.com/teste-dispositivo/receber%
!CMD->urlportas:nimbus.nucleodeprevisao.com%
```

Valores originais, para retorno à dualBASE:

```text
!CMD->urldados:http://recepcao.dualbase.com.br/recep/recep.php?cmd=%
!CMD->urlportas:pcdnaweb.com.br%
!CMD->porta:10664%
!CMD->ddns:http://update.pcdnaweb.com.br/ddns.php%
```

## Fontes usadas

| Fonte | Onde | O que trouxe |
| --- | --- | --- |
| Folha de instrução TCelDB, dualBASE, versão 02.050724 | [dualbase.com.br/suporte](https://dualbase.com.br/suporte/) → [PDF](https://dualbase.com.br/site/uploads/2024/07/Folha-de-instrucao-TCelDB-PT.pdf) | Lista pública de comandos `!CMD->`; diz que APN e URL de envio são obrigatórias, mas publica só o comando da APN |
| E-mails com a dualBASE, set/2025 | `docs/Webmail UFPel __ Re_ Estação dualBASE UFPel.PDF` (fora do Git) | Serial 9600 8N1, `destdebug`, `status`, `apn`, `dbsd`, `erasedb`, `toff`; envio por HTTP; exemplo de log com `Status envio` |
| Manual de operação da estação, 03/10/2025 | `docs/Dados de operacao Estacao dualBASE NIP-PO.pdf` (fora do Git; contém senhas) | Mesmos comandos; acesso remoto ao datalogger por `pcd.dualbase.com.br:10665` (PC400, PakBus 1) |
| Programa do datalogger | `docs/UFPEL_DBHIDRO_RADAROTT FINAL.CR2` (fora do Git) | Comandos `DBSD`, `LMPSTGON`, `TOFF` e `porta:10664` enviados pelo CR200X |
| Pacote ABS CEL S 4G | [abstelemetria.com](https://abstelemetria.com/abs-cel-s-4g/) | Pinagem RS-232 (0V→5, RX→3, TX→2), LEDs, alimentação; Modbus e configurador da ABS não se aplicam a este firmware |
| `docs/Configurador_cel.exe` (fora do Git) | Decompilado estaticamente | Configurador da ABS por Modbus; não contém os comandos da dualBASE |

## Como o comando foi encontrado

1. **Velocidade e enlace.** A leitura Modbus documentada pela ABS não teve resposta.
   O LED RX do modem piscou com envios em 9600 e não em 115200. Os comandos dos
   e-mails, a 9600 8N1, responderam a partir de 14:42.
2. **Leitura da configuração.** `destdebug:SERIAL` + `status` mostraram a URL de
   dados (`linhadados`), o canal `pcdnaweb.com.br`/`10664`, a APN e o baudrate.
3. **Hipótese descartada.** Os rótulos do `status` não são comandos: `version` e
   `url_portas:pcdnaweb.com.br` (mesmo valor gravado) voltaram
   `[PWL-33] Comando nao reconhecido`, sem alterar nada.
4. **Busca na web.** A dualBASE vende o app como produto (TCelDB). A folha de
   instrução pública confirmou o protocolo, acrescentou `emsg`, `baudrate`,
   `quit`, `iccid` e `resetconfig`, mas omitiu o comando da URL.
5. **Código de retorno.** Toda resposta termina em `E` quando o comando é executado
   e em `F` + `Comando nao reconhecido` quando o nome não existe. Isso permite
   testar nomes sem efeito colateral.
6. **Nomes testados regravando o valor atual.** `porta:10664` aceito
   (`[PWL-27] Armazenando porta principal`); `url:` recusado; `urldados:` aceito.
   Como o valor era o mesmo, nada mudou.
7. **Confirmação reversível.** `urldados` com `...recep.php?teste=1&cmd=`, que ainda
   entrega na dualBASE, mudou `linhadados` em duas leituras; o valor original foi
   regravado e conferido em mais duas.
8. **Troca para o `nimbus`.** HTTPS falhou no TLS; HTTP recebeu um 301. O `nimbus` foi
   ajustado para responder HTTP sem redirecionar, com corpo `|`; após `toff` e
   religamento, a fila foi entregue.
9. **Canal remoto e DDNS.** O boot revelou `UrlDDNS` e a conexão permanente com
   `pcdnaweb.com.br:10664`. Pelo mesmo método: `urlportas:` aceito (silencioso),
   `ddns:` aceito (`[PWL-31] Armazenando url ddns`); `urlporta`, `url_porta`,
   `urlsocket`, `socket`, `host`, `servidor`, `urlremoto`, `urlacesso`, `acesso`,
   `urlddns`, `url_ddns` e `urldns` recusados. `urlportas:pcd.dualbase.com.br`, mesmo
   IP da dualBASE, mudou `url_portas` em duas leituras e foi revertido antes da troca.

## Comandos conhecidos

Formato: `!CMD-><comando>%`, ASCII, 9600 8N1, sem fim de linha. As respostas só
aparecem na serial com `destdebug:SERIAL`.

| Comando | Situação | Efeito |
| --- | --- | --- |
| `destdebug:NULL`, `:PRINT`, `:SERIAL` | Folha e ensaio | Destino do log; usar `NULL` antes de religar o datalogger |
| `status` | Folha e ensaio | Configuração, sinal, tempo ativo, versão |
| `emsg` | Folha e ensaio | Fila de envio: `E` vazia, `F` com registros |
| `dbsd:<id>:<texto>` | Folha e ensaio | Grava na fila e dispara o envio |
| `urldados:<URL>` | Ensaio (não publicado) | Troca a URL de dados |
| `urlportas:<host>` | Ensaio (não publicado) | Host do canal remoto; `url_acesso` passa a ser `<host>:<porta+1>` |
| `porta:<n>` | Programa do datalogger e ensaio | Grava a "porta principal" do canal remoto |
| `ddns:<URL>` | Ensaio (não publicado) | URL de atualização de DDNS; aparece só no log de boot |
| `lmpstgon` / `lmpstgoff` | Programa do datalogger e ensaio | Liga/desliga a "limpeza de string" |
| `toff` | Folha e ensaio | Encerra o app com segurança; volta só com religamento |
| `apn:<apn>:<user>:<senha>` | Folha, e-mails | Não testado nesta visita |
| `baudrate:<n>` | Folha | Não testado; mudar perde a serial atual |
| `quit` | Folha | Para o Java e devolve o modo AT (em geral 115200) |
| `iccid`, `erasedb` | Folha, e-mails | Não testados |
| `resetconfig` | Folha | Volta à configuração padrão; não usar sem plano |
| `url`, `version`, `help`, `url_portas:`, `urlddns`, `host`, `servidor` | Ensaio | Não reconhecidos |

## Procedimento de troca e retorno

1. Conectar o notebook ao DB9 do modem com cabo RS-232 (não TTL); 9600 8N1. Fechar
   qualquer outro programa que use a porta COM.
2. `!CMD->destdebug:SERIAL%`, depois `!CMD->emsg%` para registrar o estado da fila.
3. `!CMD->urldados:<nova URL>%` e conferir `E`.
4. Ler `!CMD->status%` três vezes. A serial deste conjunto corrompe bytes recebidos
   (sempre o bit 2: `c`→`g`, `1`→`5`, espaço→`$`); aceitar o valor que se repete.
5. `!CMD->dbsd:1000:teste%` e acompanhar `Enviando` / `Status envio: true` no log e o
   registro no receptor.
6. Se a resposta for rejeitada (`Linha invalida`, `IO Exception`), o modem pode parar
   de tentar. Corrigir o receptor, enviar `!CMD->toff%`, cortar a energia por ~10 s e
   religar; os registros pendentes são enviados no boot.
7. Antes de religar o datalogger: `!CMD->destdebug:NULL%`.

Para voltar à dualBASE, repetir os passos 3 a 5 com a URL original.

## O que o receptor precisa atender

Observado no `nimbus` com o modem real:

| Item | Requisito |
| --- | --- |
| Transporte | `http://` puro, sem redirecionar. O modem não segue 301 e lê o corpo HTML como resposta. HTTPS falhou com `-313 SSL-Error: revcd alert fatal error` |
| Requisição | `POST` com corpo vazio (`Content-Length: 0`); linha no parâmetro `cmd` da URL |
| Cabeçalhos | `User-Agent: EHS6/<IMEI> Profile/IMP-NG Configuration/CLDC-1.1` |
| Resposta | `200` com corpo exatamente `|`. Corpo JSON ou HTML gera `[CWE-04] Linha erro` por caractere e `[CWE-03] Linha invalida`; a mensagem fica na fila |
| Formato da linha | `<id>:<dados>,iccid=<ICCID>,imei=<IMEI>,porta=<n>,sinal=<n>:TCelDB_V2.0:<tentativa>` |
| Mensagens | Medições do datalogger (`9061:data=...`), `BOOT:estacao=...` a cada boot e testes `1000:...` |
| Duplicatas | O sufixo final conta as tentativas; reenvios mudam só esse número |
| Privacidade | ICCID e IMEI vão na URL e no User-Agent; não usar painel público em produção |

Em HTTPS, o modem tentou de novo a cada ~11 s. Depois da `Linha invalida` em HTTP,
parou de tentar por mais de 25 min, até ser religado.

## Canal remoto e DDNS

No boot o modem abre `socket://<url_portas>:<porta>` (`SocketWebListen` e
`SocketWebClient`). Na dualBASE, esse canal liga o modem ao PC400 em
`<url_portas>:<porta+1>` e permite acesso remoto ao datalogger e, em princípio, ao
modem. Desde o boot de 18:04 UTC o canal aponta para `nimbus.nucleodeprevisao.com:10664`,
onde nada escuta: a cada ~2 min o log registra `Estabelecendo conexao`,
`[SWC-01] Iniciando SocketWebClient`, `[SBG-08] Erro no loop leitura: Stream closed`
e `Cliente encerrado`. Em 4 min de observação não houve reinício, e o envio de dados
seguiu com `Status envio: true`. A dualBASE e a UFPel ficam sem acesso remoto até
existir um serviço nosso nessas portas.

Para recriar o acesso remoto no servidor próprio:

1. Host com IP público e portas TCP abertas: 10664 (modem) e 10665 (PC400). No
   `nimbus`, ambas estavam fechadas; hospedagem LiteSpeed não costuma permitir serviço
   TCP próprio. Se o host ou a porta forem outros, gravar com `urlportas:` e `porta:`.
2. Primeiro, um serviço que só aceite a conexão em 10664 e registre os bytes recebidos,
   já que o protocolo do canal é desconhecido.
3. Depois, o repasse 10664↔10665 para o PC400 (CR200X, PakBus 1).

A chamada de DDNS não apareceu no painel do `nimbus` até 18:10 UTC; formato e momento
ainda são desconhecidos.

Às 18:12 UTC a porta 10664 do `nimbus` passou a aceitar conexão (serviço da equipe, sem
banner; espera o cliente falar); a 10665 seguia fechada. Um teste de conexão do notebook
na 10664 às 18:13 durou 8 s. Depois disso o modem parou de registrar tentativas e passou a
logar `[SBG-13] Erro de escrita byte array: Stream closed` a cada resposta de comando:
ele espelha a saída de comandos no canal, e o canal está fechado. Sem reconexão em 8 min
de observação; o envio de dados seguiu com `Status envio: true` (18:21). O log do
servidor é que dirá se o modem conectou, o que enviou e quem fechou a conexão.

### Ponte 10664/10665 validada pelo notebook — 28/10/2026, 18:38–18:41 UTC

Relato da equipe (horários GMT−3): às 15:05–15:11 o modem abriu 3 sessões na 10664,
sem enviar nada ao conectar; cerca de 1 min depois mandava só o byte `0x16` e a sessão
terminava por EOF vindo do lado remoto. Depois de 3 ciclos parou de tentar. A equipe
ativou a ponte: 10664 = modem; 10665 = ponte bidirecional ao PC400, liberada só ao IP
do notebook de teste; resposta automática ao `0x16` ainda não implementada.

Após `toff` (18:35) e religamento, com `destdebug:NULL`:

| Teste | Resultado |
| --- | --- |
| Texto no TCP da 10665 | Saiu pela serial do modem em ~8 s, idêntico ao enviado |
| Texto pela serial | Chegou ao cliente TCP da 10665, idêntico |
| Duração da sessão | Ativa por 150 s sem queda (antes: ~2 min) |
| Byte `0x16` | Apareceu na serial às 18:39:17 e 18:40:19, ~62 s de intervalo; não chegou ao cliente TCP |
| `BOOT` ao `nimbus` | Entregue às 15:37:39 locais (18:37 UTC) |

O significado de `0x16` e o motivo de a sessão não cair desta vez seguem sem
confirmação. Falta o teste com o PC400 e o datalogger reais.

## Pendências

- O boot registra `[PWL-08] Erro no profile; Forcando padrao`; causa desconhecida.
- Houve dois boots seguidos (18:01 e 18:04 UTC) para um religamento informado; o
  segundo não se repetiu em 4 min de observação.
- Ainda não houve medição real do datalogger chegando ao novo destino.
- O teste usou a rota pública `teste-dispositivo`; os registros do modem ficam visíveis
  por 24 h com IMEI e ICCID.
