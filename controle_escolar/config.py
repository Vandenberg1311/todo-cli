import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-troque-em-producao")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'escola.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB, limite para upload de planilhas

    # Valores padrão usados ao criar o ParametroAprovacao de um novo ano letivo.
    MEDIA_MINIMA_PADRAO = 6.0
    FREQUENCIA_MINIMA_PADRAO = 75.0
