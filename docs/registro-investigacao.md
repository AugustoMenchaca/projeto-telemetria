# Registro de investigação

Estado de referência: **27/10/2026**, segundo o [contexto recebido](contexto-tecnico-2026-10-27.md).
A preparação dos scripts não constitui ensaio com hardware.

## Observação local de preparação — 27/10/2026

O inventário de 28/10/2026 às 01:12:54 UTC (27/10 às 22:12:54, UTC−03:00)
enumerou somente COM3–COM6, descritas pelo Windows como portas Bluetooth.
O conversor Prolific/COM8 não apareceu nesse inventário. Nenhuma porta foi aberta;
isso não demonstra defeito no conversor nem muda o registro histórico de COM8.
Repetir o inventário com o conversor conectado antes do ensaio físico.

O relatório local está em dados/verificacoes/, separado das evidências dos modems.
A suíte de software usa simulações, loopback e binários sintéticos; seu resultado
não constitui leitura de configuração ou análise do firmware de Pedro Osório.

## Ensaio serial em Pedro Osório — 28/10/2026

Unidade `pedro-osorio`, LED ON e LINK acesos, datalogger desconectado do DB9 do
modem pelo operador, notebook na bateria. Logs em `dados/capturas/pedro-osorio/`.

| Etapa (UTC) | Procedimento | Resultado |
| --- | --- | --- |
| 14:16–14:21 | Escuta 115200 e 9600 8N1; leitura Modbus ABS (end. 200, função 04, 65000–65002) nas 8 velocidades do manual | 0 bytes em todas; PL2303 caiu do USB (erro 433) em parte das aberturas, nas portas USB 1-2 (COM8) e 1-1 (COM7) |
| 14:26–14:33 | Envio periódico observando o LED RX, com janelas por horário | RX pisca em 9600 e não pisca em 115200 (janela A de 115200 saiu 11 s atrasada; a observação válida é a das 14:28) |
| 14:42–14:44 | `!CMD->destdebug:SERIAL%`, `!CMD->status%`, `!CMD->help%`, `!CMD->status%`, `!CMD->destdebug:NULL%` | Resposta completa ao `status`; `help` não reconhecido; debug devolvido a NULL |

Protocolo, conforme e-mails da dualBASE (set/2025) e confirmado no ensaio: texto
`!CMD-><comando>%`, 9600 8N1, sem fim de linha. Respostas só saem na serial
com `destdebug:SERIAL`; antes de religar o datalogger, enviar `destdebug:NULL`.

Configuração lida por `status` (identificadores do modem e do SIM ficam só no log privado):

| Campo | Valor |
| --- | --- |
| Programa | `TCelDB_V2.0`, baudrate 9600 |
| URL de dados (`linhadados`) | `http://recepcao.dualbase.com.br/recep/recep.php?cmd=` |
| Canal de portas (`url_portas` / `porta`) | `pcdnaweb.com.br` / `10664` |
| URL de acesso (`url_acesso`) | `pcdnaweb.com.br:10665` (uma leitura veio `50665`, por erro de bit) |
| APN | `zap.vivo.com.br:vivo:vivo`; rede 3G, MCC 724 / MNC 06 |
| Sinal / IP | 9–11 / "Não conectado" nas duas leituras; o modem reiniciou por volta de 14:36 UTC |

O link serial corrompeu bytes recebidos: em todos os casos o bit 2 passou de 0 a 1
(`1`→`5`, espaço→`$`, `c`→`g`, `S`→`W`). Qualquer escrita de parâmetro precisa
ser conferida por mais de uma leitura de `status`. Os campos de `status` têm o mesmo
formato dos comandos de escrita conhecidos (`porta:`, `apn:`), o que sugere
`linhadados:` como comando de troca do destino. Isso não foi testado nem confirmado.

Pendências antes de trocar o destino: resposta (ACK) esperada pelo modem para
apagar a mensagem do buffer; função do canal `pcdnaweb.com.br:10664/10665` e
possibilidade de reversão remota; servidor HTTP público (sem TLS) para receber
GET em `?cmd=`; acordo sobre a continuidade do PCDWeb; e o próprio modem sem IP.
`!CMD->toff%` enviado às 14:51:26 UTC, a pedido do operador, antes da troca do cabo.

### Endpoints testados sem o modem — 28/10/2026, 14:56–14:59 UTC

Requisições do notebook com dados fictícios (estação `1000`, IMEI/ICCID zerados no
`nimbus`). Respostas em `dados/analises/endpoints-*/`.

| Destino | Requisição | Resposta |
| --- | --- | --- |
| `recepcao.dualbase.com.br/recep/recep.php` | sem `cmd` / `cmd` vazio | 200, corpo vazio |
| idem | `cmd=1000:teste:abc123` e linha no formato do modem | 200, corpo `|` |
| idem | `cmd=xyz` | 500, corpo vazio |
| `pcdnaweb.com.br:10664` e `:10665` (mesmo IP do receptor) | conexão TCP, só escuta | aceita e fica em silêncio |
| `nimbus.nucleodeprevisao.com/teste-dispositivo/receber` | HTTPS, com `variavel` ou `cmd` | 200, JSON `{"ok":true,...}`; linha gravada intacta |
| idem | HTTP | 301 para HTTPS |

### Envio de teste pelo modem — 28/10/2026, 16:41–16:47 UTC

Após religamento manual (16:28 UTC) e antena nova, sinal 28–29 e RSCP −55 dBm;
`status` mostrava "IP: Não conectado" e `NOCONN` sem nada a enviar. Comandos:
`destdebug:SERIAL`, `LMPSTGON` (responde "Limpeza de string ativada", desliga com
`lmpstgoff`) e `dbsd:1000:teste:abc123`. O modem armazenou e, 9 s depois, enviou:

```text
GET http://recepcao.dualbase.com.br/recep/recep.php?cmd=1000:teste:abc123,iccid=<ICCID>,imei=<IMEI>,porta=10664,sinal=28:TCelDB_V2.0:0
Status envio: true   (2 s)
```

A conexão de dados é aberta sob demanda: a rede Vivo e o chip funcionam. Debug
deixado em SERIAL ao fim do ensaio.

Às 16:52 UTC, `version` e `url_portas:pcdnaweb.com.br` (mesmo valor já gravado)
retornaram "Comando nao reconhecido"; o `status` seguinte não mudou. Os rótulos
do `status` não são nomes de comando, e `linhadados:` não deve ser presumido como
comando de troca. Segundo o manual de operação (03/10/2025), `pcd.dualbase.com.br:10665`
é o acesso remoto ao datalogger pelo PC400 (PakBus 1), e a dualBASE oferece um
WebService com usuário próprio; a documentação dele não veio no PDF.

A folha de instrução pública do TCelDB (dualBASE, versão 02.050724, em
`dualbase.com.br/suporte`) documenta o mesmo app sobre módulo Cinterion EHS6. Ela
declara a URL de envio obrigatória, mas só publica o comando da APN. Comandos
listados: `apn:`, `dbsd:`, `emsg` (E = buffer vazio, F = não vazio), `status`,
`destdebug:NULL|PRINT|SERIAL`, `baudrate:9600|115200`, `quit` (para o Java e
devolve o modo AT, em geral a 115200), `iccid`, `resetconfig` e `toff`. Em modo AT:
`AT^SJAM=4`/`=5` (apps instalados/em execução), `AT^SCFG="Userware/Autostart"`
e `AT^SMSO`. `resetconfig` não deve ser usado sem plano de restauração.

### Comando de troca do destino — 28/10/2026, 17:01–17:04 UTC

Cada comando termina com `E` quando executado e com `F` + `[PWL-33] Comando nao
reconhecido` quando o nome não existe. Nomes testados regravando o valor atual:
`porta:10664` aceito (`[PWL-27] Armazenando porta principal`); `url:` recusado;
`urldados:` aceito sem linha própria de log. Confirmação reversível:

| Passo | Comando | `linhadados` lido (2 leituras) |
| --- | --- | --- |
| 1 | `!CMD->urldados:http://recepcao.dualbase.com.br/recep/recep.php?teste=1&cmd=%` | `...recep.php?teste=1&cmd=` |
| 2 | `!CMD->urldados:http://recepcao.dualbase.com.br/recep/recep.php?cmd=%` | `...recep.php?cmd=` (original restaurado) |

O valor aceita `:` e `?`/`&` sem truncar. A linha legível do debug mostra
`regepcao` por erro de bit; a linha `linhadados:` veio correta nas quatro leituras.

### Destino `nimbus` testado pelo modem — 28/10/2026, 17:07–17:12 UTC

Mensagem de teste `dbsd:1000:teste_https`, com o datalogger desconectado:

| URL gravada | Resultado no debug |
| --- | --- |
| `https://nimbus.nucleodeprevisao.com/teste-dispositivo/receber?cmd=` | `[CWE-07] IO Exception: -313 SSL-Error: revcd alert fatal error`; nova tentativa a cada ~11 s, sufixo `:0`, `:1`... conta as tentativas |
| `http://` na mesma rota | 301 do LiteSpeed; o modem não segue o redirecionamento, lê o corpo HTML como resposta (`[CWE-04] Linha erro: {60}{33}{68}...` = `<!DOCTYPE html>`) e registra `[CWE-03] Linha invalida` |

Nenhum registro chegou ao painel do `nimbus`. `emsg` respondeu `F`: a mensagem
segue na fila, sem perda. Com a dualBASE, a resposta `200` com corpo `|` produziu
`Status envio: true`; o modem valida o corpo da resposta.

Às 17:38 o `nimbus` passou a responder HTTP sem redirecionar, com `200` e corpo `|`.
O modem continuou sem tentar até `toff` (17:41) e religamento manual. No boot
(17:42) enviou os 4 pendentes e um `BOOT`, todos com `Status envio: true`, como
`POST` com corpo vazio. Procedimento e requisitos consolidados em
[modem-tceldb.md](modem-tceldb.md).

O `nimbus` aceita só TLS 1.2/1.3, com certificado Let's Encrypt `YE1`. O receptor
dualBASE responde `|` ao aceitar e 500 quando não interpreta; não se sabe se o
modem exige o `|` ou apenas o 200. O painel `teste-dispositivo` é público e
mostraria IMEI, ICCID e IP de origem de um envio real.

## Fatos relatados e limites

| Evidência disponível | O que estabelece | O que permanece pendente |
| --- | --- | --- |
| Relato da estação de Pedro Osório | ABS CEL S em operação no ecossistema Dualbase/PCDWeb, com firmware customizado | Versão, configuração, transporte e receptor efetivo |
| Relato do equipamento alternativo | Segundo ABS CEL S com firmware diferente | Origem do firmware e compatibilidade com o datalogger |
| Prolific reconhecido como COM8 | Conversor USB/RS-232 disponível no Windows naquele teste | Comunicação com o modem; COM atual deve ser conferida |
| Bancada sem alimentação externa apropriada | Teste anterior não foi conclusivo | Tensão/polaridade da revisão e ensaio energizado |
| Servidor próprio disponível | Existe infraestrutura informada | Endereço, rede, capacidade, autenticação e receptor |
| Visita prevista para 28/10/2026 | Há uma oportunidade de coleta física | Resultados ainda não existem |

Não há binário do modem principal, captura celular, configuração exportada,
resposta AT principal ou transmissão validada para o novo servidor. Nenhum
protocolo foi confirmado; não presumir API REST, HTTP nem acesso direto a PCDWeb.
O texto anterior sobre Supabase permanece somente como histórico arquivado.

## Hipóteses de trabalho

| ID | Hipótese | Estado | Evidência / experimento para decidir |
| --- | --- | --- | --- |
| H1 | Destino configurável em memória persistente | Indício forte (28/10) | `status` lê a URL de dados como parâmetro (`linhadados`); comando de escrita e persistência ainda não confirmados |
| H2 | Destino embutido no firmware | Enfraquecida (28/10) | Destino aparece como parâmetro lido em `status`; valor padrão pode estar no app Java |
| H3 | Protocolo proprietário Dualbase | Parcial (28/10) | Transporte HTTP GET com a linha em `?cmd=`, segundo e-mail da dualBASE e `status`; ACK esperado desconhecido |
| H4 | Provisionamento remoto define ou restaura o destino | Em aberto, com indício | `status` mostra canal `pcdnaweb.com.br`, porta 10664 e URL de acesso porta 10665; função não confirmada |
| H5 | Interface serial não expõe comandos AT | Indício (28/10) | DB9 aceita comandos `!CMD->...%` do app dualBASE; AT aparece apenas executado internamente (`AT^SMONI`) |

Investigar também provisionamento remoto e serviços intermediários. Exportação
ou encaminhamento autorizado pelo PCDWeb pode ser uma etapa transitória, mas sua
existência e os acessos necessários ainda não foram confirmados.

## Registro de cada experimento

Copie o bloco para um novo ensaio, preservando os registros anteriores.
Não cole senhas, tokens ou identificadores sensíveis neste arquivo.

```text
ID / responsável:
Unidade: pedro-osorio ou bancada
Data/hora UTC / data/hora local com fuso:
Questão e hipótese:
Estado inicial (alimentação, LEDs, cabos, datalogger e última medição):
Interface / pinagem / parâmetros / origem da confirmação:
Permissão de acesso e condições para observação sem interromper produção:
Procedimento ou comando exato:
Evidência original (caminho privado, hash e unidade de origem):
Resultado medido (duração, bytes, versão, campos lidos, erro):
Interpretação: o que confirma e o que não confirma:
Próximo experimento que distingue as hipóteses:
Alteração realizada (ou nenhuma) / restauração / resultado:
Estado final / nova medição / etapas não executadas:
```

Para calcular hash de uma exportação, trabalhe sobre o original preservado:

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath 'dados\configuracoes\pedro-osorio\exportacao-original.arquivo'
```

O nome é ilustrativo; não existe uma exportação real nessa pasta no estado recebido.

## Entregas após a visita

| Entrega | Evidência mínima | Situação |
| --- | --- | --- |
| Inventário técnico | Ficha por unidade, fotos, interface, versões e alimentação | Modelo inicial documentado; coleta de campo pendente |
| Relatório de diagnóstico | Ensaios, arquivos/hash, medidas, limitações e estado final | Modelo acima; resultados pendentes |
| Análise de firmware/protocolo | Configuração real ou binário/captura de origem conhecida | Ferramenta offline disponível; análise real pendente |
| Decisão arquitetural | Critérios do plano de migração preenchidos | Em aberto |
| Especificação do receptor | Contrato real, ACK, segurança, sensores e horários | Requisitos preliminares em receptor.md |
| Plano de migração | Ensaio, restauração, monitoramento e critérios numéricos acordados | Proposta em plano-migracao.md; execução pendente |
| Implementação/validação | Medições reais recebidas, persistidas e conferidas | Ainda não realizada |

