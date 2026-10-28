# Migração de telemetria — Pedro Osório/RS

Migrar a recepção e o armazenamento das medições de Dualbase/PCDWeb para um
servidor próprio, preservando a continuidade da estação. Contexto de referência:
**27/10/2026**; visita prevista: **28/10/2026**.

**Plano A:** manter o ABS CEL S instalado, cujo firmware foi customizado para
Dualbase, segundo o relato recebido. **Plano B:** avaliar o segundo ABS CEL S,
disponível em bancada com firmware diferente. Seu firmware não foi confirmado
como original. Mesmo modelo não garante intercambialidade.

O protocolo, o destino, a porta, as confirmações e a possibilidade de configurar
o modem instalado permanecem desconhecidos. Não há binário de seu firmware,
captura real nem receptor compatível validado. Não se presume API REST ou
Supabase. O receptor HTTP desta pasta é apenas um ensaio local.

## Documentação

- [Contexto técnico vigente](docs/contexto-tecnico-2026-10-27.md): cópia integral do documento recebido.
- [Ficha dos dois equipamentos](docs/equipamento.md): fatos, fontes e campos a coletar.
- [Roteiro da visita](docs/roteiro.md): preparação, sequência e conferência da operação.
- [Registro de investigação](docs/registro-investigacao.md): hipóteses, ensaios e interpretação.
- [Requisitos do receptor](docs/receptor.md): arquitetura proposta e contrato ainda pendente.
- [Plano de migração](docs/plano-migracao.md): decisão, validação e retorno à configuração original.
- [Evidências locais](dados/README.md): organização e limites dos registros.
- [Testes e preparação](docs/testes.md): verificação automática, instalação offline e matriz de campo.

`docs/referencia-original.txt` preserva o texto histórico anterior. Suas hipóteses
sobre modelo não identificado, API e Supabase foram substituídas pelo contexto
vigente; ele não orienta a execução atual.

## Preparar o ambiente

Python 3.10 ou superior, no PowerShell desta pasta:

O kit inclui o PySerial 3.5 para instalar sem internet e um preparador que também
executa os testes. Caminho recomendado no Windows:

```powershell
.\Preparar.ps1 -Offline
```

Preparação manual equivalente:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Somente inventário e comunicação serial precisam de `pyserial`. Neste computador,
use `python`; o lançador `py` não reconheceu a instalação anterior.

O conversor Prolific foi observado como **COM8**. Isso confirma o conversor,
sem demonstrar comunicação com o firmware. A porta pode mudar. O modem de bancada
estava sem alimentação externa apropriada; seu teste serial foi inconclusivo.
USB/DB9 não fornece a alimentação esperada pelo modem. Confira tensão, polaridade,
pinagem e revisão na etiqueta/manual antes de energizar.

## Scripts de diagnóstico

Os cinco scripts de diagnóstico mantêm sua numeração. Os scripts 06 e 07 verificam
o ambiente local e validam evidências. Use `--help` em qualquer um.
**Mudança de uso:** scripts 02, 03 e 04 exigem `--equipment pedro-osorio` ou
`--equipment bancada`; os dois scripts seriais também exigem `--baud`.
As saídas padrão de captura e análise são separadas por unidade.

Todo o trabalho fica nesta pasta: scripts em `scripts/`, testes em `tests/`,
documentação em `docs/`, dependência offline em `offline/` e evidências/relatórios
em `dados/`. Execute os comandos diretamente daqui.

### 01 — Inventário sem abrir portas

```powershell
.\.venv\Scripts\python.exe scripts\01_portas.py --output dados\capturas\portas.json
```

Usa arquivo novo e não conversa com o modem. Conectar DB9 não cria um novo
dispositivo no Windows: RS-232 não possui enumeração USB.

### 02 — Captura sem enviar bytes de aplicação

Depois de verificar alimentação, pinagem e parâmetros da interface de bancada:

```powershell
$portaConfirmada = 'COM8' # conferir no inventário atual
$baudConfirmado = [int](Read-Host 'Baud rate verificado no manual/configuração')
.\.venv\Scripts\python.exe scripts\02_captura_serial.py --equipment bancada --port $portaConfirmada --baud $baudConfirmado --seconds 60
```

O padrão de formato é 8N1, sem fluxo; ajuste `--data-bits`, `--parity` e
`--stop-bits` conforme a interface. **9600 bps e 8N1 não foram confirmados.**
DTR/RTS são solicitados como desativados antes da abertura, mas driver e adaptador
podem gerar transições. Para `--equipment pedro-osorio`, exige-se também
`--confirm-production-interface`, somente após verificar uma interface de
diagnóstico apropriada, autorização de acesso e impacto na operação. Isso não
substitui a verificação física nem autoriza desconectar o datalogger.

O JSONL preserva bytes, horários UTC e parâmetros. Silêncio é inconclusivo;
leituras binárias podem indicar protocolo binário ou parâmetros incorretos.
Blocos de leitura não equivalem a pacotes completos. Serial não é captura celular.

### 03 — Identificação AT condicional

Somente após confirmar documentalmente que a interface expõe AT:

```powershell
.\.venv\Scripts\python.exe scripts\03_identificar_firmware.py --equipment bancada --port $portaConfirmada --baud $baudConfirmado --confirm-at
```

Envia somente `AT`, `ATI`, `AT+CGMI`, `AT+CGMM` e `AT+CGMR`. Sem confirmação,
encerra antes de preparar a porta. Se `AT` não retorna `OK`, interrompe a sequência.
A resposta pode identificar apenas o módulo celular. O script não extrai firmware.
AT não é uma etapa automática da visita à estação em produção.

### 04 — Análise de arquivo offline

Quando houver uma imagem obtida por procedimento autorizado, com origem conhecida:

```powershell
.\.venv\Scripts\python.exe scripts\04_analisar_firmware.py dados\firmware\bancada\equipamento.bin --equipment bancada
```

Procura strings ASCII e UTF-16 LE/BE, incluindo Dualbase/PCDWeb, domínios, IPs e
indicadores de transporte. Salva hash SHA-256, tamanho, unidade e offsets em arquivo
novo. Não extrai, descomprime, decifra, altera ou grava firmware no hardware.
String encontrada é pista; sua ausência não exclui destino embutido. Nenhum binário
real do modem de Pedro Osório está disponível no contexto recebido.
O limite padrão é 64 MiB e 1000 pistas, ajustável por `--max-bytes` e
`--max-findings`. O relatório informa truncamento; limites excedidos são erros.

### 05 — Ensaio HTTP local

Para testar exclusivamente a recepção HTTP no computador:

```powershell
.\.venv\Scripts\python.exe scripts\05_receptor_teste.py
```

Em outro terminal:

```powershell
Invoke-RestMethod -Uri 'http://127.0.0.1:8080/telemetria' -Method Post -ContentType 'application/json' -Body '{"sensor":"teste","valor":25.3}'
```

Aceita POST `/telemetria`, exige `Content-Length`, limita o corpo a 1 MiB e grava
os bytes antes de responder `200 {"ok": true}`. Esse retorno é provisório, sem
relação comprovada com o ACK exigido pelo modem. O log permite acrescentar registros.
Sem TLS/autenticação, decodificação de medições ou banco de dados, não constitui
o receptor de produção. TCP, UDP, FTP, MQTT ou protocolo próprio exigirão outro
receptor, conforme evidência. `127.0.0.1` só atende localmente; um modem celular
precisa de destino alcançável na rede apropriada.
`GET /health` informa apenas que o ensaio HTTP está ativo. O corpo é sincronizado
com o disco antes do 200; erro de gravação/sincronização retorna 500. Um log existente
sem quebra de linha final é recusado para preservar o arquivo incompleto.

## Verificações sem hardware

```powershell
.\Verificar.ps1
```

O comando executa todas as verificações e salva um relatório em dados/verificacoes/.
`-Inventario` inclui enumeração dos conversores sem abrir portas. Para executar
somente a suíte: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`.
Os detalhes e a validação de evidências estão em [testes.md](docs/testes.md).

Os testes usam serial simulada, imagens sintéticas e HTTP em loopback. Não validam
compatibilidade elétrica, firmware real, conectividade celular ou migração.
Nenhum script realiza reset, atualização de firmware ou mudança de destino.
Comece pelo roteiro e registre também resultados vazios, erros e etapas não feitas.

