from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField
from wtforms.validators import DataRequired

class PhenCardsForm(FlaskForm):
    phenname = StringField('phenotype_names')
    doc2phen_check = BooleanField('doc2phen_check')
    doc2phen_notes = StringField('doc2phen_notes')

class Phen2GeneForm(FlaskForm):
    HPO_list = StringField('HPO_list')
    weight_model = StringField('weight_model', validators=[DataRequired()])
    doc2hpo_check = BooleanField('doc2hpo_check')
    doc2hpo_notes = StringField('doc2hpo_notes')
