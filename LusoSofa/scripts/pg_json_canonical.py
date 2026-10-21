"""Reescreve um ficheiro JSON na forma canonica do framework.

Existe porque o ConvertTo-Json do Windows PowerShell 5.1 e o do PowerShell 7
formatam de maneira diferente (indentacao cumulativa vs 2 espacos, dois espacos
depois de ':', arrays vazios em tres linhas vs '[]'). Quem gerava o
doc_templates/MANIFEST.json reescrevia-o de ponta a ponta consoante o shell que
corresse o pull, o que produzia diffs de ~1000 linhas sem uma unica mudanca de
conteudo. Passando o JSON por aqui, o ficheiro depende do conteudo e nao do shell.

Forma canonica: indentacao de 2 espacos, nao-ASCII literal (sem \\uXXXX), ordem
das chaves preservada tal como vem do produtor, LF como fim de linha e uma linha
em branco final.
"""

import argparse
import json


def canonical_text(payload):
    """Devolve o texto canonico de um objeto ja desserializado."""
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def canonicalize_file(input_path, output_path):
    with open(input_path, "r", encoding="utf-8-sig") as handle:
        payload = json.load(handle)

    # newline="\n" e obrigatorio: sem ele, o Python em Windows traduz "\n" para
    # "\r\n" ao escrever, o que reintroduzia exactamente a divergencia que este
    # script existe para eliminar.
    with open(output_path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(canonical_text(payload))


def _main():
    parser = argparse.ArgumentParser(description="Reescreve um JSON na forma canonica do framework.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    canonicalize_file(args.input, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
