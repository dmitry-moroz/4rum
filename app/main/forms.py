from flask import current_app
from flask_pagedown.fields import PageDownField
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SelectField, SubmitField
from wtforms import ValidationError
from wtforms.validators import DataRequired, Length, Email, Regexp

from ..models import Role, User


class NameForm(FlaskForm):
    name = StringField('What is your name?', validators=[DataRequired()])
    submit = SubmitField('Submit')


class EditProfileForm(FlaskForm):
    name = StringField('Real name', validators=[Length(0, 64)])
    homeland = StringField('Homeland', validators=[Length(0, 64)])
    about = TextAreaField('About me')
    avatar = StringField('Link to avatar', validators=[Length(0, 256)])
    submit = SubmitField('Submit')


class EditProfileAdminForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64), Email()])
    username = StringField('Username', validators=[
        DataRequired(), Length(1, 64),
        Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0, 'Usernames must have only letters, numbers, dots or underscores')])
    confirmed = BooleanField('Confirmed')
    role = SelectField('Role', coerce=int)
    name = StringField('Real name', validators=[Length(0, 64)])
    homeland = StringField('Location', validators=[Length(0, 64)])
    about = TextAreaField('About me')
    avatar = StringField('Link to avatar', validators=[Length(0, 256)])
    submit = SubmitField('Submit')

    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name) for role in Role.query.order_by(Role.name).all()]
        self.user = user

    def validate_email(self, field):
        if field.data != self.user.email and User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        if field.data != self.user.username and User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')


class TopicForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(0, 64)])
    body = PageDownField('Text', validators=[DataRequired()], render_kw={'rows': 20})
    submit = SubmitField('Submit')
    cancel = SubmitField('Cancel')

    def validate_body(self, field):
        max_len = current_app.config['MAX_WORD_LENGTH_FOR_TOPIC']
        parts = field.data.split(' ')
        for part in parts:
            if len(part) > max_len:
                if current_app.config['RAISE_ON_WORD_LENGTH_EXCEEDED']:
                    raise ValidationError('Maximum word length for topic exceeded [{0}].'.format(max_len))
                new_subparts = [part[n * max_len: n * max_len + max_len] for n in xrange(len(part) // max_len)]
                new_subparts.append(part[len(part) // max_len * max_len:])
                new_part = ' '.join(new_subparts)
                field.data = field.data.replace(part, new_part)


class TopicGroupForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(0, 64)])
    priority = SelectField('Priority', coerce=int)
    protected = BooleanField('Protected')
    submit = SubmitField('Submit')
    cancel = SubmitField('Cancel')

    def __init__(self, *args, **kwargs):
        super(TopicGroupForm, self).__init__(*args, **kwargs)
        self.priority.choices = [(p, p) for p in current_app.config['TOPIC_GROUP_PRIORITY']]
