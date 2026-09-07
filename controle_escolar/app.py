import getpass
import os

import click
from flask import Flask, redirect, url_for
from flask_login import current_user

from config import Config
from extensions import csrf, db, login_manager


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    os.makedirs(os.path.join(app.root_path, "instance"), exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    from models import Usuario

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(Usuario, int(user_id))

    register_blueprints(app)
    register_cli(app)

    from models import PAPEL_ADMIN

    @app.route("/")
    def index():
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
        if current_user.papel == PAPEL_ADMIN:
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("professor.dashboard"))

    return app


def register_blueprints(app):
    from admin.routes import bp as admin_bp
    from auth.routes import bp as auth_bp
    from boletim.routes import bp as boletim_bp
    from professor.routes import bp as professor_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(professor_bp)
    app.register_blueprint(boletim_bp)


def register_cli(app):
    @app.cli.command("init-db")
    def init_db():
        """Cria todas as tabelas no banco de dados (não apaga dados existentes)."""
        db.create_all()
        click.echo("Banco de dados inicializado.")

    @app.cli.command("create-admin")
    @click.argument("login")
    @click.argument("nome")
    def create_admin(login, nome):
        """Cria um usuário administrador. Pede a senha de forma oculta no terminal."""
        from models import PAPEL_ADMIN, Usuario

        if Usuario.query.filter_by(login=login).first():
            click.echo(f"Já existe um usuário com login '{login}'.")
            return

        senha = getpass.getpass("Senha: ")
        confirmacao = getpass.getpass("Confirme a senha: ")
        if senha != confirmacao:
            click.echo("As senhas não coincidem.")
            return

        usuario = Usuario(nome=nome, login=login, papel=PAPEL_ADMIN, ativo=True)
        usuario.set_senha(senha)
        db.session.add(usuario)
        db.session.commit()
        click.echo(f"Administrador '{login}' criado com sucesso.")


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
