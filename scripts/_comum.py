"""Utilidades locais. Nenhum acesso a hardware acontece durante a importação."""

import argparse
import base64
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import sys
import uuid

RAIZ = Path(__file__).resolve().parent.parent


def agora():
    return datetime.now(timezone.utc).isoformat()


def destino(pasta, prefixo, extensao="jsonl"):
    instante = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    return RAIZ / "dados" / pasta / f"{prefixo}-{instante}-{uuid.uuid4().hex[:8]}.{extensao}"


def inteiro_positivo(valor):
    numero = int(valor)
    if numero <= 0:
        raise argparse.ArgumentTypeError("Informe um inteiro maior que zero.")
    return numero


def segundos_positivos(valor):
    numero = float(valor)
    if not math.isfinite(numero) or numero <= 0:
        raise argparse.ArgumentTypeError("Informe uma duração finita maior que zero.")
    return numero


def argumentos_seriais(parser):
    argumento_equipamento(parser)
    parser.add_argument("--port", required=True, help="Porta confirmada, por exemplo COM8.")
    parser.add_argument("--baud", type=inteiro_positivo, required=True,
                        help="Velocidade verificada para esta interface; 9600 não está confirmado.")
    parser.add_argument("--data-bits", type=int, choices=(5, 6, 7, 8), default=8)
    parser.add_argument("--parity", choices=("N", "E", "O", "M", "S"), default="N")
    parser.add_argument("--stop-bits", type=float, choices=(1, 1.5, 2), default=1)
    parser.add_argument("--confirm-production-interface", action="store_true",
                        help="Em Pedro Osório: interface de diagnóstico, alimentação e pinagem "
                             "verificadas, acesso autorizado e impacto de DTR/RTS avaliado.")


def argumento_equipamento(parser):
    parser.add_argument("--equipment", required=True, choices=("pedro-osorio", "bancada"),
                        help="Unidade de origem da evidência; os firmwares são diferentes.")


def validar_interface(parser, args):
    if args.equipment == "pedro-osorio" and not args.confirm_production_interface:
        parser.error("Para Pedro Osório, confirme uma interface de diagnóstico apropriada "
                     "com --confirm-production-interface antes de abrir a serial.")


def biblioteca_serial():
    try:
        import serial
    except ImportError as exc:
        raise RuntimeError("Instale as dependências: python -m pip install -r requirements.txt") from exc
    return serial


def serial_preparada(args):
    serial = biblioteca_serial()
    porta = serial.Serial(port=None)
    porta.port = args.port
    porta.baudrate = args.baud
    porta.bytesize = args.data_bits
    porta.parity = args.parity
    porta.stopbits = args.stop_bits
    porta.timeout = 0.2
    porta.write_timeout = 1
    porta.xonxoff = False
    porta.rtscts = False
    porta.dsrdtr = False
    porta.dtr = False
    porta.rts = False
    return porta


def metadados_seriais(args):
    return {"equipment": args.equipment,
            "production_interface_confirmed": args.confirm_production_interface,
            "port": args.port, "baud": args.baud, "data_bits": args.data_bits,
            "parity": args.parity, "stop_bits": args.stop_bits,
            "dtr": False, "rts": False, "flow_control": False}


def bytes_registro(dados):
    return {"bytes": len(dados), "hex": dados.hex(),
            "base64": base64.b64encode(dados).decode("ascii"),
            "text": dados.decode("utf-8", errors="replace")}


def abrir_saida(caminho, modo="x"):
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    return caminho.open(modo, encoding="utf-8", newline="\n")


def registrar(arquivo, evento, **campos):
    arquivo.write(json.dumps({"timestamp": agora(), "event": evento, **campos},
                             ensure_ascii=False) + "\n")
    arquivo.flush()


def executar(funcao):
    try:
        return funcao() or 0
    except KeyboardInterrupt:
        print("\nInterrompido pelo usuário.", file=sys.stderr)
        return 130
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1
