from flask import render_template, redirect, url_for, abort, flash, request, current_app
from flask_login import login_required, current_user

from . import main
from .forms import EditProfileForm, EditProfileAdminForm, TopicForm, TopicGroupForm
from .. import db
from ..decorators import admin_required, permission_required
from ..models import Permission, Role, User, Topic, TopicGroup


@main.route('/')
def index():
    t_group = TopicGroup.query.get_or_404(current_app.config['ROOT_TOPIC_GROUP'])
    t_groups = t_group.topic_groups.order_by(TopicGroup.priority, TopicGroup.created_at.desc()).all()
    page = request.args.get('page', 1, type=int)
    pagination = t_group.topics.order_by(Topic.created_at.desc()).paginate(
        page, per_page=current_app.config['TOPICS_PER_PAGE'], error_out=False)
    return render_template('index.html', topic_group=t_group, topic_groups=t_groups,
                           topics=pagination.items, pagination=pagination)


@main.route('/create_topic/<int:topic_group_id>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.WRITE)
def create_topic(topic_group_id):
    form = TopicForm()
    t_group = TopicGroup.query.get_or_404(topic_group_id)
    if t_group.protected and not current_user.is_moderator():
        abort(403)
    if form.cancel.data:
        flash('Topic creation has been cancelled.')
        return redirect(url_for('main.topic_group', topic_group_id=topic_group_id))
    if form.submit.data and form.validate_on_submit():
        topic = Topic(title=form.title.data, body=form.body.data,
                      author=current_user._get_current_object(), group=t_group)
        db.session.add(topic)
        return redirect(url_for('main.topic_group', topic_group_id=topic_group_id))
    return render_template('create_topic.html', form=form, topic_group=t_group)


@main.route('/topic_group/<int:topic_group_id>')
def topic_group(topic_group_id):
    if topic_group_id == current_app.config['ROOT_TOPIC_GROUP']:
        return redirect(url_for('main.index'))
    t_group = TopicGroup.query.get_or_404(topic_group_id)
    t_groups = t_group.topic_groups.order_by(TopicGroup.priority, TopicGroup.created_at.desc()).all()
    page = request.args.get('page', 1, type=int)
    pagination = t_group.topics.order_by(Topic.created_at.desc()).paginate(
        page, per_page=current_app.config['TOPICS_PER_PAGE'], error_out=False)
    return render_template('topic_group.html', topic_group=t_group, topic_groups=t_groups,
                           topics=pagination.items, pagination=pagination)


@main.route('/create_topic_group/<int:topic_group_id>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MODERATE)
def create_topic_group(topic_group_id):
    form = TopicGroupForm()
    t_group = TopicGroup.query.get_or_404(topic_group_id)
    if form.cancel.data:
        flash('Topic group creation has been cancelled.')
        return redirect(url_for('main.topic_group', topic_group_id=topic_group_id))
    if form.submit.data and form.validate_on_submit():
        if form.priority.data not in current_app.config['TOPIC_GROUP_PRIORITY']:
            abort(404)
        new_t_group = TopicGroup(title=form.title.data, priority=form.priority.data,
                                 protected=form.protected.data, author=current_user._get_current_object(),
                                 group=t_group)
        db.session.add(new_t_group)
        return redirect(url_for('main.topic_group', topic_group_id=topic_group_id))
    return render_template('create_topic_group.html', form=form, topic_group=t_group)


@main.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    pagination = user.topics.order_by(Topic.created_at.desc()).paginate(
        page, per_page=current_app.config['TOPICS_PER_PAGE'], error_out=False)
    return render_template('user.html', user=user, topics=pagination.items, pagination=pagination)


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


@main.route('/edit_profile/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(user_id):
    user = User.query.get_or_404(user_id)
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
