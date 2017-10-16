from flask import render_template, redirect, request, url_for, flash
from flask_babel import lazy_gettext
from flask_login import login_user, logout_user, login_required, current_user

from . import auth
from .forms import LoginForm, RegistrationForm, ChangePasswordForm, ChangeEmailForm, ResetPasswordRequestForm,\
    ResetPasswordForm
from .. import db
from ..email import send_email
from ..models import User


@auth.before_app_request
def check_confirmed():
    if current_user.is_authenticated:
        current_user.ping()
        if (not current_user.confirmed and request.endpoint and
                request.endpoint[:5] != 'auth.' and request.endpoint != 'static'):
            return redirect(url_for('auth.unconfirmed'))


@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('main.index'))
        flash(lazy_gettext('Invalid username or password.'))
    return render_template('auth/login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash(lazy_gettext('You have been logged out.'))
    return redirect(url_for('main.index'))


@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data, username=form.username.data, password=form.password.data)
        db.session.add(user)
        db.session.commit()
        token = user.generate_token()
        send_email(user.email, lazy_gettext('Confirm your account'), 'auth/email/confirm', user=user, token=token)
        flash(lazy_gettext('A confirmation email has been sent to you by email.'))
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)


@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm_registration(token):
        flash(lazy_gettext('You have confirmed your account. Thanks!'))
    else:
        flash(lazy_gettext('The confirmation link is invalid or has expired.'))
    return redirect(url_for('main.index'))


@auth.route('/confirm')
@login_required
def resend_confirmation():
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    token = current_user.generate_token()
    send_email(current_user.email, lazy_gettext('Confirm your account'), 'auth/email/confirm', user=current_user,
               token=token)
    flash(lazy_gettext('A new confirmation email has been sent to you by email.'))
    return redirect(url_for('main.index'))


@auth.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        current_user.password = form.new_password.data
        db.session.add(current_user)
        flash(lazy_gettext('Your password has been updated.'))
        return redirect(request.args.get('next') or url_for('main.index'))
    return render_template('auth/change_password.html', form=form)


@auth.route('/change_email', methods=['GET', 'POST'])
@login_required
def change_email():
    form = ChangeEmailForm()
    if form.validate_on_submit():
        token = current_user.generate_token(new_email=form.new_email.data)
        send_email(form.new_email.data, lazy_gettext('Confirm your new email'), 'auth/email/confirm_new_email',
                   user=current_user, token=token)
        flash(lazy_gettext('A confirmation email has been sent to your new email.'))
        return redirect(request.args.get('next') or url_for('main.index'))
    return render_template('auth/change_email.html', form=form)


@auth.route('/change_email/<token>')
@login_required
def confirm_new_email(token):
    if current_user.confirm_new_email(token):
        flash(lazy_gettext('You have confirmed your new email. Thanks!'))
    else:
        flash(lazy_gettext('The confirmation link is invalid or has expired.'))
    return redirect(url_for('main.index'))


@auth.route('/reset_password', methods=['GET', 'POST'])
def reset_password_request():
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        token = user.generate_token()
        send_email(user.email, lazy_gettext('Instructions to reset your password'), 'auth/email/reset_password',
                   user=user, token=token)
        flash(lazy_gettext('An email with instructions to reset password has been sent to you by email.'))
        return redirect(request.args.get('next') or url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)


@auth.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user.confirm_reset(token, form.password.data):
            flash(lazy_gettext('You have reset your password to new.'))
            return redirect(request.args.get('next') or url_for('auth.login'))
        else:
            flash(lazy_gettext('The confirmation link is invalid or has expired.'))
            return redirect(request.args.get('next') or url_for('auth.reset_password_request'))
    return render_template('auth/reset_password.html', form=form)
