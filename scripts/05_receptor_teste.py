"""Ensaio HTTP local, sem compatibilidade confirmada com Dualbase/PCDWeb."""

import argparse
import base64
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import threading

from _comum import abrir_saida, agora, destino, executar, segundos_positivos

LIMITE_CORPO = 1024 * 1024


class Receptor(BaseHTTPRequestHandler):
    def setup(self):
        super().setup()
        self.connection.settimeout(self.server.read_timeout)

    def do_GET(self):
        if self.path != "/health":
            self.send_error(404)
            return
        self.responder_json({"status": "ok", "mode": "http-bench", "protocol_confirmed": False})

    def responder_json(self, conteudo):
        resposta = (json.dumps(conteudo) + "\n").encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(resposta)))
        self.end_headers()
        self.wfile.write(resposta)

    def handle(self):
        try:
            super().handle()
        except (ConnectionError, TimeoutError):
            # Cliente desconectado não apaga uma evidência já gravada.
            pass

    def do_POST(self):
        if self.headers.get("Expect") is not None:
            self.send_error(417, "Expect nao suportado neste ensaio")
            return
        if self.path != "/telemetria":
            self.send_error(404)
            return
        if self.headers.get("Transfer-Encoding") is not None:
            self.send_error(501, "Transfer-Encoding nao suportado neste receptor")
            return
        tamanhos = self.headers.get_all("Content-Length", [])
        if not tamanhos:
            self.send_error(411)
            return
        if len(tamanhos) != 1 or not tamanhos[0].isascii() or not tamanhos[0].isdigit():
            self.send_error(400, "Content-Length invalido")
            return
        try:
            tamanho = int(tamanhos[0])
        except ValueError:
            self.send_error(400)
            return
        if tamanho <= 0:
            self.send_error(400)
            return
        if tamanho > LIMITE_CORPO:
            self.send_error(413)
            return
        try:
            corpo = self.rfile.read(tamanho)
        except TimeoutError:
            self.send_error(408)
            return
        if len(corpo) != tamanho:
            self.send_error(400, "Corpo incompleto")
            return
        registro = {"timestamp": agora(), "method": "POST", "path": self.path,
                    "peer": self.client_address[0], "content_type": self.headers.get("Content-Type", ""),
                    "content_encoding": self.headers.get("Content-Encoding", ""),
                    "body_bytes": len(corpo), "body_sha256": hashlib.sha256(corpo).hexdigest(),
                    "body_base64": base64.b64encode(corpo).decode("ascii")}
        try:
            with self.server.log_lock:
                with abrir_saida(self.server.output, "a") as arquivo:
                    arquivo.write(json.dumps(registro, ensure_ascii=False) + "\n")
                    arquivo.flush()
                    os.fsync(arquivo.fileno())
        except OSError:
            self.send_error(500, "Nao foi possivel gravar a evidencia")
            return
        self.responder_json({"ok": True})

    def log_message(self, formato, *args):
        # O log de evidência não inclui cabeçalhos de autenticação/cookies.
        print(f"{agora()} | {formato % args}")


def criar_servidor(host, porta, saida, read_timeout=5):
    saida = Path(saida)
    if saida.exists() and saida.stat().st_size:
        with saida.open("rb") as arquivo:
            arquivo.seek(-1, 2)
            if arquivo.read(1) != b"\n":
                raise ValueError("Log existente termina com registro incompleto; preserve-o e use outro arquivo.")
    servidor = ThreadingHTTPServer((host, porta), Receptor)
    servidor.output = Path(saida)
    servidor.log_lock = threading.Lock()
    servidor.read_timeout = read_timeout
    return servidor


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--output", type=Path, help="Log JSONL; acrescenta se já existir.")
    parser.add_argument("--read-timeout", type=segundos_positivos, default=5,
                        help="Prazo sem dados durante a leitura HTTP, em segundos.")
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("A porta deve estar entre 1 e 65535.")
    saida = args.output or destino("receptor", "http")
    with abrir_saida(saida, "a"):
        pass
    with criar_servidor(args.host, args.port, saida, args.read_timeout) as servidor:
        print(f"Receptor: http://{args.host}:{args.port}/telemetria | Log: {saida.resolve()}")
        print("Ensaio HTTP de bancada; protocolo e confirmação do ABS CEL S ainda desconhecidos.")
        print("127.0.0.1 atende só este computador. Encerre com Ctrl+C.")
        try:
            servidor.serve_forever()
        except KeyboardInterrupt:
            print("\nReceptor encerrado.")


if __name__ == "__main__":
    raise SystemExit(executar(main))
