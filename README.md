# Projetos

Este repositório contém dois projetos independentes:

- **todo-cli** (raiz deste repositório): CLI simples de lista de tarefas, descrita abaixo.
- **[controle_escolar](controle_escolar/README.md)**: sistema web em Flask para controle escolar (turmas, disciplinas, professores, alunos, notas por bimestre, presença e boletim em PDF). Veja as instruções de instalação e uso no [README do projeto](controle_escolar/README.md).

---

# todo-cli

CLI simples em Python para gerenciar uma lista de tarefas, armazenada em `tarefas.json`.

## Requisitos

- Python 3

## Uso

```
python todo.py adicionar <descrição da tarefa>
python todo.py listar
python todo.py concluir <número>
python todo.py remover <número>
```

### Exemplos

```
python todo.py adicionar comprar uva
python todo.py listar
python todo.py concluir 1
python todo.py remover 1
```

## Armazenamento

As tarefas ficam em `tarefas.json`, no mesmo diretório do script, como uma lista de objetos:

```json
[
  {
    "descricao": "comprar uva",
    "concluida": false
  }
]
```

- Cada comando carrega o arquivo inteiro, aplica a alteração em memória e regrava o arquivo por completo.
- Se o arquivo não existir, ele é tratado como uma lista vazia.
- Se o arquivo contiver JSON inválido ou algo que não seja uma lista, o programa avisa o erro e encerra sem travar.
