from datetime import datetime, timedelta

from flask import render_template, redirect, url_for, abort, flash, request, current_app
from flask_login import login_required, current_user
from sqlalchemy import func, case, between, and_

from . import main
from .forms import (EditProfileForm, EditProfileAdminForm, TopicForm, TopicGroupForm, TopicEditForm,
                    TopicWithPollForm, TopicWithPollEditForm, CommentForm, CommentEditForm)
from .. import db
from ..decorators import admin_required, permission_required
from ..models import Permission, Role, User, Topic, TopicGroup, Comment, PollAnswer, Message


# TODO: Make common template for Up button?


def _topic_group(topic_group_id):
    t_group = TopicGroup.query.get_or_404(topic_group_id)
    t_groups = TopicGroup.query.with_entities(
        TopicGroup, func.sum(case([(Topic.deleted == False, 1)], else_=0))).outerjoin(
        Topic, TopicGroup.id == Topic.group_id).filter(
        TopicGroup.group_id == t_group.id).group_by(
        TopicGroup.id).order_by(TopicGroup.priority, TopicGroup.created_at.desc()).all()

    page = request.args.get('page', 1, type=int)
    pagination = Topic.query.with_entities(
        Topic, User, func.sum(case([(Comment.deleted == False, 1)], else_=0))).join(
        User, Topic.author_id == User.id).outerjoin(
        Comment, Topic.id == Comment.topic_id).filter(
        and_(Topic.group_id == t_group.id, Topic.deleted == False)).group_by(Topic.id).order_by(
        Topic.created_at.desc()).paginate(page, per_page=current_app.config['TOPICS_PER_PAGE'], error_out=False)

    return t_group, t_groups, pagination


@main.route('/')
def index():
    t_group, t_groups, pagination = _topic_group(current_app.config['ROOT_TOPIC_GROUP'])
    return render_template('index.html', topic_group=t_group, topic_groups=t_groups, topics=pagination.items,
                           pagination=pagination)


# TODO: Check POST for anonymous
@main.route('/topic/<int:topic_id>', methods=['GET', 'POST'])
def topic(topic_id):
    tpc = Topic.query.filter_by(id=topic_id, deleted=False).first_or_404()

    if current_user.can(Permission.PARTICIPATE):
        form = CommentForm(current_user)
    else:
        form = None

    if form and form.validate_on_submit():
        tpc.add_comment(current_user, form.body.data)
        flash('Your message has been published.')
        return redirect(url_for('main.topic', topic_id=topic_id, page=-1))

    page = request.args.get('page', 1, type=int)
    if page == -1:
        page = (tpc.comments_count - 1) // current_app.config['COMMENTS_PER_PAGE'] + 1

    pagination = Comment.query.with_entities(
        Comment, User).join(User, Comment.author_id == User.id).filter(
        and_(Comment.topic_id == tpc.id, Comment.deleted == False)).order_by(
        Comment.created_at.asc()).paginate(page, per_page=current_app.config['COMMENTS_PER_PAGE'], error_out=False)

    if tpc.poll and current_user.is_voted(tpc):
        is_voted = True
        poll_data = tpc.get_poll_results()
    else:
        is_voted = False
        poll_data = [(a.id, a.body) for a in tpc.poll_answers.filter_by(deleted=False).all()]

    return render_template('topic.html', topic=tpc, form=form, comments=pagination.items, pagination=pagination,
                           is_voted=is_voted, poll_data=poll_data)


@main.route('/create_topic/<int:topic_group_id>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.WRITE)
def create_topic(topic_group_id):
    t_group = TopicGroup.query.get_or_404(topic_group_id)
    if t_group.protected and not current_user.is_moderator():
        abort(403)

    with_poll = request.args.get('poll', 0, type=int)
    if with_poll:
        form = TopicWithPollForm()
    else:
        form = TopicForm()

    if form.submit.data and form.validate_on_submit():
        new_topic = Topic(title=form.title.data, body=form.body.data, group=t_group,
                          author=current_user._get_current_object())
        if with_poll:
            new_topic.poll = form.poll_question.data
        db.session.add(new_topic)
        db.session.commit()
        if with_poll:
            for answer in form.poll_answers.data.strip().splitlines():
                db.session.add(PollAnswer(topic_id=new_topic.id, body=answer))
        flash('Topic has been created.')
        return redirect(url_for('main.topic', topic_id=new_topic.id))

    elif not with_poll and form.add_poll.data:
        if form.title.data or form.body.data:
            if form.validate_on_submit():
                new_topic = Topic(title=form.title.data, body=form.body.data, group=t_group,
                                  author=current_user._get_current_object())
                db.session.add(new_topic)
                db.session.commit()
                flash('Topic has been saved. Fill data for a poll.')
                return redirect(url_for('main.edit_topic', topic_id=new_topic.id, poll=1))
        else:
            return redirect(url_for('main.create_topic', topic_group_id=topic_group_id, poll=1))

    elif form.cancel.data:
        flash('Topic creation has been cancelled.')
        return redirect(url_for('main.topic_group', topic_group_id=topic_group_id))

    return render_template('create_topic.html', form=form, topic_group=t_group)


@main.route('/edit/<int:topic_id>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.WRITE)
def edit_topic(topic_id):
    tpc = Topic.query.filter_by(id=topic_id, deleted=False).first_or_404()
    if current_user != tpc.author and not current_user.is_moderator():
        abort(403)

    with_poll = request.args.get('poll', 0, type=int) or tpc.poll
    if with_poll:
        form = TopicWithPollEditForm()
    else:
        form = TopicEditForm()

    if form.submit.data and form.validate_on_submit():
        tpc.title = form.title.data
        tpc.body = form.body.data
        if with_poll:
            tpc.poll = form.poll_question.data
            tpc.update_poll_answers(form.poll_answers.data.strip().splitlines())
        db.session.add(tpc)
        flash('The topic has been updated.')
        return redirect(url_for('main.topic', topic_id=tpc.id))

    elif not with_poll and form.add_poll.data and form.validate_on_submit():
        tpc.title = form.title.data
        tpc.body = form.body.data
        db.session.add(tpc)
        flash('Topic has been saved. Fill data for a poll.')
        return redirect(url_for('main.edit_topic', topic_id=tpc.id, poll=1))

    elif form.cancel.data:
        flash('Topic editing has been cancelled.')
        return redirect(url_for('main.topic', topic_id=tpc.id))

    elif form.delete.data:
        # TODO: Use bootstrap_modal for confirmation
        tpc.comments.update(dict(deleted=True))
        tpc.poll_answers.update(dict(deleted=True))
        tpc.poll_votes.update(dict(deleted=True))
        tpc.deleted = True
        db.session.add(tpc)
        flash('The topic has been deleted.')
        return redirect(request.args.get('next') or url_for('main.topic_group', topic_group_id=tpc.group_id))

    form.title.data = tpc.title
    form.body.data = tpc.body
    if tpc.poll:
        form.poll_question.data = tpc.poll
        form.poll_answers.data = '\n'.join([a.body for a in tpc.poll_answers.filter_by(deleted=False).all()])

    return render_template('edit_topic.html', form=form, topic=tpc)


@main.route('/topic_group/<int:topic_group_id>')
def topic_group(topic_group_id):
    if topic_group_id == current_app.config['ROOT_TOPIC_GROUP']:
        return redirect(url_for('main.index'))
    t_group, t_groups, pagination = _topic_group(topic_group_id)
    return render_template('topic_group.html', topic_group=t_group, topic_groups=t_groups, topics=pagination.items,
                           pagination=pagination)


@main.route('/create_topic_group/<int:topic_group_id>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MODERATE)
def create_topic_group(topic_group_id):
    t_group = TopicGroup.query.get_or_404(topic_group_id)

    form = TopicGroupForm()

    if form.submit.data and form.validate_on_submit():
        if form.priority.data not in current_app.config['TOPIC_GROUP_PRIORITY']:
            abort(404)
        new_t_group = TopicGroup(title=form.title.data, priority=form.priority.data, protected=form.protected.data,
                                 author=current_user._get_current_object(), group=t_group)
        db.session.add(new_t_group)
        db.session.commit()
        flash('Topic group has been created.')
        return redirect(url_for('main.topic_group', topic_group_id=new_t_group.id))

    elif form.cancel.data:
        flash('Topic group creation has been cancelled.')
        return redirect(url_for('main.topic_group', topic_group_id=topic_group_id))

    return render_template('create_topic_group.html', form=form, topic_group=t_group)


@main.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()

    page = request.args.get('page', 1, type=int)
    pagination = Topic.query.with_entities(
        Topic, User, func.sum(case([(Comment.deleted == False, 1)], else_=0))).join(
        User, Topic.author_id == User.id).outerjoin(
        Comment, Topic.id == Comment.topic_id).filter(
        and_(Topic.author_id == user.id, Topic.deleted == False)).group_by(Topic.id).order_by(
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


@main.route('/latest')
def latest():
    page_arg = request.args.get('page', 1, type=int)
    target_arg = request.args.get('target', 'topics', type=str)

    if target_arg == 'topics':
        pagination = Topic.query.with_entities(
            Topic, User, func.sum(case([(Comment.deleted == False, 1)], else_=0))).join(
            User, Topic.author_id == User.id).outerjoin(
            Comment, Topic.id == Comment.topic_id).filter(Topic.deleted == False).group_by(Topic.id).order_by(
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


@main.route('/delete_comment/<int:comment_id>')
@login_required
@permission_required(Permission.WRITE)
def delete_comment(comment_id):
    comment = Comment.query.filter_by(id=comment_id, deleted=False).first_or_404()
    if current_user != comment.author and not current_user.is_moderator():
        abort(403)
    comment.deleted = True
    db.session.add(comment)
    flash('The comment has been deleted.')
    return redirect(request.args.get('next') or url_for('main.topic', topic_id=comment.topic_id))


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
        db.session.add(comment)
        flash('The comment has been updated.')
        return redirect(request.args.get('next') or url_for('main.topic', topic_id=comment.topic_id))

    elif form.cancel.data:
        flash('Comment editing has been cancelled.')
        return redirect(request.args.get('next') or url_for('main.topic', topic_id=comment.topic_id))

    elif form.delete.data:
        comment.deleted = True
        db.session.add(comment)
        flash('The comment has been deleted.')
        return redirect(request.args.get('next') or url_for('main.topic', topic_id=comment.topic_id))

    form.body.data = comment.body

    return render_template('edit_comment.html', form=form, comment=comment)


@main.route('/vote/<int:answer_id>')
@login_required
@permission_required(Permission.PARTICIPATE)
def vote(answer_id):
    answer = PollAnswer.query.filter_by(id=answer_id, deleted=False).first_or_404()
    if current_user.is_voted(answer.topic):
        flash('You have already voted for this poll.')
    else:
        answer.topic.add_vote(current_user, answer)
        flash('Your vote has been taken.')
    return redirect(request.args.get('next') or url_for('main.topic', topic_id=answer.topic_id))


@main.route('/hot')
def hot():
    page_arg = request.args.get('page', 1, type=int)
    period_arg = request.args.get('period', 'day', type=str)

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
        ).group_by(Topic.id).order_by(Topic.interest.desc()).paginate(
        page_arg, per_page=current_app.config['TOPICS_PER_PAGE'], error_out=False)

    return render_template('hot.html', period=period_arg, topics=pagination.items, pagination=pagination)


@main.route('/messages')
@login_required
@permission_required(Permission.PARTICIPATE)
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
