"""Instala (uma vez por maquina) o hook de UTILIZADOR que faz o bootstrap automatico.

O ritual e os hooks do projeto nao podem bootstrapar um repositorio novo: correm a partir
de `.pg_framework\\scripts\\` e de `.claude/settings.json`, e ambos sao criados PELO
bootstrap. O que existe antes de qualquer repositorio e a configuracao do utilizador --
e e ai que este script regista o `pg_auto_bootstrap.ps1`, com o caminho absoluto do
`_pg_template` desta maquina.

Escreve em:
  - ~/.claude/settings.json  -> hooks.SessionStart (Claude Code)
  - ~/.codex/hooks.json      -> hooks.SessionStart (Codex; `PONTO POR VALIDAR`: requer a
                                feature de hooks, e a leitura do ficheiro ao nivel do
                                utilizador nao esta confirmada em todas as versoes)
  - ~/.gemini/config/hooks.json -> "pg-auto-bootstrap".PreInvocation (Antigravity; so nas
                                maquinas onde ele esta instalado, isto e, com
                                ~/.gemini/antigravity. O Antigravity nao tem SessionStart:
                                o pg_hook_antigravity.ps1 -Modo utilizador corre o
                                auto-bootstrap na primeira invocacao de cada conversa.
                                `PONTO POR VALIDAR`: a leitura de hooks.json na
                                configuracao global esta documentada, mas nao foi
                                observada a disparar)

Idempotente: se o hook ja la estiver, atualiza o caminho (o _pg_template pode ter mudado de
sitio) e nao duplica. Faz copia de seguranca do ficheiro antes de o alterar, e nunca toca
noutras chaves.

Em Python, e nao em PowerShell, porque o ConvertTo-Json do PS 5.1 reescreve o ficheiro do
utilizador com escapes \\u0027 e indentacao propria -- e este ficheiro e dele, nao nosso.

Uso (em macOS/Linux, `python3` em vez de `py`):
  py scripts\\pg_install_user_hooks.py            # instala / atualiza
  py scripts\\pg_install_user_hooks.py --whatif   # mostra o que faria
  py scripts\\pg_install_user_hooks.py --check    # sai com 1 se nao estiver instalado
  py scripts\\pg_install_user_hooks.py --remover  # retira o hook
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARCA = "pg_auto_bootstrap.ps1"
MARCA_ANTIGRAVITY = "pg_hook_antigravity.ps1"
CHAVE_ANTIGRAVITY = "pg-auto-bootstrap"
TIMEOUT_SEGUNDOS = 300


def script_path() -> Path:
    return Path(__file__).resolve().parent / MARCA


def comando_windows() -> str:
    return f'powershell -NoProfile -ExecutionPolicy Bypass -File "{script_path()}" -Hook'


def comando_pwsh() -> str:
    return f'pwsh -NoProfile -File "{script_path()}" -Hook'


def comando_desta_plataforma(plataforma: str | None = None) -> str:
    # Ha gente da equipa em macOS, onde `powershell.exe` nao existe: um hook com ele
    # falharia em todas as sessoes. O Claude Code nao tem `command_windows` como o Codex,
    # pelo que se escolhe aqui, na maquina onde o hook fica instalado.
    plataforma = sys.platform if plataforma is None else plataforma
    return comando_windows() if plataforma.startswith("win") else comando_pwsh()


def entrada_claude(plataforma: str | None = None) -> dict:
    return {
        "matcher": "*",
        "hooks": [{"type": "command", "command": comando_desta_plataforma(plataforma), "timeout": TIMEOUT_SEGUNDOS}],
    }


def entrada_codex() -> dict:
    return {
        "hooks": [
            {
                "type": "command",
                "command": comando_pwsh(),
                "command_windows": comando_windows(),
                "timeout": TIMEOUT_SEGUNDOS,
            }
        ]
    }


def entrada_antigravity(plataforma: str | None = None) -> dict:
    # Formato do Antigravity: hooks com nome no topo do ficheiro, e PreInvocation e uma
    # lista plana de handlers (sem `matcher`). O comando corre por `cmd /c` no Windows e
    # `sh -c` nos outros, pelo que se escolhe o PowerShell aqui, como para o Claude.
    #
    # Sem aspas duplas no comando. O Antigravity (em Go) passa-o ao `cmd /c` escapando as
    # aspas internas como \", e o PowerShell recebe-as como parte do caminho:
    # `Processing -File '"C:\...\pg_hook_antigravity.ps1"' failed: Caracteres invalidos no
    # caminho`. FACTO OBSERVADO (2026-10-07): o hook falhou em todas as invocacoes da
    # primeira conversa real. Por isso `-Command . '<caminho>'`: aspas simples sobrevivem
    # ao escape, aceitam espacos, e o `.` (ao contrario do `&`) nao e operador do cmd.
    plataforma = sys.platform if plataforma is None else plataforma
    script = str(Path(__file__).resolve().parent / MARCA_ANTIGRAVITY).replace("'", "''")
    exe = "powershell -NoProfile -ExecutionPolicy Bypass" if plataforma.startswith("win") else "pwsh -NoProfile"
    comando = f"{exe} -Command . '{script}' -Evento PreInvocation -Modo utilizador"
    return {"PreInvocation": [{"type": "command", "command": comando, "timeout": TIMEOUT_SEGUNDOS}]}


def aplicar_antigravity(dados: dict, nova: dict | None) -> tuple[dict, str]:
    """Como `aplicar`, para o formato do Antigravity: so a chave CHAVE_ANTIGRAVITY e nossa."""
    if nova is None:
        if CHAVE_ANTIGRAVITY not in dados:
            return dados, "nada a remover"
        del dados[CHAVE_ANTIGRAVITY]
        return dados, "removido"
    if CHAVE_ANTIGRAVITY not in dados:
        dados[CHAVE_ANTIGRAVITY] = nova
        return dados, "instalado"
    if dados[CHAVE_ANTIGRAVITY] == nova:
        return dados, "ja instalado"
    dados[CHAVE_ANTIGRAVITY] = nova
    return dados, "atualizado"


def antigravity_instalado(home: Path) -> bool:
    return (home / ".gemini" / "antigravity").is_dir()


def ler_json(path: Path) -> dict:
    if not path.exists():
        return {}
    texto = path.read_text(encoding="utf-8-sig").strip()
    if not texto:
        return {}
    dados = json.loads(texto)  # JSON invalido: falha aqui, antes de escrever o que quer que seja
    if not isinstance(dados, dict):
        raise ValueError(f"{path} nao contem um objeto JSON")
    return dados


def tem_marca(grupo: dict) -> bool:
    return any(MARCA in str(h.get("command", "")) + str(h.get("command_windows", "")) for h in grupo.get("hooks", []))


def aplicar(dados: dict, nova: dict | None) -> tuple[dict, str]:
    """Devolve (dados alterados, acao). `nova=None` remove."""
    hooks = dados.setdefault("hooks", {})
    grupos = hooks.setdefault("SessionStart", [])
    existentes = [i for i, g in enumerate(grupos) if isinstance(g, dict) and tem_marca(g)]

    if nova is None:
        if not existentes:
            return dados, "nada a remover"
        hooks["SessionStart"] = [g for i, g in enumerate(grupos) if i not in existentes]
        if not hooks["SessionStart"]:
            del hooks["SessionStart"]
        if not hooks:
            del dados["hooks"]
        return dados, "removido"

    if not existentes:
        grupos.append(nova)
        return dados, "instalado"
    if grupos[existentes[0]] == nova and len(existentes) == 1:
        return dados, "ja instalado"
    grupos[existentes[0]] = nova
    hooks["SessionStart"] = [g for i, g in enumerate(grupos) if i not in existentes[1:]]
    return dados, "atualizado"


def processar(path: Path, nova: dict | None, whatif: bool, aplicador=aplicar) -> str:
    dados = ler_json(path)
    antes = json.dumps(dados, sort_keys=True)
    dados, acao = aplicador(dados, nova)
    if json.dumps(dados, sort_keys=True) == antes or whatif:
        return acao + (" (whatif)" if whatif and json.dumps(dados, sort_keys=True) != antes else "")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        copia = path.with_name(f"{path.name}.bak-{datetime.now():%Y%m%d_%H%M%S}")
        shutil.copy2(path, copia)
    path.write_text(json.dumps(dados, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return acao


def falta_pwsh(plataforma: str | None = None, procurar=shutil.which) -> str | None:
    """Mensagem de erro quando o PowerShell de que o hook depende nao existe, senao None.

    No macOS o PowerShell nao vem com o sistema. Um hook instalado sem ele falha no
    arranque de TODAS as sessoes, em qualquer pasta -- que e pior do que nao ter hook.
    `FACTO OBSERVADO` (2026-09-28): foi o primeiro reparo de quem o experimentou num Mac.
    """
    plataforma = sys.platform if plataforma is None else plataforma
    if plataforma.startswith("win") or procurar("pwsh"):
        return None
    instalar = "brew install powershell" if plataforma == "darwin" else "instalar o PowerShell 7 (pwsh)"
    return (f"o PowerShell (pwsh) nao esta instalado nesta maquina, e o hook precisa dele em todas as sessoes. "
            f"Instalar primeiro ({instalar}) e voltar a correr este comando.")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--whatif", action="store_true")
    ap.add_argument("--check", action="store_true", help="sai com 1 se o hook do Claude nao estiver instalado")
    ap.add_argument("--remover", action="store_true")
    ap.add_argument("--sem-codex", action="store_true")
    ap.add_argument("--sem-antigravity", action="store_true")
    ap.add_argument("--home", type=Path, default=Path.home(), help="testes: outra pasta pessoal")
    args = ap.parse_args(argv)

    claude = args.home / ".claude" / "settings.json"
    codex = args.home / ".codex" / "hooks.json"
    antigravity = args.home / ".gemini" / "config" / "hooks.json"

    if args.check:
        try:
            grupos = ler_json(claude).get("hooks", {}).get("SessionStart", [])
        except (ValueError, json.JSONDecodeError):
            grupos = []
        ok = any(isinstance(g, dict) and tem_marca(g) and entrada_claude() == g for g in grupos)
        print("OK: hook de auto-bootstrap instalado" if ok else "FALTA: hook de auto-bootstrap nao instalado (ou com caminho antigo)")
        erro = falta_pwsh()
        if erro:
            print(f"FALTA: {erro}")
            return 1
        return 0 if ok else 1

    if not script_path().exists():
        print(f"ERRO: {script_path()} nao existe", file=sys.stderr)
        return 2

    erro = None if args.remover else falta_pwsh()
    if erro:
        print(f"ERRO: {erro} Nada foi alterado.", file=sys.stderr)
        return 2

    alvos = [(claude, None if args.remover else entrada_claude(), aplicar)]
    if not args.sem_codex:
        alvos.append((codex, None if args.remover else entrada_codex(), aplicar))
    # So onde o Antigravity existe: criar ~/.gemini numa maquina sem ele nao serviria a ninguem.
    if not args.sem_antigravity and (antigravity_instalado(args.home) or (args.remover and antigravity.exists())):
        alvos.append((antigravity, None if args.remover else entrada_antigravity(), aplicar_antigravity))

    for path, nova, aplicador in alvos:
        try:
            acao = processar(path, nova, args.whatif, aplicador)
        except (ValueError, json.JSONDecodeError) as exc:
            print(f"ERRO: {path}: {exc} -- ficheiro NAO alterado", file=sys.stderr)
            return 2
        print(f"{acao}: {path}")
    if not args.remover:
        print(f"hook: {comando_desta_plataforma()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
