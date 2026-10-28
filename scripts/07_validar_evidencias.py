"""Confere integridade de inventários, capturas, análise de firmware e logs HTTP locais."""

import argparse
import base64
import binascii
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re

from _comum import abrir_saida, agora, executar, inteiro_positivo

COMANDOS = ("AT", "ATI", "AT+CGMI", "AT+CGMM", "AT+CGMR")


def exigir(condicao, mensagem):
    if not condicao:
        raise ValueError(mensagem)


def inteiro(valor, minimo=0):
    return type(valor) is int and valor >= minimo


def timestamp(registro):
    valor = registro.get("timestamp")
    exigir(isinstance(valor, str), "timestamp ausente ou inválido")
    instante = datetime.fromisoformat(valor.replace("Z", "+00:00"))
    exigir(instante.utcoffset() is not None, "timestamp sem fuso horário")


def bytes_conferidos(registro, prefixo=""):
    try:
        dados = base64.b64decode(registro[prefixo + "base64"], validate=True)
    except (KeyError, TypeError, binascii.Error, ValueError) as exc:
        raise ValueError("Base64 ausente ou inválido") from exc
    tamanho = registro.get(prefixo + "bytes")
    exigir(inteiro(tamanho) and tamanho == len(dados), "Contagem de bytes divergente")
    if prefixo:
        exigir(registro.get(prefixo + "sha256") == hashlib.sha256(dados).hexdigest(), "SHA-256 do corpo divergente")
    else:
        exigir(registro.get("hex") == dados.hex(), "Hexadecimal diverge dos bytes originais")
    return dados


def validar_serial(registros):
    inicio = registros[0]
    unidade = inicio.get("equipment")
    exigir(unidade in ("pedro-osorio", "bancada"), "Unidade ausente ou inválida")
    exigir(inteiro(inicio.get("baud"), 1), "Baud rate inválido")
    exigir(bool(inicio.get("port")), "Porta ausente")
    if unidade == "pedro-osorio":
        exigir(inicio.get("production_interface_confirmed") is True, "Interface de produção não confirmada")
    exigir(len(registros) >= 2 and registros[-1].get("event") == "end", "Captura incompleta: falta evento end")
    at = inicio.get("confirmed_at") is True
    permitidos = {"tx_attempt", "at_rx", "at_response"} if at else {"rx"}
    total = 0
    blocos = 0
    enviados = []
    respostas = []
    parcial = bytearray()
    for registro in registros[1:-1]:
        evento = registro.get("event")
        exigir(evento in permitidos, "Evento inesperado na captura")
        dados = bytes_conferidos(registro)
        if not at:
            total += len(dados)
            blocos += 1
            continue
        comando = registro.get("command")
        if evento == "tx_attempt":
            exigir(len(enviados) < len(COMANDOS) and comando == COMANDOS[len(enviados)], "Sequência AT inesperada")
            exigir(len(respostas) == len(enviados), "Nova consulta AT antes do registro da resposta")
            exigir(dados == (comando + "\r").encode("ascii"), "Bytes de consulta AT divergentes")
            enviados.append(comando)
            parcial.clear()
        else:
            exigir(enviados and comando == enviados[-1], "Resposta AT sem consulta correspondente")
            exigir(len(respostas) < len(enviados), "Resposta AT duplicada")
            if evento == "at_rx":
                parcial.extend(dados)
            else:
                if parcial:
                    exigir(bytes(parcial) == dados, "Resumo AT diverge dos blocos recebidos")
                terminal = None
                for linha in re.split(rb"[\r\n]", dados)[:-1]:
                    linha = linha.strip()
                    if linha in (b"OK", b"ERROR") or linha.startswith((b"+CME ERROR:", b"+CMS ERROR:")):
                        terminal = linha.decode("ascii", errors="replace")
                        break
                exigir(registro.get("terminal") == terminal, "Estado terminal AT diverge dos bytes")
                respostas.append(registro.get("terminal"))
    fim = registros[-1]
    motivo = fim.get("reason")
    exigir(motivo in ("completed", "interrupted", "serial_error", "open_error", "inconclusive"), "Motivo de término inválido")
    if at and motivo == "completed":
        exigir(len(enviados) == len(COMANDOS) and respostas == ["OK"] * len(COMANDOS), "Identificação AT marcada como completa sem cinco respostas OK")
    if not at:
        exigir(inteiro(fim.get("total_bytes")) and fim["total_bytes"] == total, "Total de bytes da captura divergente")
        exigir(inteiro(fim.get("chunks")) and fim["chunks"] == blocos, "Total de blocos divergente")
    status = "valid" if motivo == "completed" and (at or total > 0) else "inconclusive"
    return {"kind": "serial-at" if at else "serial", "equipment": unidade,
            "status": status, "reason": motivo, "received_bytes": total if not at else None}


def validar_json(documento, origem=None):
    timestamp(documento)
    if "ports" in documento:
        exigir(isinstance(documento["ports"], list), "Inventário de portas inválido")
        portas = []
        for porta in documento["ports"]:
            exigir(isinstance(porta, dict) and isinstance(porta.get("port"), str) and porta["port"], "Porta inválida")
            portas.append(porta["port"])
        exigir(len(portas) == len(set(portas)), "Porta duplicada no inventário")
        return {"kind": "inventory", "status": "valid", "ports": len(portas)}
    exigir(documento.get("equipment") in ("pedro-osorio", "bancada"), "Origem do firmware não identificada")
    tamanho = documento.get("size_bytes")
    exigir(inteiro(tamanho, 1), "Tamanho da imagem inválido")
    exigir(isinstance(documento.get("sha256"), str) and re.fullmatch(r"[0-9a-f]{64}", documento["sha256"]), "SHA-256 da imagem inválido")
    exigir(isinstance(documento.get("findings"), list), "Lista de pistas inválida")
    original = None
    if origem is not None:
        origem = Path(origem)
        exigir(origem.stat().st_size == tamanho, "Tamanho do binário original divergente")
        resumo = hashlib.sha256()
        with origem.open("rb") as arquivo:
            for bloco in iter(lambda: arquivo.read(1024 * 1024), b""):
                resumo.update(bloco)
        exigir(resumo.hexdigest() == documento["sha256"], "Binário original diverge do SHA-256")
        original = origem
    for achado in documento["findings"]:
        exigir(isinstance(achado, dict), "Pista inválida")
        posicao = achado.get("offset")
        exigir(inteiro(posicao) and posicao < tamanho, "Offset fora da imagem")
        exigir(achado.get("encoding") in ("ascii", "utf-16le", "utf-16be"), "Codificação de pista inválida")
        exigir(isinstance(achado.get("indicator"), str) and achado["indicator"], "Indicador vazio")
        esperado = achado["indicator"].encode(achado["encoding"])
        exigir(posicao + len(esperado) <= tamanho, "Pista ultrapassa a imagem")
        if original is not None:
            with original.open("rb") as arquivo:
                arquivo.seek(posicao)
                exigir(arquivo.read(len(esperado)) == esperado, "Pista diverge do binário no offset informado")
    return {"kind": "firmware-analysis", "equipment": documento["equipment"],
            "status": "valid", "source_verified": original is not None,
            "findings_truncated": documento.get("findings_truncated", False)}


def validar(caminho, origem=None, max_bytes=64 * 1024 * 1024):
    caminho = Path(caminho)
    with caminho.open("rb") as arquivo:
        bruto = arquivo.read(max_bytes + 1)
    exigir(len(bruto) <= max_bytes, "Evidência excede o limite de leitura")
    if not bruto.strip():
        return {"kind": "empty", "status": "inconclusive", "records": 0}
    texto = bruto.decode("utf-8-sig")
    try:
        documento = json.loads(texto)
    except json.JSONDecodeError:
        registros = [json.loads(linha) for linha in texto.splitlines() if linha.strip()]
    else:
        exigir(isinstance(documento, dict), "Objeto JSON esperado")
        if "event" not in documento and "method" not in documento:
            return {**validar_json(documento, origem), "sha256": hashlib.sha256(bruto).hexdigest()}
        registros = [documento]
    exigir(bruto.endswith(b"\n"), "JSONL incompleto: falta quebra de linha final")
    for registro in registros:
        exigir(isinstance(registro, dict), "Registro JSON inválido")
        timestamp(registro)
    if registros[0].get("event") == "start":
        resultado = validar_serial(registros)
    else:
        for registro in registros:
            exigir(registro.get("method") == "POST" and registro.get("path") == "/telemetria", "Registro HTTP inesperado")
            bytes_conferidos(registro, "body_")
        resultado = {"kind": "http-bench", "status": "valid"}
    return {**resultado, "records": len(registros), "sha256": hashlib.sha256(bruto).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--source", type=Path, help="Binário original para conferir um único relatório de firmware.")
    parser.add_argument("--output", type=Path, help="Relatório JSON novo, sem sobrescrever evidências.")
    parser.add_argument("--max-bytes", type=inteiro_positivo, default=64 * 1024 * 1024)
    args = parser.parse_args()
    if args.source and len(args.files) != 1:
        parser.error("--source exige exatamente um relatório de firmware.")
    resultados = []
    for caminho in args.files:
        try:
            resultado = validar(caminho, args.source, args.max_bytes)
            if args.source:
                exigir(resultado["kind"] == "firmware-analysis", "--source se aplica somente à análise de firmware")
        except (OSError, ValueError, TypeError, KeyError) as exc:
            resultado = {"status": "invalid", "error": str(exc)}
        resultados.append({"file": str(caminho.resolve()), **resultado})
        print(f"{caminho.name}: {resultado['status']}")
    if args.output:
        with abrir_saida(args.output) as arquivo:
            json.dump({"timestamp": agora(), "results": resultados}, arquivo, ensure_ascii=False, indent=2)
            arquivo.write("\n")
    estados = {r["status"] for r in resultados}
    return 1 if "invalid" in estados else 2 if "inconclusive" in estados else 0


if __name__ == "__main__":
    raise SystemExit(executar(main))
