from flask import current_app
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
    title = StringField('Title', validators=[DataRequired(), Length(0, 128)])
    body = TextAreaField('Text', validators=[DataRequired()], render_kw={'rows': 20})
    submit = SubmitField('Submit')
    add_poll = SubmitField('Add poll')
    cancel = SubmitField('Cancel')


class TopicEditForm(TopicForm):
    delete = SubmitField('Delete')


class TopicWithPollForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(0, 128)])
    body = TextAreaField('Text', validators=[DataRequired()], render_kw={'rows': 20})
    poll_question = StringField('Poll question', validators=[DataRequired(), Length(0, 256)])
    poll_answers = TextAreaField('Poll answers', validators=[DataRequired()], render_kw={'rows': 10})
    submit = SubmitField('Submit')
    cancel = SubmitField('Cancel')


class TopicWithPollEditForm(TopicWithPollForm):
    delete = SubmitField('Delete')


class TopicGroupForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(0, 64)])
    priority = SelectField('Priority', coerce=int)
    protected = BooleanField('Protected')
    submit = SubmitField('Submit')
    cancel = SubmitField('Cancel')

    def __init__(self, *args, **kwargs):
        super(TopicGroupForm, self).__init__(*args, **kwargs)
        self.priority.choices = [(p, p) for p in current_app.config['TOPIC_GROUP_PRIORITY']]


class CommentForm(FlaskForm):
    body = TextAreaField('Leave your comment, {username}:', validators=[DataRequired()], render_kw={'rows': 4})
    submit = SubmitField('Submit')

    def __init__(self, user, *args, **kwargs):
        super(CommentForm, self).__init__(*args, **kwargs)
        self.body.label.text = self.body.label.text.format(username=user.username)


class CommentEditForm(FlaskForm):
    body = TextAreaField('Text', validators=[DataRequired()], render_kw={'rows': 4})
    submit = SubmitField('Submit')
    cancel = SubmitField('Cancel')
    delete = SubmitField('Delete')


class MessageReplyForm(FlaskForm):
    title = StringField('Subject', validators=[DataRequired(), Length(0, 128)])
    body = TextAreaField('Text', validators=[DataRequired()], render_kw={'rows': 4})
    send = SubmitField('Send')
    close = SubmitField('Close')
    delete = SubmitField('Delete')


class MessageSendForm(FlaskForm):
    title = StringField('Subject', validators=[DataRequired(), Length(0, 128)])
    body = TextAreaField('Text', validators=[DataRequired()], render_kw={'rows': 4})
    send = SubmitField('Send')
    cancel = SubmitField('Cancel')
