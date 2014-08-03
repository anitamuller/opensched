import cgi
import os
from flask import Flask, render_template, abort, url_for, request, flash, session, redirect
from flaskext.markdown import Markdown
from mdx_github_gists import GitHubGistExtension
from mdx_strike import StrikeExtension
from mdx_quote import QuoteExtension
from werkzeug.contrib.atom import AtomFeed
import event
import talk
import user
import pagination
import settings
from helper_functions import *


app = Flask(__name__)
md = Markdown(app)
md.register_extension(GitHubGistExtension)
md.register_extension(StrikeExtension)
md.register_extension(QuoteExtension)
app.config.from_object('config')


@app.route('/', defaults={'page': 1})
@app.route('/page-<int:page>')
def index(page):
    skip = (page - 1) * int(app.config['PER_PAGE'])
    events = eventClass.get_events(int(app.config['PER_PAGE']), skip)
    count = eventClass.get_total_count()
    pag = pagination.Pagination(page, app.config['PER_PAGE'], count)
    return render_template('index.html', events=events['data'], pagination=pag, meta_title=app.config['SITE_TITLE'])


@app.route('/tag/<tag>', defaults={'page': 1})
@app.route('/tag/<tag>/page-<int:page>')
def events_by_tag(tag, page):
    skip = (page - 1) * int(app.config['PER_PAGE'])
    events = eventClass.get_events(int(app.config['PER_PAGE']), skip, tag=tag)
    count = eventClass.get_total_count(tag=tag)
    if not events['data']:
        abort(404)
    pag = pagination.Pagination(page, app.config['PER_PAGE'], count)
    return render_template('index.html', events=events['data'], pagination=pag, meta_title='Events by tag: ' + tag)

@app.route('/<event_permalink>/talks/tag/<tag>', defaults={'page': 1})
@app.route('/<event_permalink>/talks/tag/<tag>/page-<int:page>')
def talks_by_tag(event_permalink, tag, page):
    skip = (page - 1) * int(app.config['PER_PAGE'])
    talks = talkClass.get_talks(int(app.config['PER_PAGE']), skip, event_permalink=event_permalink, tag=tag)
    count = talkClass.get_total_count(tag=tag)
    if not talks['data']:
        abort(404)
    pag = pagination.Pagination(page, app.config['PER_PAGE'], count)
    # Tenemos que hacer un indice para las charlas
    # ahora al hacer click funciona pero no se ve toda
    # la informacion porque usa events en vez de talks para acceder
    return render_template('index.html', events=talks['data'], pagination=pag, meta_title='Talks by tag: ' + tag)


@app.route('/<permalink>')
def single_event(permalink):
    event = eventClass.get_event_by_permalink(permalink)
    if not event['data']:
        abort(404)
    talks_list = event['data']['talks']
    talks = []

    for talk in talks_list:
        talk_event = talkClass.get_talk_by_permalink(talk)
        talks.append(talk_event['data'])
        tags = talkClass.get_tags(permalink)

    return render_template('single_event.html', event=event['data'], talks=talks, tags=tags['data'], meta_title=app.config['SITE_TITLE'] + '::' + event['data']['name'])


@app.route('/q/<query>', defaults={'page': 1})
@app.route('/q/<query>/page-<int:page>')
def search_results(page, query):
    skip = (page - 1) * int(app.config['PER_PAGE'])
    if query:
        events = eventClass.get_events(
            int(app.config['PER_PAGE']), skip, search=query)
    else:
        events = []
        events['data'] = []
    count = eventClass.get_total_count(search=query)
    pag = pagination.Pagination(page, app.config['PER_PAGE'], count)
    return render_template('index.html', events=events['data'], pagination=pag, meta_title='Search results')


@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method != 'POST':
        return redirect(url_for('index'))

    query = request.form.get('query', None)
    if query:
        return redirect(url_for('search_results', query=query))
    else:
        return redirect(url_for('index'))


@app.route('/event_preview')
@login_required()
def event_preview():
    event = session.get('event-preview')
    return render_template('event_preview.html', event=event, meta_title='Preview event::' + event['name'])


@app.route('/events_list', defaults={'page': 1})
@app.route('/events_list/page-<int:page>')
@login_required()
def events(page):
    session.pop('event-preview', None)
    organizer = None if session['user']['role'] == 'Admin' else session['user']['email']
    skip = (page - 1) * int(app.config['PER_PAGE'])
    events = eventClass.get_events(int(app.config['PER_PAGE']), skip, organizer)
    count = eventClass.get_total_count()
    pag = pagination.Pagination(page, app.config['PER_PAGE'], count)

    return render_template('events.html', events=events['data'], pagination=pag, meta_title='Events')


@app.route('/result')
@login_required()
def events_by_role():
    user_id = session['user']['email']
    result_attendee = []
    result_speaker = []

    events_attendee, events_organizer = eventClass.events_by_role(user_id)

    list_events_attendee = []

    for event in events_attendee:
        list_talks_attendee = []
        list_talks_speaker = []
        list_events_attendee.append(str(event['permalink']))
        list_talks = event['talks']

        for talk in list_talks:
            aux_talk = talkClass.get_talk_by_permalink(talk)
            if user_id in aux_talk['data']['attendees']:
                list_talks_attendee.append(str(aux_talk['data']['permalink']))
            if user_id in aux_talk['data']['speaker']:
                list_talks_speaker.append(str(aux_talk['data']['permalink']))

        result_attendee.append({str(event['permalink']): list_talks_attendee})
        result_speaker.append({str(event['permalink']): list_talks_speaker})



    return render_template('result.html', result_attendee=result_attendee, result_speaker=result_speaker, result_organizer= events_organizer, meta_title='Events and talks as attendee')

@app.route('/newevent', methods=['GET', 'POST'])
@login_required()
def new_event():
    error = False
    error_type = 'validate'
    if request.method == 'POST':
        event_name = request.form.get('event-name').strip()
        event_summary = request.form.get('event-summary')
        event_description = request.form.get('event-description')

        if not event_name or not event_summary or not event_description:
            error = True
        else:
            tags = cgi.escape(request.form.get('event-tags'))
            tags_array = extract_tags(tags)

            event_data = {'name': event_name,
                          'summary': event_summary,
                          'description': event_description,
                          'start': request.form.get('event-start'),
                          'end': request.form.get('event-end'),
                          'venue': request.form.get('event-venue'),
                          'tags': tags_array,
                          'organizer': session['user']['email'],
                          'talks': [],
                          'attendees': []}

            event = eventClass.validate_event_data(event_data)
            event_with_permalink= eventClass.generate_permalink(event)

            if request.form.get('event-preview') == '1':
                session['event-preview'] = event_with_permalink
                session[
                    'event-preview']['action'] = 'edit' if request.form.get('event-id') else 'add'
                if request.form.get('event-id'):
                    session[
                        'event-preview']['redirect'] = url_for('event_edit', id=request.form.get('event-id'))
                else:
                    session['event-preview']['redirect'] = url_for('new_event')
                return redirect(url_for('event_preview'))
            else:
                session.pop('event-preview', None)

                if request.form.get('event-id'):
                    response = eventClass.edit_event(
                        request.form['event-id'], event)
                    if not response['error']:
                        flash('Event updated!', 'success')
                    else:
                        flash(response['error'], 'error')
                    return redirect(url_for('events'))
                else:
                    response = eventClass.create_new_event(event)
                    if response['error']:
                        error = True
                        error_type = 'event'
                        flash(response['error'], 'error')
                    else:
                        flash('New event created!', 'success')
                        return redirect(url_for('events'))
    else:
        if session.get('event-preview') and session['event-preview']['action'] == 'edit':
            session.pop('event-preview', None)
    return render_template('new_event.html',
                           meta_title='New event',
                           error=error,
                           error_type=error_type)


@app.route('/event_edit?id=<id>')
@login_required()
def event_edit(id):
    event = eventClass.get_event_by_id(id)
    session['event-permalink'] = event['data']['permalink']


    if event['error']:
        flash(event['error'], 'error')
        return redirect(url_for('events'))

    if session.get('event-preview') and session['event-preview']['action'] == 'add':
        session.pop('event-preview', None)
    return render_template('edit_event.html',
                           meta_title='Edit event::' + event['data']['name'],
                           event=event['data'],
                           error=False,
                           error_type=False)


@app.route('/event_delete?id=<id>')
@login_required()
def event_del(id):
    if eventClass.get_total_count() >= 1:
        response = eventClass.delete_event(id)
        if response['data'] is True:
            flash('Event removed!', 'success')
            return redirect(url_for('events'))
        else:
            flash(response['error'], 'error')
    else:
        flash('Need to be at least one event..', 'error')


@app.route('/<event_permalink>/newtalk', methods=['GET', 'POST'])
@login_required()
def new_talk(event_permalink):
    error = False
    error_type = 'validate'
    if request.method == 'POST':
        talk_name = request.form.get('talk-name').strip()
        talk_summary = request.form.get('talk-summary')
        talk_description = request.form.get('talk-description')

        if not talk_name or not talk_summary or not talk_description:
            error = True
        else:
            tags = cgi.escape(request.form.get('talk-tags'))
            tags_array = extract_tags(tags)

            talk_data = {'name': talk_name,
                         'event': event_permalink,
                         'summary': talk_summary,
                         'description': talk_description,
                         'date': request.form.get('talk-date'),
                         'start': request.form.get('talk-start'),
                         'end': request.form.get('talk-end'),
                         'room': request.form.get('talk-room'),
                         'tags': tags_array,
                         'attendees': [],
                         'speaker': request.form.get('talk-speaker')}

            talk = talkClass.validate_talk_data(talk_data)
            talk_with_permalink = talkClass.generate_permalink(talk)

            if request.form.get('talk-preview') == '1':
                session['talk-preview'] = talk_with_permalink
                session[
                    'talk-preview']['action'] = 'edit' if request.form.get('talk-id') else 'add'
                if request.form.get('talk-id'):
                    session[
                        'talk-preview']['redirect'] = url_for('talk_edit', id=request.form.get('talk-id'))
                else:
                    session['talk-preview']['redirect'] = url_for('new_talk')
                return redirect(url_for('talk_preview'))
            else:
                session.pop('talk-preview', None)

                if request.form.get('talk-id'):
                    response = talkClass.edit_talk(
                        request.form['talk-id'], talk)
                    if not response['error']:
                        flash('Talk updated!', 'success')
                        return redirect(url_for('talks_by_event', event_permalink=event_permalink))
                    else:
                        flash(response['error'], 'error')
                else:
                    response = talkClass.create_new_talk(talk)
                    eventClass.add_new_talk(event_permalink, talk)

                    speaker_mail = request.form.get('talk-speaker')
                    talk_permalink = talk_with_permalink['permalink']

                    userClass.save_speaker(speaker_mail, event_permalink, talk_permalink)

                    if response['error']:
                        error = True
                        error_type = 'event'
                        flash(response['error'], 'error')
                    else:
                        flash('New talk created!', 'success')
                        return redirect(url_for('talks_by_event', event_permalink=event_permalink))
    else:
        if session.get('talk-preview') and session['talk-preview']['action'] == 'edit':
            session.pop('talk-preview', None)

    speakers = eventClass.get_attendance_event(event_permalink)

    return render_template('new_talk.html',
                           event_permalink=event_permalink,
                           speakers_list=speakers,
                           meta_title='New talk',
                           error=error,
                           error_type=error_type)


@app.route('/<event_permalink>/talk_preview')
@login_required()
def talk_preview(event_permalink):
    talk = session.get('talk-preview')
    return render_template('talk_preview.html', event_permalink=event_permalink,
                           talk=talk, meta_title='Preview talk::' + talk['name'])


@app.route('/<event_permalink>/talk_edit?id=<id>')
@login_required()
def talk_edit(event_permalink, id):
    talk = talkClass.get_talk_by_id(id)
    session['talk-permalink'] = talk['data']['permalink']

    if talk['error']:
        flash(talk['error'], 'error')
        return redirect(url_for('talks', event_permalink=event_permalink))

    if session.get('talk-preview') and session['talk-preview']['action'] == 'add':
        session.pop('talk-preview', None)

    speakers = userClass.get_users_by_role("speaker")

    return render_template('edit_talk.html',
                           event_permalink=event_permalink,
                           meta_title='Edit talk::' + talk['data']['name'],
                           speakers_list=speakers,
                           talk=talk['data'],
                           error=False,
                           error_type=False)


@app.route('/<event_permalink>/talk_delete?id=<id>')
@login_required()
def talk_del(event_permalink, id):
    if talkClass.get_total_count() >= 1:
        talk = talkClass.get_talk_by_id(id)
        talk_permalink = talk['data']['permalink']
        response = talkClass.delete_talk(id)
        event = eventClass.get_event_by_permalink(event_permalink)
        event_talks = event['data']['talks']
        event_talks.remove(talk_permalink)
        eventClass.modify_talks_event(event_permalink, event_talks)

        if response['data'] is True:
            flash('Talk removed!', 'success')
        else:
            flash(response['error'], 'error')
    else:
        flash('Need to be at least one talk..', 'error')

    return redirect(url_for('talks_by_event', event_permalink=event_permalink))


@app.route('/<event_permalink>/<talk_permalink>')
def single_talk(event_permalink, talk_permalink):
    talk = talkClass.get_talk_by_permalink(talk_permalink)
    return render_template('single_talk.html', event_permalink=event_permalink, talk=talk['data'],
                           meta_title='Talk: ' + '::' + talk['data']['name'])

@app.route('/<event_permalink>/talks')
def talks_by_event(event_permalink):
    event = eventClass.get_event_by_permalink(event_permalink)
    event_name = event['data']['name']
    talks_permalinks = eventClass.get_talks_by_event(event_permalink)

    list_talks = []

    for talk in talks_permalinks:
        talk_complete = talkClass.get_talk_by_permalink(str(talk))
        talk_complete['data']['attendance'] = len(talk_complete['data']['attendees'])
        list_talks.append(talk_complete['data'])

    return render_template('talks.html', event_permalink=event_permalink, talks=list_talks,
                           meta_title='Talks by event: ' + event_name)

@app.route('/<event_permalink>/my_schedule')
def my_schedule(event_permalink):
    event = eventClass.get_event_by_permalink(event_permalink)
    event_name = event['data']['name']

    user_email = session['user']['email']
    user = userClass.get_user(user_email)
    talks = user['data']['attendee_at']

    if talks.has_key(event_permalink):
        talks_attendee = talks[event_permalink]
    else:
        talks_attendee = []

    list_talks = []

    for talk in talks_attendee:
        talk_complete = talkClass.get_talk_by_permalink(str(talk))
        list_talks.append(talk_complete['data'])

    return render_template('my_schedule.html', event_permalink=event_permalink, talks=list_talks,
                           meta_title='Talks attendee at of event: ' + event_name)



@app.route('/<event_permalink>/add_attendee_event')
@login_required()
def add_attendee_event(event_permalink):
    return render_template('add_attendee_event.html', event_permalink=event_permalink,
                           meta_title='Invite attendee to event')


@app.route('/<event_permalink>/<talk_permalink>/add_attendee_talk')
@login_required()
def add_attendee_talk(event_permalink, talk_permalink):
    return render_template('add_attendee_talk.html', event_permalink=event_permalink,
                           talk_permalink=talk_permalink, meta_title='Invite attendee to talk')


@app.route('/<event_permalink>/attendance')
def event_attendance(event_permalink):
    event = eventClass.get_event_by_permalink(event_permalink)
    event_name = event['data']['name']
    attendance = event['data']['attendees']
    list_attendance = []

    for attendee in attendance:
        user = userClass.get_user_by_email(str(attendee))
        list_attendance.append(user)

    return render_template('event_attendance.html', event_permalink=event_permalink, users=list_attendance,
                           event_name=event_name, meta_title='Event attendance: ' + event_name)


@app.route('/<event_permalink>/<talk_permalink>/attendance')
def talk_attendance(event_permalink, talk_permalink):
    talk = talkClass.get_talk_by_permalink(talk_permalink)
    talk_name = talk['data']['name']
    attendance = talk['data']['attendees']
    list_attendance = []

    for attendee in attendance:
        user = userClass.get_user_by_email(str(attendee))
        list_attendance.append(user)

    return render_template('talk_attendance.html', talk_permalink=talk_permalink, event_permalink= event_permalink,
                           users=list_attendance,
                           talk_name=talk_name, meta_title='Talk attendance: ' + talk_name)


@app.route('/register')
def register():
    gravatar_url = userClass.get_gravatar_link()
    return render_template('register.html', gravatar_url=gravatar_url, meta_title='Register')


@app.route('/add_user')
def add_user():
    gravatar_url = userClass.get_gravatar_link()
    role_list = ['Admin', 'User']
    return render_template('add_user.html', gravatar_url=gravatar_url, role_list=role_list,  meta_title='Register new User')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = False
    error_type = 'validate'
    if request.method == 'POST':
        email = request.form.get('login-email')
        password = request.form.get('login-password')
        if not email or not password:
            error = True
        else:
            user_data = userClass.login(email.lower().strip(), password)
            if user_data['error']:
                error = True
                error_type = 'login'
                flash(user_data['error'], 'error')
            else:
                userClass.start_session(user_data['data'])
                flash('You are logged in!', 'success')
                role = user_data['data'].get('role')
                if role == 'user':
                    return redirect(url_for('dashboard_user'))
                else:
                    return redirect(url_for('dashboard_admin'))
    else:
        if session.get('user'):
            role = session.get('user').get('role')
            if role == 'user':
                return redirect(url_for('dashboard_user'))
            else:
                return redirect(url_for('dashboard_admin'))

    return render_template('login.html',
                           meta_title='Login',
                           error=error,
                           error_type=error_type)


@app.route('/logout')
def logout():
    if userClass.logout():
        flash('You are logged out!', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard_admin')
@login_required()
@privileged_user()
def dashboard_admin():
    events_created = eventClass.get_total_count()
    talks_created = talkClass.get_total_count()
    attendees_number = len(userClass.get_users_by_role('User'))
    organizers_number = len(eventClass.get_organizers())

    user_email = session['user']['email']
    user = userClass.get_user(user_email)

    events_organizer = eventClass.events_organized_by(user_email)

    attendee_at = user['data']['attendee_at']
    list_name_events_attendee = attendee_at.keys()
    list_events_attendee = []

    for event_name in list_name_events_attendee:
        event_attendee = eventClass.get_event_by_permalink(event_name)
        list_events_attendee.append(event_attendee['data'])

    speaker_at = user['data']['speaker_at']
    list_name_events_speaker = speaker_at.keys()
    list_events_speaker = []

    for event_name in list_name_events_speaker:
        event_speaker = eventClass.get_event_by_permalink(event_name)
        list_events_speaker.append(event_speaker['data'])

    return render_template('dashboard_admin.html',
                           events_organized_by=events_organizer,
                           events_attendee=list_events_attendee,
                           events_speaker=list_events_speaker,
                           events_created=events_created,
                           talks_created=talks_created,
                           attendees_number=attendees_number,
                           organizers_number=organizers_number,
                           meta_title='Admin dashboard')


@app.route('/dashboard_user')
@login_required()
def dashboard_user():
    user_email = session['user']['email']
    user = userClass.get_user(user_email)

    events_organizer = eventClass.events_organized_by(user_email)

    attendee_at = user['data']['attendee_at']
    list_name_events_attendee = attendee_at.keys()
    list_events_attendee = []

    for event_name in list_name_events_attendee:
        event_attendee = eventClass.get_event_by_permalink(event_name)
        list_events_attendee.append(event_attendee['data'])

    speaker_at = user['data']['speaker_at']
    list_name_events_speaker = speaker_at.keys()
    list_events_speaker = []

    for event_name in list_name_events_speaker:
        event_speaker = eventClass.get_event_by_permalink(event_name)
        list_events_speaker.append(event_speaker['data'])

    return render_template('dashboard_user.html',
                           events_organized_by=events_organizer,
                           events_attendee=list_events_attendee,
                           events_speaker=list_events_speaker,
                           meta_title='Users dashboard')


@app.route('/users')
@login_required()
@privileged_user()
def users_list():
    users = userClass.get_users()
    return render_template('users.html', users=users['data'], meta_title='Users')


@app.route('/edit_user?id=<id>')
@login_required()
@privileged_user()
def edit_user(id):
    user = userClass.get_user(id)
    role_list = ['Admin', 'User']
    return render_template('edit_user.html', user=user['data'], role_list=role_list, meta_title='Edit user')


@app.route('/view_user?id=<id>')
@login_required()
def view_user(id):
    user = userClass.get_user(id)
    return render_template('view_user.html', user=user['data'], meta_title='View user')


@app.route('/delete_user?id=<id>')
@login_required()
@privileged_user()
def delete_user(id):
    if id != session['user']['email']:
        user = userClass.delete_user(id)
        if user['error']:
            flash(user['error'], 'error')
        else:
            flash('User deleted!', 'success')
    return redirect(url_for('users_list'))


@app.route('/save_user', methods=['POST'])
@login_required()
def save_user():
    post_data = {
        '_id': request.form.get('user-id', None),
        'name': request.form.get('user-name', None),
        'old_pass': request.form.get('user-old-password', None),
        'new_pass': request.form.get('user-new-password', None),
        'new_pass_again': request.form.get('user-new-password-again', None),
        'role': request.form.get('user-role', None),
        'active': request.form.get('user-active', None),
        'update': request.form.get('user-update', False)
    }

    if not post_data['name'] or not post_data['_id']:
        flash('Name and Email are required..', 'error')
        if post_data['update']:
                return redirect(url_for('edit_user', id=post_data['_id']))
        else:
            return redirect(url_for('add_user'))
    else:
        user = userClass.save_user(post_data)
        if user['error']:
            flash(user['error'], 'error')
            if post_data['update']:
                return redirect(url_for('edit_user', id=post_data['_id']))
            else:
                return redirect(url_for('add_user'))
        else:
            message = 'User updated!' if post_data['update'] else 'User added!'
            flash(message, 'success')

    if session['user']['role'] == 'User':
        return redirect(url_for('dashboard_user'))
    else:
        return redirect(url_for('users_list'))


@app.route('/register_user', methods=['POST'])
def register_user():

    post_data = {
        '_id': request.form.get('user-id', None),
        'name': request.form.get('user-name', None),
        'old_pass': request.form.get('user-old-password', None),
        'new_pass': request.form.get('user-new-password', None),
        'new_pass_again': request.form.get('user-new-password-again', None),
        'role': request.form.get('user-role', None),
        'active': request.form.get('user-active', None),
        'update': request.form.get('user-update', False)
    }

    if not post_data['_id'] or not post_data['name']:
        flash('Name and Email are required..', 'error')
        if post_data['update']:
                return redirect(url_for('edit_user', id=post_data['_id']))
        else:
            return redirect(url_for('register'))
    else:
        user = userClass.save_user(post_data)
        if user['error']:
            flash(user['error'], 'error')
            return redirect(url_for('register'))
        else:
            message = 'User updated!' if post_data['update'] else 'User added!'
            flash(message, 'success')
    return redirect(url_for('login'))



@app.route('/<event_permalink>/save_attendee', methods=['POST'])
@login_required()
def save_attendee_event(event_permalink):

    post_data = {
        '_id': request.form.get('user-id', None).lower().strip(),
        'role': request.form.get('user-role', None),
        'active': request.form.get('user-active', None)
    }
    if not post_data['_id']:
        flash('Email is required..', 'error')
        return redirect(url_for('add_attendee_event'))
    else:
        userClass.save_attendee(post_data, event_permalink)
        attendee_email = request.form.get('user-id', None)
        eventClass.add_new_attendee(event_permalink, attendee_email)

    return redirect(url_for('events'))


@app.route('/<event_permalink>/<talk_permalink>/save_attendee_talk', methods=['POST'])
@login_required()
def save_attendee_talk(event_permalink, talk_permalink):
    post_data = {
        '_id': request.form.get('user-id', None),
        'role': request.form.get('user-role', None),
        'active': request.form.get('user-active', None)
    }
    if not post_data['_id'] :
        flash('Email is required..', 'error')
        return redirect(url_for('add_attendee_talk'))
    else:
        userClass.save_attendee(post_data, event_permalink, talk_permalink)
        attendee_email = request.form.get('user-id', None)
        eventClass.add_new_attendee(event_permalink, attendee_email)
        talkClass.add_new_attendee(talk_permalink, attendee_email)

    return redirect(url_for('talks_by_event', event_permalink=event_permalink))

@app.route('/<event_permalink>/<talk_permalink>/new_schedule_talk')
@login_required()
def new_schedule_talk(event_permalink, talk_permalink):
    attendee_email = session['user']['email']
    attendee_data = userClass.get_user(attendee_email)
    attendee = attendee_data['data']

    userClass.save_attendee(attendee, event_permalink, talk_permalink)
    eventClass.add_new_attendee(event_permalink, attendee_email)
    talkClass.add_new_attendee(talk_permalink, attendee_email)

    return redirect(url_for('single_talk', event_permalink=event_permalink, talk_permalink=talk_permalink))


@app.route('/settings', methods=['GET', 'POST'])
@login_required()
def configure_settings():
    user_email = session['user']['email']
    user = userClass.get_user(user_email)
    role_list = ['Admin', 'User']
    error = None
    error_type = 'validate'
    if request.method == 'POST':
        site_data = {
            'title': request.form.get('site-title', None),
            'description': request.form.get('site-description', None),
            'per_page': request.form.get('site-perpage', None),
            'text_search': request.form.get('site-text-search', None)
        }
        site_data['text_search'] = 1 if site_data['text_search'] else 0
        for key, value in site_data.items():
            if not value and key != 'text_search' and key != 'description':
                error = True
                break
        if not error:
            update_result = settingsClass.update_settings(site_data)
            if update_result['error']:
                flash(update_result['error'], 'error')
            else:
                flash('Settings updated!', 'success')
                return redirect(url_for('configure_settings'))

    return render_template('settings.html',
                           default_settings=app.config,
                           meta_title='Settings',
                           error=error,
                           error_type=error_type,
                           user=user['data'], role_list=role_list)


@app.route('/install', methods=['GET', 'POST'])
def install():
    if session.get('installed', None):
        return redirect(url_for('index'))

    error = False
    error_type = 'validate'

    if request.method == 'POST':
        user_error = False
        site_error = False

        user_data = {
            '_id': request.form.get('user-email', None),
            'name': request.form.get('user-name', None),
            'role': 'Admin',
            'active': 1,
            'new_pass': request.form.get('user-new-password', None),
            'new_pass_again': request.form.get('user-new-password-again', None),
            'update': False
        }

        site_data = {
            'title': request.form.get('site-title', None),
            'description': request.form.get('site-description', None)
        }

        for key, value in user_data.items():
            if not value and key != 'update':
                user_error = True
                break
        for key, value in site_data.items():
            if not value and key != 'description':
                site_error = True
                break

        if user_error or site_error:
            error = True
        else:
            install_result = settingsClass.install(site_data, user_data)
            if install_result['error']:
                for i in install_result['error']:
                    if i is not None:
                        flash(i, 'error')
            else:
                session['installed'] = True
                flash('Successfully installed!', 'success')
                user_login = userClass.login(
                    user_data['_id'], user_data['new_pass'])
                if user_login['error']:
                    flash(user_login['error'], 'error')
                else:
                    userClass.start_session(user_login['data'])
                    flash('You are logged in!', 'success')
                    return redirect(url_for('events'))
    else:
        if settingsClass.is_installed():
            return redirect(url_for('index'))

    return render_template('install.html',
                           default_settings=app.config,
                           error=error,
                           error_type=error_type,
                           meta_title='Install')


@app.before_request
def csrf_protect():
    if request.method == "POST":
        token = session.pop('_csrf_token', None)
        if not token or token != request.form.get('_csrf_token'):
            abort(400)


@app.before_request
def is_installed():
    app.config = settingsClass.get_config()
    app.jinja_env.globals['meta_description'] = app.config['SITE_DESCRIPTION']
    if not session.get('installed', None):
        if url_for('static', filename='') not in request.path and request.path != url_for('install'):
            if not settingsClass.is_installed():
                return redirect(url_for('install'))


@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html', meta_title='404'), 404


@app.template_filter('formatdate')
def format_datetime_filter(input_value, format_="%a, %d %b %Y"):
    return input_value.strftime(format_)


settingsClass = settings.Settings(app.config)
eventClass = event.Event(app.config)
talkClass = talk.Talk(app.config)
userClass = user.User(app.config)

app.jinja_env.globals['url_for_other_page'] = url_for_other_page
app.jinja_env.globals['csrf_token'] = generate_csrf_token
app.jinja_env.globals['meta_description'] = app.config['SITE_DESCRIPTION']
app.jinja_env.globals['recent_events'] = eventClass.get_events(10, 0)['data']
app.jinja_env.globals['tags'] = eventClass.get_tags()['data']

if not app.config['DEBUG']:
    import logging
    from logging import FileHandler
    file_handler = FileHandler(app.config['LOG_FILE'])
    file_handler.setLevel(logging.WARNING)
    app.logger.addHandler(file_handler)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)),
            debug=app.config['DEBUG'])



