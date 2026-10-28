"""Falhas, limites, integração PySerial loopback e concorrência HTTP sem modem."""

import argparse
from concurrent.futures import ThreadPoolExecutor
from contextlib import redirect_stderr, redirect_stdout
import hashlib
from http.client import HTTPConnection
import io
import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import test_investigacao as base
from test_investigacao import (RAIZ, SerialSimulada, at, captura,
                                carregar, comum, firmware, http)

portas = carregar("portas", "01_portas.py")


class TestUtilidades(unittest.TestCase):
    def test_duracoes_invalidas(self):
        for valor in ("0", "-1", "nan", "inf", "-inf"):
            with self.subTest(value=valor), self.assertRaises(argparse.ArgumentTypeError):
                comum.segundos_positivos(valor)

    def test_inteiros_invalidos(self):
        for valor in ("0", "-1"):
            with self.subTest(value=valor), self.assertRaises(argparse.ArgumentTypeError):
                comum.inteiro_positivo(valor)

    def test_destinos_unicos_com_unidade(self):
        with tempfile.TemporaryDirectory() as pasta, patch.object(comum, "RAIZ", Path(pasta)):
            caminhos = {comum.destino("capturas/bancada", "serial") for _ in range(100)}
            self.assertEqual(len(caminhos), 100)
            self.assertTrue(all(p.parent == Path(pasta) / "dados/capturas/bancada" for p in caminhos))

    def test_serial_configurada_sem_abrir_e_sinais_desativados(self):
        parametros = SimpleNamespace(port="COM-TESTE", baud=19200, data_bits=7, parity="E", stop_bits=2)
        porta = SerialSimulada()
        with patch.object(comum, "biblioteca_serial", return_value=SimpleNamespace(Serial=lambda port: porta)):
            preparada = comum.serial_preparada(parametros)
        self.assertIs(preparada, porta)
        self.assertFalse(porta.aberta)
        self.assertFalse(porta.dtr or porta.rts or porta.rtscts or porta.dsrdtr or porta.xonxoff)
        self.assertEqual((porta.baudrate, porta.bytesize, porta.parity, porta.stopbits), (19200, 7, "E", 2))

    def test_falta_pyserial_e_reportada_sem_traceback(self):
        original = __import__
        def importar(nome, *args, **kwargs):
            if nome == "serial":
                raise ImportError("simulado")
            return original(nome, *args, **kwargs)
        with patch("builtins.__import__", side_effect=importar):
            with self.assertRaisesRegex(RuntimeError, "Instale as dependências"):
                comum.biblioteca_serial()

    def test_codigos_de_saida_e_erros_sem_traceback(self):
        for erro, codigo in ((OSError("falha"), 1), (RuntimeError("falha"), 1), (KeyboardInterrupt(), 130)):
            with self.subTest(error=type(erro).__name__), redirect_stderr(io.StringIO()):
                def falhar():
                    raise erro
                self.assertEqual(comum.executar(falhar), codigo)


class TestInventario(unittest.TestCase):
    def test_lista_e_salva_sem_abrir_dispositivo(self):
        from serial.tools import list_ports
        dispositivo = SimpleNamespace(device="COM-TESTE", description="Conversor simulado", manufacturer="Teste",
                                      vid=1234, pid=5678, serial_number="SINTETICO", hwid="TEST")
        with tempfile.TemporaryDirectory() as pasta:
            saida = Path(pasta) / "portas.json"
            with patch.object(sys, "argv", ["portas", "--output", str(saida)]):
                with patch.object(list_ports, "comports", return_value=[dispositivo]), patch("serial.Serial") as abrir:
                    with redirect_stdout(io.StringIO()):
                        portas.main()
                abrir.assert_not_called()
            self.assertEqual(json.loads(saida.read_text(encoding="utf-8"))["ports"][0]["port"], "COM-TESTE")

    def test_inventario_vazio_e_valido_sem_inferir_modem(self):
        from serial.tools import list_ports
        with patch.object(sys, "argv", ["portas"]), patch.object(list_ports, "comports", return_value=[]):
            saida = io.StringIO()
            with redirect_stdout(saida):
                portas.main()
            self.assertIn("Nenhuma porta", saida.getvalue())

    def test_inventario_nao_sobrescreve_arquivo(self):
        from serial.tools import list_ports
        with tempfile.TemporaryDirectory() as pasta:
            saida = Path(pasta) / "portas.json"
            saida.write_text("original", encoding="utf-8")
            with patch.object(sys, "argv", ["portas", "--output", str(saida)]):
                with patch.object(list_ports, "comports", return_value=[]), redirect_stdout(io.StringIO()):
                    with self.assertRaises(FileExistsError):
                        portas.main()
            self.assertEqual(saida.read_text(encoding="utf-8"), "original")


class TestCapturaFalhas(unittest.TestCase):
    def test_silencio_registra_zero_bytes_e_tempo(self):
        log = io.StringIO()
        total, motivo = captura.capturar(SerialSimulada(), 0.005, log)
        fim = json.loads(log.getvalue())
        self.assertEqual((total, motivo, fim["chunks"]), (0, "completed", 0))
        self.assertGreaterEqual(fim["elapsed_seconds"], 0)

    def test_interrupcao_preserva_dados_e_resumo(self):
        porta = SerialSimulada()
        log = io.StringIO()
        with patch.object(porta, "read", side_effect=[b"abc", KeyboardInterrupt()]):
            total, motivo = captura.capturar(porta, 5, log)
        self.assertEqual((total, motivo), (3, "interrupted"))
        self.assertEqual(json.loads(log.getvalue().splitlines()[-1])["total_bytes"], 3)

    def test_desconexao_preserva_bytes_anteriores_e_erro(self):
        porta = SerialSimulada()
        log = io.StringIO()
        with patch.object(porta, "read", side_effect=[b"abc", OSError("desconectado")]):
            with self.assertRaises(OSError):
                captura.capturar(porta, 5, log)
        fim = json.loads(log.getvalue().splitlines()[-1])
        self.assertEqual((fim["reason"], fim["total_bytes"], fim["error"]), ("serial_error", 3, "desconectado"))

    def test_pyserial_real_em_loopback_sem_hardware(self):
        import serial
        with serial.serial_for_url("loop://", timeout=0.005) as porta:
            bruto = bytes(range(256))
            porta.write(bruto)  # Apenas semeia o dispositivo virtual do teste.
            log = io.StringIO()
            with patch.object(porta, "write", wraps=porta.write) as escrever:
                total, motivo = captura.capturar(porta, 0.03, log)
            escrever.assert_not_called()
        self.assertEqual((total, motivo), (len(bruto), "completed"))
        self.assertEqual(json.loads(log.getvalue().splitlines()[0])["hex"], bruto.hex())


class TestATFalhas(unittest.TestCase):
    def test_erro_em_identificacao_interrompe_sem_proximo_comando(self):
        porta = SerialSimulada(responder_at=False)
        def responder(dados):
            porta.escritas.append(dados)
            porta.blocos.append(b"OK\r\n" if dados == b"AT\r" else b"ERROR\r\n")
            return len(dados)
        with patch.object(porta, "write", side_effect=responder), redirect_stdout(io.StringIO()):
            self.assertFalse(at.consultar(porta, io.StringIO(), 0.1))
        self.assertEqual(porta.escritas, [b"AT\r", b"ATI\r"])

    def test_linhas_fragmentadas_nao_confundem_ok_com_payload(self):
        porta = SerialSimulada([b"TOKEN_OK\r\nO", b"K", b"\r", b"\n"])
        dados, terminal = at.ler_resposta(porta, 0.1)
        self.assertEqual(terminal, "OK")
        self.assertEqual(dados, b"TOKEN_OK\r\nOK\r")

    def test_terminais_erro_estendido(self):
        for erro in (b"ERROR", b"+CME ERROR: 10", b"+CMS ERROR: 500"):
            with self.subTest(error=erro):
                dados, terminal = at.ler_resposta(SerialSimulada([erro + b"\r\n"]), 0.1)
                self.assertEqual(terminal, erro.decode("ascii"))

    def test_resposta_limitada_nao_cresce_sem_fim(self):
        porta = SerialSimulada([b"abcd", b"efgh"])
        with patch.object(at, "LIMITE_RESPOSTA", 8):
            dados, terminal = at.ler_resposta(porta, 1)
        self.assertEqual((len(dados), terminal), (8, None))

    def test_escrita_parcial_interrompe(self):
        porta = SerialSimulada()
        with patch.object(porta, "write", return_value=1), self.assertRaisesRegex(RuntimeError, "incompleta"):
            at.consultar(porta, io.StringIO(), 0.1)

    def test_bytes_antes_de_desconectar_ficam_no_log(self):
        porta = SerialSimulada(responder_at=False)
        log = io.StringIO()
        with patch.object(porta, "read", side_effect=[b"PARCIAL", OSError("desconectado")]):
            with self.assertRaises(OSError):
                at.consultar(porta, log, 1)
        registros = [json.loads(linha) for linha in log.getvalue().splitlines()]
        self.assertEqual(registros[-1]["event"], "at_rx")
        self.assertEqual(registros[-1]["hex"], b"PARCIAL".hex())

    def test_interrupcao_main_fecha_porta_e_registra_termino(self):
        porta = SerialSimulada()
        with tempfile.TemporaryDirectory() as pasta:
            saida = Path(pasta) / "at.jsonl"
            argumentos = ["at", "--equipment", "bancada", "--port", "COM-TESTE", "--baud", "9600", "--confirm-at", "--output", str(saida)]
            with patch.object(sys, "argv", argumentos), patch.object(at, "serial_preparada", return_value=porta):
                with patch.object(at, "consultar", side_effect=KeyboardInterrupt()), self.assertRaises(KeyboardInterrupt):
                    at.main()
            self.assertFalse(porta.aberta)
            self.assertEqual(json.loads(saida.read_text(encoding="utf-8").splitlines()[-1])["reason"], "interrupted")


class TestFirmwareLimites(unittest.TestCase):
    def rodar(self, dados, *extras):
        with tempfile.TemporaryDirectory() as pasta:
            imagem = Path(pasta) / "imagem.bin"
            saida = Path(pasta) / "relatorio.json"
            imagem.write_bytes(dados)
            processo = subprocess.run([sys.executable, str(RAIZ / "scripts/04_analisar_firmware.py"), str(imagem),
                                      "--equipment", "bancada", "--output", str(saida), *extras], capture_output=True, text=True)
            resultado = json.loads(saida.read_text(encoding="utf-8")) if saida.exists() else None
            self.assertEqual(imagem.read_bytes(), dados)
            return processo, resultado

    def test_arquivo_vazio_rejeitado(self):
        processo, relatorio = self.rodar(b"")
        self.assertEqual(processo.returncode, 1)
        self.assertIsNone(relatorio)

    def test_tamanho_excessivo_rejeitado_antes_de_analisar(self):
        processo, relatorio = self.rodar(b"12345", "--max-bytes", "4")
        self.assertEqual(processo.returncode, 1)
        self.assertIsNone(relatorio)

    def test_truncamento_de_pistas_e_explicito(self):
        processo, relatorio = self.rodar(b"dualbase\x00pcdweb\x00tcp\x00", "--max-findings", "1")
        self.assertEqual(processo.returncode, 0, processo.stderr)
        self.assertEqual(len(relatorio["findings"]), 1)
        self.assertTrue(relatorio["findings_truncated"])

    def test_sem_pistas_nao_e_considerado_destino_ausente(self):
        processo, relatorio = self.rodar(b"\x01\x02\xff\x00")
        self.assertEqual(processo.returncode, 0)
        self.assertEqual(relatorio["findings"], [])
        self.assertFalse(relatorio["findings_truncated"])

    def test_analise_nao_sobrescreve_relatorio(self):
        with tempfile.TemporaryDirectory() as pasta:
            imagem = Path(pasta) / "imagem.bin"
            saida = Path(pasta) / "relatorio.json"
            imagem.write_bytes(b"dualbase")
            saida.write_text("original", encoding="utf-8")
            argumentos = ["firmware", str(imagem), "--equipment", "bancada", "--output", str(saida)]
            with patch.object(sys, "argv", argumentos), self.assertRaises(FileExistsError):
                firmware.main()
            self.assertEqual(saida.read_text(encoding="utf-8"), "original")


class TestArgumentosHTTP(unittest.TestCase):
    def test_portas_invalidas_nao_iniciam_servidor(self):
        for porta in ("0", "-1", "65536"):
            with self.subTest(port=porta), patch.object(sys, "argv", ["http", "--port", porta]):
                with patch.object(http, "criar_servidor") as criar, redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as resultado:
                        http.main()
                    self.assertEqual(resultado.exception.code, 2)
                    criar.assert_not_called()


class TestHTTPAdicional(unittest.TestCase):
    setUp = base.TestReceptor.setUp
    tearDown = base.TestReceptor.tearDown
    enviar = base.TestReceptor.enviar

    def bruto(self, dados, finalizar=True):
        with socket.create_connection(("127.0.0.1", self.servidor.server_port), timeout=2) as conexao:
            conexao.sendall(dados)
            if finalizar:
                conexao.shutdown(socket.SHUT_WR)
            recebido = bytearray()
            while True:
                bloco = conexao.recv(65536)
                if not bloco:
                    break
                recebido.extend(bloco)
            return bytes(recebido)

    def test_health_informa_ensaio_sem_validar_modem(self):
        conexao = HTTPConnection("127.0.0.1", self.servidor.server_port, timeout=2)
        try:
            conexao.request("GET", "/health")
            resposta = conexao.getresponse()
            self.assertEqual(resposta.status, 200)
            self.assertFalse(json.loads(resposta.read())["protocol_confirmed"])
        finally:
            conexao.close()
        self.assertFalse(self.saida.exists())

    def test_content_length_duplicado_rejeitado(self):
        resposta = self.bruto(b"POST /telemetria HTTP/1.0\r\nContent-Length: 3\r\nContent-Length: 3\r\n\r\nabc")
        self.assertIn(b" 400 ", resposta.split(b"\r\n")[0])
        self.assertFalse(self.saida.exists())

    def test_corpo_truncado_nao_e_confirmado(self):
        resposta = self.bruto(b"POST /telemetria HTTP/1.0\r\nContent-Length: 5\r\n\r\nabc")
        self.assertIn(b" 400 ", resposta.split(b"\r\n")[0])
        self.assertFalse(self.saida.exists())

    def test_timeout_de_leitura_nao_grava_nem_confirma(self):
        self.servidor.read_timeout = 0.05
        resposta = self.bruto(b"POST /telemetria HTTP/1.0\r\nContent-Length: 5\r\n\r\nabc", finalizar=False)
        self.assertIn(b" 408 ", resposta.split(b"\r\n")[0])
        self.assertFalse(self.saida.exists())

    def test_fsync_falhou_nao_confirma(self):
        with patch.object(http.os, "fsync", side_effect=OSError("disco indisponível")):
            self.assertEqual(self.enviar()[0], 500)

    def test_concorrencia_preserva_registros_integros(self):
        corpos = [f"amostra-{i}".encode("ascii") for i in range(12)]
        with ThreadPoolExecutor(max_workers=4) as pool:
            resultados = list(pool.map(lambda corpo: self.enviar(corpo=corpo), corpos))
        self.assertTrue(all(status == 200 for status, _ in resultados))
        registros = [json.loads(linha) for linha in self.saida.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(len(registros), len(corpos))
        self.assertEqual({r["body_sha256"] for r in registros}, {hashlib.sha256(c).hexdigest() for c in corpos})

    def test_corpo_no_limite_e_preservado(self):
        corpo = b"x" * http.LIMITE_CORPO
        self.assertEqual(self.enviar(corpo=corpo)[0], 200)
        self.assertEqual(json.loads(self.saida.read_text(encoding="utf-8"))["body_bytes"], len(corpo))

    def test_log_existente_incompleto_nao_e_continuado(self):
        self.saida.write_text('{"parcial":', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "incompleto"):
            http.criar_servidor("127.0.0.1", 0, self.saida)

    def test_expect_rejeitado_sem_aguardar_corpo(self):
        resposta = self.bruto(b"POST /telemetria HTTP/1.0\r\nContent-Length: 5\r\nExpect: 100-continue\r\n\r\n")
        self.assertIn(b" 417 ", resposta.split(b"\r\n")[0])
        self.assertFalse(self.saida.exists())


if __name__ == "__main__":
    unittest.main()
