from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from auth.forms import LoginForm
from models import PAPEL_ADMIN, Usuario

bp = Blueprint("auth", __name__, url_prefix="/auth")


def _url_pagina_inicial(usuario):
    if usuario.papel == PAPEL_ADMIN:
        return url_for("admin.dashboard")
    return url_for("professor.dashboard")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(_url_pagina_inicial(current_user))

    form = LoginForm()
    if form.validate_on_submit():
        usuario = Usuario.query.filter_by(login=form.login.data).first()
        if usuario and usuario.ativo and usuario.checar_senha(form.senha.data):
            login_user(usuario, remember=form.lembrar.data)
            next_page = request.args.get("next")
            return redirect(next_page or _url_pagina_inicial(usuario))
        flash("Usuário ou senha inválidos.", "error")

    return render_template("auth/login.html", form=form)


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Você saiu do sistema.", "info")
    return redirect(url_for("auth.login"))
