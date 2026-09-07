from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from auth.decorators import professor_required
from calculos import frequencia, media_bimestre, media_final
from extensions import db
from models import Aula, Avaliacao, Nota, Presenca, TurmaDisciplina
from professor.forms import AulaForm, AvaliacaoForm

bp = Blueprint("professor", __name__, url_prefix="/professor")

BIMESTRES = (1, 2, 3, 4)


def _turma_disciplina_do_professor_ou_404(td_id):
    td = db.session.get(TurmaDisciplina, td_id)
    if not td or td.professor_id != current_user.professor_id:
        abort(404)
    return td


def _bimestre_da_query():
    bimestre = request.args.get("bimestre", default=1, type=int)
    return bimestre if bimestre in BIMESTRES else 1


@bp.route("/")
@login_required
@professor_required
def dashboard():
    atribuicoes = (
        TurmaDisciplina.query.filter_by(professor_id=current_user.professor_id)
        .join(TurmaDisciplina.turma)
        .order_by(TurmaDisciplina.turma_id)
        .all()
    )
    return render_template("professor/dashboard.html", atribuicoes=atribuicoes)


@bp.route("/turmas/<int:td_id>")
@login_required
@professor_required
def turma_disciplina_detalhe(td_id):
    td = _turma_disciplina_do_professor_ou_404(td_id)
    bimestre = _bimestre_da_query()

    avaliacoes = (
        Avaliacao.query.filter_by(turma_disciplina_id=td.id, bimestre_numero=bimestre)
        .order_by(Avaliacao.id)
        .all()
    )
    alunos = sorted((a for a in td.turma.alunos if a.ativo), key=lambda a: a.nome)

    notas = {}
    for avaliacao in avaliacoes:
        for nota in avaliacao.notas:
            if nota.valor is not None:
                notas[(nota.aluno_id, avaliacao.id)] = nota.valor

    medias_bimestre = {aluno.id: media_bimestre(td.id, aluno.id, bimestre) for aluno in alunos}

    form = AvaliacaoForm()
    return render_template(
        "professor/turma_disciplina_detalhe.html",
        td=td,
        bimestre=bimestre,
        bimestres=BIMESTRES,
        avaliacoes=avaliacoes,
        alunos=alunos,
        notas=notas,
        medias_bimestre=medias_bimestre,
        form=form,
    )


@bp.route("/turmas/<int:td_id>/avaliacoes", methods=["POST"])
@login_required
@professor_required
def avaliacao_nova(td_id):
    td = _turma_disciplina_do_professor_ou_404(td_id)
    bimestre = _bimestre_da_query()

    form = AvaliacaoForm()
    if form.validate_on_submit():
        avaliacao = Avaliacao(
            turma_disciplina_id=td.id, bimestre_numero=bimestre, nome=form.nome.data, peso=form.peso.data
        )
        db.session.add(avaliacao)
        db.session.commit()
        flash("Avaliação criada.", "info")
    else:
        flash("Não foi possível criar a avaliação. Verifique os dados.", "error")

    return redirect(url_for("professor.turma_disciplina_detalhe", td_id=td.id, bimestre=bimestre))


@bp.route("/avaliacoes/<int:avaliacao_id>/editar", methods=["GET", "POST"])
@login_required
@professor_required
def avaliacao_editar(avaliacao_id):
    avaliacao = db.session.get(Avaliacao, avaliacao_id)
    if not avaliacao or avaliacao.turma_disciplina.professor_id != current_user.professor_id:
        abort(404)

    form = AvaliacaoForm(obj=avaliacao)
    if form.validate_on_submit():
        avaliacao.nome = form.nome.data
        avaliacao.peso = form.peso.data
        db.session.commit()
        flash("Avaliação atualizada.", "info")
        return redirect(
            url_for(
                "professor.turma_disciplina_detalhe",
                td_id=avaliacao.turma_disciplina_id,
                bimestre=avaliacao.bimestre_numero,
            )
        )
    return render_template("professor/avaliacao_form.html", form=form, avaliacao=avaliacao)


@bp.route("/avaliacoes/<int:avaliacao_id>/excluir", methods=["POST"])
@login_required
@professor_required
def avaliacao_excluir(avaliacao_id):
    avaliacao = db.session.get(Avaliacao, avaliacao_id)
    if not avaliacao or avaliacao.turma_disciplina.professor_id != current_user.professor_id:
        abort(404)

    td_id = avaliacao.turma_disciplina_id
    bimestre = avaliacao.bimestre_numero

    if any(nota.valor is not None for nota in avaliacao.notas):
        flash("Não é possível excluir: já existem notas lançadas nessa avaliação.", "error")
    else:
        db.session.delete(avaliacao)
        db.session.commit()
        flash("Avaliação excluída.", "info")

    return redirect(url_for("professor.turma_disciplina_detalhe", td_id=td_id, bimestre=bimestre))


@bp.route("/turmas/<int:td_id>/notas", methods=["POST"])
@login_required
@professor_required
def notas_salvar(td_id):
    td = _turma_disciplina_do_professor_ou_404(td_id)
    bimestre = _bimestre_da_query()

    avaliacoes = Avaliacao.query.filter_by(turma_disciplina_id=td.id, bimestre_numero=bimestre).all()
    alunos_ids = [a.id for a in td.turma.alunos if a.ativo]

    algum_erro = False
    for avaliacao in avaliacoes:
        for aluno_id in alunos_ids:
            campo = f"nota_{aluno_id}_{avaliacao.id}"
            if campo not in request.form:
                continue
            valor_bruto = request.form.get(campo, "").strip()

            if valor_bruto == "":
                valor = None
            else:
                try:
                    valor = float(valor_bruto.replace(",", "."))
                except ValueError:
                    flash(f"Valor '{valor_bruto}' inválido em {avaliacao.nome} foi ignorado.", "error")
                    algum_erro = True
                    continue
                if valor < 0 or valor > 10:
                    flash(f"Nota {valor_bruto} fora do intervalo 0-10 em {avaliacao.nome} foi ignorada.", "error")
                    algum_erro = True
                    continue

            nota = Nota.query.filter_by(avaliacao_id=avaliacao.id, aluno_id=aluno_id).first()
            if nota is None:
                nota = Nota(avaliacao_id=avaliacao.id, aluno_id=aluno_id, valor=valor)
                db.session.add(nota)
            else:
                nota.valor = valor

    db.session.commit()
    if not algum_erro:
        flash("Notas salvas com sucesso.", "info")
    return redirect(url_for("professor.turma_disciplina_detalhe", td_id=td.id, bimestre=bimestre))


@bp.route("/turmas/<int:td_id>/medias-finais")
@login_required
@professor_required
def medias_finais(td_id):
    td = _turma_disciplina_do_professor_ou_404(td_id)
    alunos = sorted((a for a in td.turma.alunos if a.ativo), key=lambda a: a.nome)

    linhas = []
    for aluno in alunos:
        medias_bim = [media_bimestre(td.id, aluno.id, n) for n in BIMESTRES]
        final, completo = media_final(td.id, aluno.id)
        freq_geral = frequencia(td.id, aluno.id)
        linhas.append(
            {
                "aluno": aluno,
                "medias_bim": medias_bim,
                "final": final,
                "completo": completo,
                "frequencia": freq_geral,
            }
        )

    return render_template("professor/medias_finais.html", td=td, linhas=linhas)


# ---------------------------------------------------------------------------
# Aulas e presença
# ---------------------------------------------------------------------------

def _aula_do_professor_ou_404(aula_id):
    aula = db.session.get(Aula, aula_id)
    if not aula or aula.turma_disciplina.professor_id != current_user.professor_id:
        abort(404)
    return aula


@bp.route("/turmas/<int:td_id>/aulas", methods=["GET", "POST"])
@login_required
@professor_required
def aulas_lista(td_id):
    td = _turma_disciplina_do_professor_ou_404(td_id)
    bimestre = _bimestre_da_query()

    form = AulaForm()
    if form.validate_on_submit():
        aula = Aula(turma_disciplina_id=td.id, data=form.data.data, bimestre_numero=bimestre)
        db.session.add(aula)
        db.session.flush()
        for aluno in td.turma.alunos:
            if aluno.ativo:
                db.session.add(Presenca(aula_id=aula.id, aluno_id=aluno.id, presente=True))
        db.session.commit()
        flash("Aula criada com todos os alunos marcados como presentes. Ajuste as faltas, se houver.", "info")
        return redirect(url_for("professor.aula_presenca", aula_id=aula.id))

    aulas = (
        Aula.query.filter_by(turma_disciplina_id=td.id, bimestre_numero=bimestre)
        .order_by(Aula.data)
        .all()
    )
    return render_template(
        "professor/aulas_lista.html", td=td, bimestre=bimestre, bimestres=BIMESTRES, aulas=aulas, form=form
    )


@bp.route("/aulas/<int:aula_id>", methods=["GET", "POST"])
@login_required
@professor_required
def aula_presenca(aula_id):
    aula = _aula_do_professor_ou_404(aula_id)
    alunos = sorted((a for a in aula.turma_disciplina.turma.alunos if a.ativo), key=lambda a: a.nome)

    if request.method == "POST":
        for aluno in alunos:
            presente = request.form.get(f"presente_{aluno.id}") == "on"
            presenca = Presenca.query.filter_by(aula_id=aula.id, aluno_id=aluno.id).first()
            if presenca is None:
                presenca = Presenca(aula_id=aula.id, aluno_id=aluno.id, presente=presente)
                db.session.add(presenca)
            else:
                presenca.presente = presente
        db.session.commit()
        flash("Presença salva.", "info")
        return redirect(
            url_for("professor.aulas_lista", td_id=aula.turma_disciplina_id, bimestre=aula.bimestre_numero)
        )

    presencas = {p.aluno_id: p.presente for p in aula.presencas}
    return render_template("professor/aula_presenca.html", aula=aula, alunos=alunos, presencas=presencas)


@bp.route("/aulas/<int:aula_id>/excluir", methods=["POST"])
@login_required
@professor_required
def aula_excluir(aula_id):
    aula = _aula_do_professor_ou_404(aula_id)
    td_id = aula.turma_disciplina_id
    bimestre = aula.bimestre_numero
    db.session.delete(aula)
    db.session.commit()
    flash("Aula excluída.", "info")
    return redirect(url_for("professor.aulas_lista", td_id=td_id, bimestre=bimestre))
