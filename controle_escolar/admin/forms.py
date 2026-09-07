from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import DateField, FloatField, IntegerField, PasswordField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional


class TurmaForm(FlaskForm):
    nome = StringField("Nome/Série", validators=[DataRequired(), Length(max=80)])
    ano_letivo = IntegerField("Ano letivo", validators=[DataRequired(), NumberRange(min=2000, max=2100)])
    submit = SubmitField("Salvar")


class DisciplinaForm(FlaskForm):
    nome = StringField("Nome", validators=[DataRequired(), Length(max=80)])
    submit = SubmitField("Salvar")


class ProfessorForm(FlaskForm):
    nome = StringField("Nome", validators=[DataRequired(), Length(max=120)])
    email = StringField("E-mail", validators=[Optional(), Email(), Length(max=120)])
    telefone = StringField("Telefone", validators=[Optional(), Length(max=30)])
    login = StringField("Login de acesso", validators=[DataRequired(), Length(max=80)])
    senha = PasswordField(
        "Senha",
        validators=[Optional(), Length(min=4, message="A senha deve ter ao menos 4 caracteres.")],
    )
    submit = SubmitField("Salvar")


class AtribuicaoForm(FlaskForm):
    disciplina_id = SelectField("Disciplina", coerce=int, validators=[DataRequired()])
    professor_id = SelectField("Professor responsável", coerce=int, validators=[DataRequired()])
    submit = SubmitField("Atribuir")


class AlunoForm(FlaskForm):
    nome = StringField("Nome", validators=[DataRequired(), Length(max=120)])
    matricula = StringField("Matrícula", validators=[DataRequired(), Length(max=30)])
    data_nascimento = DateField("Data de nascimento", validators=[Optional()], format="%Y-%m-%d")
    nome_responsavel = StringField("Nome do responsável", validators=[Optional(), Length(max=120)])
    contato_responsavel = StringField("Contato do responsável", validators=[Optional(), Length(max=120)])
    turma_id = SelectField("Turma", coerce=int, validators=[DataRequired()])
    submit = SubmitField("Salvar")


class ImportarAlunosForm(FlaskForm):
    arquivo = FileField(
        "Planilha (.xlsx ou .csv)",
        validators=[
            FileRequired(message="Selecione um arquivo."),
            FileAllowed(["xlsx", "csv"], "Envie um arquivo .xlsx ou .csv"),
        ],
    )
    submit = SubmitField("Importar")


class ParametroAprovacaoForm(FlaskForm):
    media_minima = FloatField(
        "Média mínima para aprovação", validators=[DataRequired(), NumberRange(min=0, max=10)]
    )
    frequencia_minima_percentual = FloatField(
        "Frequência mínima (%)", validators=[DataRequired(), NumberRange(min=0, max=100)]
    )
    submit = SubmitField("Salvar")
