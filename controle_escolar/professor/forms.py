from datetime import date

from flask_wtf import FlaskForm
from wtforms import DateField, FloatField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange


class AvaliacaoForm(FlaskForm):
    nome = StringField("Nome da avaliação", validators=[DataRequired(), Length(max=80)])
    peso = FloatField("Peso", validators=[DataRequired(), NumberRange(min=0.01, max=100)])
    submit = SubmitField("Salvar")


class AulaForm(FlaskForm):
    data = DateField("Data da aula", validators=[DataRequired()], format="%Y-%m-%d", default=date.today)
    submit = SubmitField("Adicionar aula")
