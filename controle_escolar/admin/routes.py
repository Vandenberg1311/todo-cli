from flask import Blueprint, current_app, flash, redirect, render_template, url_for
from flask_login import login_required

from admin.forms import (
    AlunoForm,
    AtribuicaoForm,
    DisciplinaForm,
    ImportarAlunosForm,
    ParametroAprovacaoForm,
    ProfessorForm,
    TurmaForm,
)
from auth.decorators import admin_required
from extensions import db
from importacao.alunos import ler_planilha
from models import (
    PAPEL_PROFESSOR,
    Aluno,
    Disciplina,
    Nota,
    ParametroAprovacao,
    Presenca,
    Professor,
    Turma,
    TurmaDisciplina,
    Usuario,
)

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.route("/")
@login_required
@admin_required
def dashboard():
    return render_template("admin/dashboard.html")


# ---------------------------------------------------------------------------
# Turmas
# ---------------------------------------------------------------------------

@bp.route("/turmas")
@login_required
@admin_required
def turmas_lista():
    turmas = Turma.query.order_by(Turma.ano_letivo.desc(), Turma.nome).all()
    return render_template("admin/turmas_lista.html", turmas=turmas)


@bp.route("/turmas/nova", methods=["GET", "POST"])
@login_required
@admin_required
def turma_nova():
    form = TurmaForm()
    if form.validate_on_submit():
        existente = Turma.query.filter_by(nome=form.nome.data, ano_letivo=form.ano_letivo.data).first()
        if existente:
            flash("Já existe uma turma com esse nome nesse ano letivo.", "error")
        else:
            turma = Turma(nome=form.nome.data, ano_letivo=form.ano_letivo.data)
            db.session.add(turma)
            db.session.commit()
            flash("Turma criada com sucesso.", "info")
            return redirect(url_for("admin.turmas_lista"))
    return render_template("admin/turma_form.html", form=form, titulo="Nova turma")


@bp.route("/turmas/<int:turma_id>")
@login_required
@admin_required
def turma_detalhe(turma_id):
    turma = db.session.get(Turma, turma_id)
    if not turma:
        flash("Turma não encontrada.", "error")
        return redirect(url_for("admin.turmas_lista"))

    form = AtribuicaoForm()
    disciplinas_disponiveis = (
        Disciplina.query.filter(
            ~Disciplina.id.in_([td.disciplina_id for td in turma.turmas_disciplinas])
        )
        .order_by(Disciplina.nome)
        .all()
    )
    form.disciplina_id.choices = [(d.id, d.nome) for d in disciplinas_disponiveis]
    form.professor_id.choices = [(p.id, p.nome) for p in Professor.query.order_by(Professor.nome).all()]

    return render_template("admin/turma_detalhe.html", turma=turma, form=form)


@bp.route("/turmas/<int:turma_id>/editar", methods=["GET", "POST"])
@login_required
@admin_required
def turma_editar(turma_id):
    turma = db.session.get(Turma, turma_id)
    if not turma:
        flash("Turma não encontrada.", "error")
        return redirect(url_for("admin.turmas_lista"))

    form = TurmaForm(obj=turma)
    if form.validate_on_submit():
        turma.nome = form.nome.data
        turma.ano_letivo = form.ano_letivo.data
        db.session.commit()
        flash("Turma atualizada com sucesso.", "info")
        return redirect(url_for("admin.turmas_lista"))
    return render_template("admin/turma_form.html", form=form, titulo="Editar turma")


@bp.route("/turmas/<int:turma_id>/excluir", methods=["POST"])
@login_required
@admin_required
def turma_excluir(turma_id):
    turma = db.session.get(Turma, turma_id)
    if not turma:
        flash("Turma não encontrada.", "error")
        return redirect(url_for("admin.turmas_lista"))

    if Aluno.query.filter_by(turma_id=turma.id).count() > 0:
        flash("Não é possível excluir: existem alunos vinculados a essa turma.", "error")
        return redirect(url_for("admin.turmas_lista"))
    if TurmaDisciplina.query.filter_by(turma_id=turma.id).count() > 0:
        flash("Não é possível excluir: remova as disciplinas atribuídas antes.", "error")
        return redirect(url_for("admin.turmas_lista"))

    db.session.delete(turma)
    db.session.commit()
    flash("Turma excluída.", "info")
    return redirect(url_for("admin.turmas_lista"))


@bp.route("/turmas/<int:turma_id>/disciplinas", methods=["POST"])
@login_required
@admin_required
def turma_atribuir_disciplina(turma_id):
    turma = db.session.get(Turma, turma_id)
    if not turma:
        flash("Turma não encontrada.", "error")
        return redirect(url_for("admin.turmas_lista"))

    form = AtribuicaoForm()
    form.disciplina_id.choices = [(d.id, d.nome) for d in Disciplina.query.all()]
    form.professor_id.choices = [(p.id, p.nome) for p in Professor.query.all()]

    if form.validate_on_submit():
        ja_existe = TurmaDisciplina.query.filter_by(
            turma_id=turma.id, disciplina_id=form.disciplina_id.data
        ).first()
        if ja_existe:
            flash("Essa disciplina já está atribuída a essa turma.", "error")
        else:
            atribuicao = TurmaDisciplina(
                turma_id=turma.id,
                disciplina_id=form.disciplina_id.data,
                professor_id=form.professor_id.data,
            )
            db.session.add(atribuicao)
            db.session.commit()
            flash("Disciplina atribuída à turma.", "info")
    else:
        flash("Não foi possível atribuir a disciplina. Verifique os dados.", "error")

    return redirect(url_for("admin.turma_detalhe", turma_id=turma.id))


@bp.route("/turmas/<int:turma_id>/disciplinas/<int:td_id>/remover", methods=["POST"])
@login_required
@admin_required
def turma_remover_disciplina(turma_id, td_id):
    atribuicao = db.session.get(TurmaDisciplina, td_id)
    if not atribuicao or atribuicao.turma_id != turma_id:
        flash("Atribuição não encontrada.", "error")
        return redirect(url_for("admin.turma_detalhe", turma_id=turma_id))

    if atribuicao.avaliacoes or atribuicao.aulas:
        flash("Não é possível remover: já existem avaliações ou aulas lançadas para essa disciplina.", "error")
        return redirect(url_for("admin.turma_detalhe", turma_id=turma_id))

    db.session.delete(atribuicao)
    db.session.commit()
    flash("Disciplina removida da turma.", "info")
    return redirect(url_for("admin.turma_detalhe", turma_id=turma_id))


# ---------------------------------------------------------------------------
# Disciplinas
# ---------------------------------------------------------------------------

@bp.route("/disciplinas")
@login_required
@admin_required
def disciplinas_lista():
    disciplinas = Disciplina.query.order_by(Disciplina.nome).all()
    return render_template("admin/disciplinas_lista.html", disciplinas=disciplinas)


@bp.route("/disciplinas/nova", methods=["GET", "POST"])
@login_required
@admin_required
def disciplina_nova():
    form = DisciplinaForm()
    if form.validate_on_submit():
        if Disciplina.query.filter_by(nome=form.nome.data).first():
            flash("Já existe uma disciplina com esse nome.", "error")
        else:
            db.session.add(Disciplina(nome=form.nome.data))
            db.session.commit()
            flash("Disciplina criada com sucesso.", "info")
            return redirect(url_for("admin.disciplinas_lista"))
    return render_template("admin/disciplina_form.html", form=form, titulo="Nova disciplina")


@bp.route("/disciplinas/<int:disciplina_id>/editar", methods=["GET", "POST"])
@login_required
@admin_required
def disciplina_editar(disciplina_id):
    disciplina = db.session.get(Disciplina, disciplina_id)
    if not disciplina:
        flash("Disciplina não encontrada.", "error")
        return redirect(url_for("admin.disciplinas_lista"))

    form = DisciplinaForm(obj=disciplina)
    if form.validate_on_submit():
        disciplina.nome = form.nome.data
        db.session.commit()
        flash("Disciplina atualizada com sucesso.", "info")
        return redirect(url_for("admin.disciplinas_lista"))
    return render_template("admin/disciplina_form.html", form=form, titulo="Editar disciplina")


@bp.route("/disciplinas/<int:disciplina_id>/excluir", methods=["POST"])
@login_required
@admin_required
def disciplina_excluir(disciplina_id):
    disciplina = db.session.get(Disciplina, disciplina_id)
    if not disciplina:
        flash("Disciplina não encontrada.", "error")
        return redirect(url_for("admin.disciplinas_lista"))

    if TurmaDisciplina.query.filter_by(disciplina_id=disciplina.id).count() > 0:
        flash("Não é possível excluir: essa disciplina está atribuída a alguma turma.", "error")
        return redirect(url_for("admin.disciplinas_lista"))

    db.session.delete(disciplina)
    db.session.commit()
    flash("Disciplina excluída.", "info")
    return redirect(url_for("admin.disciplinas_lista"))


# ---------------------------------------------------------------------------
# Professores
# ---------------------------------------------------------------------------

@bp.route("/professores")
@login_required
@admin_required
def professores_lista():
    professores = Professor.query.order_by(Professor.nome).all()
    return render_template("admin/professores_lista.html", professores=professores)


@bp.route("/professores/novo", methods=["GET", "POST"])
@login_required
@admin_required
def professor_novo():
    form = ProfessorForm()
    if form.validate_on_submit():
        if Usuario.query.filter_by(login=form.login.data).first():
            flash("Já existe um usuário com esse login.", "error")
        elif not form.senha.data:
            flash("Defina uma senha inicial para o professor.", "error")
        else:
            professor = Professor(nome=form.nome.data, email=form.email.data, telefone=form.telefone.data)
            db.session.add(professor)
            db.session.flush()

            usuario = Usuario(
                nome=form.nome.data,
                login=form.login.data,
                papel=PAPEL_PROFESSOR,
                ativo=True,
                professor_id=professor.id,
            )
            usuario.set_senha(form.senha.data)
            db.session.add(usuario)
            db.session.commit()
            flash("Professor cadastrado com sucesso.", "info")
            return redirect(url_for("admin.professores_lista"))
    return render_template("admin/professor_form.html", form=form, titulo="Novo professor", eh_novo=True)


@bp.route("/professores/<int:professor_id>/editar", methods=["GET", "POST"])
@login_required
@admin_required
def professor_editar(professor_id):
    professor = db.session.get(Professor, professor_id)
    if not professor:
        flash("Professor não encontrado.", "error")
        return redirect(url_for("admin.professores_lista"))

    form = ProfessorForm(obj=professor)
    if not form.is_submitted():
        form.login.data = professor.usuario.login if professor.usuario else ""

    if form.validate_on_submit():
        outro_com_login = Usuario.query.filter(
            Usuario.login == form.login.data, Usuario.professor_id != professor.id
        ).first()
        if outro_com_login:
            flash("Já existe um usuário com esse login.", "error")
        else:
            professor.nome = form.nome.data
            professor.email = form.email.data
            professor.telefone = form.telefone.data
            if professor.usuario:
                professor.usuario.nome = form.nome.data
                professor.usuario.login = form.login.data
                if form.senha.data:
                    professor.usuario.set_senha(form.senha.data)
            db.session.commit()
            flash("Professor atualizado com sucesso.", "info")
            return redirect(url_for("admin.professores_lista"))

    return render_template("admin/professor_form.html", form=form, titulo="Editar professor", eh_novo=False)


@bp.route("/professores/<int:professor_id>/excluir", methods=["POST"])
@login_required
@admin_required
def professor_excluir(professor_id):
    professor = db.session.get(Professor, professor_id)
    if not professor:
        flash("Professor não encontrado.", "error")
        return redirect(url_for("admin.professores_lista"))

    if TurmaDisciplina.query.filter_by(professor_id=professor.id).count() > 0:
        flash("Não é possível excluir: remova as atribuições desse professor nas turmas antes.", "error")
        return redirect(url_for("admin.professores_lista"))

    if professor.usuario:
        db.session.delete(professor.usuario)
    db.session.delete(professor)
    db.session.commit()
    flash("Professor excluído.", "info")
    return redirect(url_for("admin.professores_lista"))


# ---------------------------------------------------------------------------
# Alunos
# ---------------------------------------------------------------------------

def _opcoes_turma():
    return [(t.id, f"{t.nome} ({t.ano_letivo})") for t in Turma.query.order_by(Turma.ano_letivo.desc(), Turma.nome).all()]


@bp.route("/alunos")
@login_required
@admin_required
def alunos_lista():
    alunos = (
        Aluno.query.join(Turma)
        .order_by(Turma.ano_letivo.desc(), Turma.nome, Aluno.nome)
        .all()
    )
    return render_template("admin/alunos_lista.html", alunos=alunos)


@bp.route("/turmas/<int:turma_id>/alunos/novo", methods=["GET", "POST"])
@login_required
@admin_required
def aluno_novo(turma_id):
    turma = db.session.get(Turma, turma_id)
    if not turma:
        flash("Turma não encontrada.", "error")
        return redirect(url_for("admin.turmas_lista"))

    form = AlunoForm()
    form.turma_id.choices = _opcoes_turma()
    if not form.is_submitted():
        form.turma_id.data = turma.id

    if form.validate_on_submit():
        if Aluno.query.filter_by(matricula=form.matricula.data).first():
            flash("Já existe um aluno com essa matrícula.", "error")
        else:
            aluno = Aluno(
                nome=form.nome.data,
                matricula=form.matricula.data,
                data_nascimento=form.data_nascimento.data,
                nome_responsavel=form.nome_responsavel.data,
                contato_responsavel=form.contato_responsavel.data,
                turma_id=form.turma_id.data,
            )
            db.session.add(aluno)
            db.session.commit()
            flash("Aluno cadastrado com sucesso.", "info")
            return redirect(url_for("admin.turma_detalhe", turma_id=form.turma_id.data))

    return render_template("admin/aluno_form.html", form=form, titulo="Novo aluno")


@bp.route("/alunos/<int:aluno_id>/editar", methods=["GET", "POST"])
@login_required
@admin_required
def aluno_editar(aluno_id):
    aluno = db.session.get(Aluno, aluno_id)
    if not aluno:
        flash("Aluno não encontrado.", "error")
        return redirect(url_for("admin.alunos_lista"))

    form = AlunoForm(obj=aluno)
    form.turma_id.choices = _opcoes_turma()
    if not form.is_submitted():
        form.turma_id.data = aluno.turma_id

    if form.validate_on_submit():
        outro_com_matricula = Aluno.query.filter(
            Aluno.matricula == form.matricula.data, Aluno.id != aluno.id
        ).first()
        if outro_com_matricula:
            flash("Já existe outro aluno com essa matrícula.", "error")
        else:
            aluno.nome = form.nome.data
            aluno.matricula = form.matricula.data
            aluno.data_nascimento = form.data_nascimento.data
            aluno.nome_responsavel = form.nome_responsavel.data
            aluno.contato_responsavel = form.contato_responsavel.data
            aluno.turma_id = form.turma_id.data
            db.session.commit()
            flash("Aluno atualizado com sucesso.", "info")
            return redirect(url_for("admin.turma_detalhe", turma_id=aluno.turma_id))

    return render_template("admin/aluno_form.html", form=form, titulo="Editar aluno")


@bp.route("/alunos/<int:aluno_id>/excluir", methods=["POST"])
@login_required
@admin_required
def aluno_excluir(aluno_id):
    aluno = db.session.get(Aluno, aluno_id)
    if not aluno:
        flash("Aluno não encontrado.", "error")
        return redirect(url_for("admin.alunos_lista"))

    if Nota.query.filter_by(aluno_id=aluno.id).count() > 0 or Presenca.query.filter_by(aluno_id=aluno.id).count() > 0:
        flash("Não é possível excluir: já existem notas ou presenças lançadas para esse aluno.", "error")
        return redirect(url_for("admin.turma_detalhe", turma_id=aluno.turma_id))

    turma_id = aluno.turma_id
    db.session.delete(aluno)
    db.session.commit()
    flash("Aluno excluído.", "info")
    return redirect(url_for("admin.turma_detalhe", turma_id=turma_id))


@bp.route("/turmas/<int:turma_id>/alunos/importar", methods=["GET", "POST"])
@login_required
@admin_required
def alunos_importar(turma_id):
    turma = db.session.get(Turma, turma_id)
    if not turma:
        flash("Turma não encontrada.", "error")
        return redirect(url_for("admin.turmas_lista"))

    form = ImportarAlunosForm()
    if form.validate_on_submit():
        registros, erros = ler_planilha(form.arquivo.data, form.arquivo.data.filename)

        criados = 0
        duplicados = []
        if registros:
            for registro in registros:
                if Aluno.query.filter_by(matricula=registro["matricula"]).first():
                    duplicados.append(registro["matricula"])
                    continue
                db.session.add(Aluno(turma_id=turma.id, **registro))
                criados += 1
            db.session.commit()

        for erro in erros[:20]:
            flash(erro, "error")
        if duplicados:
            flash(
                f"{len(duplicados)} linha(s) ignorada(s) por matrícula já existente: "
                + ", ".join(duplicados),
                "error",
            )
        if criados:
            flash(f"{criados} aluno(s) importado(s) com sucesso.", "info")
            return redirect(url_for("admin.turma_detalhe", turma_id=turma.id))
        if not erros and not duplicados:
            flash("Nenhum aluno encontrado na planilha.", "error")

    return render_template("admin/alunos_importar.html", form=form, turma=turma)


# ---------------------------------------------------------------------------
# Parâmetros de aprovação
# ---------------------------------------------------------------------------

@bp.route("/parametros")
@login_required
@admin_required
def parametros_lista():
    parametros = {p.ano_letivo: p for p in ParametroAprovacao.query.all()}
    anos = sorted({t.ano_letivo for t in Turma.query.all()} | set(parametros.keys()), reverse=True)
    linhas = [(ano, parametros.get(ano)) for ano in anos]
    return render_template("admin/parametros_lista.html", linhas=linhas)


@bp.route("/parametros/<int:ano_letivo>/editar", methods=["GET", "POST"])
@login_required
@admin_required
def parametro_editar(ano_letivo):
    parametro = ParametroAprovacao.query.filter_by(ano_letivo=ano_letivo).first()

    if parametro:
        form = ParametroAprovacaoForm(obj=parametro)
    else:
        form = ParametroAprovacaoForm(
            media_minima=current_app.config["MEDIA_MINIMA_PADRAO"],
            frequencia_minima_percentual=current_app.config["FREQUENCIA_MINIMA_PADRAO"],
        )

    if form.validate_on_submit():
        if parametro is None:
            parametro = ParametroAprovacao(ano_letivo=ano_letivo)
            db.session.add(parametro)
        parametro.media_minima = form.media_minima.data
        parametro.frequencia_minima_percentual = form.frequencia_minima_percentual.data
        db.session.commit()
        flash("Parâmetros salvos.", "info")
        return redirect(url_for("admin.parametros_lista"))

    return render_template("admin/parametro_form.html", form=form, ano_letivo=ano_letivo)
