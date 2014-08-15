import cgi
import os
from flask import Flask, render_template, abort, url_for, request, flash, session, redirect, Markup
import base64
import event
import talk
import user
import pagination
import settings
from helper_functions import *
from flask import jsonify


app = Flask(__name__)
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
    return render_template('index.html',
                           events=events['data'],
                           pagination=pag,
                           meta_title=app.config['SITE_TITLE'] + ' :: ' + 'Events by tag: ' + tag)


@app.route('/<event_permalink>/talks/tag/<tag>', defaults={'page': 1})
@app.route('/<event_permalink>/talks/tag/<tag>/page-<int:page>')
def talks_by_tag(event_permalink, tag, page):
    event_permalink = cgi.escape(event_permalink)
    skip = (page - 1) * int(app.config['PER_PAGE'])
    talks = talkClass.get_talks(int(app.config['PER_PAGE']), skip, event_permalink=event_permalink, tag=tag)
    count = talkClass.get_total_count(tag=tag)
    if not talks['data']:
        abort(404)
    pag = pagination.Pagination(page, app.config['PER_PAGE'], count)
    return render_template('index.html',
                           events=talks['data'],
                           pagination=pag,
                           meta_title=app.config['SITE_TITLE'] + ' :: ' + 'Talks by tag: ' + tag)


@app.route('/<event_permalink>')
def single_event(event_permalink):
    event_permalink = cgi.escape(event_permalink)

    if session.has_key('user'):
        if session.has_key('redirect_event'):
            session.pop('redirect_event')
    else:
        session['redirect_event'] = event_permalink

    event = eventClass.get_event_by_permalink(event_permalink)

    if not event['data']:
        abort(404)

    user_schedule, talks, attendees, speakers, tags = [], [], [], [], []

    if session.get('user'):
        user_email = session['user']['email']
        user = userClass.get_user(user_email)
        user_events = user['data']['attendee_at']
        #  Returns a list of talks for the queried event
        user_talks = user_events[event_permalink] if event_permalink in user_events else []

        for talk_permalink in user_talks:
            talk = talkClass.get_talk_by_permalink(str(talk_permalink))
            user_schedule.append(talk['data'])

        user_schedule.sort(key=lambda item:item['date'], reverse=False)

    talks_ = event['data']['talks']

    speakers_ = []

    for talk_permalink in talks_:
        talk = talkClass.get_talk_by_permalink(talk_permalink)
        if not talk['data']['speaker'] in speakers_:
            speakers_.append(str(talk['data']['speaker']))
        talks.append(talk['data'])

    talks.sort(key=lambda item: item['date'], reverse=False)

    tags = talkClass.get_tags(event_permalink)['data']

    attendees_ = eventClass.get_attendance_event(event_permalink)

    for attendee_name in attendees_:
        attendee = userClass.get_user(attendee_name)
        attendees.append(attendee['data'])

    for speaker_name in speakers_:
        speaker = userClass.get_user(speaker_name)
        speakers.append(speaker['data'])

    # Format data retrieved from the DB
    event['data']['summary'] = base64.b64decode(event['data']['summary']).decode('utf-8')
    event['data']['description'] = base64.b64decode(event['data']['description']).decode('utf-8')
    event['data']['start'] = date_to_string(event['data']['start'], 'short')
    event['data']['end'] = date_to_string(event['data']['end'], 'short')

    return render_template('single_event.html',
                           event=event['data'],
                           event_start=event['data']['start'],
                           event_end=event['data']['end'],
                           talks=talks,
                           tags=tags,
                           attendees=attendees,
                           speakers=speakers,
                           user_schedule=user_schedule,
                           meta_title=app.config['SITE_TITLE'] + ' :: ' + event['data']['name'])


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
    return render_template('index.html',
                           events=events['data'],
                           pagination=pag,
                           meta_title=app.config['SITE_TITLE'] + ' :: ' + 'Search results')


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

    event['start'] = date_to_string(event['start'], 'short')
    event['end'] = date_to_string(event['end'], 'short')

    event['summary'] = base64.b64decode(event['summary']).decode('utf-8')
    event['description'] = base64.b64decode(event['description']).decode('utf-8')

    return render_template('event_preview.html',
                           event=event,
                           meta_title=app.config['SITE_TITLE'] + ' :: ' + 'Preview event: ' + event['name'])


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

    return render_template('events.html',
                           events=events['data'],
                           pagination=pag,
                           meta_title=app.config['SITE_TITLE'] + ' :: ' + 'Events')


@app.route('/newevent', methods=['GET', 'POST'])
@login_required()
def new_event():
    error = False
    error_type = 'validate'
    if request.method == 'POST':
        event_name = request.form.get('event-name').strip()
        event_summary = base64.b64encode(request.form.get('event-summary').encode('utf-8'))
        event_venue = request.form.get('event-venue')
        event_start = request.form.get('event-start')
        event_end = request.form.get('event-end')

        if not (event_name and event_summary and event_venue
                and event_start and event_end):
            error = True
        else:
            tags = cgi.escape(request.form.get('event-tags'))
            tags_array = extract_tags(tags)

            event_data = {'name': event_name,
                          'summary': event_summary,
                          'description': base64.b64encode(request.form.get('event-description').encode('utf-8')),
                          'start': string_to_date(request.form.get('event-start')),
                          'end': string_to_date(request.form.get('event-end')),
                          'venue': event_venue,
                          'tags': tags_array,
                          'organizer': session['user']['email'],
                          'talks': [],
                          'attendees': []}

            event = eventClass.validate_event_data(event_data)
            event_with_permalink = eventClass.generate_permalink(event)

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
                    response = eventClass.edit_event(request.form['event-id'], event)

                    if response['permalink-changed']:
                        old_event_permalink, new_event_permalink = response['permalink-changed']
                        event = eventClass.get_event_by_permalink(new_event_permalink)
                        event_talks = event['data']['talks']

                        for talk in event_talks:
                            talkClass.modify_event_talk(talk, new_event_permalink)

                        # Update users invited to the event speaker_at and attendee_at fields
                        event_attendees = event['data']['attendees']

                        for attendee in event_attendees:
                            userClass.replace_event_attendee_at(attendee, old_event_permalink, new_event_permalink)

                        userClass.modify_events_organized(session['user']['email'],
                                                          new_event_permalink, old_event_permalink)

                    if not response['error']:
                        flash('Event updated!', 'success')
                    else:
                        flash(response['error'], 'error')
                    return redirect(url_for('events'))
                else:
                    response = eventClass.create_new_event(event)
                    userClass.modify_events_organized(session['user']['email'], event['permalink'])
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
                           meta_title=app.config['SITE_TITLE'] + ' :: ' + 'New event',
                           error=error,
                           error_type=error_type)


@app.route('/event_edit?id=<id>')
@login_required()
def event_edit(id):
    event = eventClass.get_event_by_id(id)

    if event['data']['attendees'] == []:
        event['data']['attendees'] = ""

    session['event-permalink'] = event['data']['permalink']

    if event['error']:
        flash(event['error'], 'error')
        return redirect(url_for('events'))

    if session.get('event-preview') and session['event-preview']['action'] == 'add':
        session.pop('event-preview', None)

    # Format data retrieved from the DB
    event['data']['summary'] = base64.b64decode(event['data']['summary']).decode('utf-8')
    event['data']['description'] = base64.b64decode(event['data']['description']).decode('utf-8')
    event['data']['start'] = format_date(event['data']['start'])
    event['data']['end'] = format_date(event['data']['end'])

    return render_template('edit_event.html',
                           meta_title=app.config['SITE_TITLE'] + ' :: ' + 'Edit event: ' + event['data']['name'],
                           event=event['data'],
                           error=False,
                           error_type=False)


@app.route('/event_delete?id=<id>')
@login_required()
def event_del(id):

    # Update users invited to the event attendee_at field
    event = eventClass.get_event_by_id(id)
    event_permalink = event['data']['permalink']
    event_attendees = event['data']['attendees']
    for attendee in event_attendees:
        userClass.remove_attendee(attendee, event_permalink)

    # Remove event talks
    event_talks = event['data']['talks']
    for talk in event_talks:
        talk_event = talkClass.get_talk_by_permalink(talk)
        talk_id = talk_event['data']['_id']
        talk_del(event_permalink,talk_id)

    # Remove event from the list of events of the organizer
    event_organizer = event['data']['organizer']
    userClass.modify_events_organized(event_organizer, None, event_permalink)
    response = eventClass.delete_event(id)

    if response['data'] is True:
        flash('Event removed!', 'success')
        return redirect(url_for('events'))
    else:
        flash(response['error'], 'error')


@app.route('/bulk_delete_events', methods=['POST'])
def bulk_delete_events():
    events_to_remove = request.json['events_to_remove']

    for event_permalink in events_to_remove:
        event = eventClass.get_event_by_permalink(event_permalink)
        event_id = event['data']['_id']

        response = eventClass.delete_event(event_id)

    if response['data'] is True:
        flash('Event removed!', 'success')
    else:
        flash(response['error'], 'error')

    # Retorna el resultado de la ultima eliminacion
    return jsonify({'value': response['data']})

@app.route('/<event_permalink>/newtalk', methods=['GET', 'POST'])
@login_required()
def new_talk(event_permalink):
    event_permalink = cgi.escape(event_permalink)
    event = eventClass.get_event_by_permalink(event_permalink)

    error = False
    error_type = 'validate'
    if request.method == 'POST':
        # Fields description and tags are optional
        talk_name = request.form.get('talk-name').strip()
        talk_summary = base64.b64encode(request.form.get('talk-summary').encode('utf-8'))
        talk_room = request.form.get('talk-room')
        talk_date = request.form.get('talk-date')
        talk_start = request.form.get('talk-start')
        talk_end = request.form.get('talk-end')
        talk_speaker = request.form.get('talk-speaker')

        if not (talk_name and talk_summary and talk_room
                and talk_date and talk_start and talk_end
                and talk_speaker):
            error = True
        else:
            tags = cgi.escape(request.form.get('talk-tags'))
            tags_array = extract_tags(tags)

            talk_data = {'name': talk_name,
                         'event': event_permalink,
                         'summary': talk_summary,
                         'description': base64.b64encode(request.form.get('talk-description').encode('utf-8')),
                         'date': string_to_date(request.form.get('talk-date')),
                         'start': string_to_time(request.form.get('talk-date'), request.form.get('talk-start')),
                         'end': string_to_time(request.form.get('talk-date'), request.form.get('talk-end')),
                         'room': talk_room,
                         'tags': tags_array,
                         'attendees': [],
                         'speaker': talk_speaker}

            talk = talkClass.validate_talk_data(talk_data)
            talk_with_permalink = talkClass.generate_permalink(talk)
            talk_permalink = talk_with_permalink['permalink']

            if request.form.get('talk-preview') == '1':
                session['talk-preview'] = talk_with_permalink
                session[
                    'talk-preview']['action'] = 'edit' if request.form.get('talk-id') else 'add'
                if request.form.get('talk-id'):
                    session[
                        'talk-preview']['redirect'] = url_for('talk_edit', id=request.form.get('talk-id'))
                else:
                    session['talk-preview']['redirect'] = url_for('new_talk', event_permalink=event_permalink)
                return redirect(url_for('talk_preview',event_permalink=event_permalink))
            else:
                session.pop('talk-preview', None)

                if request.form.get('talk-id'):

                    response = talkClass.edit_talk(request.form['talk-id'], talk)

                    if response['permalink-changed']:
                        old_permalink, new_permalink = response['permalink-changed']
                        talk = talkClass.get_talk_by_permalink(event_permalink)
                        event_talks = event['data']['talks']
                        event_talks.remove(old_permalink)
                        event_talks.append(new_permalink)
                        eventClass.modify_talks_event(event_permalink, event_talks)

                        # Update users invited to the event speaker_at and attendee_at fields
                        talk_attendees = talk['data']['attendees']

                        for attendee in talk_attendees:
                            user_attendee = userClass.get_user_by_email(attendee)
                            userClass.remove_attendee(attendee, event_permalink, old_permalink)
                            userClass.save_attendee(user_attendee, event_permalink, new_permalink)
                            userClass.save_speaker(attendee, event_permalink, new_permalink)

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

                    eventClass.add_new_attendee(event_permalink, speaker_mail)
                    talkClass.add_new_attendee(talk_permalink, speaker_mail)

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
                           start_date=date_to_string(event['data']['start'], 'short'),
                           end_date=date_to_string(event['data']['end'], 'short'),
                           event_permalink=event_permalink,
                           speakers_list=speakers,
                           meta_title=app.config['SITE_TITLE'] + ' :: ' + 'New talk',
                           error=error,
                           error_type=error_type)


@app.route('/talks_list', defaults={'page': 1})
@app.route('/talks_list/page-<int:page>')
@privileged_user()
@login_required()
def talks(page):
    session.pop('talk-preview', None)
    skip = (page - 1) * int(app.config['PER_PAGE'])
    talks = talkClass.get_talks(int(app.config['PER_PAGE']), skip)
    count = talkClass.get_total_count()
    pag = pagination.Pagination(page, app.config['PER_PAGE'], count)

    if talks['data']:
        for talk in talks['data']:
            event_permalink = talk['event']
            event = eventClass.get_event_by_permalink(event_permalink)
            talk['event_name'] = event['data']['name']

    return render_template('talks_list.html',
                           talks=talks['data'],
                           pagination=pag,
                           meta_title=app.config['SITE_TITLE'] + ' :: ' + 'Talks')

@app.route('/<event_permalink>/talk_preview')
@login_required()
def talk_preview(event_permalink):
    event_permalink = cgi.escape(event_permalink)

    talk = session.get('talk-preview')

    talk_date = date_to_string(talk['date'], 'short')
    talk['date'] = talk_date
    talk_start = time_to_string(talk['start'])
    talk['start'] = talk_start
    talk_end = time_to_string(talk['end'])
    talk['end'] = talk_end

    talk['summary'] = base64.b64decode(talk['summary']).decode('utf-8')
    talk['description'] = base64.b64decode(talk['description']).decode('utf-8')

    return render_template('talk_preview.html',
                           event_permalink=event_permalink,
                           talk=talk,
                           talk_start=talk_start,
                           talk_end=talk_end,
                           talk_date=talk_date,
                           meta_title=app.config['SITE_TITLE'] + ' :: ' + 'Preview talk: ' + talk['name'])


@app.route('/<event_permalink>/talk_edit?id=<id>')
@login_required()
def talk_edit(event_permalink, id):
    event_permalink = cgi.escape(event_permalink)
    event = eventClass.get_event_by_permalink(event_permalink)

    talk = talkClass.get_talk_by_id(id)
    session['talk-permalink'] = talk['data']['permalink']

    if talk['error']:
        flash(talk['error'], 'error')
        return redirect(url_for('talks', event_permalink=event_permalink))

    if session.get('talk-preview') and session['talk-preview']['action'] == 'add':
        session.pop('talk-preview', None)

    speakers = eventClass.get_attendance_event(event_permalink)

    old_speaker = talk['data']['speaker']

    if old_speaker in speakers:
        speakers.remove(old_speaker)
        speakers.append(old_speaker)  # quedando el speaker de la charla seleccionado como corresponde

    talk['data']['date'] = format_date(talk['data']['date'])
    talk['data']['summary'] = base64.b64decode(talk['data']['summary']).decode('utf-8')
    talk['data']['description'] = base64.b64decode(talk['data']['description']).decode('utf-8')

    return render_template('edit_talk.html',
                           event_start=date_to_string(event['data']['start'], 'short'),
                           event_end=date_to_string(event['data']['end'], 'short'),
                           event_permalink=event_permalink,
                           meta_title=app.config['SITE_TITLE'] + ' :: ' + 'Edit talk: ' + talk['data']['name'],
                           speakers_list=speakers,
                           talk=talk['data'],
                           error=False,
                           error_type=False)


@app.route('/<event_permalink>/talk_delete?id=<id>')
@login_required()
def talk_del(event_permalink, id):
    event_permalink = cgi.escape(event_permalink)

    talk = talkClass.get_talk_by_id(id)
    talk_permalink = talk['data']['permalink']
    response = talkClass.delete_talk(id)
    event = eventClass.get_event_by_permalink(event_permalink)
    event_talks = event['data']['talks']
    event_talks.remove(talk_permalink)
    eventClass.modify_talks_event(event_permalink, event_talks)

    # Update users invited to the event speaker_at and attendee_at fields
    event_attendees = event['data']['attendees']
    for attendee in event_attendees:
        userClass.remove_attendee(attendee, event_permalink, talk_permalink)

    if response['data'] is True:
        flash('Talk removed!', 'success')
    else:
        flash(response['error'], 'error')

    return redirect(url_for('talks_by_event', event_permalink=event_permalink))


@app.route('/bulk_delete_talks', methods=['POST'])
def bulk_delete_talks():
    talks_to_remove = request.json['talks_to_remove']

    for talk_permalink in talks_to_remove:
        talk = talkClass.get_talk_by_permalink(talk_permalink)
        talk_id = talk['data']['_id']
        event_permalink = talk['data']['event']
        response = talkClass.delete_talk(talk_id)
        event = eventClass.get_event_by_permalink(event_permalink)
        event_talks = event['data']['talks']
        event_talks.remove(talk_permalink)
        eventClass.modify_talks_event(event_permalink, event_talks)

        # Update users invited to the event speaker_at and attendee_at fields
        event_attendees = event['data']['attendees']
        for attendee in event_attendees:
            userClass.remove_attendee(attendee, event_permalink, talk_permalink)
            response = talkClass.delete_talk(talk_id)

    if response['data'] is True:
        flash('Talk removed!', 'success')
    else:
        flash(response['error'], 'error')

    # Retorna el resultado de la ultima eliminacion
    return jsonify({'value': response['data']})


@app.route('/<event_permalink>/<talk_permalink>')
def single_talk(event_permalink, talk_permalink):
    event_permalink = cgi.escape(event_permalink)
    talk_permalink = cgi.escape(talk_permalink)

    if session.has_key('user'):
        if session.has_key('redirect_talk') and session.has_key('redirect_event'):
            session.pop('redirect_event')
            session.pop('redirect_talk')
    else:
        session['redirect_event'] = event_permalink
        session['redirect_talk'] = talk_permalink

    event = eventClass.get_event_by_permalink(event_permalink)
    talk = talkClass.get_talk_by_permalink(talk_permalink)

    if not talk['data']:
        abort(404)

    talk_speaker = talk['data']['speaker']
    speaker_with_gravatar = userClass.get_user(talk_speaker)

    talk_attendees = talk['data']['attendees']
    attendees = []
    for talk_attendee in talk_attendees:
        attendee = userClass.get_user(talk_attendee)
        attendees.append(attendee['data'])

    talk['data']['summary'] = base64.b64decode(talk['data']['summary']).decode('utf-8')
    talk['data']['description'] = base64.b64decode(talk['data']['description']).decode('utf-8')
    talk['data']['date'] = date_to_string(talk['data']['date'], 'short')
    talk['data']['start'] = time_to_string(talk['data']['start'])
    talk['data']['end'] = time_to_string(talk['data']['end'])

    return render_template('single_talk.html',
                           event_permalink=event_permalink,
                           talk=talk['data'],
                           speaker=speaker_with_gravatar['data'],
                           attendees=attendees,
                           meta_title=app.config['SITE_TITLE'] + ' :: ' + event['data']['name'] + " - " + talk['data']['name'])

@app.route('/<event_permalink>/talks')
def talks_by_event(event_permalink):
    event_permalink = cgi.escape(event_permalink)

    event = eventClass.get_event_by_permalink(event_permalink)
    event_name = event['data']['name']

    talks_list = eventClass.get_talks_by_event(event_permalink)
    talks = []

    for talk_permalink in talks_list:
        talk = talkClass.get_talk_by_permalink(str(talk_permalink))
        if talk['data']:
            talk['data']['attendance'] = len(talk['data']['attendees'])
            talk['data']['date'] = date_to_string(talk['data']['date'], 'short')
            talk['data']['start'] = time_to_string(talk['data']['start'])
            talk['data']['end'] = time_to_string(talk['data']['end'])
            talks.append(talk['data'])

    return render_template('talks.html',
                           event_permalink=event_permalink,
                           talks=talks,
                           meta_title=app.config['SITE_TITLE'] + ' :: ' + 'Talks by event: ' + event_name)

@app.route('/<event_permalink>/my_schedule')
def my_schedule(event_permalink):
    event_permalink = cgi.escape(event_permalink)

    event = eventClass.get_event_by_permalink(event_permalink)
    event_name = event['data']['name']

    user_email = session['user']['email']
    user = userClass.get_user(user_email)

    user_events = user['data']['attendee_at']
    user_talks = user_events[event_permalink] if event_permalink in user_events else []
    user_schedule = []

    for talk_name in user_talks:
        talk = talkClass.get_talk_by_permalink(str(talk_name))
        user_schedule.append(talk['data'])

    user_schedule.sort(key=lambda item:item['date'], reverse=False)

    event['data']['summary'] = base64.b64decode(event['data']['summary']).decode('utf-8')
    event['data']['description'] = base64.b64decode(event['data']['description']).decode('utf-8')
    event['data']['start'] = date_to_string(event['data']['start'], 'short')
    event['data']['end'] = date_to_string(event['data']['end'], 'short')

    tags = talkClass.get_tags(event_permalink)['data']

    return render_template('my_schedule.html',
                           tags=tags,
                           event=event['data'],
                           user_schedule=user_schedule,
                           meta_title=app.config['SITE_TITLE'] + ' :: ' + 'My schedule for ' + event_name)



@app.route('/<event_permalink>/add_attendee_event')
@login_required()
def add_attendee_event(event_permalink):
    event_permalink = cgi.escape(event_permalink)
    event = eventClass.get_event_by_permalink(event_permalink)

    return render_template('add_attendee_event.html',
                           event_name=event['data']['name'],
                           event_permalink=event_permalink,
                           meta_title=app.config['SITE_TITLE'] + ' :: ' + 'Invite attendee to ' + event['data']['name'])


@app.route('/<event_permalink>/<talk_permalink>/add_attendee_talk')
@login_required()
def add_attendee_talk(event_permalink, talk_permalink):
    event_permalink = cgi.escape(event_permalink)
    talk = talkClass.get_talk_by_permalink(talk_permalink)

    return render_template('add_attendee_talk.html',
                           event_permalink=event_permalink,
                           talk_name=talk['data']['name'],
                           talk_permalink=talk_permalink,
                           meta_title=app.config['SITE_TITLE'] + ' :: ' + 'Invite attendee to ' + talk['data']['name'])


@app.route('/<event_permalink>/attendance')
def event_attendance(event_permalink):
    event_permalink = cgi.escape(event_permalink)

    event = eventClass.get_event_by_permalink(event_permalink)
    event_name = event['data']['name']
    attendance = event['data']['attendees']
    list_attendance = []

    for attendee in attendance:
        user = userClass.get_user(str(attendee))
        list_attendance.append(user['data'])

    return render_template('event_attendance.html',
                           event_permalink=event_permalink,
                           users=list_attendance,
                           event_name=event_name,
                           meta_title=app.config['SITE_TITLE'] + ' :: ' + 'Event attendance: ' + event_name)


@app.route('/<event_permalink>/<talk_permalink>/attendance')
def talk_attendance(event_permalink, talk_permalink):
    event_permalink = cgi.escape(event_permalink)
    talk_permalink = cgi.escape(talk_permalink)

    talk = talkClass.get_talk_by_permalink(talk_permalink)
    talk_name = talk['data']['name']
    attendance = talk['data']['attendees']
    list_attendance = []

    for attendee in attendance:
        user = userClass.get_user(str(attendee))
        list_attendance.append(user['data'])

    return render_template('talk_attendance.html',
                           talk_permalink=talk_permalink,
                           event_permalink= event_permalink,
                           users=list_attendance,
                           talk_name=talk_name,
                           meta_title=app.config['SITE_TITLE'] + ' :: ' + 'Talk attendance: ' + talk_name)


@app.route('/<event_permalink>/<talk_permalink>/talk_attendance')
def talk_attendance_(event_permalink, talk_permalink):
    event_permalink = cgi.escape(event_permalink)
    talk_permalink = cgi.escape(talk_permalink)

    talk = talkClass.get_talk_by_permalink(talk_permalink)
    talk_name = talk['data']['name']
    attendance = talk['data']['attendees']
    list_attendance = []

    for attendee in attendance:
        user = userClass.get_user(str(attendee))
        list_attendance.append(user['data'])

    return render_template('talk_attendance_.html', talk_permalink=talk_permalink, event_permalink= event_permalink,
                           users=list_attendance,
                           talk_name=talk_name, meta_title='Talk attendance: ' + talk_name)


@app.route('/register')
def register():
    gravatar_url = userClass.get_gravatar_link()
    return render_template('register.html',
                           gravatar_url=gravatar_url,
                           meta_title=app.config['SITE_TITLE'] + ' :: ' + 'Register')


@app.route('/add_user')
def add_user():
    gravatar_url = userClass.get_gravatar_link()
    role_list = ['Admin', 'User']
    return render_template('add_user.html',
                           gravatar_url=gravatar_url,
                           role_list=role_list,
                           meta_title=app.config['SITE_TITLE'] + ' :: ' + 'Register a new user')


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
                role = user_data['data'].get('role')
                if role == 'User':
                    if not session.has_key('redirect_event') and not session.has_key('redirect_talk'):
                        return redirect(url_for('dashboard_user'))
                    else:
                        if session.has_key('redirect_talk'):
                            return redirect(url_for('single_talk', event_permalink=session['redirect_event'],
                                                    talk_permalink=session['redirect_talk']))
                        elif session.has_key('redirect_event'):
                            return redirect(url_for('single_event', event_permalink=session['redirect_event']))
                else:
                    if not session.has_key('redirect_event') and not session.has_key('redirect_talk'):
                        return redirect(url_for('dashboard_admin'))
                    else:
                        if session.has_key('redirect_talk'):
                            return redirect(url_for('single_talk', event_permalink=session['redirect_event'],
                                                    talk_permalink=session['redirect_talk']))
                        elif session.has_key('redirect_event'):
                            return redirect(url_for('single_event', event_permalink=session['redirect_event']))
    else:
        if session.get('user'):
            role = session.get('user').get('role')
            if role == 'User':
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
    attendees_number = len(eventClass.get_attendees())
    organizers_number = len(eventClass.get_organizers())

    user_email = session['user']['email']

    organizer_at, speaker_at, attendee_at = _events_by_user(user_email)

    return render_template('dashboard_admin.html',
                           organizer_at=organizer_at,
                           speaker_at=speaker_at,
                           attendee_at=attendee_at,
                           events_created=events_created,
                           talks_created=talks_created,
                           attendees_number=attendees_number,
                           organizers_number=organizers_number,
                           meta_title=app.config['SITE_TITLE'] + ' :: ' + 'Admin dashboard')


@app.route('/dashboard_user')
@login_required()
def dashboard_user():
    user_email = session['user']['email']

    organizer_at, speaker_at, attendee_at = _events_by_user(user_email)

    return render_template('dashboard_user.html',
                           organizer_at=organizer_at,
                           speaker_at=speaker_at,
                           attendee_at=attendee_at,
                           meta_title=app.config['SITE_TITLE'] + ' :: ' + 'Users dashboard')


def _events_by_user(user_email):
    user = userClass.get_user(user_email)

    list_organizer_at = user['data']['organizer_at']
    organizer_at = []

    for event_name in list_organizer_at:
        event = eventClass.get_event_by_permalink(event_name)
        event['data']['start'] = date_to_string(event['data']['start'], 'short')
        event['data']['end'] = date_to_string(event['data']['end'], 'short')
        organizer_at.append(event['data'])

    list_speaker_at = user['data']['speaker_at']
    list_speaker_at_ = list_speaker_at.keys()
    speaker_at = []

    for event_name in list_speaker_at_:
        event = eventClass.get_event_by_permalink(event_name)
        event['data']['start'] = date_to_string(event['data']['start'], 'short')
        event['data']['end'] = date_to_string(event['data']['end'], 'short')
        speaker_at.append(event['data'])

    list_attendee_at = user['data']['attendee_at']
    list_attendee_at_ = list_attendee_at.keys()
    attendee_at = []

    for event_name in list_attendee_at_:
        event = eventClass.get_event_by_permalink(event_name)
        event['data']['start'] = date_to_string(event['data']['start'], 'short')
        event['data']['end'] = date_to_string(event['data']['end'], 'short')
        attendee_at.append(event['data'])

    return organizer_at, speaker_at, attendee_at


@app.route('/users')
@login_required()
@privileged_user()
def users_list():
    users = userClass.get_users()
    list_users = []
    for user in users['data']:
        user_id = user['id']
        user_with_gravatar = userClass.get_user(user_id)
        list_users.append(user_with_gravatar['data'])

    return render_template('users.html',
                           users=list_users,
                           meta_title=app.config['SITE_TITLE'] + ' :: ' + 'Users')


@app.route('/attendees')
@login_required()
@privileged_user()
def attendees():
    attendees = eventClass.get_attendees()
    list_users = []

    for attendee in attendees:
        user = userClass.get_user(attendee)
        list_users.append(user['data'])

    return render_template('attendees.html',
                           users=list_users,
                           meta_title=app.config['SITE_TITLE'] + ' :: ' + 'Attendees')


@app.route('/organizers')
@login_required()
@privileged_user()
def organizers_list():
    organizers = eventClass.get_organizers()
    list_users = []

    for organizer in organizers:
        user = userClass.get_user(organizer)
        list_users.append(user['data'])

    return render_template('organizers.html',
                           users=list_users,
                           meta_title=app.config['SITE_TITLE'] + ' :: ' + 'Organizers')


@app.route('/edit_user?id=<id>')
@login_required()
@privileged_user()
def edit_user(id):
    user = userClass.get_user(id)
    role_list = ['Admin', 'User']
    return render_template('edit_user.html', user=user['data'], role_list=role_list,
                           old_email=id, meta_title=app.config['SITE_TITLE'] + ' :: ' + 'Edit user')


@app.route('/edit_inactive_user?id=<id>')
@login_required()
@privileged_user()
def edit_inactive_user(id):
    user = userClass.get_user(id)
    return render_template('edit_inactive_user.html', user=user['data'],
                           old_email=id, meta_title=app.config['SITE_TITLE'] + ' :: ' + 'Edit user')


@app.route('/view_user?id=<id>')
@login_required()
def view_user(id):
    user = userClass.get_user(id)
    return render_template('view_user.html',
                           user=user['data'],
                           meta_title=app.config['SITE_TITLE'] + ' :: ' + 'User profile')


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


@app.route('/<event_permalink>/delete_attendee_event/<attendee_email>')
@login_required()
def delete_attendee_event(attendee_email, event_permalink):
    event_permalink = cgi.escape(event_permalink)

    event = eventClass.get_event_by_permalink(event_permalink)
    talks = event['data']['talks']

    for talk in talks:
        talk_event = talkClass.get_talk_by_permalink(talk)
        talk_speaker = talk_event['data']['speaker']
        if attendee_email == talk_speaker:
            flash('The attendee cannot be deleted. Speakers removal is not allowed.', 'error')
            return redirect(url_for('event_attendance', event_permalink=event_permalink))

    event_attendees = event['data']['attendees']
    event_attendees.remove(attendee_email)
    eventClass.modify_attendees_event(event_permalink, event_attendees)
    userClass.remove_attendee(attendee_email, event_permalink)

    for talk in talks:
        talk_event= talkClass.get_talk_by_permalink(talk)
        talk_attendees = talk_event['data']['attendees']
        if attendee_email in talk_attendees:
            talk_attendees.remove(attendee_email)
            talkClass.modify_attendees_talk(talk, talk_attendees)
            userClass.remove_attendee(attendee_email, event_permalink, talk)

    flash('The attendee has been deleted.', 'success')
    return redirect(url_for('event_attendance', event_permalink=event_permalink))


@app.route('/<event_permalink>/<talk_permalink>/delete_attendee_talk/<attendee_email>')
@login_required()
def delete_attendee_talk(attendee_email, event_permalink, talk_permalink):
    event_permalink = cgi.escape(event_permalink)
    talk_permalink = cgi.escape(talk_permalink)

    talk = talkClass.get_talk_by_permalink(talk_permalink)
    talk_speaker = talk['data']['speaker']

    if attendee_email == talk_speaker:
        flash('The attendee cannot be deleted. Speakers removal is not allowed.', 'error')
        return redirect(url_for('talk_attendance', event_permalink=event_permalink, talk_permalink=talk_permalink))
    else:
        talk_attendees = talk['data']['attendees']
        talk_attendees.remove(attendee_email)
        talkClass.modify_attendees_talk(talk_permalink, talk_attendees)
        userClass.remove_attendee(attendee_email, event_permalink, talk_permalink)
        flash('The attendee has been deleted!', 'success')
        return redirect(url_for('talk_attendance', event_permalink=event_permalink, talk_permalink=talk_permalink))


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
        'bio': request.form.get('user-bio', None),
        'update': request.form.get('user-update', False)
    }

    if not post_data['name']:
            post_data['name'] = ""
    if not post_data['_id']:
        flash('Email is required..', 'error')
        if post_data['update']:
                return redirect(url_for('edit_user', id=post_data['_id']))
        else:
            return redirect(url_for('add_user'))
    else:
        old_email = request.form.get('user-id', None)
        new_email = request.form.get('user-email', None)
        exist_user = userClass.get_user_by_email(old_email)
        if exist_user:
            if not old_email == new_email and not new_email == None:
                user = userClass.get_user_by_email(old_email)

                list_attendee_at = user['attendee_at']
                list_attendee_at_ = list_attendee_at.keys()

                for event_name in list_attendee_at_:
                    event = eventClass.get_event_by_permalink(event_name)
                    attendees_event = event['data']['attendees']

                    if old_email in attendees_event:
                        attendees_event.remove(old_email)
                        attendees_event.append(new_email)
                        eventClass.modify_attendees_event(event_name, attendees_event)

                    talks_event = event['data']['talks']
                    for talk in talks_event:
                        talk_event = talkClass.get_talk_by_permalink(talk)
                        attendees_talk = talk_event['data']['attendees']
                        speaker = talk_event['data']['speaker']

                        if old_email in attendees_talk:
                            attendees_talk.remove(old_email)
                            attendees_talk.append(new_email)
                            talkClass.modify_attendees_talk(talk, attendees_talk)

                        if old_email == speaker:
                            talkClass.modify_speaker_talk(talk, new_email)

                events_organized = user['organizer_at']
                for event in events_organized:
                    eventClass.modify_organizer_event(event, new_email)

                user_deleted = userClass.delete_user(old_email)
                if old_email == session['user']['email']:
                    session.pop('user')
                    user['_id']= new_email
                    user['email'] = new_email
                    userClass.start_session(user)

                user_saved = userClass.save_new_user(new_email, user)
                message = 'User updated!' if post_data['update'] else 'User added!'
                flash(message, 'success')
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


@app.route('/save_profile_user', methods=['POST'])
@login_required()
def save_profile_user():
    post_data = {
        '_id': request.form.get('user-email', None),
        'name': request.form.get('user-name', None),
        'old_pass': request.form.get('user-old-password', None),
        'new_pass': request.form.get('user-new-password', None),
        'new_pass_again': request.form.get('user-new-password-again', None),
        'role': request.form.get('user-role', None),
        'active': request.form.get('user-active', None),
        'bio': request.form.get('user-bio', None),
        'update': request.form.get('user-update', False)
    }

    if not post_data['name']:
            post_data['name'] = ""
    if not post_data['_id']:
        flash('Email is required..', 'error')
        if post_data['update']:
                return redirect(url_for('edit_user', id=post_data['_id']))
        else:
            return redirect(url_for('add_user'))
    else:
        old_email = request.form.get('user-id', None)
        new_email = request.form.get('user-email', None)

        if not old_email == new_email:
            user = userClass.get_user_by_email(old_email)

            list_attendee_at = user['attendee_at']
            list_attendee_at_ = list_attendee_at.keys()

            for event_name in list_attendee_at_:
                event = eventClass.get_event_by_permalink(event_name)
                attendees_event = event['data']['attendees']

                if old_email in attendees_event:
                    attendees_event.remove(old_email)
                    attendees_event.append(new_email)
                    eventClass.modify_attendees_event(event_name, attendees_event)

                talks_event = event['data']['talks']
                for talk in talks_event:
                    talk_event = talkClass.get_talk_by_permalink(talk)
                    attendees_talk = talk_event['data']['attendees']
                    speaker = talk_event['data']['speaker']

                    if old_email in attendees_talk:
                        attendees_talk.remove(old_email)
                        attendees_talk.append(new_email)
                        talkClass.modify_attendees_talk(talk, attendees_talk)

                    if old_email == speaker:
                        talkClass.modify_speaker_talk(talk, new_email)

            events_organized = user['organizer_at']
            for event in events_organized:
                eventClass.modify_organizer_event(event, new_email)

            user_deleted = userClass.delete_user(old_email)
            if old_email == session['user']['email']:
                session.pop('user')
                user['_id']= new_email
                user['email'] = new_email
                userClass.start_session(user)
            user_saved = userClass.save_new_user(new_email, user)
            message = 'User updated!' if post_data['update'] else 'User added!'
            flash(message, 'success')

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

    return redirect(url_for('configure_settings'))


@app.route('/register_user', methods=['POST'])
def register_user():

    post_data = {
        '_id': request.form.get('user-id', None),
        'name': request.form.get('user-name', None),
        'old_pass': request.form.get('user-old-password', None),
        'new_pass': request.form.get('user-new-password', None),
        'new_pass_again': request.form.get('user-new-password-again', None),
        'role': request.form.get('user-role', None),
        'active': 1,
        'bio': request.form.get('user-bio', None),
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
    event_permalink = cgi.escape(event_permalink)

    post_data = {
        '_id': request.form.get('user-id', None).lower().strip(),
        'name': request.form.get('user-name', None),
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
    event_permalink = cgi.escape(event_permalink)
    talk_permalink = cgi.escape(talk_permalink)

    post_data = {
        '_id': request.form.get('user-id', None),
        'name': request.form.get('user-name', None),
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


@app.route('/<event_permalink>/<talk_permalink>/schedule_talk')
@login_required()
def schedule_talk(event_permalink, talk_permalink):
    #  Add to my schedule/Remove from my schedule buttons in single_talk
    attendee_email = session['user']['email']

    _schedule_talk(event_permalink, talk_permalink, attendee_email)

    return redirect(url_for('single_talk', event_permalink=event_permalink, talk_permalink=talk_permalink))


@app.route('/schedule_talk_event', methods=['POST'])
@login_required()
def schedule_talk_event():
    #  Talks checkboxes in single_event
    event_permalink = request.json['event_permalink']
    talk_permalink = request.json['talk_permalink']
    user_email = request.json['user_email']

    _schedule_talk(event_permalink, talk_permalink, user_email)

    return jsonify({'value': True})


def _schedule_talk(event_permalink, talk_permalink, user_email):
    # Auxiliary function for schedule_talk and schedule_talk_event
    user_data = userClass.get_user(user_email)
    attendee = user_data['data']

    event_permalink = cgi.escape(event_permalink)
    talk_permalink = cgi.escape(talk_permalink)

    talk = talkClass.get_talk_by_permalink(talk_permalink)

    if attendee['_id'] in talk['data']['attendees']:
        userClass.remove_attendee(user_email, event_permalink, talk_permalink)
        #  The user is not removed from the event, just from the talk
        talkClass.remove_attendee(talk_permalink, user_email)
    else:
        userClass.save_attendee(attendee, event_permalink, talk_permalink)
        eventClass.add_new_attendee(event_permalink, user_email)
        talkClass.add_new_attendee(talk_permalink, user_email)


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
                           meta_title=app.config['SITE_TITLE'] + ' :: ' + 'Settings',
                           error=error,
                           error_type=error_type,
                           user=user['data'], old_email=user_email,
                           role_list=role_list)


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
            'bio': request.form.get('user-bio', None),
            'new_pass': request.form.get('user-new-password', None),
            'new_pass_again': request.form.get('user-new-password-again', None),
            'update': False
        }

        site_data = {
            'title': request.form.get('site-title', None),
            'description': request.form.get('site-description', None)
        }

        for key, value in user_data.items():
            if not value and key != 'update' and key != 'bio':
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

app.jinja_env.autoescape = False
app.jinja_env.globals['url_for_other_page'] = url_for_other_page
app.jinja_env.globals['csrf_token'] = generate_csrf_token
app.jinja_env.globals['meta_description'] = app.config['SITE_DESCRIPTION']
app.jinja_env.globals['recent_events'] = eventClass.get_events(10, 0)['data']
app.jinja_env.globals['tags'] = eventClass.get_tags()['data']
app.jinja_env.globals.update(date_to_string=date_to_string)
app.jinja_env.globals.update(chunker=chunker)

if not app.config['DEBUG']:
    import logging
    from logging import FileHandler
    file_handler = FileHandler(app.config['LOG_FILE'])
    file_handler.setLevel(logging.WARNING)
    app.logger.addHandler(file_handler)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)),
            debug=app.config['DEBUG'])