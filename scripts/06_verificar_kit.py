"""Verificação local do kit; não abre serial nem transmite comandos ao modem."""

import argparse
import hashlib
from importlib import metadata
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from _comum import RAIZ, abrir_saida, agora, destino, executar


def conferir_fontes(raiz):
    arquivos = [*(raiz / "scripts").glob("*.py"), *(raiz / "tests").glob("*.py")]
    for caminho in arquivos:
        compile(caminho.read_bytes(), str(caminho), "exec")
    return f"{len(arquivos)} fontes Python compiladas"


def conferir_documentacao(raiz):
    obrigatorios = ["README.md", "requirements.txt", "Preparar.ps1", "Verificar.ps1",
                    "docs/equipamento.md", "docs/roteiro.md", "docs/registro-investigacao.md",
                    "docs/receptor.md", "docs/plano-migracao.md", "docs/testes.md",
                    "docs/contexto-tecnico-2026-10-27.md", "dados/README.md"]
    for relativo in obrigatorios:
        if not (raiz / relativo).is_file():
            raise ValueError(f"Arquivo necessário ausente: {relativo}")
    links = 0
    for caminho in [raiz / "README.md", raiz / "dados/README.md", *(raiz / "docs").glob("*.md")]:
        texto = re.sub(r"```.*?```", "", caminho.read_text(encoding="utf-8-sig"), flags=re.S)
        for alvo in re.findall(r"\[[^\]]*\]\(([^)]+)\)", texto):
            if "://" in alvo or alvo.startswith("#"):
                continue
            if not (caminho.parent / alvo.split("#")[0]).exists():
                raise ValueError(f"Link local ausente em {caminho.name}: {alvo}")
            links += 1
    return f"{len(obrigatorios)} arquivos necessários e {links} links locais conferidos"


def conferir_dependencia_offline(raiz):
    requisito = (raiz / "requirements.txt").read_text(encoding="utf-8-sig").strip()
    correspondencia = re.fullmatch(r"pyserial==3\.5 --hash=sha256:([0-9a-f]{64})", requisito)
    if not correspondencia:
        raise ValueError("requirements.txt deve fixar PySerial 3.5 com hash SHA-256")
    wheel = raiz / "offline/pyserial-3.5-py2.py3-none-any.whl"
    if hashlib.sha256(wheel.read_bytes()).hexdigest() != correspondencia[1]:
        raise ValueError("Wheel offline diverge do hash fixado em requirements.txt")
    return "Wheel PySerial 3.5 conferida por SHA-256"


def rodar_comando(comando, raiz, timeout=120):
    ambiente = os.environ.copy()
    ambiente["PYTHONIOENCODING"] = "utf-8"
    ambiente["PYTHONWARNINGS"] = "error"
    try:
        processo = subprocess.run(comando, cwd=raiz, capture_output=True, text=True,
                                  encoding="utf-8", errors="replace", timeout=timeout, env=ambiente)
    except subprocess.TimeoutExpired:
        return {"status": "FAIL", "exit_code": None, "error": f"Prazo de {timeout}s excedido"}
    return {"status": "PASS" if processo.returncode == 0 else "FAIL", "exit_code": processo.returncode,
            "stdout": processo.stdout[-65536:], "stderr": processo.stderr[-65536:]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Relatório JSON novo; padrão em dados/verificacoes/.")
    parser.add_argument("--inventory", action="store_true", help="Também enumera conversores sem abrir portas.")
    args = parser.parse_args()
    verificacoes = []

    def verificar(nome, funcao):
        try:
            detalhe = funcao()
            resultado = {"name": nome, "status": "PASS", "detail": detalhe}
        except (OSError, ValueError, SyntaxError, metadata.PackageNotFoundError) as exc:
            resultado = {"name": nome, "status": "FAIL", "error": str(exc)}
        verificacoes.append(resultado)
        print(f"{nome}: {resultado['status']}")

    def python_compativel():
        if sys.version_info < (3, 10):
            raise ValueError("Python 3.10 ou superior necessário")
        return sys.version.split()[0]

    def pyserial_compativel():
        versao = metadata.version("pyserial")
        if versao != "3.5":
            raise ValueError(f"PySerial {versao}; necessário 3.5 conforme requirements.txt")
        return versao

    verificar("Python", python_compativel)
    verificar("PySerial", pyserial_compativel)
    verificar("Sintaxe Python", lambda: conferir_fontes(RAIZ))
    verificar("Documentação", lambda: conferir_documentacao(RAIZ))
    verificar("Dependência offline", lambda: conferir_dependencia_offline(RAIZ))
    comandos = [("Dependências", [sys.executable, "-m", "pip", "check"]),
                ("Testes", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"])]
    if args.inventory:
        comandos.append(("Inventário sem abrir serial", [sys.executable, str(RAIZ / "scripts/01_portas.py")]))
    for nome, comando in comandos:
        resultado = {"name": nome, "command": comando, **rodar_comando(comando, RAIZ)}
        verificacoes.append(resultado)
        print(f"{nome}: {resultado['status']}")
        if resultado["status"] == "FAIL":
            print(resultado.get("error") or resultado.get("stderr", "")[-4000:])
    aprovado = all(v["status"] == "PASS" for v in verificacoes)
    relatorio = {"timestamp": agora(), "verdict": "PASS" if aprovado else "FAIL",
                 "scope": "software-local", "hardware_tests": "not_run",
                 "migration_validation": "pending", "checks": verificacoes}
    saida = args.output or destino("verificacoes", "kit", "json")
    with abrir_saida(saida) as arquivo:
        json.dump(relatorio, arquivo, ensure_ascii=False, indent=2)
        arquivo.write("\n")
    print(f"Resultado local: {relatorio['verdict']}. Relatório: {saida.resolve()}")
    print("Modems, interface elétrica, protocolo real e migração: validação de campo pendente.")
    return 0 if aprovado else 1


if __name__ == "__main__":
    raise SystemExit(executar(main))
