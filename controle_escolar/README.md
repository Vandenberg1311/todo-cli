# Controle Escolar

Sistema web em Flask para controle escolar de pequeno porte: turmas, disciplinas, professores, alunos, notas por bimestre, presença e boletim em PDF. Banco de dados SQLite (arquivo único), pensado para uso local por uma secretaria/coordenação.

## Requisitos

- Python 3.10 ou superior
- pip

## Instalação

```
cd controle_escolar
python -m venv .venv
```

Ativar o ambiente virtual:

```
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # macOS/Linux
```

Instalar as dependências:

```
pip install -r requirements.txt
```

## Configuração inicial

Definir a variável `FLASK_APP` (necessária para os comandos `flask ...` abaixo):

```
set FLASK_APP=app.py          # Windows (cmd)
$env:FLASK_APP = "app.py"     # Windows (PowerShell)
export FLASK_APP=app.py       # macOS/Linux
```

Criar as tabelas do banco de dados:

```
flask init-db
```

Criar o primeiro usuário administrador (pede a senha de forma oculta — precisa rodar num terminal interativo de verdade, não funciona com senha enviada via pipe):

```
flask create-admin <login> "<Nome completo>"
```

Exemplo:

```
flask create-admin secretaria "Secretaria da Escola"
```

## Como rodar

```
flask run
```

Ou diretamente:

```
python app.py
```

Acesse `http://127.0.0.1:5000` — a página inicial redireciona para o login. Faça login com o usuário administrador criado acima.

## Estrutura do projeto

```
controle_escolar/
├── app.py              # application factory, blueprints, comandos de CLI
├── config.py           # configuração (SECRET_KEY, banco, limite de upload)
├── extensions.py       # instâncias do SQLAlchemy, Flask-Login e CSRFProtect
├── models.py           # modelo de dados (usuários, turmas, notas, presença...)
├── calculos.py         # cálculo de médias (bimestre/final) e frequência
├── auth/               # login, logout e controle de acesso por papel
├── admin/              # cadastros: turmas, disciplinas, professores, alunos, parâmetros
├── professor/          # avaliações, lançamento de notas, aulas e presença
├── boletim/            # geração do boletim em PDF
├── importacao/         # leitura de planilhas de alunos (.csv/.xlsx)
├── templates/          # páginas HTML (Jinja2)
├── static/             # CSS
└── instance/           # banco de dados SQLite (escola.db) — não versionado
```

## Papéis

- **Administrador** (secretaria/coordenação): cadastra turmas, disciplinas, professores (já cria o usuário/senha de acesso do professor), atribui professor a cada disciplina de uma turma, cadastra alunos (manualmente ou importando planilha), configura os parâmetros de aprovação por ano letivo e gera os boletins em PDF.
- **Professor**: enxerga e edita apenas as turmas/disciplinas atribuídas a ele. Cria as avaliações de cada bimestre (nome e peso à sua escolha), lança as notas, registra as aulas dadas e marca presença/falta, e acompanha médias e frequência.

## Notas, médias e frequência

- Notas na escala de 0 a 10.
- Média do bimestre = média ponderada pelos pesos das avaliações definidas pelo professor.
- Média final = média simples das 4 médias bimestrais (exibida como "parcial" enquanto nem todos os bimestres têm nota lançada).
- Frequência = presenças ÷ total de aulas lançadas (por disciplina/bimestre, ou geral no ano).
- A situação final (Aprovado/Reprovado) no boletim usa a média mínima e a frequência mínima configuradas em **Parâmetros** (menu do administrador), por ano letivo. Enquanto não configurados, o boletim avisa que os parâmetros ainda não foram definidos.

## Importação de alunos por planilha

Em Turmas → (turma) → Importar planilha, aceita `.csv` ou `.xlsx` com cabeçalho na primeira linha:

| coluna | obrigatória | formato |
|---|---|---|
| `nome` | sim | texto |
| `matricula` | sim | texto |
| `data_nascimento` | não | `AAAA-MM-DD` ou `DD/MM/AAAA` |
| `nome_responsavel` | não | texto |
| `contato_responsavel` | não | texto |

Todos os alunos da planilha são vinculados à turma escolhida. Linhas inválidas (sem nome/matrícula, data mal formatada) e linhas com matrícula já cadastrada são reportadas e ignoradas — as demais são importadas normalmente.

## Configuração via variáveis de ambiente (opcional)

- `SECRET_KEY`: chave usada para sessão e proteção CSRF. Por padrão usa um valor de desenvolvimento — **defina uma chave própria antes de qualquer uso além de testes locais**.
- `DATABASE_URL`: string de conexão do banco. Por padrão aponta para `instance/escola.db` (SQLite).

## Segurança

- Senhas armazenadas com hash (Werkzeug).
- Proteção CSRF habilitada globalmente em todos os formulários (Flask-WTF).
- Upload de planilha limitado a 5 MB.
- Acesso a cada tela controlado por papel (administrador vs. professor); um professor nunca acessa dados de turmas/disciplinas que não são dele.
