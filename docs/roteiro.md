# Roteiro da visita — 28/10/2026

Objetivo: coletar evidências para escolher entre preservar o modem de Pedro Osório
e validar o alternativo. A primeira visita prioriza diagnóstico e continuidade;
a migração não precisa ocorrer nessa data. Contexto de referência: 27/10/2026.

## Preparação

- Notebook Windows, Python/PySerial e scripts verificados sem hardware.
- Conversor Prolific USB/RS-232, cabos/adaptadores DB9 adequados e multímetro.
- Manual da revisão disponível offline e Configurador Celular da ABS.
- Pasta privada para fotos, exportações e capturas separadas por unidade.
- Contato do responsável e acesso autorizado ao PCDWeb, se disponível.
- Para a bancada: fonte/cabo compatíveis, com tensão e polaridade confirmadas.

Não há binário do firmware principal. Não realizar extração invasiva, reflashing,
reset de fábrica, escrita em memória ou troca de firmware nesta primeira visita.
Não alterar destino nem desconectar alimentação/cabeamento de produção sem plano
e conhecimento de sua função. Leitura por software também depende da identificação
correta da interface; abrir serial pode alterar sinais elétricos.

## Sequência e evidências

| Etapa | Procedimento | Critério verificável / registro |
| --- | --- | --- |
| 1. Estado inicial | Fotografar etiqueta, conexões, alimentação e LEDs; identificar sensores/datalogger; anotar última medição no PCDWeb | Fotos vinculadas a `pedro-osorio`, horário/fuso e medição inicial registrados |
| 2. Interface | Identificar porta de diagnóstico, padrão elétrico, pinagem e parâmetros; inventariar conversor sem abrir a porta | Fonte de pinagem/parâmetros registrada; nenhum cabo de função desconhecida removido |
| 3. Configurador | Se compatível, consultar identificação, versão e parâmetros; preservar exportação original | Reconhecimento ou falha documentados, campos lidos e arquivo original com hash quando houver |
| 4. Observação serial | Somente em interface apropriada, capturar sem bytes de aplicação; registrar duração, bytes e parâmetros | Log por unidade, inclusive vazio/erro; nenhum comando AT automático |
| 5. Encerramento | Conferir energia, LEDs e conexões; acompanhar uma nova medição no PCDWeb | Horário de chegada registrado; se não chegar no prazo esperado, registrar incidente e acionar responsável |

Prefira a consulta suportada de configuração antes de tentar comandos. Se o
configurador não reconhecer o firmware customizado, registre versão e erro;
isso não comprova bloqueio ou inviabilidade. Sem interface segura identificada,
encerre a parte serial e continue a inspeção/documentação.

AT só se aplica após evidência de suporte da porta e avaliação do impacto.
O script 03 exige `--confirm-at`; para a unidade principal exige também a
confirmação de interface de produção. Nenhum desses flags comprova compatibilidade.
Captura serial não revela necessariamente destino ou tráfego celular.

## Como interpretar os resultados

| Observação | Limite da evidência | Próximo experimento |
| --- | --- | --- |
| Configurador reconhece | Demonstra alguma compatibilidade | Consultar versão e leitura de destino, sem salvar alterações |
| Lê host/porta | Sugere parâmetro acessível | Confirmar uso em transmissão real e procedimento de restauração |
| Não reconhece | Pode ser interface, parâmetros ou protocolo diferente | Conferir manual, versão e documentação da customização |
| Texto serial legível | Pode ser diagnóstico, datalogger ou resposta | Correlacionar horários e eventos, preservando bytes |
| Bytes binários | Pode ser protocolo ou parâmetros incorretos | Confirmar configuração serial e analisar cópia da captura |
| Nenhum byte | Inconclusivo | Verificar alimentação, pinagem, modo de operação e atividade |
| String de endpoint no binário futuro | Não demonstra uso em execução | Correlacionar com configuração e transmissão autorizada |
| Nenhuma string | Não exclui destino embutido | Investigar compressão/configuração externa por via suportada |

## Registro de encerramento

```text
Visita / responsáveis / unidade:
Início e fim (UTC e horário local com fuso):
Última medição antes / nova medição depois (horário da medição e da consulta):
Cadência esperada e prazo de espera / origem dessa informação:
Energia, LEDs e cabos antes/depois:
Procedimentos executados / arquivos e hashes:
Etapas não feitas e motivo:
Anomalia / ação do responsável / situação ao sair:
Pendências que impedem escolher Plano A ou Plano B:
```

Sem cadência conhecida ou acesso às medições, declare a continuidade não
verificada; não conclua sucesso apenas pelos LEDs. Registre o prazo acordado com
o responsável para acompanhamento e a pessoa que fará a conferência posterior.

