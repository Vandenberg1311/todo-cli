import csv
import io
from datetime import date, datetime

import openpyxl

COLUNAS_OBRIGATORIAS = {"nome", "matricula"}


class LinhaInvalida(Exception):
    pass


def _normalizar_cabecalho(valor):
    return (valor or "").strip().lower().replace(" ", "_")


def _parse_data(valor):
    if valor in (None, ""):
        return None
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    texto = str(valor).strip()
    for formato in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(texto, formato).date()
        except ValueError:
            continue
    raise LinhaInvalida(f"data de nascimento inválida: '{texto}' (use AAAA-MM-DD ou DD/MM/AAAA)")


def _linhas_de_csv(arquivo):
    texto = arquivo.read().decode("utf-8-sig")
    leitor = csv.DictReader(io.StringIO(texto))
    for linha in leitor:
        yield {_normalizar_cabecalho(chave): valor for chave, valor in linha.items()}


def _linhas_de_xlsx(arquivo):
    planilha = openpyxl.load_workbook(arquivo, read_only=True, data_only=True).active
    linhas = planilha.iter_rows(values_only=True)
    cabecalho = [_normalizar_cabecalho(c) for c in next(linhas)]
    for valores in linhas:
        if all(v is None for v in valores):
            continue
        yield dict(zip(cabecalho, valores))


def ler_planilha(arquivo, nome_arquivo):
    """Lê um arquivo .csv ou .xlsx e retorna (registros_validos, mensagens_de_erro)."""
    if nome_arquivo.lower().endswith(".csv"):
        linhas = list(_linhas_de_csv(arquivo))
    else:
        linhas = list(_linhas_de_xlsx(arquivo))

    if not linhas:
        return [], ["A planilha está vazia."]

    faltando = COLUNAS_OBRIGATORIAS - set(linhas[0].keys())
    if faltando:
        return [], [f"Colunas obrigatórias ausentes: {', '.join(sorted(faltando))}."]

    registros = []
    erros = []
    for numero, linha in enumerate(linhas, start=2):  # linha 1 é o cabeçalho
        nome = (linha.get("nome") or "").strip()
        matricula = str(linha.get("matricula") or "").strip()
        if not nome or not matricula:
            erros.append(f"Linha {numero}: nome e matrícula são obrigatórios.")
            continue
        try:
            data_nascimento = _parse_data(linha.get("data_nascimento"))
        except LinhaInvalida as exc:
            erros.append(f"Linha {numero}: {exc}")
            continue

        registros.append(
            {
                "nome": nome,
                "matricula": matricula,
                "data_nascimento": data_nascimento,
                "nome_responsavel": (str(linha.get("nome_responsavel") or "").strip() or None),
                "contato_responsavel": (str(linha.get("contato_responsavel") or "").strip() or None),
            }
        )

    return registros, erros
