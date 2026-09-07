import json
import sys
from pathlib import Path

ARQUIVO = Path(__file__).parent / "tarefas.json"


def carregar_tarefas():
    if not ARQUIVO.exists():
        return []
    try:
        with open(ARQUIVO, "r", encoding="utf-8") as f:
            dados = json.load(f)
    except json.JSONDecodeError:
        print(f"Erro: {ARQUIVO.name} contém JSON inválido.")
        sys.exit(1)
    except OSError as e:
        print(f"Erro ao ler {ARQUIVO.name}: {e}")
        sys.exit(1)

    if not isinstance(dados, list):
        print(f"Erro: {ARQUIVO.name} deve conter uma lista de tarefas.")
        sys.exit(1)
    return dados


def salvar_tarefas(tarefas):
    try:
        with open(ARQUIVO, "w", encoding="utf-8") as f:
            json.dump(tarefas, f, ensure_ascii=False, indent=2)
    except OSError as e:
        print(f"Erro ao salvar {ARQUIVO.name}: {e}")
        sys.exit(1)


def adicionar_tarefa(descricao):
    tarefas = carregar_tarefas()
    tarefas.append({"descricao": descricao, "concluida": False})
    salvar_tarefas(tarefas)
    print(f"Tarefa adicionada: {descricao}")


def listar_tarefas():
    tarefas = carregar_tarefas()
    if not tarefas:
        print("Nenhuma tarefa cadastrada.")
        return
    for i, tarefa in enumerate(tarefas, start=1):
        status = "x" if tarefa["concluida"] else " "
        print(f"[{status}] {i}. {tarefa['descricao']}")


def remover_tarefa(indice):
    tarefas = carregar_tarefas()
    if indice < 1 or indice > len(tarefas):
        print("Número de tarefa inválido.")
        return
    removida = tarefas.pop(indice - 1)
    salvar_tarefas(tarefas)
    print(f"Tarefa removida: {removida['descricao']}")


def concluir_tarefa(indice):
    tarefas = carregar_tarefas()
    if indice < 1 or indice > len(tarefas):
        print("Número de tarefa inválido.")
        return
    tarefas[indice - 1]["concluida"] = True
    salvar_tarefas(tarefas)
    print(f"Tarefa concluída: {tarefas[indice - 1]['descricao']}")


def imprimir_ajuda():
    print("Uso:")
    print("  python todo.py adicionar <descrição da tarefa>")
    print("  python todo.py listar")
    print("  python todo.py remover <número>")
    print("  python todo.py concluir <número>")


def main():
    if len(sys.argv) < 2:
        imprimir_ajuda()
        return

    comando = sys.argv[1]

    if comando == "adicionar":
        if len(sys.argv) < 3:
            print("Informe a descrição da tarefa.")
            return
        descricao = " ".join(sys.argv[2:])
        adicionar_tarefa(descricao)

    elif comando == "listar":
        listar_tarefas()

    elif comando == "remover":
        if len(sys.argv) < 3:
            print("Informe o número da tarefa a remover.")
            return
        try:
            indice = int(sys.argv[2])
        except ValueError:
            print("O número da tarefa deve ser um inteiro.")
            return
        remover_tarefa(indice)

    elif comando == "concluir":
        if len(sys.argv) < 3:
            print("Informe o número da tarefa a concluir.")
            return
        try:
            indice = int(sys.argv[2])
        except ValueError:
            print("O número da tarefa deve ser um inteiro.")
            return
        concluir_tarefa(indice)

    else:
        imprimir_ajuda()


if __name__ == "__main__":
    main()
