#!/usr/bin/env python3
import argparse
import re
import sys
from pathlib import Path

DESTINOS_PROJETO = {
    "claude": ".claude/skills",
    "codex": ".agents/skills",
    "gemini": ".agents/skills",
    "cursor": ".agents/skills",
    "copilot": ".github/skills",
}

DESTINOS_GLOBAL = {
    "claude": "~/.claude/skills",
    "codex": "~/.agents/skills",
    "gemini": "~/.agents/skills",
    "cursor": "~/.agents/skills",
}

TODAS_AS_IAS = list(DESTINOS_PROJETO)


def perguntar(texto):
    return input(texto).strip()


def criar_skill(nome, descricao, instrucoes, destino, ias, escopo, forcar):
    nome = nome.strip().lower()

    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", nome):
        raise ValueError(
            "Nome inválido. Use letras minúsculas, números e hífens, "
            "por exemplo: revisar-codigo."
        )

    if not descricao.strip():
        raise ValueError("A descrição não pode ficar vazia.")

    if not instrucoes.strip():
        raise ValueError("As instruções não podem ficar vazias.")

    mapa = DESTINOS_PROJETO if escopo == "projeto" else DESTINOS_GLOBAL

    ias_invalidas = [ia for ia in ias if ia not in mapa]
    if ias_invalidas:
        nomes = ", ".join(ias_invalidas)
        raise ValueError(
            f"Estas IAs não têm destino configurado para escopo "
            f"'{escopo}': {nomes}"
        )

    raiz = Path(destino).expanduser().resolve()
    conteudo = (
        "---\n"
        f"name: {nome}\n"
        f"description: {descricao.strip()!r}\n"
        "---\n\n"
        f"{instrucoes.strip()}\n"
    )

    # Algumas ferramentas compartilham a mesma pasta. Agrupamos os destinos
    # para criar o arquivo apenas uma vez.
    destinos = {}
    for ia in ias:
        pasta_base = Path(mapa[ia]).expanduser()
        if not pasta_base.is_absolute():
            pasta_base = raiz / pasta_base

        pasta_skill = (pasta_base / nome).resolve()
        destinos.setdefault(pasta_skill, []).append(ia)

    # Verifica tudo antes de gravar, para evitar instalação parcial.
    existentes = [
        pasta / "SKILL.md"
        for pasta in destinos
        if (pasta / "SKILL.md").exists()
    ]
    if existentes and not forcar:
        lista = "\n".join(f"  - {arquivo}" for arquivo in existentes)
        raise FileExistsError(
            "Já existe uma skill com esse nome:\n"
            f"{lista}\n"
            "Use --forcar para substituí-la."
        )

    for pasta in destinos:
        pasta.mkdir(parents=True, exist_ok=True)
        (pasta / "SKILL.md").write_text(conteudo, encoding="utf-8")

    print(f"\nSkill '{nome}' criada com sucesso:")
    for pasta, ferramentas in destinos.items():
        print(f"  - {pasta} ({', '.join(ferramentas)})")


def main():
    parser = argparse.ArgumentParser(
        description="Cria e instala uma skill em várias ferramentas de IA."
    )
    parser.add_argument("--nome", help="Nome da skill, por exemplo: revisar-codigo")
    parser.add_argument("--descricao", help="Quando e para que a skill deve ser usada")
    parser.add_argument(
        "--instrucoes",
        help="Conteúdo/instruções da skill. Se omitido, será solicitado no terminal.",
    )
    parser.add_argument(
        "--ias",
        help="Lista separada por vírgulas: claude,codex,gemini,cursor,copilot",
    )
    parser.add_argument(
        "--escopo",
        choices=["projeto", "global"],
        default="projeto",
        help="Instala no projeto atual ou na pasta global do usuário.",
    )
    parser.add_argument(
        "--destino",
        default=".",
        help="Pasta do projeto. Usado no escopo 'projeto'.",
    )
    parser.add_argument(
        "--forcar",
        action="store_true",
        help="Permite substituir uma skill que já existe.",
    )
    args = parser.parse_args()

    try:
        nome = args.nome or perguntar("Nome da skill: ")
        descricao = args.descricao or perguntar("Descrição: ")

        if args.instrucoes:
            instrucoes = args.instrucoes
        else:
            print(
                "\nDigite as instruções da skill. "
                "Quando terminar, escreva FIM em uma linha separada:"
            )
            linhas = []
            while True:
                linha = sys.stdin.readline()
                if not linha:
                    break
                if linha.strip() == "FIM":
                    break
                linhas.append(linha.rstrip("\n"))
            instrucoes = "\n".join(linhas)

        if args.ias:
            ias = [ia.strip().lower() for ia in args.ias.split(",") if ia.strip()]
        else:
            sugestao = ", ".join(
                ["claude", "codex", "gemini", "cursor"]
                if args.escopo == "global"
                else TODAS_AS_IAS
            )
            resposta = perguntar(
                f"Ferramentas ({sugestao}) ou Enter para usar todas: "
            )
            ias = (
                [ia.strip().lower() for ia in resposta.split(",") if ia.strip()]
                if resposta
                else (
                    ["claude", "codex", "gemini", "cursor"]
                    if args.escopo == "global"
                    else TODAS_AS_IAS
                )
            )

        criar_skill(
            nome=nome,
            descricao=descricao,
            instrucoes=instrucoes,
            destino=args.destino,
            ias=ias,
            escopo=args.escopo,
            forcar=args.forcar,
        )

    except (ValueError, FileExistsError) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
