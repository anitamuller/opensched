import datetime
import re
import string
import random
from urlparse import urljoin
from flask import request, url_for, session, flash, redirect
from functools import wraps


def url_for_other_page(page):
    args = request.view_args.copy()
    args['page'] = page
    return url_for(request.endpoint, **args)


def extract_tags(tags):
    whitespace = re.compile('\s')
    nowhite = whitespace.sub("", tags)
    tags_array = nowhite.split(',')

    cleaned = []
    for tag in tags_array:
        if tag not in cleaned and tag != "":
            cleaned.append(tag)

    return cleaned


def random_string(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for x in range(size))


def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = random_string()
    return session['_csrf_token']


def make_external(url):
    return urljoin(request.url_root, url)


def login_required():
    def wrapper(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not session.get('user'):
                flash('You must be logged in..', 'error')
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return wrapped
    return wrapper


def privileged_user():
    def wrapper(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not session.get('user'):
                flash('You must be logged in..', 'error')
                return redirect(url_for('login'))
            elif session.get('user').get('role') != 'Admin':
                flash('Not authorized..', 'error')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return wrapped
    return wrapper


def string_to_date(date):
    """Transforms a string date in a python date"""
    parsed = datetime.datetime.strptime(date, "%d/%m/%Y")
    return parsed


def date_to_string(date, date_format):
    """Transforms a python date in a string date"""
    if date_format == 'short':
        parsed = date.strftime('%d') + "/" + date.strftime('%m') + "/" + date.strftime('%y')
    else:
        parsed = date.strftime('%A') + date.strftime('%d') + ", " + \
                      date.strftime('%B') + ", " + date.strftime('%Y')
    return parsed


def string_to_time(time):
    """Transforms a string time in a python time"""
    # Intentar guardar el dia tambien
    parsed = datetime.datetime.strptime(time, "%I:%M %p")
    return parsed


def time_to_string(time):
    """Transforms a python time in a string time"""
    return time.strftime('%I') + ":" + time.strftime('%M') + " " + time.strftime('%p')