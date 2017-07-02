from flask import render_template, redirect, url_for, abort, flash
from flask_login import login_required, current_user
from . import main
from .forms import EditProfileForm, EditProfileAdminForm, TopicForm
from .. import db
from ..models import Permission, Role, User, Topic
from ..decorators import admin_required


@main.route('/', methods=['GET', 'POST'])
def index():
    form = None
    if current_user.can(Permission.WRITE):
        form = TopicForm()
        if form.validate_on_submit():
            topic = Topic(body=form.body.data, author=current_user._get_current_object())
            db.session.add(topic)
            return redirect(url_for('main.index'))
    topics = Topic.query.order_by(Topic.created_at.desc()).all()
    return render_template('index.html', form=form, topics=topics)


@main.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    topics = user.topics.order_by(Topic.created_at.desc()).all()
    return render_template('user.html', user=user, topics=topics)


@main.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.homeland = form.homeland.data
        current_user.about = form.about.data
        current_user.avatar = form.avatar.data if form.avatar.data else current_user.gravatar()
        db.session.add(current_user)
        flash('Your profile has been updated.')
        return redirect(url_for('main.user', username=current_user.username))
    form.name.data = current_user.name
    form.homeland.data = current_user.homeland
    form.about.data = current_user.about
    form.avatar.data = current_user.avatar
    return render_template('edit_profile.html', form=form)


@main.route('/edit_profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.homeland = form.homeland.data
        user.about = form.about.data
        user.avatar = form.avatar.data if form.avatar.data else user.gravatar()
        db.session.add(user)
        flash('The profile has been updated.')
        return redirect(url_for('main.user', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.name
    form.homeland.data = user.homeland
    form.about.data = user.about
    form.avatar.data = user.avatar
    return render_template('edit_profile.html', form=form, user=user)
