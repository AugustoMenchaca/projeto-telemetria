"""Procura pistas de destino/protocolo em uma imagem local sem modificá-la."""

import argparse
import hashlib
import json
from pathlib import Path
import re

from _comum import abrir_saida, agora, argumento_equipamento, destino, executar, inteiro_positivo

PADROES = (("ascii", re.compile(rb"[\x20-\x7e]{3,}")),
           ("utf-16le", re.compile(rb"(?:[\x20-\x7e]\x00){3,}")),
           ("utf-16be", re.compile(rb"(?:\x00[\x20-\x7e]){3,}")))
INDICADORES = re.compile(
    r"dualbase|pcdweb|(?:https?|mqtts?|ftps?)://|"
    r"\b(?:mqtt|http|https|tcp|udp|ftp|endpoint|server|host|apn|api|protocol|device_id)\b|"
    r"\b(?:server_host|server_ip|server_port)\b|"
    r"\b(?:1883|8883)\b|\b(?:\d{1,3}\.){3}\d{1,3}\b|"
    r"\b(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z]{2,63}\b", re.I)


def analisar(dados, limite=None):
    achados = []
    for codificacao, padrao in PADROES:
        passo = 1 if codificacao == "ascii" else 2
        for trecho in padrao.finditer(dados):
            texto = trecho.group().decode(codificacao)
            for pista in INDICADORES.finditer(texto):
                achados.append({"offset": trecho.start() + pista.start() * passo,
                                "encoding": codificacao, "indicator": pista.group(),
                                "context": texto[max(0, pista.start() - 60):pista.end() + 120]})
                if limite is not None and len(achados) >= limite:
                    return sorted(achados, key=lambda item: (item["offset"], item["encoding"]))
    return sorted(achados, key=lambda item: (item["offset"], item["encoding"]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    argumento_equipamento(parser)
    parser.add_argument("firmware", type=Path, help="Imagem original .bin/.img obtida com autorização.")
    parser.add_argument("--output", type=Path, help="Relatório JSON novo; padrão em dados/analises/.")
    parser.add_argument("--max-bytes", type=inteiro_positivo, default=64 * 1024 * 1024,
                        help="Limite de leitura da imagem; padrão 64 MiB.")
    parser.add_argument("--max-findings", type=inteiro_positivo, default=1000,
                        help="Máximo de pistas no relatório; truncamento é informado.")
    args = parser.parse_args()
    with args.firmware.open("rb") as arquivo:
        dados = arquivo.read(args.max_bytes + 1)
    if len(dados) > args.max_bytes:
        raise ValueError("A imagem excede --max-bytes; revise o tamanho antes de elevar o limite.")
    if not dados:
        raise ValueError("O arquivo de firmware está vazio.")
    achados = analisar(dados, args.max_findings + 1)
    truncado = len(achados) > args.max_findings
    achados = achados[:args.max_findings]
    relatorio = {"timestamp": agora(), "equipment": args.equipment,
                 "source": str(args.firmware.resolve()),
                 "size_bytes": len(dados), "sha256": hashlib.sha256(dados).hexdigest(),
                 "findings": achados,
                 "findings_truncated": truncado, "max_findings": args.max_findings,
                 "limitations": "Pistas de strings, não confirmação do destino em uso. "
                 "Não descomprime, decifra, extrai ou modifica firmware."}
    saida = args.output or destino(f"analises/{args.equipment}", "firmware", "json")
    with abrir_saida(saida) as arquivo:
        json.dump(relatorio, arquivo, ensure_ascii=False, indent=2)
        arquivo.write("\n")
    print(f"Imagem: {len(dados)} bytes | SHA-256: {relatorio['sha256']}")
    print(f"Pistas: {len(achados)}. Relatório: {saida.resolve()}")
    if truncado:
        print("Relatório truncado; eleve --max-findings para ampliar a busca (ASCII antes de UTF-16).")
    if not achados:
        print("Nenhuma pista encontrada; isso não comprova ausência de destino no firmware.")


if __name__ == "__main__":
    raise SystemExit(executar(main))
