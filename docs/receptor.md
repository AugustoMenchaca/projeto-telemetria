# Receptor no servidor próprio — requisitos preliminares

O protocolo e o modelo de dados definitivo dependem da investigação de campo.
Este documento registra requisitos e lacunas; não atesta compatibilidade do
script HTTP com o ABS CEL S ou com Dualbase/PCDWeb.

## Caminho dos dados

Atual, conforme relato (datalogger e tecnologia celular ainda a confirmar):

```text
Sensores → datalogger/controlador? → ABS CEL S customizado
        → rede celular → infraestrutura Dualbase → PCDWeb → consulta/armazenamento
```

Desejado:

```text
Sensores/datalogger → ABS CEL S → rede celular → receptor compatível
                  → mensagem bruta → decodificação/validação → banco → API/consulta
```

A API de consulta posterior pode ser HTTP mesmo quando a entrada de telemetria
usa TCP, UDP ou outro transporte. Não confundir esses dois contratos.
Também não está confirmado se há um receptor intermediário antes do PCDWeb.

## Contrato a descobrir

| Campo | Valor / evidência necessária |
| --- | --- |
| Componente que inicia conexão e provisionamento | A confirmar no equipamento/configuração |
| Destino efetivo, DNS/IP, porta e transporte | A confirmar; não presumir HTTP, MQTT ou TCP |
| Sessão, enquadramento e mensagens incompletas | Capturas reais; limites e reconstrução de mensagens |
| Identificação de estação, sensores e canais | Datalogger e exemplos reais |
| Autenticação e proteção da comunicação | Identificar mecanismo sem publicar os segredos |
| Estrutura, codificação, checksum/CRC | Exemplos reais íntegros e inválidos, com valores sensíveis ocultados |
| Timestamp do dispositivo, fuso e relógio | Comparação com observação em campo |
| Unidades, escala, precisão e valores válidos | Documentação dos sensores e datalogger |
| ACK/resposta, sequência e prazo | Resposta aceita pelo modem e efeito de atraso/falha |
| Cadência, fila offline, reconexão e reinicialização | Medidas em ensaio controlado |
| Duplicatas, ordem e identidade da mensagem | Estratégia compatível com sequência/IDs realmente existentes |
| Exportação/encaminhamento pelo PCDWeb | Disponibilidade e acesso autorizado a confirmar |

## Requisitos de implementação após confirmar o contrato

- Receber o transporte comprovado; limitar tamanhos e tratar mensagens truncadas.
- Autenticar o equipamento e validar enquadramento/integridade conforme o contrato.
- Preservar bytes originais, origem, horário UTC de recebimento e hash para auditoria
  e reprocessamento. Hash do conteúdo sozinho não define identidade de uma medição.
- Separar horário observado do dispositivo de horário do servidor; manter a origem
  e o fuso da interpretação. Não adivinhar unidade/escala dos valores.
- Decodificar com versão identificada, validar canais e valores e registrar falhas
  sem descartar a evidência bruta. Definir quarentena e política de retenção.
- Persistir histórico e rastrear a mensagem de origem. Processar retransmissões
  de modo idempotente com chave determinada pelo protocolo.
- Enviar confirmação compatível e no prazo exigido. Definir quando confirmar
  em relação à persistência durável; nunca sinalizar sucesso em caso de perda.
- Monitorar última transmissão e atraso da estação; definir limite offline a partir
  da cadência observada e do prazo acordado com o responsável.
- Proteger credenciais, controlar acesso, prover logs, backups e recuperação testada.
  Confirmar alcance pela rede celular, DNS, firewall e TLS quando suportado.

## Alcance do script 05

Implementa somente POST HTTP local em `/telemetria`, com log de bytes e resposta
provisória. Confirma a gravação no log do ensaio antes de responder, mas não
implementa banco de produção, persistência durável garantida, parser do protocolo,
deduplicação, autenticação ou ACK real. Não abrir acesso externo como forma de
contornar a descoberta do contrato. O receptor definitivo será implementado e
testado após obter as evidências acima.

