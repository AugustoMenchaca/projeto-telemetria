"""Validação das evidências e do ambiente local; nenhum acesso ao modem."""

import base64
from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from test_investigacao import RAIZ, SerialSimulada, at, captura, carregar, comum, firmware

validacao = carregar("validacao", "07_validar_evidencias.py")
verificacao = carregar("verificacao", "06_verificar_kit.py")


class TestEvidencias(unittest.TestCase):
    def setUp(self):
        self.temporario = tempfile.TemporaryDirectory()
        self.raiz = Path(self.temporario.name)
        self.caminho = self.raiz / "evidencia.jsonl"

    def tearDown(self):
        self.temporario.cleanup()

    def salvar(self, registros):
        self.caminho.write_text("".join(json.dumps(r) + "\n" for r in registros), encoding="utf-8")

    def serial(self, vazio=False):
        log = io.StringIO()
        comum.registrar(log, "start", equipment="bancada", port="COM-TESTE", baud=9600)
        captura.capturar(SerialSimulada([] if vazio else [b"\x00\xffabc"]), 0.005, log)
        return [json.loads(linha) for linha in log.getvalue().splitlines()]

    def test_captura_real_do_script_valida(self):
        self.salvar(self.serial())
        resultado = validacao.validar(self.caminho)
        self.assertEqual((resultado["status"], resultado["received_bytes"], resultado["equipment"]), ("valid", 5, "bancada"))

    def test_silencio_e_inconclusivo(self):
        self.salvar(self.serial(vazio=True))
        self.assertEqual(validacao.validar(self.caminho)["status"], "inconclusive")

    def test_alteracoes_de_bytes_ou_resumo_sao_rejeitadas(self):
        for indice, chave, valor in ((1, "base64", "?"), (1, "hex", "00"), (1, "bytes", 999),
                                    (-1, "total_bytes", 999), (-1, "chunks", 999), (0, "equipment", "outra"),
                                    (0, "timestamp", "2026-10-28T12:00:00")):
            with self.subTest(field=chave):
                registros = self.serial()
                registros[indice][chave] = valor
                self.salvar(registros)
                with self.assertRaises(ValueError):
                    validacao.validar(self.caminho)

    def test_captura_sem_evento_final_e_rejeitada(self):
        self.salvar(self.serial()[:-1])
        with self.assertRaisesRegex(ValueError, "falta evento end"):
            validacao.validar(self.caminho)

    def test_producao_sem_confirmacao_e_rejeitada(self):
        registros = self.serial()
        registros[0]["equipment"] = "pedro-osorio"
        self.salvar(registros)
        with self.assertRaisesRegex(ValueError, "produção"):
            validacao.validar(self.caminho)

    def test_jsonl_sem_nova_linha_e_rejeitado(self):
        self.salvar(self.serial())
        self.caminho.write_bytes(self.caminho.read_bytes().rstrip(b"\n"))
        with self.assertRaisesRegex(ValueError, "quebra de linha"):
            validacao.validar(self.caminho)

    def test_arquivo_vazio_e_inconclusivo(self):
        self.caminho.write_bytes(b"")
        self.assertEqual(validacao.validar(self.caminho)["status"], "inconclusive")

    def test_tamanho_de_evidencia_e_limitado(self):
        self.caminho.write_bytes(b"12345")
        with self.assertRaisesRegex(ValueError, "limite"):
            validacao.validar(self.caminho, max_bytes=4)

    def test_at_do_script_valida_e_confere_terminal(self):
        log = io.StringIO()
        comum.registrar(log, "start", equipment="bancada", port="COM-TESTE", baud=9600, confirmed_at=True)
        with redirect_stdout(io.StringIO()):
            self.assertTrue(at.consultar(SerialSimulada(), log, 0.1))
        comum.registrar(log, "end", reason="completed")
        registros = [json.loads(linha) for linha in log.getvalue().splitlines()]
        self.salvar(registros)
        self.assertEqual(validacao.validar(self.caminho)["kind"], "serial-at")
        next(r for r in registros if r["event"] == "at_response")["terminal"] = "ERROR"
        self.salvar(registros)
        with self.assertRaisesRegex(ValueError, "terminal"):
            validacao.validar(self.caminho)

    def test_http_confere_hash_e_bytes(self):
        corpo = b"\xff\x00amostra"
        registro = {"timestamp": comum.agora(), "method": "POST", "path": "/telemetria",
                    "body_bytes": len(corpo), "body_base64": base64.b64encode(corpo).decode("ascii"),
                    "body_sha256": hashlib.sha256(corpo).hexdigest()}
        self.salvar([registro])
        self.assertEqual(validacao.validar(self.caminho)["kind"], "http-bench")
        registro["body_sha256"] = "0" * 64
        self.salvar([registro])
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            validacao.validar(self.caminho)

    def test_inventario_vazio_nao_confirma_modem(self):
        documento = {"timestamp": comum.agora(), "ports": []}
        self.assertEqual(validacao.validar_json(documento)["ports"], 0)
        documento["ports"] = [{"port": "COM1"}, {"port": "COM1"}]
        with self.assertRaisesRegex(ValueError, "duplicada"):
            validacao.validar_json(documento)

    def test_analise_de_firmware_confere_hash_e_offset_no_original(self):
        bruto = b"\x00dualbase\x00pcdweb\x00"
        imagem = self.raiz / "origem.bin"
        imagem.write_bytes(bruto)
        documento = {"timestamp": comum.agora(), "equipment": "bancada", "size_bytes": len(bruto),
                     "sha256": hashlib.sha256(bruto).hexdigest(), "findings": firmware.analisar(bruto)}
        self.assertTrue(validacao.validar_json(documento, imagem)["source_verified"])
        documento["findings"][0]["offset"] += 1
        with self.assertRaisesRegex(ValueError, "offset"):
            validacao.validar_json(documento, imagem)

    def test_cli_retorna_codigo_e_relatorio_para_arquivo_corrompido(self):
        self.caminho.write_text('{"incompleto":', encoding="utf-8")
        saida = self.raiz / "relatorio.json"
        processo = subprocess.run([sys.executable, str(RAIZ / "scripts/07_validar_evidencias.py"),
                                  str(self.caminho), "--output", str(saida)], capture_output=True, text=True)
        self.assertEqual(processo.returncode, 1)
        self.assertEqual(json.loads(saida.read_text(encoding="utf-8"))["results"][0]["status"], "invalid")

    def test_cli_silencio_retorna_inconclusivo(self):
        self.salvar(self.serial(vazio=True))
        processo = subprocess.run([sys.executable, str(RAIZ / "scripts/07_validar_evidencias.py"), str(self.caminho)],
                                 capture_output=True, text=True)
        self.assertEqual(processo.returncode, 2)


class TestVerificacao(unittest.TestCase):
    def test_fontes_e_documentacao_do_projeto(self):
        self.assertIn("fontes", verificacao.conferir_fontes(RAIZ))
        self.assertIn("links", verificacao.conferir_documentacao(RAIZ))

    def test_falta_arquivo_obrigatorio_falha(self):
        with tempfile.TemporaryDirectory() as pasta, self.assertRaisesRegex(ValueError, "ausente"):
            verificacao.conferir_documentacao(Path(pasta))

    def test_dependencia_offline_confere_hash(self):
        self.assertIn("SHA-256", verificacao.conferir_dependencia_offline(RAIZ))

    def test_dependencia_offline_alterada_falha(self):
        with tempfile.TemporaryDirectory() as pasta:
            raiz = Path(pasta)
            (raiz / "offline").mkdir()
            (raiz / "requirements.txt").write_text("pyserial==3.5 --hash=sha256:" + "0" * 64, encoding="utf-8")
            (raiz / "offline/pyserial-3.5-py2.py3-none-any.whl").write_bytes(b"alterado")
            with self.assertRaisesRegex(ValueError, "diverge"):
                verificacao.conferir_dependencia_offline(raiz)

    def test_subprocesso_falho_e_reportado(self):
        resultado = verificacao.rodar_comando([sys.executable, "-c", "raise SystemExit(7)"], RAIZ)
        self.assertEqual((resultado["status"], resultado["exit_code"]), ("FAIL", 7))

    def test_subprocesso_timeout_e_reportado(self):
        with patch.object(verificacao.subprocess, "run", side_effect=subprocess.TimeoutExpired("teste", 1)):
            self.assertEqual(verificacao.rodar_comando(["teste"], RAIZ, timeout=1)["status"], "FAIL")

    def test_powershell_tem_sintaxe_valida(self):
        comando = shutil.which("pwsh") or shutil.which("powershell")
        if not comando:
            self.skipTest("PowerShell indisponível neste sistema")
        for nome in ("Preparar.ps1", "Verificar.ps1"):
            caminho = str(RAIZ / nome).replace("'", "''")
            script = "$telemetriaTokens=$null; $telemetriaErrors=$null; [void][System.Management.Automation.Language.Parser]::ParseFile('" + caminho + "',[ref]$telemetriaTokens,[ref]$telemetriaErrors); if($telemetriaErrors.Count){exit 1}"
            processo = subprocess.run([comando, "-NoProfile", "-NonInteractive", "-Command", script], capture_output=True, text=True)
            self.assertEqual(processo.returncode, 0, processo.stderr)


if __name__ == "__main__":
    unittest.main()
