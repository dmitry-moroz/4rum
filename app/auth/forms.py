from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms import ValidationError
from wtforms.validators import Required, Length, Email, Regexp, EqualTo

from ..models import User


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[Required(), Length(1, 64),
                                             Email()])
    password = PasswordField('Password', validators=[Required()])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log In')


class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[Required(), Length(1, 64),
                                           Email()])
    username = StringField('Username', validators=[
        Required(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                          'Usernames must have only letters, '
                                          'numbers, dots or underscores')])
    password = PasswordField('Password', validators=[
        Required(), EqualTo('password2', message='Passwords must match.')])
    password2 = PasswordField('Confirm password', validators=[Required()])
    submit = SubmitField('Register')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Old password', validators=[Required()])
    new_password = PasswordField('New password', validators=[
        Required(), EqualTo('new_password2', message='Passwords must match.')])
    new_password2 = PasswordField('Confirm new password', validators=[Required()])
    submit = SubmitField('Change password')

    def validate_old_password(self, field):
        if not current_user.verify_password(field.data):
            raise ValidationError('Invalid old password.')

    def validate_new_password(self, field):
        if self.old_password.data == field.data:
            raise ValidationError('New password is the same as old password.')


class ChangeEmailForm(FlaskForm):
    new_email = StringField('New email', validators=[Required(), Length(1, 64), Email()])
    password = PasswordField('Password', validators=[Required()])
    submit = SubmitField('Change email')

    def validate_new_email(self, field):
        if current_user.email == field.data:
            raise ValidationError('This is your current email.')
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_password(self, field):
        if not current_user.verify_password(field.data):
            raise ValidationError('Invalid password.')


class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[Required(), Length(1, 64), Email()])
    submit = SubmitField('Reset password')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first() is None:
            raise ValidationError('Unknown email address.')


class ResetPasswordForm(FlaskForm):
    email = StringField('Email', validators=[Required(), Length(1, 64), Email()])
    password = PasswordField('New password', validators=[
        Required(), EqualTo('password2', message='Passwords must match.')])
    password2 = PasswordField('Confirm password', validators=[Required()])
    submit = SubmitField('Reset password')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first() is None:
            raise ValidationError('Unknown email address.')
