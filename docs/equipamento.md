# Inventário técnico dos equipamentos

Referência: contexto recebido em 27/10/2026. Informações abaixo são relatos,
salvo indicação de evidência local. A visita está prevista para 28/10/2026.

## Unidades conhecidas

| Campo | `pedro-osorio` — principal | `bancada` — alternativo |
| --- | --- | --- |
| Modelo | ABS CEL S | ABS CEL S |
| Local/situação | Estação de Pedro Osório/RS, em operação | Disponível fisicamente para investigação |
| Firmware | Customizado para Dualbase, conforme usuário | Diferente do principal; origem não confirmada |
| Recepção atual | Ecossistema Dualbase/PCDWeb | Destino não confirmado |
| Papel na migração | Plano A: preservar, se viável | Plano B: substituir somente após validação |
| Teste serial | Ainda não realizado | Inconclusivo: faltava alimentação externa apropriada |
| Imagem binária | Não obtida | Disponibilidade não confirmada |

O Windows reconheceu **Prolific USB-to-Serial Comm Port (COM8)** no teste de bancada.
É evidência do conversor USB/RS-232, sem confirmação de resposta do ABS CEL S.
O conector foi identificado como serial DB9, inicialmente confundido com VGA.
Não há evidência de falha de driver nessa observação. Confira a porta atual no
inventário; RS-232 não enumera um novo dispositivo quando se conecta o modem.

Na preparação local de 27/10/2026, um novo inventário encontrou apenas portas
Bluetooth (COM3–COM6); não enumerou o Prolific. Essa observação está no registro de
investigação e não substitui o teste com o adaptador conectado na visita.

## Ficha a completar para cada unidade

Duplique a ficha e registre a origem de cada informação. Não copie valores entre
unidades só por terem o mesmo modelo.

| Campo | Valor / evidência / data |
| --- | --- |
| Unidade (`pedro-osorio` ou `bancada`) | A preencher |
| Etiqueta, número de série e revisão de hardware | A coletar; identificadores completos somente em evidência privada |
| Versão de firmware e responsável pela customização | A coletar |
| Fotos de etiqueta, conectores, cabos e LEDs | Caminhos privados a registrar |
| Datalogger/controlador, sensores e canais | Não identificados |
| Manual da revisão / página / configurador e versão | A coletar |
| Alimentação: fonte, tensão medida e polaridade | A confirmar antes de energizar |
| Interface elétrica, pinagem e terra | A confirmar para a porta utilizada |
| Conversor/cabo: direto ou cruzado, VID/PID e COM atual | A registrar |
| Baud / bits / paridade / stop / fluxo / DTR / RTS | Não confirmados; 9600/8N1 é só hipótese de teste |
| Suporte AT nessa porta e fonte da confirmação | Não confirmado |
| Destino, porta, protocolo e provisionamento remoto | Não lidos |
| Operadora, tecnologia celular e APN | A coletar; 3G/4G ainda a confirmar |
| Exportação original da configuração e hash | Não obtida |
| Procedimento suportado de leitura/restauração | A confirmar |
| Cadência, relógio, buffer e retransmissão | A medir |

A faixa de aproximadamente 10–30 V CC foi discutida para a família, mas **não é
especificação confirmada da revisão presente**. Confira etiqueta/manual, tensão e
polaridade; USB/DB9 não substitui a alimentação externa. Não energize bornes por
suposição nem conecte RS-232 diretamente a TTL ou RS-485.

## Acessos e condições de ensaio

Servidor próprio: existência informada; rede, capacidade e receptor pendentes.
PCDWeb: uso confirmado; credenciais administrativas, exportações e logs internos
não confirmados. Visualizar medições não demonstra acesso à configuração do modem.
Código-fonte e documentação da customização não estão disponíveis.

Por ensaio, registre unidade, operador, data/hora UTC e local com fuso,
alimentação, pinagem, cabos, LEDs, instrumento ligado e ação que iniciou a atividade.
Em produção, registre a última medição antes e a nova medição após a inspeção.
Mantenha credenciais, SIM/ICCID e identificadores sensíveis fora da documentação pública.

