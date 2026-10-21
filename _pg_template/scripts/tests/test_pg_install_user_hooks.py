import json
import tempfile
import unittest
from pathlib import Path

from scripts import pg_install_user_hooks as mod


class TestInstalador(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.home = Path(self._tmp.name)
        self.claude = self.home / ".claude" / "settings.json"
        self.codex = self.home / ".codex" / "hooks.json"

    def tearDown(self):
        self._tmp.cleanup()

    def correr(self, *args):
        return mod.main(["--home", str(self.home), *args])

    def grupos(self, path):
        return json.loads(path.read_text(encoding="utf-8"))["hooks"]["SessionStart"]

    def test_instala_nos_dois_ficheiros_sem_existirem(self):
        self.assertEqual(self.correr(), 0)
        self.assertEqual(self.grupos(self.claude), [mod.entrada_claude()])
        self.assertEqual(self.grupos(self.codex), [mod.entrada_codex()])

    def test_o_comando_usa_o_caminho_absoluto_deste_template(self):
        self.correr()
        comando = self.grupos(self.claude)[0]["hooks"][0]["command"]
        self.assertIn(str(mod.script_path()), comando)
        self.assertTrue(comando.endswith("-Hook"))

    def test_fora_do_windows_usa_pwsh(self):
        # powershell.exe so existe no Windows; num Mac o hook falharia em todas as sessoes.
        self.assertTrue(mod.entrada_claude("darwin")["hooks"][0]["command"].startswith("pwsh "))
        self.assertTrue(mod.entrada_claude("win32")["hooks"][0]["command"].startswith("powershell "))
        self.assertNotIn("ExecutionPolicy", mod.entrada_claude("linux")["hooks"][0]["command"])

    def test_mac_sem_pwsh_e_avisado_com_o_comando_do_brew(self):
        erro = mod.falta_pwsh("darwin", procurar=lambda _: None)
        self.assertIn("brew install powershell", erro)
        self.assertIsNone(mod.falta_pwsh("darwin", procurar=lambda _: "/usr/local/bin/pwsh"))
        self.assertIsNone(mod.falta_pwsh("win32", procurar=lambda _: None))

    def test_mac_sem_pwsh_nao_escreve_nada(self):
        original = mod.falta_pwsh
        mod.falta_pwsh = lambda plataforma=None, procurar=None: "sem pwsh"
        try:
            self.assertEqual(self.correr(), 2)
            self.assertEqual(self.correr("--check"), 1)
        finally:
            mod.falta_pwsh = original
        self.assertFalse(self.claude.exists())
        self.assertFalse(self.codex.exists())

    def test_preserva_o_resto_da_configuracao_do_utilizador(self):
        self.claude.parent.mkdir(parents=True)
        original = {
            "permissions": {"allow": ["Bash(git commit -m ' *)"]},
            "effortLevel": "high",
            "hooks": {"Stop": [{"hooks": [{"type": "command", "command": "outro"}]}],
                      "SessionStart": [{"hooks": [{"type": "command", "command": "meu-hook"}]}]},
        }
        self.claude.write_text(json.dumps(original), encoding="utf-8")
        self.correr("--sem-codex")
        dados = json.loads(self.claude.read_text(encoding="utf-8"))
        self.assertEqual(dados["permissions"], original["permissions"])
        self.assertEqual(dados["effortLevel"], "high")
        self.assertEqual(dados["hooks"]["Stop"], original["hooks"]["Stop"])
        self.assertEqual(dados["hooks"]["SessionStart"][0], original["hooks"]["SessionStart"][0])
        self.assertEqual(len(dados["hooks"]["SessionStart"]), 2)
        # Sem escapes \u0027: o ficheiro e do utilizador e deve continuar legivel.
        self.assertIn("git commit -m ' *", self.claude.read_text(encoding="utf-8"))

    def test_segunda_execucao_nao_duplica_nem_cria_copia(self):
        self.correr("--sem-codex")
        self.correr("--sem-codex")
        self.assertEqual(len(self.grupos(self.claude)), 1)
        self.assertEqual(list(self.claude.parent.glob("settings.json.bak-*")), [])

    def test_caminho_antigo_e_atualizado_com_copia_de_seguranca(self):
        self.claude.parent.mkdir(parents=True)
        antigo = {"hooks": {"SessionStart": [
            {"matcher": "*", "hooks": [{"type": "command", "command": 'powershell -File "D:\\velho\\scripts\\pg_auto_bootstrap.ps1" -Hook'}]}]}}
        self.claude.write_text(json.dumps(antigo), encoding="utf-8")
        self.assertEqual(self.correr("--check"), 1)
        self.correr("--sem-codex")
        self.assertEqual(self.grupos(self.claude), [mod.entrada_claude()])
        self.assertEqual(len(list(self.claude.parent.glob("settings.json.bak-*"))), 1)
        self.assertEqual(self.correr("--check"), 0)

    def test_whatif_nao_escreve(self):
        self.correr("--whatif")
        self.assertFalse(self.claude.exists())
        self.assertFalse(self.codex.exists())

    def test_json_invalido_nao_e_tocado(self):
        self.claude.parent.mkdir(parents=True)
        self.claude.write_text("{ isto nao e json", encoding="utf-8")
        self.assertEqual(self.correr("--sem-codex"), 2)
        self.assertEqual(self.claude.read_text(encoding="utf-8"), "{ isto nao e json")

    def test_remover_tira_so_o_nosso_hook(self):
        self.claude.parent.mkdir(parents=True)
        self.claude.write_text(json.dumps({"hooks": {"SessionStart": [{"hooks": [{"type": "command", "command": "meu-hook"}]}]}}), encoding="utf-8")
        self.correr("--sem-codex")
        self.correr("--sem-codex", "--remover")
        self.assertEqual(self.grupos(self.claude), [{"hooks": [{"type": "command", "command": "meu-hook"}]}])

    def test_remover_limpa_as_chaves_que_criou(self):
        self.correr("--sem-codex")
        self.correr("--sem-codex", "--remover")
        self.assertEqual(json.loads(self.claude.read_text(encoding="utf-8")), {})


class TestInstaladorAntigravity(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.home = Path(self._tmp.name)
        self.ficheiro = self.home / ".gemini" / "config" / "hooks.json"

    def tearDown(self):
        self._tmp.cleanup()

    def correr(self, *args):
        return mod.main(["--home", str(self.home), "--sem-codex", *args])

    def ler(self):
        return json.loads(self.ficheiro.read_text(encoding="utf-8"))

    def test_sem_antigravity_na_maquina_nao_cria_gemini(self):
        self.assertEqual(self.correr(), 0)
        self.assertFalse((self.home / ".gemini").exists())

    def test_instala_com_o_formato_do_antigravity(self):
        (self.home / ".gemini" / "antigravity").mkdir(parents=True)
        self.assertEqual(self.correr(), 0)
        entrada = self.ler()[mod.CHAVE_ANTIGRAVITY]
        self.assertEqual(entrada, mod.entrada_antigravity())
        comando = entrada["PreInvocation"][0]["command"]
        self.assertIn(mod.MARCA_ANTIGRAVITY, comando)
        self.assertIn("-Modo utilizador", comando)
        # PreInvocation e lista plana: sem `matcher` nem `hooks` aninhados.
        self.assertNotIn("matcher", entrada["PreInvocation"][0])

    def test_preserva_outros_hooks_e_remove_so_o_nosso(self):
        (self.home / ".gemini" / "antigravity").mkdir(parents=True)
        self.ficheiro.parent.mkdir(parents=True)
        alheio = {"lint": {"PostToolUse": [{"matcher": "*", "hooks": [{"command": "x"}]}]}}
        self.ficheiro.write_text(json.dumps(alheio), encoding="utf-8")
        self.correr()
        self.assertEqual(self.ler()["lint"], alheio["lint"])
        self.correr()
        self.assertEqual(len(list(self.ficheiro.parent.glob("hooks.json.bak-*"))), 1)
        self.correr("--remover")
        self.assertEqual(self.ler(), alheio)

    def test_comando_sem_aspas_duplas(self):
        # O Antigravity escapa as aspas duplas como \" ao chamar o cmd, e o PowerShell
        # passava a procurar um ficheiro com aspas no nome (falhou em todas as invocacoes).
        for plataforma in ("win32", "darwin"):
            self.assertNotIn('"', mod.entrada_antigravity(plataforma)["PreInvocation"][0]["command"])

    def test_fora_do_windows_usa_pwsh(self):
        self.assertTrue(mod.entrada_antigravity("darwin")["PreInvocation"][0]["command"].startswith("pwsh "))
        self.assertTrue(mod.entrada_antigravity("win32")["PreInvocation"][0]["command"].startswith("powershell "))


if __name__ == "__main__":
    unittest.main()
