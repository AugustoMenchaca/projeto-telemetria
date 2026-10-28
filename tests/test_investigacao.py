"""Testes de comportamento com serial simulada e HTTP apenas em loopback."""

import base64
from contextlib import redirect_stderr, redirect_stdout
import hashlib
from http.client import HTTPConnection
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
import _comum as comum


def carregar(nome, arquivo):
    spec = importlib.util.spec_from_file_location(nome, RAIZ / "scripts" / arquivo)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


captura = carregar("captura", "02_captura_serial.py")
at = carregar("identificacao", "03_identificar_firmware.py")
firmware = carregar("firmware", "04_analisar_firmware.py")
http = carregar("receptor", "05_receptor_teste.py")


class SerialSimulada:
    def __init__(self, blocos=(), responder_at=True):
        self.blocos = list(blocos)
        self.escritas = []
        self.responder_at = responder_at
        self.aberta = False

    def open(self):
        self.aberta = True

    def close(self):
        self.aberta = False

    def read(self, quantidade):
        if self.blocos:
            return self.blocos.pop(0)
        time.sleep(0.001)
        return b""

    def write(self, dados):
        self.escritas.append(dados)
        if self.responder_at:
            self.blocos.append(b"\r\nMODELO-TESTE\r\nOK\r\n")
        return len(dados)


class TestSerial(unittest.TestCase):
    def test_captura_preserva_bytes_sem_escrever(self):
        porta = SerialSimulada([b"\x00\xff\r\n", b"sensor=25", b""])
        arquivo = io.StringIO()
        with patch.object(captura.time, "monotonic", side_effect=[0, 0, 0.25, 0.6, 1.1, 1.2]):
            total, motivo = captura.capturar(porta, 1, arquivo)
        registros = [json.loads(linha) for linha in arquivo.getvalue().splitlines()]
        bruto = b"".join(base64.b64decode(r["base64"]) for r in registros if r["event"] == "rx")
        self.assertEqual(bruto, b"\x00\xff\r\nsensor=25")
        self.assertEqual(total, len(bruto))
        self.assertEqual(registros[-1]["total_bytes"], total)
        self.assertEqual(motivo, "completed")
        self.assertEqual(porta.escritas, [])

    def test_sem_confirmacao_at_nao_prepara_nem_abre_serial(self):
        argumentos = ["03_identificar_firmware.py", "--equipment", "bancada",
                      "--port", "COM-TESTE", "--baud", "9600"]
        with patch.object(sys, "argv", argumentos):
            with patch.object(at, "serial_preparada") as preparar, redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as resultado:
                    at.main()
                self.assertEqual(resultado.exception.code, 2)
                preparar.assert_not_called()

    def test_at_envia_somente_consultas_e_preserva_respostas(self):
        porta = SerialSimulada()
        arquivo = io.StringIO()
        with redirect_stdout(io.StringIO()):
            self.assertTrue(at.consultar(porta, arquivo, 0.1))
        self.assertEqual(porta.escritas, [b"AT\r", b"ATI\r", b"AT+CGMI\r", b"AT+CGMM\r", b"AT+CGMR\r"])
        respostas = [json.loads(linha) for linha in arquivo.getvalue().splitlines()
                     if json.loads(linha)["event"] == "at_response"]
        self.assertEqual(len(respostas), 5)
        self.assertTrue(all(r["terminal"] == "OK" for r in respostas))
        self.assertEqual(base64.b64decode(respostas[0]["base64"]), b"\r\nMODELO-TESTE\r\nOK\r\n")

    def test_sem_resposta_at_interrompe_apos_primeira_consulta(self):
        porta = SerialSimulada(responder_at=False)
        with redirect_stdout(io.StringIO()):
            self.assertFalse(at.consultar(porta, io.StringIO(), 0.01))
        self.assertEqual(porta.escritas, [b"AT\r"])

    def test_captura_nao_sobrescreve_evidencia_existente(self):
        with tempfile.TemporaryDirectory() as pasta:
            saida = Path(pasta) / "original.jsonl"
            saida.write_text("original", encoding="utf-8")
            porta = SerialSimulada()
            argumentos = ["02_captura_serial.py", "--equipment", "bancada",
                          "--port", "COM-TESTE", "--baud", "9600", "--output", str(saida)]
            with patch.object(sys, "argv", argumentos), patch.object(captura, "serial_preparada", return_value=porta):
                with self.assertRaises(FileExistsError):
                    captura.main()
            self.assertFalse(porta.aberta)
            self.assertEqual(saida.read_text(encoding="utf-8"), "original")

    def test_principal_sem_confirmacao_interface_nao_prepara_serial(self):
        for modulo in (captura, at):
            with self.subTest(script=modulo.__name__):
                argumentos = ["teste", "--equipment", "pedro-osorio", "--port", "COM-TESTE",
                              "--baud", "9600"]
                if modulo is at:
                    argumentos.append("--confirm-at")
                with patch.object(sys, "argv", argumentos), patch.object(modulo, "serial_preparada") as preparar:
                    with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as resultado:
                        modulo.main()
                    self.assertEqual(resultado.exception.code, 2)
                    preparar.assert_not_called()

    def test_unidade_e_baud_sao_obrigatorios_antes_de_preparar_serial(self):
        for modulo in (captura, at):
            for faltante in ("--equipment", "--baud"):
                with self.subTest(script=modulo.__name__, missing=faltante):
                    argumentos = ["teste", "--port", "COM-TESTE"]
                    if faltante != "--equipment":
                        argumentos.extend(["--equipment", "bancada"])
                    if faltante != "--baud":
                        argumentos.extend(["--baud", "9600"])
                    if modulo is at:
                        argumentos.append("--confirm-at")
                    with patch.object(sys, "argv", argumentos), patch.object(modulo, "serial_preparada") as preparar:
                        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                            modulo.main()
                        preparar.assert_not_called()

    def test_logs_e_pastas_identificam_unidade_em_captura_e_at(self):
        with tempfile.TemporaryDirectory() as pasta:
            for modulo in (captura, at):
                for unidade in ("bancada", "pedro-osorio"):
                    with self.subTest(script=modulo.__name__, equipment=unidade):
                        porta = SerialSimulada([b"\x00\xff"] if modulo is captura else [])
                        argumentos = ["teste", "--equipment", unidade, "--port", "COM-TESTE", "--baud", "19200"]
                        argumentos.extend(["--seconds", "0.01"] if modulo is captura else ["--confirm-at"])
                        if unidade == "pedro-osorio":
                            argumentos.append("--confirm-production-interface")
                        with patch.object(sys, "argv", argumentos), patch.object(comum, "RAIZ", Path(pasta)):
                            with patch.object(modulo, "serial_preparada", return_value=porta), redirect_stdout(io.StringIO()):
                                self.assertEqual(modulo.main(), 0)
                        prefixo = "serial" if modulo is captura else "identificacao-at"
                        arquivos = list((Path(pasta) / "dados" / "capturas" / unidade).glob(f"{prefixo}-*.jsonl"))
                        self.assertEqual(len(arquivos), 1)
                        registros = [json.loads(linha) for linha in arquivos[0].read_text(encoding="utf-8").splitlines()]
                        self.assertEqual(registros[0]["equipment"], unidade)
                        self.assertEqual(registros[0]["baud"], 19200)
                        self.assertEqual(registros[0]["production_interface_confirmed"], unidade == "pedro-osorio")
                        self.assertEqual(registros[-1]["reason"], "completed")
                        self.assertFalse(porta.aberta)
                        if modulo is captura:
                            self.assertEqual(porta.escritas, [])
                            self.assertEqual(registros[-1]["total_bytes"], 2)

    def test_falha_de_abertura_preserva_erro_e_fecha_porta(self):
        for modulo in (captura, at):
            with self.subTest(script=modulo.__name__), tempfile.TemporaryDirectory() as pasta:
                saida = Path(pasta) / "erro.jsonl"
                porta = SerialSimulada()
                argumentos = ["teste", "--equipment", "bancada", "--port", "COM-TESTE",
                              "--baud", "9600", "--output", str(saida)]
                if modulo is at:
                    argumentos.append("--confirm-at")
                with patch.object(sys, "argv", argumentos), patch.object(modulo, "serial_preparada", return_value=porta):
                    with patch.object(porta, "open", side_effect=OSError("porta indisponível")):
                        with patch.object(porta, "close", wraps=porta.close) as fechar:
                            with self.assertRaisesRegex(OSError, "porta indisponível"):
                                modulo.main()
                            fechar.assert_called_once()
                registros = [json.loads(linha) for linha in saida.read_text(encoding="utf-8").splitlines()]
                self.assertEqual(registros[0]["equipment"], "bancada")
                self.assertEqual(registros[-1]["event"], "end")
                self.assertIn(registros[-1]["reason"], ("open_error", "serial_error"))
                self.assertEqual(registros[-1]["error"], "porta indisponível")


class TestFirmware(unittest.TestCase):
    def test_indicadores_e_offsets_em_tres_codificacoes(self):
        for codificacao in ("ascii", "utf-16le", "utf-16be"):
            with self.subTest(encoding=codificacao):
                prefixo = b"\xff\xfe\x01"
                dados = prefixo + "https://telemetria.example.invalid/coleta".encode(codificacao) + b"\xff\x01"
                achados = firmware.analisar(dados)
                self.assertTrue(any(a["offset"] == len(prefixo) and a["encoding"] == codificacao
                                    and a["indicator"] == "https://" for a in achados))

    def test_dualbase_pcdweb_e_transportes_curtos_em_tres_codificacoes(self):
        for codificacao in ("ascii", "utf-16le", "utf-16be"):
            for texto in ("dualbase", "pcdweb", "tcp", "udp", "ftp", "SERVER_PORT"):
                with self.subTest(encoding=codificacao, indicator=texto):
                    prefixo = b"\xff\xfe\x01"
                    dados = prefixo + texto.encode(codificacao) + b"\xff\x01"
                    achados = firmware.analisar(dados)
                    self.assertTrue(any(a["offset"] == len(prefixo) and a["encoding"] == codificacao
                                        and a["indicator"].lower() == texto.lower() for a in achados))

    def test_relatorio_tem_hash_e_nao_modifica_imagem(self):
        with tempfile.TemporaryDirectory() as pasta:
            imagem = Path(pasta) / "teste.bin"
            saida = Path(pasta) / "relatorio.json"
            dados = b"\x00\x01https://teste.invalid/telemetria\x00"
            imagem.write_bytes(dados)
            resultado = subprocess.run([sys.executable, str(RAIZ / "scripts" / "04_analisar_firmware.py"),
                                        str(imagem), "--equipment", "bancada", "--output", str(saida)], capture_output=True, text=True)
            self.assertEqual(resultado.returncode, 0, resultado.stderr)
            relatorio = json.loads(saida.read_text(encoding="utf-8"))
            self.assertEqual(relatorio["sha256"], hashlib.sha256(dados).hexdigest())
            self.assertEqual(relatorio["size_bytes"], len(dados))
            self.assertEqual(relatorio["equipment"], "bancada")
            self.assertTrue(relatorio["findings"])
            self.assertEqual(imagem.read_bytes(), dados)


class TestReceptor(unittest.TestCase):
    def setUp(self):
        self.temporario = tempfile.TemporaryDirectory()
        self.saida = Path(self.temporario.name) / "recebido.jsonl"
        self.silenciar = patch.object(http.Receptor, "log_message", return_value=None)
        self.silenciar.start()
        self.servidor = http.criar_servidor("127.0.0.1", 0, self.saida)
        self.worker = threading.Thread(target=self.servidor.serve_forever, daemon=True)
        self.worker.start()

    def tearDown(self):
        self.servidor.shutdown()
        self.servidor.server_close()
        self.worker.join(timeout=2)
        self.silenciar.stop()
        self.temporario.cleanup()

    def enviar(self, caminho="/telemetria", corpo=b"abc", cabecalhos=None, automatico=True):
        conexao = HTTPConnection("127.0.0.1", self.servidor.server_port, timeout=3)
        try:
            if automatico:
                conexao.request("POST", caminho, body=corpo, headers=cabecalhos or {})
            else:
                conexao.putrequest("POST", caminho)
                for chave, valor in (cabecalhos or {}).items():
                    conexao.putheader(chave, valor)
                conexao.endheaders()
            resposta = conexao.getresponse()
            return resposta.status, resposta.read()
        finally:
            conexao.close()

    def test_receptor_preserva_bytes_e_acrescenta_registros(self):
        for corpo in (b"\x00\xff{\"valor\":25.3}\r\n", b"segunda amostra"):
            status, resposta = self.enviar(corpo=corpo, cabecalhos={"Content-Type": "application/octet-stream"})
            self.assertEqual(status, 200)
            self.assertTrue(json.loads(resposta)["ok"])
        registros = [json.loads(linha) for linha in self.saida.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(len(registros), 2)
        self.assertEqual(base64.b64decode(registros[0]["body_base64"]), b"\x00\xff{\"valor\":25.3}\r\n")
        self.assertEqual(registros[1]["body_sha256"], hashlib.sha256(b"segunda amostra").hexdigest())

    def test_rejeita_caminho_e_enquadramentos_invalidos_sem_registrar(self):
        self.assertEqual(self.enviar(caminho="/outro")[0], 404)
        casos = [({}, 411), ({"Content-Length": "abc"}, 400),
                 ({"Content-Length": "-1"}, 400), ({"Content-Length": "0"}, 400),
                 ({"Content-Length": str(http.LIMITE_CORPO + 1)}, 413),
                 ({"Transfer-Encoding": "chunked"}, 501)]
        for cabecalhos, esperado in casos:
            with self.subTest(headers=cabecalhos):
                self.assertEqual(self.enviar(cabecalhos=cabecalhos, automatico=False)[0], esperado)
        self.assertFalse(self.saida.exists())

    def test_falha_de_gravacao_nao_confirma_recebimento(self):
        with patch.object(http, "abrir_saida", side_effect=OSError("falha simulada")):
            self.assertEqual(self.enviar()[0], 500)
        self.assertFalse(self.saida.exists())


class TestComandos(unittest.TestCase):
    def test_ajuda_de_todos_os_scripts_sem_dependencia_serial(self):
        for arquivo in sorted((RAIZ / "scripts").glob("[0-9][0-9]_*.py")):
            with self.subTest(script=arquivo.name):
                resultado = subprocess.run([sys.executable, "-S", str(arquivo), "--help"], capture_output=True, text=True)
                self.assertEqual(resultado.returncode, 0, resultado.stderr)
                self.assertIn("usage:", resultado.stdout)


if __name__ == "__main__":
    unittest.main()
