# Verificação do kit e testes de campo

O kit automatiza testes locais de software e confere a integridade dos arquivos.
Testar todos os caminhos de software não demonstra compatibilidade elétrica,
suporte AT ou protocolo do modem. Nenhum teste automático abre uma porta COM real.

## Preparação e comando único no Windows

Python 3.10 ou superior precisa estar instalado. A pasta offline/ contém a wheel
do PySerial 3.5, com hash em requirements.txt. Na pasta de trabalho, a instalação
da dependência pode ocorrer sem internet:

```powershell
.\Preparar.ps1 -Offline
```

O preparador cria .venv quando necessário, instala a dependência e executa a
verificação. Se a política local de execução impedir scripts PowerShell, os
comandos Python do README continuam disponíveis; não é necessário alterar a
política global do computador.

Para repetir a verificação, a partir de qualquer diretório:

```powershell
.\Verificar.ps1
```

Ou, na pasta do projeto:

```powershell
.\.venv\Scripts\python.exe scripts\06_verificar_kit.py
```

O script 06 verifica versão do Python/PySerial, sintaxe das fontes, documentos e
links, hash da dependência offline, dependências e toda a suíte de
testes. Guarda o resultado e as saídas em dados/verificacoes/. O relatório identifica
explicitamente software-local, hardware não testado e migração pendente. Não
sobrescreve relatórios. Código 0 indica verificação local aprovada; 1 indica falha.

Para incluir o inventário real de conversores, sem abrir a serial:

```powershell
.\Verificar.ps1 -Inventario
```

## Matriz de testes locais

| Área | O que a suíte exercita | Limite |
| --- | --- | --- |
| Ambiente e comandos | Ajuda de todos os scripts sem PySerial, argumentos, códigos de erro e dependência ausente | Python deve estar instalado no computador de destino |
| Inventário | Conversor simulado, lista vazia e arquivo exportado, sem abertura de serial | Presença de COM não identifica o firmware |
| Serial | Preservação de todos os valores de byte, silêncio, interrupção, desconexão e arquivo já existente | Usa serial simulada e PySerial loop:// virtual |
| Condições de acesso | Unidade/baud obrigatórios, confirmação da interface principal e AT condicional | Flags declaram condições; não as verificam eletricamente |
| AT | Respostas fragmentadas, OK/ERROR, erros estendidos, limite, escrita parcial e desconexão | Respostas artificiais não provam suporte na DB9 |
| Firmware | ASCII/UTF-16 LE/BE, offsets/hash, arquivo vazio, limites e truncamento explícito | Binários sintéticos; nenhuma extração ou análise real do principal |
| HTTP | Bytes binários, limites, enquadramento inválido, timeout, corpo incompleto, concorrência e falha de gravação/sincronização | Somente HTTP em loopback e resposta provisória |
| Evidências | Base64/hex/hash, contagens, término, timestamps e origem; arquivos corrompidos/incompletos | Integridade interna não confirma veracidade da medição |
| Ambiente local | Dependência offline com hash e sintaxe dos preparadores PowerShell | Python deve estar instalado no computador utilizado |

## Conferir os arquivos coletados

Exemplo com caminho substituído pelo arquivo real:

```powershell
.\.venv\Scripts\python.exe scripts\07_validar_evidencias.py dados\capturas\bancada\captura.jsonl --output dados\analises\validacao-captura.json
```

Aceita inventário JSON, capturas serial/AT JSONL, análise de firmware JSON e log
HTTP JSONL. Confere bytes, metadados e resumo aplicáveis. Em análise de firmware,
para conferir também hash e offsets contra o binário original:

```powershell
.\.venv\Scripts\python.exe scripts\07_validar_evidencias.py dados\analises\bancada\firmware.json --source dados\firmware\bancada\equipamento.bin
```

Código 0: estrutura/integridade válidas. Código 1: arquivo inválido, incompleto ou
inacessível. Código 2: ensaio inconclusivo, como silêncio, interrupção, erro serial
registrado ou arquivo vazio. Um arquivo válido não prova o destino de transmissão.
Logs legados sem unidade/resumo podem ser rejeitados; preserve-os e registre a
origem no relatório, sem inventar metadados para fazê-los passar.

## Organização da pasta de trabalho

Use os arquivos diretamente nesta pasta. `Preparar.ps1` prepara o ambiente e
`Verificar.ps1` executa a verificação. Scripts e testes ficam em scripts/ e tests/;
documentação em docs/; dependência para instalação sem internet em offline/.
Os relatórios JSON e o histórico ficam em dados/verificacoes/. Evidências reais
permanecem em dados/, separadas por equipamento, com acesso privado.

## Matriz pendente para a visita e a bancada

| Verificação física/operacional | Unidade | Evidência mínima | Situação inicial |
| --- | --- | --- | --- |
| Alimentação, polaridade, revisão e pinagem | Ambas, separadamente | Etiqueta/manual e medidas com identificação da unidade | Pendente |
| Serial energizada | Bancada primeiro | Parâmetros confirmados e captura com resultado, mesmo vazio | Teste anterior inconclusivo |
| Identificação do firmware/configurador | Ambas | Versão e leitura suportada, sem alterar produção | Pendente |
| Continuidade na visita | Pedro Osório | Última medição antes e nova medição depois, horário/fuso e cabos/LEDs | Pendente |
| Transporte, mensagens, autenticação e ACK | Principal e depois alternativo | Contrato real correlacionado à origem | Pendente |
| Compatibilidade do alternativo com datalogger | Bancada | Ensaio elétrico e funcional controlado | Pendente |
| Reenvio, buffer, queda e retorno | Bancada | Conjunto esperado recuperado, duplicatas e limites medidos | Pendente |
| Destino próprio e restauração | Unidade apropriada, após plano | Critérios de plano-migracao.md atendidos e retorno comprovado | Pendente |

Use o roteiro e o registro de investigação para guardar o resultado de cada etapa,
inclusive falhas, limitações, etapas não executadas e o próximo experimento.
