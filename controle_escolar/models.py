from datetime import date

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db

PAPEL_ADMIN = "admin"
PAPEL_PROFESSOR = "professor"


class Usuario(UserMixin, db.Model):
    __tablename__ = "usuario"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    login = db.Column(db.String(80), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    papel = db.Column(db.String(20), nullable=False)
    ativo = db.Column(db.Boolean, nullable=False, default=True)

    professor_id = db.Column(db.Integer, db.ForeignKey("professor.id"), unique=True)
    professor = db.relationship("Professor", back_populates="usuario")

    def set_senha(self, senha_plana):
        self.senha_hash = generate_password_hash(senha_plana)

    def checar_senha(self, senha_plana):
        return check_password_hash(self.senha_hash, senha_plana)

    def is_admin(self):
        return self.papel == PAPEL_ADMIN

    def is_professor(self):
        return self.papel == PAPEL_PROFESSOR

    def __repr__(self):
        return f"<Usuario {self.login} ({self.papel})>"


class Professor(db.Model):
    __tablename__ = "professor"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120))
    telefone = db.Column(db.String(30))

    usuario = db.relationship("Usuario", back_populates="professor", uselist=False)
    turmas_disciplinas = db.relationship("TurmaDisciplina", back_populates="professor")

    def __repr__(self):
        return f"<Professor {self.nome}>"


class Turma(db.Model):
    __tablename__ = "turma"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), nullable=False)
    ano_letivo = db.Column(db.Integer, nullable=False)

    alunos = db.relationship("Aluno", back_populates="turma")
    turmas_disciplinas = db.relationship("TurmaDisciplina", back_populates="turma")

    __table_args__ = (
        db.UniqueConstraint("nome", "ano_letivo", name="uq_turma_nome_ano"),
    )

    def __repr__(self):
        return f"<Turma {self.nome}/{self.ano_letivo}>"


class Disciplina(db.Model):
    __tablename__ = "disciplina"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), unique=True, nullable=False)

    turmas_disciplinas = db.relationship("TurmaDisciplina", back_populates="disciplina")

    def __repr__(self):
        return f"<Disciplina {self.nome}>"


class TurmaDisciplina(db.Model):
    """Vincula uma disciplina a uma turma e define o professor responsável."""

    __tablename__ = "turma_disciplina"

    id = db.Column(db.Integer, primary_key=True)
    turma_id = db.Column(db.Integer, db.ForeignKey("turma.id"), nullable=False)
    disciplina_id = db.Column(db.Integer, db.ForeignKey("disciplina.id"), nullable=False)
    professor_id = db.Column(db.Integer, db.ForeignKey("professor.id"), nullable=False)

    turma = db.relationship("Turma", back_populates="turmas_disciplinas")
    disciplina = db.relationship("Disciplina", back_populates="turmas_disciplinas")
    professor = db.relationship("Professor", back_populates="turmas_disciplinas")

    avaliacoes = db.relationship("Avaliacao", back_populates="turma_disciplina")
    aulas = db.relationship("Aula", back_populates="turma_disciplina")

    __table_args__ = (
        db.UniqueConstraint("turma_id", "disciplina_id", name="uq_turma_disciplina"),
    )

    def __repr__(self):
        return f"<TurmaDisciplina turma={self.turma_id} disciplina={self.disciplina_id}>"


class Aluno(db.Model):
    __tablename__ = "aluno"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    data_nascimento = db.Column(db.Date)
    matricula = db.Column(db.String(30), unique=True, nullable=False)
    nome_responsavel = db.Column(db.String(120))
    contato_responsavel = db.Column(db.String(120))
    turma_id = db.Column(db.Integer, db.ForeignKey("turma.id"), nullable=False)
    ativo = db.Column(db.Boolean, nullable=False, default=True)

    turma = db.relationship("Turma", back_populates="alunos")
    notas = db.relationship("Nota", back_populates="aluno")
    presencas = db.relationship("Presenca", back_populates="aluno")

    def __repr__(self):
        return f"<Aluno {self.nome} ({self.matricula})>"


class Bimestre(db.Model):
    """Registro opcional de datas de início/fim de cada bimestre do ano letivo."""

    __tablename__ = "bimestre"

    id = db.Column(db.Integer, primary_key=True)
    ano_letivo = db.Column(db.Integer, nullable=False)
    numero = db.Column(db.Integer, nullable=False)  # 1 a 4
    data_inicio = db.Column(db.Date)
    data_fim = db.Column(db.Date)

    __table_args__ = (
        db.UniqueConstraint("ano_letivo", "numero", name="uq_bimestre_ano_numero"),
    )

    def __repr__(self):
        return f"<Bimestre {self.numero}/{self.ano_letivo}>"


class Avaliacao(db.Model):
    """Uma avaliação criada livremente pelo professor (ex: prova, trabalho)."""

    __tablename__ = "avaliacao"

    id = db.Column(db.Integer, primary_key=True)
    turma_disciplina_id = db.Column(db.Integer, db.ForeignKey("turma_disciplina.id"), nullable=False)
    bimestre_numero = db.Column(db.Integer, nullable=False)  # 1 a 4
    nome = db.Column(db.String(80), nullable=False)
    peso = db.Column(db.Float, nullable=False, default=1.0)

    turma_disciplina = db.relationship("TurmaDisciplina", back_populates="avaliacoes")
    notas = db.relationship("Nota", back_populates="avaliacao", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Avaliacao {self.nome} (bim {self.bimestre_numero})>"


class Nota(db.Model):
    __tablename__ = "nota"

    id = db.Column(db.Integer, primary_key=True)
    avaliacao_id = db.Column(db.Integer, db.ForeignKey("avaliacao.id"), nullable=False)
    aluno_id = db.Column(db.Integer, db.ForeignKey("aluno.id"), nullable=False)
    valor = db.Column(db.Float)

    avaliacao = db.relationship("Avaliacao", back_populates="notas")
    aluno = db.relationship("Aluno", back_populates="notas")

    __table_args__ = (
        db.UniqueConstraint("avaliacao_id", "aluno_id", name="uq_nota_avaliacao_aluno"),
    )

    def __repr__(self):
        return f"<Nota aluno={self.aluno_id} avaliacao={self.avaliacao_id} valor={self.valor}>"


class Aula(db.Model):
    """Uma aula dada, usada para controle de presença."""

    __tablename__ = "aula"

    id = db.Column(db.Integer, primary_key=True)
    turma_disciplina_id = db.Column(db.Integer, db.ForeignKey("turma_disciplina.id"), nullable=False)
    data = db.Column(db.Date, nullable=False, default=date.today)
    bimestre_numero = db.Column(db.Integer, nullable=False)  # 1 a 4

    turma_disciplina = db.relationship("TurmaDisciplina", back_populates="aulas")
    presencas = db.relationship("Presenca", back_populates="aula", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Aula {self.data} (bim {self.bimestre_numero})>"


class Presenca(db.Model):
    __tablename__ = "presenca"

    id = db.Column(db.Integer, primary_key=True)
    aula_id = db.Column(db.Integer, db.ForeignKey("aula.id"), nullable=False)
    aluno_id = db.Column(db.Integer, db.ForeignKey("aluno.id"), nullable=False)
    presente = db.Column(db.Boolean, nullable=False, default=True)

    aula = db.relationship("Aula", back_populates="presencas")
    aluno = db.relationship("Aluno", back_populates="presencas")

    __table_args__ = (
        db.UniqueConstraint("aula_id", "aluno_id", name="uq_presenca_aula_aluno"),
    )

    def __repr__(self):
        return f"<Presenca aluno={self.aluno_id} aula={self.aula_id} presente={self.presente}>"


class ParametroAprovacao(db.Model):
    """Parâmetros configuráveis pelo admin para calcular a situação final do aluno."""

    __tablename__ = "parametro_aprovacao"

    id = db.Column(db.Integer, primary_key=True)
    ano_letivo = db.Column(db.Integer, unique=True, nullable=False)
    media_minima = db.Column(db.Float, nullable=False, default=6.0)
    frequencia_minima_percentual = db.Column(db.Float, nullable=False, default=75.0)

    def __repr__(self):
        return f"<ParametroAprovacao {self.ano_letivo}>"
