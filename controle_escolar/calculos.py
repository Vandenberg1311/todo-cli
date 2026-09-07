"""Cálculos de médias e frequência usados pelas telas do professor e pelo boletim."""

from models import Aula, Avaliacao, Nota, Presenca


def media_bimestre(turma_disciplina_id, aluno_id, bimestre_numero):
    """Média ponderada do aluno no bimestre, ou None se não há nenhuma nota lançada."""
    avaliacoes = Avaliacao.query.filter_by(
        turma_disciplina_id=turma_disciplina_id, bimestre_numero=bimestre_numero
    ).all()

    soma_pontos = 0.0
    soma_pesos = 0.0
    for avaliacao in avaliacoes:
        nota = Nota.query.filter_by(avaliacao_id=avaliacao.id, aluno_id=aluno_id).first()
        if nota is not None and nota.valor is not None:
            soma_pontos += nota.valor * avaliacao.peso
            soma_pesos += avaliacao.peso

    if soma_pesos == 0:
        return None
    return soma_pontos / soma_pesos


def media_final(turma_disciplina_id, aluno_id):
    """Média simples dos 4 bimestres. Retorna (media, completo) — completo indica
    se os 4 bimestres já têm nota lançada; caso contrário a média é parcial."""
    medias = [media_bimestre(turma_disciplina_id, aluno_id, n) for n in range(1, 5)]
    medias_validas = [m for m in medias if m is not None]

    if not medias_validas:
        return None, False

    completo = len(medias_validas) == 4
    media = sum(medias_validas) / 4 if completo else sum(medias_validas) / len(medias_validas)
    return media, completo


def frequencia(turma_disciplina_id, aluno_id, bimestre_numero=None):
    """Frequência do aluno na disciplina — no bimestre informado, ou no ano todo se omitido.
    Retorna None se ainda não houve nenhuma aula lançada nesse recorte."""
    consulta = Aula.query.filter_by(turma_disciplina_id=turma_disciplina_id)
    if bimestre_numero is not None:
        consulta = consulta.filter_by(bimestre_numero=bimestre_numero)
    aulas_ids = [aula.id for aula in consulta.all()]

    total = len(aulas_ids)
    if total == 0:
        return None

    presentes = Presenca.query.filter(
        Presenca.aula_id.in_(aulas_ids), Presenca.aluno_id == aluno_id, Presenca.presente.is_(True)
    ).count()

    return {"presentes": presentes, "total": total, "percentual": (presentes / total) * 100}
