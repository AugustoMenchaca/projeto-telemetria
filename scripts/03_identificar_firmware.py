"""Consulta identificação AT com suporte confirmado; não lê nem extrai o firmware."""

import argparse
from pathlib import Path
import re
import time

from _comum import (abrir_saida, argumentos_seriais, bytes_registro, destino,
                    executar, metadados_seriais, registrar, segundos_positivos,
                    serial_preparada, validar_interface)

COMANDOS = ("AT", "ATI", "AT+CGMI", "AT+CGMM", "AT+CGMR")
LIMITE_RESPOSTA = 1024 * 1024


def ler_resposta(porta, segundos, ao_receber=None):
    fim = time.monotonic() + segundos
    resposta = bytearray()
    terminal = None
    while time.monotonic() < fim and len(resposta) < LIMITE_RESPOSTA:
        bloco = porta.read(min(4096, LIMITE_RESPOSTA - len(resposta)))
        if bloco and ao_receber:
            ao_receber(bloco)
        resposta.extend(bloco)
        # Só reconhecer linhas completas, evitando aceitar fragmentos de dados.
        linhas = re.split(rb"[\r\n]", bytes(resposta))[:-1]
        for linha in linhas:
            linha = linha.strip()
            if linha in (b"OK", b"ERROR") or linha.startswith((b"+CME ERROR:", b"+CMS ERROR:")):
                terminal = linha.decode("ascii", errors="replace")
                break
        if terminal:
            break
    return bytes(resposta), terminal


def consultar(porta, arquivo, segundos):
    for comando in COMANDOS:
        enviado = (comando + "\r").encode("ascii")
        registrar(arquivo, "tx_attempt", command=comando, **bytes_registro(enviado))
        quantidade = porta.write(enviado)
        if quantidade != len(enviado):
            raise RuntimeError("Escrita serial incompleta; sequência AT interrompida.")
        resposta, terminal = ler_resposta(
            porta, segundos,
            lambda bloco: registrar(arquivo, "at_rx", command=comando, **bytes_registro(bloco)))
        registrar(arquivo, "at_response", command=comando, terminal=terminal,
                  **bytes_registro(resposta))
        print(f"{comando}: {terminal or 'sem resposta terminal'} ({len(resposta)} bytes)")
        if terminal != "OK":
            print("Sequência interrompida. Revise a identificação da interface e o log.")
            return False
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    argumentos_seriais(parser)
    parser.add_argument("--confirm-at", action="store_true",
                        help="Confirmo suporte a AT nesta porta com base no manual/módulo.")
    parser.add_argument("--response-seconds", type=segundos_positivos, default=2)
    parser.add_argument("--output", type=Path, help="Arquivo JSONL novo; padrão em dados/capturas/.")
    args = parser.parse_args()
    if not args.confirm_at:
        parser.error("Confirme suporte a comandos AT nesta interface com --confirm-at.")
    validar_interface(parser, args)
    saida = args.output or destino(f"capturas/{args.equipment}", "identificacao-at")
    porta = serial_preparada(args)
    with abrir_saida(saida) as arquivo:
        registrar(arquivo, "start", **metadados_seriais(args), confirmed_at=True,
                  response_seconds=args.response_seconds)
        try:
            porta.open()
            concluido = consultar(porta, arquivo, args.response_seconds)
            registrar(arquivo, "end", reason="completed" if concluido else "inconclusive")
        except (OSError, RuntimeError) as exc:
            registrar(arquivo, "end", reason="serial_error", error=str(exc))
            raise
        except KeyboardInterrupt:
            registrar(arquivo, "end", reason="interrupted")
            raise
        finally:
            porta.close()
    print(f"Log: {saida.resolve()}")
    return 0 if concluido else 2


if __name__ == "__main__":
    raise SystemExit(executar(main))
