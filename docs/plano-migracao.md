# Plano de decisão e migração

Proposta baseada no contexto de 27/10/2026; depende dos resultados da visita de
28/10/2026. **Não há autorização operacional implícita neste plano para alterar
a estação em funcionamento.** Nesta etapa, preparar e coletar evidências.

## Escolha do caminho

| Caminho | Condições para escolher | Evidência que ainda falta |
| --- | --- | --- |
| Plano A1: manter modem e firmware, alterar configuração | Leitura e alteração suportadas do destino; exportação e restauração conhecidas; receptor compatível | Interface, host/porta/protocolo, contrato e ensaio |
| Plano A2: manter modem e implementar receptor especializado | Destino redirecionável e protocolo próprio compreendido | Enquadramento, autenticação, ACK, integridade e reenvios |
| Plano B: substituir pelo ABS CEL S de bancada | Plano A inviável ou inadequado, com motivo documentado; alternativo compatível | Revisão, fonte/polaridade, pinagem, datalogger, rede, buffer e ensaio real |
| Integração transitória pelo PCDWeb | Existe exportação/encaminhamento autorizado que atende às medições | Funcionalidade, acesso, contrato e limites de dependência |

Prioridade: Plano A, quando viável e seguro. Falha do configurador ou serial
silenciosa não bastam para descartá-lo. Não copiar firmware entre unidades por
suposição. Destino fixo, proteção de leitura ou protocolo sem documentação exigem
análise posterior, inclusive de procedimentos oficiais e permissões aplicáveis.

## Preparação antes de qualquer alteração de produção

1. Preservar configuração original, fotos, versões e parâmetros de rede em local
   privado; registrar hashes e procedimento suportado de restauração.
2. Confirmar compatibilidade com datalogger/sensores e o contrato de transmissão.
3. Implementar o receptor adequado e confirmar que o destino é alcançável pela
   rede celular. Definir autenticação e confirmação de recebimento.
4. Validar primeiro em bancada. A unidade alternativa tem firmware diferente;
   seu sucesso não comprova que a principal usa o mesmo protocolo.
5. Acordar janela, responsável, prazo de rollback e cobertura das medições durante
   o ensaio. Registrar limitações da fila/buffer para evitar perda.
6. Verificar autorização de alteração da integração/customização e suporte à
   recuperação antes da mudança operacional.

## Critérios propostos para ensaio

Os números abaixo são **critérios de aceite propostos**, não resultados observados
nem garantias do equipamento. Definir a duração a partir da cadência real.

| Verificação | Predicado de aceite |
| --- | --- |
| Recepção normal | Pelo menos 3 ciclos consecutivos completos no destino de teste, cada um correlacionado à fonte |
| Integridade | 100% das medições esperadas desses ciclos presentes; nenhuma diferença de canal, valor, unidade ou horário além da precisão documentada |
| Confirmação | 100% das mensagens que exigem ACK recebem resposta válida no prazo observado/documentado |
| Reenvio e duplicata | Reenviar uma mensagem controlada resulta em 1 medição lógica, mantendo rastreabilidade das tentativas |
| Perda de conectividade | Em bancada, interromper por intervalo acordado; recuperar 100% do conjunto esperado dentro da capacidade de buffer comprovada |
| Mensagem inválida/incompleta | Não produzir medição válida nem confirmação enganosa; falha rastreável e bytes preservados |
| Restauração | Configuração original restaurada por procedimento conhecido e ao menos 1 nova medição confirmada no destino anterior |
| Operação | Limite offline, responsável, backup e restauração testados e registrados antes da migração definitiva |

Se buffer ou identidade das mensagens não forem conhecidos, o ensaio de perda ou
deduplicação permanece pendente. Não inventar um mecanismo para considerá-lo aprovado.
Testes com interrupção são de bancada; uma interrupção de produção requer plano
específico para a continuidade das medições.

## Execução futura e rollback

Na janela acordada, registrar a última medição e configuração em uso; aplicar
somente a mudança validada; acompanhar receptor, ACK e medições. Comparar o conjunto
esperado com o persistido. O intervalo de comparação e o limite tolerável de atraso
devem constar no registro antes do início.

Rollback se o receptor não confirmar no prazo, se houver lacunas/valores incorretos
ou se surgir comportamento não previsto: restaurar a configuração original ou
reinstalar a unidade original conforme o procedimento testado. Não realizar reset
ou regravação improvisada. Confirmar ao menos uma nova medição no PCDWeb e registrar
lacunas, duplicatas, horários e responsável pela reconciliação.

Sem cumprir os critérios aplicáveis ou documentar uma limitação aceita pelo
responsável, manter a decisão em aberto. Após o corte definitivo, monitorar
transmissões, reprocessar evidências quando necessário e testar recuperação.

