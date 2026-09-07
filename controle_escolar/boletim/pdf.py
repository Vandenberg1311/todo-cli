import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from calculos import frequencia, media_bimestre, media_final
from models import ParametroAprovacao

BIMESTRES = (1, 2, 3, 4)


def _fmt(valor, sufixo=""):
    return f"{valor:.1f}{sufixo}" if valor is not None else "-"


def _situacao_final(turma, aluno):
    parametro = ParametroAprovacao.query.filter_by(ano_letivo=turma.ano_letivo).first()
    if parametro is None:
        return "Situação final: parâmetros de aprovação não configurados para este ano letivo."

    todas_completas = True
    aprovado = True
    for td in turma.turmas_disciplinas:
        final, completo = media_final(td.id, aluno.id)
        freq = frequencia(td.id, aluno.id)
        if not completo or freq is None:
            todas_completas = False
        if final is not None and final < parametro.media_minima:
            aprovado = False
        if freq is not None and freq["percentual"] < parametro.frequencia_minima_percentual:
            aprovado = False

    if not todas_completas:
        return "Situação: em andamento (nem todos os bimestres foram lançados)."
    return "Situação final: " + ("APROVADO" if aprovado else "REPROVADO")


def gerar_boletim_pdf(aluno):
    """Gera o PDF do boletim do aluno (notas por bimestre, média final e frequência
    em todas as disciplinas da turma) e retorna um buffer pronto para download."""
    turma = aluno.turma
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, topMargin=1.5 * cm, bottomMargin=1.5 * cm, leftMargin=1.5 * cm, rightMargin=1.5 * cm
    )
    styles = getSampleStyleSheet()
    elementos = [
        Paragraph("Boletim Escolar", styles["Title"]),
        Paragraph(f"Aluno: {aluno.nome} &nbsp;&nbsp; Matrícula: {aluno.matricula}", styles["Normal"]),
        Paragraph(f"Turma: {turma.nome} &nbsp;&nbsp; Ano letivo: {turma.ano_letivo}", styles["Normal"]),
        Spacer(1, 0.5 * cm),
    ]

    cabecalho = ["Disciplina", "1º Bim", "2º Bim", "3º Bim", "4º Bim", "Média Final", "Frequência"]
    linhas = [cabecalho]

    disciplinas_ordenadas = sorted(turma.turmas_disciplinas, key=lambda td: td.disciplina.nome)
    for td in disciplinas_ordenadas:
        medias_bim = [media_bimestre(td.id, aluno.id, n) for n in BIMESTRES]
        final, _completo = media_final(td.id, aluno.id)
        freq = frequencia(td.id, aluno.id)
        freq_txt = f"{freq['percentual']:.0f}%" if freq else "-"
        linhas.append([td.disciplina.nome] + [_fmt(m) for m in medias_bim] + [_fmt(final), freq_txt])

    tabela = Table(linhas, repeatRows=1)
    tabela.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2d3d")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    elementos.append(tabela)
    elementos.append(Spacer(1, 0.5 * cm))
    elementos.append(Paragraph(_situacao_final(turma, aluno), styles["Normal"]))

    doc.build(elementos)
    buffer.seek(0)
    return buffer
