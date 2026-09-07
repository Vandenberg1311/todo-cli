from flask import Blueprint, flash, redirect, send_file, url_for
from flask_login import login_required

from auth.decorators import admin_required
from boletim.pdf import gerar_boletim_pdf
from extensions import db
from models import Aluno

bp = Blueprint("boletim", __name__, url_prefix="/boletim")


@bp.route("/aluno/<int:aluno_id>")
@login_required
@admin_required
def boletim_aluno(aluno_id):
    aluno = db.session.get(Aluno, aluno_id)
    if not aluno:
        flash("Aluno não encontrado.", "error")
        return redirect(url_for("admin.alunos_lista"))

    buffer = gerar_boletim_pdf(aluno)
    nome_arquivo = f"boletim_{aluno.matricula}.pdf"
    return send_file(buffer, mimetype="application/pdf", download_name=nome_arquivo)
