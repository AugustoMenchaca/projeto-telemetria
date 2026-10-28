# Evidências locais por equipamento

Unidades: `pedro-osorio` (ABS CEL S em produção, firmware customizado Dualbase)
e `bancada` (segundo ABS CEL S, firmware diferente e origem não confirmada).
Não misture capturas, configurações ou imagens das duas unidades.

- `capturas/`: inventário do conversor; scripts 02/03 criam subpastas por unidade.
- `configuracoes/<unidade>/`: exportações originais e imagens do configurador.
- `firmware/<unidade>/`: imagens obtidas por procedimento autorizado, origem registrada.
- `analises/<unidade>/`: relatório do script 04, com unidade, hash, offsets e pistas.
- `receptor/`: log de ensaio HTTP; não comprova o protocolo da estação.
- `verificacoes/`: relatórios da suíte local e do inventário opcional, sem abrir serial.

Use um ID por ensaio, por exemplo `20261028T120000Z-pedro-osorio-01`. Os scripts
geram nomes UTC únicos por padrão; saídas de captura/análise não sobrescrevem
arquivos. `--output` personalizado deve preservar a separação por unidade.
Arquivos legados não recebem uma unidade automaticamente: confirme sua origem.

Os arquivos de evidência são ignorados pelo Git. Isso não substitui controle de
acesso e backup privado. Não publique tokens, senhas, SIM/ICCID, identificadores
sensíveis ou capturas sem revisão. Preserve originais; use cópias para análise.
A cópia do contexto em `docs/` é documentação, sem capturas reais anexadas.

JSONL contém um objeto por linha. Em capturas, o evento `start` identifica a unidade,
a serial e as confirmações declaradas; `rx` preserva bytes; `end` registra término,
inclusive captura vazia ou erro de abertura. Nos ensaios AT, `tx_attempt` e
`at_response` preservam consulta e resposta. `at_rx` preserva também cada bloco
antes de uma possível falha de leitura AT. `hex` e `base64` são os bytes;
`text` é aproximação de leitura. Os blocos não são necessariamente mensagens.
No receptor, `body_base64` preserva o corpo HTTP; não identifica nem autentica modem.

Horários dos scripts são os do computador em UTC. Registre também horário local
com fuso e o horário do dispositivo quando disponível, sem equipará-los.
Ainda não há evidência de captura real ou análise de binário do modem principal.
Use o script 07 para conferir integridade dos arquivos; os comandos e códigos de
saída estão em [testes](../docs/testes.md). Todos os relatórios permanecem nesta
pasta de trabalho; verificações anteriores são preservadas em verificacoes/.

