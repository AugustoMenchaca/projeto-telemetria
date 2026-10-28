"""Captura bytes da serial sem enviar comandos; sinais podem mudar ao abrir."""

import argparse
from pathlib import Path
import time

from _comum import (abrir_saida, argumentos_seriais, bytes_registro, destino,
                    executar, metadados_seriais, registrar, segundos_positivos,
                    serial_preparada, validar_interface)


def capturar(porta, segundos, arquivo):
    inicio = time.monotonic()
    total = 0
    blocos = 0
    motivo = "completed"
    erro = None
    try:
        while time.monotonic() - inicio < segundos:
            dados = porta.read(4096)
            if dados:
                registrar(arquivo, "rx", **bytes_registro(dados))
                total += len(dados)
                blocos += 1
    except KeyboardInterrupt:
        motivo = "interrupted"
    except OSError as exc:
        motivo = "serial_error"
        erro = str(exc)
        raise
    finally:
        registrar(arquivo, "end", reason=motivo, total_bytes=total, chunks=blocos,
                  elapsed_seconds=round(time.monotonic() - inicio, 3), error=erro)
    return total, motivo


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    argumentos_seriais(parser)
    parser.add_argument("--seconds", type=segundos_positivos, default=60)
    parser.add_argument("--output", type=Path, help="Arquivo JSONL novo; padrão em dados/capturas/.")
    args = parser.parse_args()
    validar_interface(parser, args)
    saida = args.output or destino(f"capturas/{args.equipment}", "serial")
    porta = serial_preparada(args)
    with abrir_saida(saida) as arquivo:
        registrar(arquivo, "start", **metadados_seriais(args), requested_seconds=args.seconds)
        try:
            try:
                porta.open()
            except OSError as exc:
                registrar(arquivo, "end", reason="open_error", error=str(exc),
                          total_bytes=0, chunks=0)
                raise
            print(f"Capturando {args.port} a {args.baud} bps. Log: {saida.resolve()}")
            total, motivo = capturar(porta, args.seconds, arquivo)
        finally:
            porta.close()
    print(f"Captura encerrada: {total} bytes. Log: {saida.resolve()}")
    if not total:
        print("Resultado inconclusivo: revise alimentação externa, pinagem, parâmetros e atividade.")
    return 130 if motivo == "interrupted" else 0


if __name__ == "__main__":
    raise SystemExit(executar(main))
