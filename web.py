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
    return render_template('index.html', events=events['data'], pagination=pag, meta_title=app.config['BLOG_TITLE'])


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


@app.route('/<permalink>')
def single_event(permalink):
    event = eventClass.get_event_by_permalink(permalink)
    if not event['data']:
        abort(404)
    return render_template('single_event.html', event=event['data'], meta_title=app.config['BLOG_TITLE'] + '::' + event['data']['name'])


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
    skip = (page - 1) * int(app.config['PER_PAGE'])
    events = eventClass.get_events(int(app.config['PER_PAGE']), skip)
    count = eventClass.get_total_count()
    pag = pagination.Pagination(page, app.config['PER_PAGE'], count)

    #if not events['data']:
    #    abort(404)

    return render_template('events.html', events=events['data'], pagination=pag, meta_title='Events')


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

            participants = cgi.escape(request.form.get('event-participants'))
            participants_array = extract_tags(participants)

            event_data = {'name': event_name,
                          'summary': event_summary,
                          'description': event_description,
                          'start': request.form.get('event-start'),
                          'end': request.form.get('event-end'),
                          'venue': request.form.get('event-venue'),
                          'tags': tags_array,
                          'participants': participants_array,
                          'organizer': session['user']['username']}


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
        else:
            flash(response['error'], 'error')
    else:
        flash('Need to be at least one event..', 'error')

    return redirect(url_for('events'))

@app.route('/newtalk', methods=['GET', 'POST'])
@login_required()
def new_talk():
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

            participants = cgi.escape(request.form.get('talk-participants'))
            participants_array = extract_tags(participants)

            talk_data = {'name': talk_name,
                         'summary': talk_summary,
                         'description': talk_description,
                         'date': request.form.get('talk-date'),
                         'start': request.form.get('talk-start'),
                         'end': request.form.get('talk-end'),
                         'room': request.form.get('talk-room'),
                         'tags': tags_array,
                         'participants': participants_array,
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
                    else:
                        flash(response['error'], 'error')
                    return redirect(url_for('talks'))
                else:
                    response = talkClass.create_new_talk(talk)
                    #event_permalink = request.form.get('talk-event')

                    #response_add_talk_event = eventClass.add_new_talk(event_permalink, talk)

                    #if response['error'] or response_add_talk_event['error']:
                    if response['error']:
                        error = True
                        error_type = 'event'
                        flash(response['error'], 'error')
                    else:
                        flash('New talk created!', 'success')
    else:
        if session.get('talk-preview') and session['talk-preview']['action'] == 'edit':
            session.pop('talk-preview', None)
    return render_template('new_talk.html',
                           meta_title='New talk',
                           error=error,
                           error_type=error_type)

@app.route('/talk_preview')
@login_required()
def talk_preview():
    talk = session.get('talk-preview')
    return render_template('talk_preview.html', talk=talk, meta_title='Preview talk::' + talk['name'])

@app.route('/talk_edit?id=<id>')
@login_required()
def talk_edit(id):
    talk = talkClass.get_talk_by_id(id)
    if talk['error']:
        flash(talk['error'], 'error')
        return redirect(url_for('talks'))

    if session.get('talk-preview') and session['talk-preview']['action'] == 'add':
        session.pop('talk-preview', None)
    return render_template('edit_talk.html',
                           meta_title='Edit talk::' + talk['data']['name'],
                           talk=talk['data'],
                           error=False,
                           error_type=False)

@app.route('/talk_delete?id=<id>')
@login_required()
def talk_del(id):
    if talkClass.get_total_count() >= 1:
        response = talkClass.delete_talk(id)
        if response['data'] is True:
            flash('Talk removed!', 'success')
        else:
            flash(response['error'], 'error')
    else:
        flash('Need to be at least one talk..', 'error')

    return redirect(url_for('talks'))


@app.route('/talk/<permalink>')
def single_talk(permalink):
    talk = talkClass.get_talk_by_permalink(permalink)
    if not talk['data']:
        abort(404)
    return render_template('single_talk.html', talk=talk['data'], meta_title=app.config['BLOG_TITLE'] + '::' + talk['data']['name'])


@app.route('/tag/<tag>', defaults={'page': 1})
@app.route('/tag/<tag>/page-<int:page>')
def talks_by_tag(tag, page):
    skip = (page - 1) * int(app.config['PER_PAGE'])
    talks = talkClass.get_talks(int(app.config['PER_PAGE']), skip, tag=tag)
    count = talkClass.get_total_count(tag=tag)
    if not talks['data']:
        abort(404)
    pag = pagination.Pagination(page, app.config['PER_PAGE'], count)
    return render_template('index.html', talks=talks['data'], pagination=pag, meta_title='Talks by tag: ' + tag)


@app.route('/add_participant')
@login_required()
def add_participant():
    return render_template('add_participant.html', meta_title='Add participant')


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = False
    error_type = 'validate'
    if request.method == 'POST':
        username = request.form.get('login-username')
        password = request.form.get('login-password')
        if not username or not password:
            error = True
        else:
            user_data = userClass.login(username.lower().strip(), password)
            if user_data['error']:
                error = True
                error_type = 'login'
                flash(user_data['error'], 'error')
            else:
                userClass.start_session(user_data['data'])
                flash('You are logged in!', 'success')
                return redirect(url_for('events'))
    else:
        if session.get('user'):
            return redirect(url_for('events'))

    return render_template('login.html',
                           meta_title='Login',
                           error=error,
                           error_type=error_type)


@app.route('/logout')
def logout():
    if userClass.logout():
        flash('You are logged out!', 'success')
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required()
def dashboard():
    events_created = eventClass.get_total_count()
    return render_template('dashboard.html', event=events_created)


@app.route('/users')
@login_required()
def users_list():
    users = userClass.get_users()
    return render_template('users.html', users=users['data'], meta_title='Users')


@app.route('/add_user')
@login_required()
def add_user():
    gravatar_url = userClass.get_gravatar_link()
    role_list = ['admin', 'organizer', 'assistant']
    return render_template('add_user.html', role_list=role_list, gravatar_url=gravatar_url, meta_title='Add user')


@app.route('/edit_user?id=<id>')
@login_required()
def edit_user(id):
    user = userClass.get_user(id)
    role_list = ['admin', 'organizer', 'assistant']
    return render_template('edit_user.html', user=user['data'], role_list=role_list, meta_title='Edit user')


@app.route('/view_user?id=<id>')
@login_required()
def view_user(id):
    user = userClass.get_user(id)
    return render_template('view_user.html', user=user['data'], meta_title='View user')



@app.route('/delete_user?id=<id>')
@login_required()
def delete_user(id):
    if id != session['user']['username']:
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
        '_id': request.form.get('user-id', None).lower().strip(),
        'name': request.form.get('user-name', None),
        'email': request.form.get('user-email', None),
        'old_pass': request.form.get('user-old-password', None),
        'new_pass': request.form.get('user-new-password', None),
        'new_pass_again': request.form.get('user-new-password-again', None),
        'role' : request.form.get('user-role', None),
        'active': request.form.get('user-active', None),
        'update': request.form.get('user-update', False)
    }
    if not post_data['email'] or not post_data['name'] or not post_data['_id']:
        flash('Name, Username and Email are required..', 'error')
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
    return redirect(url_for('edit_user', id=post_data['_id']))

@app.route('/save_participant', methods=['POST'])
@login_required()
def save_participant():
    event_permalink = session.get('participant-event', None)
    event = eventClass.get_event_by_permalink(event_permalink)
    #event_id = event['data']['id']

    post_data = {
        '_id': request.form.get('user-id', None).lower().strip(),
        'name': request.form.get('user-name', None),
        'email': request.form.get('user-email', None),
        'active': request.form.get('user-active', None)
    }
    if not post_data['email'] or not post_data['name'] or not post_data['_id']:
        flash('Name, Username and Email are required..', 'error')
        return redirect(url_for('add_participant'))
    else:
        user = userClass.save_participant(post_data)
        #if user['error']:
         #   flash(user['error'], 'error')
          #  return redirect(url_for('add_participant'))
        #else:
        message = 'Participant added!'
        flash(message, 'success')
    #return redirect(url_for('edit_event', id=event_id))
    return redirect(url_for('events'))


@app.route('/recent_feed')
def recent_feed():
    feed = AtomFeed(app.config['BLOG_TITLE'] + '::Recent Events',
                    feed_url=request.url, url=request.url_root)
    events = eventClass.get_events(int(app.config['PER_PAGE']), 0)
    for event in events['data']:
        event_entry = event['summary'] if event['summary'] else event['description']
        feed.add(event['name'], md(event_entry),
                 content_type='html',
                 organizer=event['organizer'],
                 url=make_external(
                     url_for('single_event', permalink=event['permalink'])))
    return feed.get_response()


@app.route('/settings', methods=['GET', 'POST'])
@login_required()
def blog_settings():
    error = None
    error_type = 'validate'
    if request.method == 'POST':
        blog_data = {
            'title': request.form.get('blog-title', None),
            'description': request.form.get('blog-description', None),
            'per_page': request.form.get('blog-perpage', None),
            'text_search': request.form.get('blog-text-search', None)
        }
        blog_data['text_search'] = 1 if blog_data['text_search'] else 0
        for key, value in blog_data.items():
            if not value and key != 'text_search' and key != 'description':
                error = True
                break
        if not error:
            update_result = settingsClass.update_settings(blog_data)
            if update_result['error']:
                flash(update_result['error'], 'error')
            else:
                flash('Settings updated!', 'success')
                return redirect(url_for('blog_settings'))

    return render_template('settings.html',
                           default_settings=app.config,
                           meta_title='Settings',
                           error=error,
                           error_type=error_type)


@app.route('/install', methods=['GET', 'POST'])
def install():
    if session.get('installed', None):
        return redirect(url_for('index'))

    error = False
    error_type = 'validate'
    if request.method == 'POST':
        user_error = False
        blog_error = False

        user_data = {
            '_id': request.form.get('user-id', None).lower().strip(),
            'name': request.form.get('user-name', None),
            'email': request.form.get('user-email', None),
            'new_pass': request.form.get('user-new-password', None),
            'new_pass_again': request.form.get('user-new-password-again', None),
            'role': 'admin',
            'active': '1',
            'update': False
        }
        blog_data = {
            'title': request.form.get('blog-title', None),
            'description': request.form.get('blog-description', None),
            'per_page': request.form.get('blog-perpage', None),
            'text_search': request.form.get('blog-text-search', None)
        }
        blog_data['text_search'] = 1 if blog_data['text_search'] else 0

        for key, value in user_data.items():
            if not value and key != 'update':
                user_error = True
                break
        for key, value in blog_data.items():
            if not value and key != 'text_search' and key != 'description':
                blog_error = True
                break

        if user_error or blog_error:
            error = True
        else:
            install_result = settingsClass.install(blog_data, user_data)
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
    app.jinja_env.globals['meta_description'] = app.config['BLOG_DESCRIPTION']
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
app.jinja_env.globals['meta_description'] = app.config['BLOG_DESCRIPTION']
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