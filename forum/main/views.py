from datetime import datetime, timedelta

from flask import render_template, redirect, url_for, abort, flash, request, current_app, session
from flask_babel import lazy_gettext
from flask_login import login_required, current_user
from sqlalchemy import func, case, between, and_, or_

from . import main
from .forms import (EditProfileForm, EditProfileAdminForm, TopicForm, TopicGroupForm, TopicWithPollForm,
                    CommentForm, CommentEditForm, MessageReplyForm, MessageSendForm, SearchForm)
from ..app import babel, db
from ..decorators import admin_required, permission_required
from ..models import Permission, Role, User, Topic, TopicGroup, Comment, PollAnswer, Message


def get_topic_group(topic_group_id):
    t_group = TopicGroup.query.filter_by(id=topic_group_id, deleted=False).first_or_404()
    t_groups = TopicGroup.query.with_entities(
        TopicGroup, func.sum(case([(Topic.deleted == False, 1)], else_=0))).outerjoin(
        Topic, TopicGroup.id == Topic.group_id).filter(
        and_(TopicGroup.deleted == False, TopicGroup.group_id == t_group.id)).group_by(
        TopicGroup.id).order_by(TopicGroup.priority, TopicGroup.created_at.desc()).all()

    page = request.args.get('page', 1, type=int)
    pagination = Topic.query.with_entities(
        Topic, User, func.sum(case([(Comment.deleted == False, 1)], else_=0))).join(
        User, Topic.author_id == User.id).outerjoin(
        Comment, Topic.id == Comment.topic_id).filter(
        and_(Topic.group_id == t_group.id, Topic.deleted == False)).group_by(Topic.id, User.id).order_by(
        Topic.created_at.desc()).paginate(page, per_page=current_app.config['TOPICS_PER_PAGE'], error_out=False)

    return t_group, t_groups, pagination


@main.route('/')
def index():
    t_group, t_groups, pagination = get_topic_group(current_app.config['ROOT_TOPIC_GROUP'])
    return render_template('index.html', topic_group=t_group, topic_groups=t_groups, topics=pagination.items,
                           pagination=pagination)


@main.route('/topic/<int:topic_id>', methods=['GET', 'POST'])
def topic(topic_id):
    tpc = Topic.query.filter_by(id=topic_id, deleted=False).first_or_404()

    form = CommentForm(current_user) if current_user.can(Permission.PARTICIPATE) else None
    if form and form.validate_on_submit():
        tpc.add_comment(current_user, form.body.data)
        flash(lazy_gettext('Your comment has been published.'))
        return redirect(url_for('main.topic', topic_id=topic_id, page=-1))

    page = request.args.get('page', 1, type=int)
    if page == -1:
        page = (tpc.comments_count - 1) // current_app.config['COMMENTS_PER_PAGE'] + 1

    pagination = Comment.query.with_entities(
        Comment, User).join(User, Comment.author_id == User.id).filter(
        and_(Comment.topic_id == tpc.id, Comment.deleted == False)).order_by(
        Comment.created_at.asc()).paginate(page, per_page=current_app.config['COMMENTS_PER_PAGE'], error_out=False)

    user_vote = current_user.get_vote(tpc)
    if tpc.poll and user_vote:
        poll_data = tpc.get_poll_results()
    else:
        poll_data = [(a.id, a.body) for a in tpc.poll_answers.filter_by(deleted=False).all()]

    return render_template('topic.html', topic=tpc, form=form, user_vote=user_vote, poll_data=poll_data,
                           comments=pagination.items, pagination=pagination)


@main.route('/create_topic/<int:topic_group_id>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.WRITE)
def create_topic(topic_group_id):
    t_group = TopicGroup.query.get_or_404(topic_group_id)
    if t_group.protected and not current_user.is_moderator():
        abort(403)

    with_poll = request.args.get('poll', 0, type=int)
    form = TopicWithPollForm() if with_poll else TopicForm()
    form.remove_edit_fields()

    if form.submit.data and form.validate_on_submit():
        new_topic = Topic(title=form.title.data, body=form.body.data, group=t_group,
                          author=current_user._get_current_object())
        if with_poll:
            new_topic.poll = form.poll_question.data
        db.session.add(new_topic)
        db.session.commit()
        if with_poll:
            poll_answers = form.poll_answers.data.strip().splitlines()
            new_topic.update_poll_answers(poll_answers)
        flash(lazy_gettext('Topic has been created.'))
        return redirect(url_for('main.topic', topic_id=new_topic.id))

    elif not with_poll and form.add_poll.data:
        if form.title.data or form.body.data:
            if form.validate_on_submit():
                new_topic = Topic(title=form.title.data, body=form.body.data, group=t_group,
                                  author=current_user._get_current_object())
                db.session.add(new_topic)
                db.session.commit()
                flash(lazy_gettext('Topic has been saved. Fill data for a poll.'))
                return redirect(url_for('main.edit_topic', topic_id=new_topic.id, poll=1))
        else:
            return redirect(url_for('main.create_topic', topic_group_id=topic_group_id, poll=1))

    elif form.cancel.data:
        flash(lazy_gettext('Topic creation was cancelled.'))
        return redirect(url_for('main.topic_group', topic_group_id=topic_group_id))

    return render_template('create_topic.html', form=form, topic_group=t_group)


@main.route('/edit_topic/<int:topic_id>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.WRITE)
def edit_topic(topic_id):
    tpc = Topic.query.filter_by(id=topic_id, deleted=False).first_or_404()
    if current_user != tpc.author and not current_user.is_moderator():
        abort(403)

    with_poll = request.args.get('poll', 0, type=int) or tpc.poll
    form = TopicWithPollForm() if with_poll else TopicForm()
    if not current_user.is_moderator():
        del form.group_id

    if form.submit.data and form.validate_on_submit():
        if current_user.is_moderator():
            tpc.group_id = form.group_id.data
        tpc.title = form.title.data
        tpc.body = form.body.data
        if with_poll:
            tpc.poll = form.poll_question.data
            tpc.update_poll_answers(form.poll_answers.data.strip().splitlines())
        tpc.updated_at = datetime.utcnow()
        db.session.add(tpc)
        flash(lazy_gettext('The topic has been updated.'))
        return redirect(url_for('main.topic', topic_id=tpc.id))

    elif not with_poll and form.add_poll.data and form.validate_on_submit():
        if current_user.is_moderator():
            tpc.group_id = form.group_id.data
        tpc.title = form.title.data
        tpc.body = form.body.data
        tpc.updated_at = datetime.utcnow()
        db.session.add(tpc)
        flash(lazy_gettext('Topic has been saved. Fill data for a poll.'))
        return redirect(url_for('main.edit_topic', topic_id=tpc.id, poll=1))

    elif form.cancel.data:
        flash(lazy_gettext('Topic editing was cancelled.'))
        return redirect(url_for('main.topic', topic_id=tpc.id))

    elif form.delete.data:
        tpc.comments.update(dict(deleted=True))
        tpc.poll_answers.update(dict(deleted=True))
        tpc.poll_votes.update(dict(deleted=True))
        tpc.deleted = True
        tpc.updated_at = datetime.utcnow()
        db.session.add(tpc)
        flash(lazy_gettext('The topic has been deleted.'))
        return redirect(url_for('main.topic_group', topic_group_id=tpc.group_id))

    if not form.is_submitted():
        form.title.data = tpc.title
        form.body.data = tpc.body
        if form.group_id:
            form.group_id.data = tpc.group_id
        if tpc.poll:
            form.poll_question.data = tpc.poll
            form.poll_answers.data = '\n'.join([a.body for a in tpc.poll_answers.filter_by(deleted=False).all()])

    return render_template('edit_topic.html', form=form, topic=tpc)


@main.route('/topic_group/<int:topic_group_id>')
def topic_group(topic_group_id):
    if topic_group_id == current_app.config['ROOT_TOPIC_GROUP']:
        return redirect(url_for('main.index'))
    t_group, t_groups, pagination = get_topic_group(topic_group_id)
    return render_template('topic_group.html', topic_group=t_group, topic_groups=t_groups, topics=pagination.items,
                           pagination=pagination)


@main.route('/create_topic_group/<int:topic_group_id>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MODERATE)
def create_topic_group(topic_group_id):
    t_group = TopicGroup.query.get_or_404(topic_group_id)

    form = TopicGroupForm()
    form.remove_edit_fields()

    if form.submit.data and form.validate_on_submit():
        if form.priority.data not in current_app.config['TOPIC_GROUP_PRIORITY']:
            abort(404)
        new_t_group = TopicGroup(title=form.title.data, priority=form.priority.data, protected=form.protected.data,
                                 author=current_user._get_current_object(), group=t_group)
        db.session.add(new_t_group)
        db.session.commit()
        flash(lazy_gettext('Topic group has been created.'))
        return redirect(url_for('main.topic_group', topic_group_id=new_t_group.id))

    elif form.cancel.data:
        flash(lazy_gettext('Topic group creation was cancelled.'))
        return redirect(url_for('main.topic_group', topic_group_id=topic_group_id))

    return render_template('create_topic_group.html', form=form, topic_group=t_group)


@main.route('/edit_topic_group/<int:topic_group_id>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MODERATE)
def edit_topic_group(topic_group_id):
    t_group = TopicGroup.query.filter_by(id=topic_group_id, deleted=False).first_or_404()

    form = TopicGroupForm()
    if t_group.is_root_topic_group():
        del form.title
        del form.priority
        del form.group_id
        del form.delete

    if form.submit.data and form.validate_on_submit():
        if form.priority and form.priority.data not in current_app.config['TOPIC_GROUP_PRIORITY']:
            abort(404)
        if form.title:
            t_group.title = form.title.data
        if form.group_id:
            t_group.group_id = form.group_id.data
        if form.priority:
            t_group.priority = form.priority.data
        t_group.protected = form.protected.data
        t_group.updated_at = datetime.utcnow()
        db.session.add(t_group)
        flash(lazy_gettext('Topic group has been updated.'))
        return redirect(url_for('main.topic_group', topic_group_id=topic_group_id))

    elif form.cancel.data:
        flash(lazy_gettext('Topic group editing was cancelled.'))
        return redirect(url_for('main.topic_group', topic_group_id=topic_group_id))

    elif form.delete and form.delete.data:
        if t_group.topics.first() or t_group.topic_groups.first():
            flash(lazy_gettext('Topic group is not deleted. Only empty topic group can be deleted.'))
            return redirect(url_for('main.topic_group', topic_group_id=topic_group_id))
        else:
            t_group.deleted = True
            t_group.updated_at = datetime.utcnow()
            db.session.add(t_group)
            return redirect(url_for('main.topic_group', topic_group_id=t_group.group_id))

    if not form.is_submitted():
        if form.title:
            form.title.data = t_group.title
        if form.group_id:
            form.group_id.data = t_group.group_id
        if form.priority:
            form.priority.data = t_group.priority
        form.protected.data = t_group.protected

    return render_template('edit_topic_group.html', form=form, topic_group=t_group)


@main.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username_normalized=username.lower()).first_or_404()

    page = request.args.get('page', 1, type=int)
    pagination = Topic.query.with_entities(
        Topic, User, func.sum(case([(Comment.deleted == False, 1)], else_=0))).join(
        User, Topic.author_id == User.id).outerjoin(
        Comment, Topic.id == Comment.topic_id).filter(
        and_(Topic.author_id == user.id, Topic.deleted == False)).group_by(Topic.id, User.id).order_by(
        Topic.created_at.desc()).paginate(page, per_page=current_app.config['TOPICS_PER_PAGE'], error_out=False)

    topics_count = db.session.query(func.count(Topic.id)).filter(
        and_(Topic.author_id == user.id, Topic.deleted == False)).scalar()
    comments_count = db.session.query(func.count(Comment.id)).filter(
        and_(Comment.author_id == user.id, Comment.deleted == False)).scalar()

    return render_template('user.html', user=user, topics=pagination.items, pagination=pagination,
                           topics_count=topics_count, comments_count=comments_count)


@main.route('/edit_profile', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.WRITE)
def edit_profile():
    form = EditProfileForm()

    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.homeland = form.homeland.data
        current_user.about = form.about.data
        current_user.avatar = form.avatar.data if form.avatar.data else current_user.gravatar()
        current_user.updated_at = datetime.utcnow()
        db.session.add(current_user)
        flash(lazy_gettext('Your profile has been updated.'))
        return redirect(url_for('main.user', username=current_user.username))

    if not form.is_submitted():
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
        user.username_normalized = form.username.data.lower()
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.homeland = form.homeland.data
        user.about = form.about.data
        user.avatar = form.avatar.data if form.avatar.data else user.gravatar()
        user.updated_at = datetime.utcnow()
        db.session.add(user)
        flash(lazy_gettext('The profile has been updated.'))
        return redirect(url_for('main.user', username=user.username))

    if not form.is_submitted():
        form.email.data = user.email
        form.username.data = user.username
        form.confirmed.data = user.confirmed
        form.role.data = user.role_id
        form.name.data = user.name
        form.homeland.data = user.homeland
        form.about.data = user.about
        form.avatar.data = user.avatar

    return render_template('edit_profile.html', form=form, user=user)


@main.route('/latest')
def latest():
    page_arg = request.args.get('page', 1, type=int)
    target_arg = request.args.get('target', 'topics', type=str)

    if target_arg == 'topics':
        pagination = Topic.query.with_entities(
            Topic, User, func.sum(case([(Comment.deleted == False, 1)], else_=0))).join(
            User, Topic.author_id == User.id).outerjoin(
            Comment, Topic.id == Comment.topic_id).filter(Topic.deleted == False).group_by(Topic.id, User.id).order_by(
            Topic.created_at.desc()).paginate(
            page_arg, per_page=current_app.config['TOPICS_PER_PAGE'], error_out=False)
    elif target_arg == 'comments':
        pagination = Comment.query.with_entities(
            Comment, User, Topic).join(User, Comment.author_id == User.id).join(
            Topic, Comment.topic_id == Topic.id).filter(Comment.deleted == False).order_by(
            Comment.created_at.desc()).paginate(
            page_arg, per_page=current_app.config['COMMENTS_PER_PAGE'], error_out=False)
    else:
        abort(400)

    return render_template('latest.html', target=target_arg, items=pagination.items, pagination=pagination)


@main.route('/edit_comment/<int:comment_id>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.WRITE)
def edit_comment(comment_id):
    comment = Comment.query.filter_by(id=comment_id, deleted=False).first_or_404()
    if current_user != comment.author and not current_user.is_moderator():
        abort(403)

    form = CommentEditForm()

    if form.submit.data and form.validate_on_submit():
        comment.body = form.body.data
        comment.updated_at = datetime.utcnow()
        db.session.add(comment)
        flash(lazy_gettext('The comment has been updated.'))
        return redirect(request.args.get('next') or url_for('main.topic', topic_id=comment.topic_id))

    elif form.cancel.data:
        flash(lazy_gettext('Comment editing was cancelled.'))
        return redirect(request.args.get('next') or url_for('main.topic', topic_id=comment.topic_id))

    elif form.delete.data:
        comment.deleted = True
        comment.updated_at = datetime.utcnow()
        db.session.add(comment)
        flash(lazy_gettext('The comment has been deleted.'))
        return redirect(request.args.get('next') or url_for('main.topic', topic_id=comment.topic_id))

    if not form.is_submitted():
        form.body.data = comment.body

    return render_template('edit_comment.html', form=form, comment=comment)


@main.route('/vote/<int:answer_id>')
@login_required
@permission_required(Permission.PARTICIPATE)
def vote(answer_id):
    answer = PollAnswer.query.filter_by(id=answer_id, deleted=False).first_or_404()
    if current_user.get_vote(answer.topic):
        flash(lazy_gettext('You have already voted for this poll.'))
    else:
        answer.topic.add_vote(current_user, answer)
        flash(lazy_gettext('Your vote has been taken.'))
    return redirect(request.args.get('next') or url_for('main.topic', topic_id=answer.topic_id))


@main.route('/hot')
def hot():
    page_arg = request.args.get('page', 1, type=int)
    period_arg = request.args.get('period', 'week', type=str)

    now = datetime.utcnow()
    periods = {
        'day': (now - timedelta(days=1), now),
        'week': (now - timedelta(days=7), now),
        'month': (now - timedelta(days=30), now),
        'year': (now - timedelta(days=365), now),
    }

    pagination = Topic.query.with_entities(
        Topic, User, func.sum(case([(Comment.deleted == False, 1)], else_=0))).join(
        User, Topic.author_id == User.id).outerjoin(
        Comment, Topic.id == Comment.topic_id).filter(
        and_(Topic.deleted == False, between(Topic.created_at, periods[period_arg][0], periods[period_arg][1]))
        ).group_by(Topic.id, User.id).order_by(Topic.interest.desc()).paginate(
        page_arg, per_page=current_app.config['TOPICS_PER_PAGE'], error_out=False)

    return render_template('hot.html', period=period_arg, topics=pagination.items, pagination=pagination)


@main.route('/messages')
@login_required
def messages():
    page = request.args.get('page', 1, type=int)
    direction = request.args.get('direction', 'received', type=str)

    if direction == 'received':
        pagination = Message.query.with_entities(Message, User).join(
            User, Message.author_id == User.id).filter(
            and_(Message.receiver_id == current_user.id, Message.receiver_deleted == False)).order_by(
            Message.created_at.desc()).paginate(page, per_page=current_app.config['MESSAGES_PER_PAGE'], error_out=False)
    elif direction == 'sent':
        pagination = Message.query.with_entities(Message, User).join(
            User, Message.receiver_id == User.id).filter(
            and_(Message.author_id == current_user.id, Message.author_deleted == False)).order_by(
            Message.created_at.desc()).paginate(page, per_page=current_app.config['MESSAGES_PER_PAGE'], error_out=False)
    else:
        abort(400)

    return render_template('messages.html', messages=pagination.items, pagination=pagination, direction=direction)


@main.route('/message/<int:message_id>', methods=['GET', 'POST'])
@login_required
def message(message_id):
    msg = Message.query.filter_by(id=message_id).filter(or_(
        and_(Message.author_id == current_user.id, Message.author_deleted == False),
        and_(Message.receiver_id == current_user.id, Message.receiver_deleted == False)
    )).first_or_404()

    form = MessageReplyForm() if current_user.can(Permission.PARTICIPATE) else None

    if form:
        if form.send.data and form.validate_on_submit():
            receiver_id = msg.author_id if msg.author_id != current_user.id else msg.receiver_id
            new_message = Message(title=form.title.data, body=form.body.data, author_id=current_user.id,
                                  receiver_id=receiver_id)
            flash(lazy_gettext('Your message has been sent.'))
            db.session.add(new_message)
            return redirect(request.args.get('next') or url_for('main.messages'))
        elif form.delete.data:
            if msg.receiver_id == current_user.id:
                msg.receiver_deleted = True
            if msg.author_id == current_user.id:
                msg.author_deleted = True
            flash(lazy_gettext('The message has been deleted.'))
            db.session.add(msg)
            return redirect(request.args.get('next') or url_for('main.messages'))
        elif form.close.data:
            return redirect(request.args.get('next') or url_for('main.messages'))

    if msg.receiver_id == current_user.id and msg.unread:
        msg.unread = False
        db.session.add(msg)

    if form:
        form.title.data = msg.title

    return render_template('message.html', message=msg, form=form)


@main.route('/send_message/<username>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.PARTICIPATE)
def send_message(username):
    receiver = User.query.filter_by(username_normalized=username.lower()).first_or_404()
    if receiver.id == current_user.id:
        abort(400)

    form = MessageSendForm()

    if form.send.data and form.validate_on_submit():
        new_message = Message(title=form.title.data, body=form.body.data, author_id=current_user.id,
                              receiver_id=receiver.id)
        flash(lazy_gettext('Your message has been sent.'))
        db.session.add(new_message)
        return redirect(request.args.get('next') or url_for('main.messages'))
    elif form.cancel.data:
        flash(lazy_gettext('The message was cancelled.'))
        return redirect(request.args.get('next') or url_for('main.messages'))

    return render_template('send_message.html', form=form, receiver=receiver)


@main.route('/community', methods=['GET', 'POST'])
@login_required
def community():
    form = SearchForm()

    if form.validate_on_submit():
        page = 1
        search_str = '%{}%'.format(form.text.data.lower())
        pagination = User.query.order_by(User.id.asc()).filter(
            or_(User.username_normalized.like(search_str), func.lower(User.name).like(search_str))).paginate(
            page, per_page=current_app.config['USERS_PER_PAGE'], error_out=False)
    else:
        page = request.args.get('page', 1, type=int)
        pagination = User.query.order_by(User.id.asc()).paginate(
            page, per_page=current_app.config['USERS_PER_PAGE'], error_out=False)

    return render_template('community.html', form=form, users=pagination.items, pagination=pagination)


@main.route('/set_locale')
def set_locale():
    locale = request.args.get('locale', current_app.config['BABEL_DEFAULT_LOCALE'], type=str)
    session['locale'] = locale
    return redirect(request.args.get('next') or url_for('main.index'))


@babel.localeselector
def get_locale():
    locale = session.get('locale', None)
    if locale:
        return locale
    return request.accept_languages.best_match(current_app.config['SUPPORTED_LANGUAGES'].keys())
