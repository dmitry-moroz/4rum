from flask_babel import lazy_gettext
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms import ValidationError
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo

from ..models import User


class LoginForm(FlaskForm):
    email = StringField(lazy_gettext('Email'), validators=[DataRequired(), Length(1, 64), Email()])
    password = PasswordField(lazy_gettext('Password'), validators=[DataRequired()])
    remember_me = BooleanField(lazy_gettext('Keep me logged in'))
    submit = SubmitField(lazy_gettext('Log In'))


class RegistrationForm(FlaskForm):
    email = StringField(lazy_gettext('Email'), validators=[DataRequired(), Length(1, 64), Email()])
    username = StringField(lazy_gettext('Username'), validators=[
        DataRequired(), Length(1, 32), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0, lazy_gettext(
            'Usernames must have only letters, numbers, dots or underscores'))])
    password = PasswordField(lazy_gettext('Password'), validators=[
        DataRequired(), EqualTo('password2', message=lazy_gettext('Passwords must match.'))])
    password2 = PasswordField(lazy_gettext('Confirm password'), validators=[DataRequired()])
    submit = SubmitField(lazy_gettext('Register'))

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError(lazy_gettext('Email already registered.'))

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError(lazy_gettext('Username already in use.'))


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField(lazy_gettext('Old password'), validators=[DataRequired()])
    new_password = PasswordField(lazy_gettext('New password'), validators=[
        DataRequired(), EqualTo('new_password2', message=lazy_gettext('Passwords must match.'))])
    new_password2 = PasswordField(lazy_gettext('Confirm new password'), validators=[DataRequired()])
    submit = SubmitField(lazy_gettext('Change password'))

    def validate_old_password(self, field):
        if not current_user.verify_password(field.data):
            raise ValidationError(lazy_gettext('Invalid old password.'))

    def validate_new_password(self, field):
        if self.old_password.data == field.data:
            raise ValidationError(lazy_gettext('New password is the same as old password.'))


class ChangeEmailForm(FlaskForm):
    new_email = StringField(lazy_gettext('New email'), validators=[DataRequired(), Length(1, 64), Email()])
    password = PasswordField(lazy_gettext('Password'), validators=[DataRequired()])
    submit = SubmitField(lazy_gettext('Change email'))

    def validate_new_email(self, field):
        if current_user.email == field.data:
            raise ValidationError(lazy_gettext('This is your current email.'))
        if User.query.filter_by(email=field.data).first():
            raise ValidationError(lazy_gettext('Email already registered.'))

    def validate_password(self, field):
        if not current_user.verify_password(field.data):
            raise ValidationError(lazy_gettext('Invalid password.'))


class ResetPasswordRequestForm(FlaskForm):
    email = StringField(lazy_gettext('Email'), validators=[DataRequired(), Length(1, 64), Email()])
    submit = SubmitField(lazy_gettext('Reset password'))

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first() is None:
            raise ValidationError(lazy_gettext('Unknown email address.'))


class ResetPasswordForm(FlaskForm):
    email = StringField(lazy_gettext('Email'), validators=[DataRequired(), Length(1, 64), Email()])
    password = PasswordField(lazy_gettext('New password'), validators=[
        DataRequired(), EqualTo('password2', message=lazy_gettext('Passwords must match.'))])
    password2 = PasswordField(lazy_gettext('Confirm password'), validators=[DataRequired()])
    submit = SubmitField(lazy_gettext('Reset password'))

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first() is None:
            raise ValidationError(lazy_gettext('Unknown email address.'))
