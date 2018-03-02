from flask import current_app, session
from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SelectField, SubmitField, IntegerField
from wtforms import ValidationError
from wtforms.validators import DataRequired, Length, Email, Regexp

from ..models import Role, User, TopicGroup


class FormHelpersMixIn(object):

    @property
    def submit_fields(self):
        return [getattr(self, field) for field, field_type in self._fields.items()
                if isinstance(field_type, SubmitField)]

    @staticmethod
    def is_has_data(*fields):
        return any([field.data for field in fields])

    def get_flashed_errors(self):
        errors = session.pop('_form_errors') if '_form_errors' in session else {}
        self.errors.update(errors)
        for field, errors in errors.items():
            if hasattr(self, field):
                form_field = getattr(self, field)
                if form_field.errors:
                    form_field.errors.extend(errors)
                else:
                    form_field.errors = errors


class EditProfileForm(FlaskForm):
    name = StringField(lazy_gettext('Real name'), validators=[Length(0, 64)])
    homeland = StringField(lazy_gettext('Homeland'), validators=[Length(0, 64)])
    about = TextAreaField(lazy_gettext('About me'))
    avatar = StringField(lazy_gettext('Link to avatar'), validators=[Length(0, 256)])
    submit = SubmitField(lazy_gettext('Submit'))


class EditProfileAdminForm(FlaskForm):
    email = StringField(lazy_gettext('Email'), validators=[DataRequired(), Length(1, 64), Email()])
    username = StringField(lazy_gettext('Username'), validators=[
        DataRequired(), Length(1, 32), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0, lazy_gettext(
            'Usernames must have only letters, numbers, dots or underscores'))])
    confirmed = BooleanField(lazy_gettext('Confirmed'))
    role = SelectField(lazy_gettext('Role'), coerce=int)
    name = StringField(lazy_gettext('Real name'), validators=[Length(0, 64)])
    homeland = StringField(lazy_gettext('Homeland'), validators=[Length(0, 64)])
    about = TextAreaField(lazy_gettext('About me'))
    avatar = StringField(lazy_gettext('Link to avatar'), validators=[Length(0, 256)])
    submit = SubmitField(lazy_gettext('Submit'))

    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name) for role in Role.query.order_by(Role.name).all()]
        self.user = user

    def validate_email(self, field):
        if field.data != self.user.email and User.query.filter_by(email=field.data).first():
            raise ValidationError(lazy_gettext('Email already registered.'))
        field.data = field.data.lower()

    def validate_username(self, field):
        if field.data != self.user.username and User.query.filter_by(username=field.data).first():
            raise ValidationError(lazy_gettext('Username already in use.'))


class TopicForm(FlaskForm):
    title = StringField(lazy_gettext('Title'), validators=[DataRequired(), Length(0, 128)])
    body = TextAreaField(lazy_gettext('Text'), validators=[DataRequired()], render_kw={'rows': 20})
    submit = SubmitField(lazy_gettext('Submit'))
    add_poll = SubmitField(lazy_gettext('Add poll'))
    cancel = SubmitField(lazy_gettext('Cancel'))


class TopicEditForm(FlaskForm):
    title = StringField(lazy_gettext('Title'), validators=[DataRequired(), Length(0, 128)])
    group_id = IntegerField(lazy_gettext('Topic group ID'), validators=[DataRequired()], render_kw={'disabled': True})
    body = TextAreaField(lazy_gettext('Text'), validators=[DataRequired()], render_kw={'rows': 20})
    submit = SubmitField(lazy_gettext('Submit'))
    add_poll = SubmitField(lazy_gettext('Add poll'))
    cancel = SubmitField(lazy_gettext('Cancel'))
    delete = SubmitField(lazy_gettext('Delete'))

    def validate_group_id(self, field):
        if not TopicGroup.query.filter_by(id=field.data).first():
            raise ValidationError(lazy_gettext('Topic group with such ID is not exist.'))


class TopicWithPollForm(FlaskForm):
    title = StringField(lazy_gettext('Title'), validators=[DataRequired(), Length(0, 128)])
    body = TextAreaField(lazy_gettext('Text'), validators=[DataRequired()], render_kw={'rows': 20})
    poll_question = StringField(lazy_gettext('Poll question'), validators=[DataRequired(), Length(0, 256)])
    poll_answers = TextAreaField(lazy_gettext('Poll answers'), validators=[DataRequired()], render_kw={'rows': 10})
    submit = SubmitField(lazy_gettext('Submit'))
    cancel = SubmitField(lazy_gettext('Cancel'))


class TopicWithPollEditForm(FlaskForm):
    title = StringField(lazy_gettext('Title'), validators=[DataRequired(), Length(0, 128)])
    group_id = IntegerField(lazy_gettext('Topic group ID'), validators=[DataRequired()], render_kw={'disabled': True})
    body = TextAreaField(lazy_gettext('Text'), validators=[DataRequired()], render_kw={'rows': 20})
    poll_question = StringField(lazy_gettext('Poll question'), validators=[DataRequired(), Length(0, 256)])
    poll_answers = TextAreaField(lazy_gettext('Poll answers'), validators=[DataRequired()], render_kw={'rows': 10})
    submit = SubmitField(lazy_gettext('Submit'))
    cancel = SubmitField(lazy_gettext('Cancel'))
    delete = SubmitField(lazy_gettext('Delete'))

    def validate_group_id(self, field):
        if not TopicGroup.query.filter_by(id=field.data).first():
            raise ValidationError(lazy_gettext('Topic group with such ID is not exist.'))


class TopicGroupForm(FlaskForm):
    title = StringField(lazy_gettext('Title'), validators=[DataRequired(), Length(0, 64)])
    priority = SelectField(lazy_gettext('Priority'), coerce=int)
    protected = BooleanField(lazy_gettext('Moderators only'))
    submit = SubmitField(lazy_gettext('Submit'))
    cancel = SubmitField(lazy_gettext('Cancel'))

    def __init__(self, *args, **kwargs):
        super(TopicGroupForm, self).__init__(*args, **kwargs)
        self.priority.choices = [(p, p) for p in current_app.config['TOPIC_GROUP_PRIORITY']]


class CommentForm(FlaskForm, FormHelpersMixIn):
    body = TextAreaField(lazy_gettext('Leave your comment, {username}:'), validators=[DataRequired()],
                         render_kw={'rows': 4})
    submit = SubmitField(lazy_gettext('Submit'))

    def __init__(self, user, *args, **kwargs):
        super(CommentForm, self).__init__(*args, **kwargs)
        self.body.label.text = self.body.label.text.format(username=user.username)


class CommentEditForm(FlaskForm, FormHelpersMixIn):
    body = TextAreaField(lazy_gettext('Text'), validators=[DataRequired()], render_kw={'rows': 8})
    submit = SubmitField(lazy_gettext('Submit'))
    cancel = SubmitField(lazy_gettext('Cancel'))
    delete = SubmitField(lazy_gettext('Delete'))


class MessageReplyForm(FlaskForm):
    title = StringField(lazy_gettext('Subject'), validators=[DataRequired(), Length(0, 128)])
    body = TextAreaField(lazy_gettext('Text'), validators=[DataRequired()], render_kw={'rows': 4})
    send = SubmitField(lazy_gettext('Send'))
    close = SubmitField(lazy_gettext('Close'))
    delete = SubmitField(lazy_gettext('Delete'))


class MessageSendForm(FlaskForm):
    title = StringField(lazy_gettext('Subject'), validators=[DataRequired(), Length(0, 128)])
    body = TextAreaField(lazy_gettext('Text'), validators=[DataRequired()], render_kw={'rows': 4})
    send = SubmitField(lazy_gettext('Send'))
    cancel = SubmitField(lazy_gettext('Cancel'))


class SearchForm(FlaskForm):
    text = StringField('', validators=[DataRequired(), Length(1, 64)])
    search = SubmitField(lazy_gettext('Search'))
