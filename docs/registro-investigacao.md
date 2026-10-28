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
| H1 | Destino configurável em memória persistente | Em aberto | Leitura suportada de host/IP/porta/protocolo e confirmação posterior em ensaio reversível |
| H2 | Destino embutido no firmware | Em aberto | Imagem de origem autorizada, hash/offset e correlação com comportamento real; strings isoladas não bastam |
| H3 | Protocolo proprietário Dualbase | Em aberto | Mensagens reais, enquadramento, integridade, autenticação, ACK e reenvio documentados |
| H4 | Provisionamento remoto define ou restaura o destino | Em aberto | Documentação/configuração e observação autorizada do provisionamento; verificar se uma mudança local seria revertida |
| H5 | Interface serial não expõe comandos AT | Em aberto | Manual da revisão/interface e identificação suportada; silêncio isolado não decide |

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

