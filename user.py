import urllib
import hashlib
import re
from werkzeug.security import check_password_hash, generate_password_hash
from flask import session


class User:

    def __init__(self, default_config):
        self.collection = default_config['USERS_COLLECTION']
        self.name = None
        self.username = None
        self.email = None
        self.role = None
        self.active = None
        self.session_key = 'user'
        self.response = {'error': None, 'data': None}
        self.debug_mode = default_config['DEBUG']

    def login(self, username, password):
        self.response['error'] = None
        try:
            user = self.collection.find_one({'_id': username})
            if user:
                if self.validate_login(user['password'], password):
                    self.username = user['_id']
                    self.name = user['name']
                    self.email = user['email']
                    self.role = user['role']
                else:
                    self.response['error'] = 'Password doesn\'t match..'
            else:
                self.response['error'] = 'User not found..'

        except Exception, e:
            self.print_debug_info(e, self.debug_mode)
            self.response['error'] = 'System error..'

        self.response['data'] = {'name': self.name,
                                 'username':self.username,
                                 'email': self.email,
                                 'role': self.role}
        return self.response

    @staticmethod
    def validate_login(password_hash, password):
        return check_password_hash(password_hash, password)

    def start_session(self, obj):
        session[self.session_key] = obj
        return True

    def logout(self):
        if session.pop(self.session_key, None):
            return True
        else:
            return False

    def get_users(self):
        self.response['error'] = None
        try:
            users = self.collection.find()
            self.response['data'] = []
            for user in users:
                self.response['data'].append({'id': user['_id'],
                                              'name': user['name'],
                                              'email': user['email'],
                                              'role': user['role']})
        except Exception, e:
            self.print_debug_info(e, self.debug_mode)
            self.response['error'] = 'Users not found..'
        return self.response

    def get_users_by_role(self, role):
        users = self.collection.find({'role': role})
        list = []

        for user in users:
            list.append(str(user['_id']))

        return list


    def get_user(self, user_id):
        self.response['error'] = None
        try:
            user = self.collection.find_one({'_id': user_id})
            gravatar_url = self.get_gravatar_link(user.get('email', ''))
            self.response['data'] = user
            self.response['data']['gravatar_url'] = gravatar_url
        except Exception, e:
            self.print_debug_info(e, self.debug_mode)
            self.response['error'] = 'User not found..'
        return self.response

    @staticmethod
    def get_gravatar_link(email=''):
        gravatar_url = "http://www.gravatar.com/avatar/" + \
            hashlib.md5(email.lower()).hexdigest() + "?"
        gravatar_url += urllib.urlencode({'d': 'retro'})
        return gravatar_url

    def delete_user(self, user_id):
        self.response['error'] = None
        try:
            self.collection.remove({'_id': user_id})
            self.response['data'] = True
        except Exception, e:
            self.print_debug_info(e, self.debug_mode)
            self.response['error'] = 'Delete user error..'
        return self.response

    def save_user(self, user_data):
        self.response['error'] = None
        if user_data:
            if not re.match(r"^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]*$", user_data['email']):
                self.response['error'] = 'Email is invalid..'
                return self.response

            exist_user = self.collection.find_one({'_id': user_data['_id']})
            if user_data['update'] is not False:
                if exist_user:
                    if user_data['old_pass']:
                        if self.validate_login(exist_user['password'], user_data['old_pass']):
                            if user_data['new_pass'] and user_data['new_pass'] == user_data['new_pass_again']:
                                password_hash = generate_password_hash(
                                    user_data['new_pass'], method='pbkdf2:sha256')
                                record = {'password': password_hash,
                                          'email': user_data['email']}
                                try:
                                    self.collection.update(
                                        {'_id': user_data['_id']}, {'$set': record}, upsert=False, multi=False)
                                    self.response['data'] = True
                                except Exception, e:
                                    self.print_debug_info(e, self.debug_mode)
                                    self.response[
                                        'error'] = 'Update user error..'
                            else:
                                self.response[
                                    'error'] = 'New password doesn\'t match..'
                                return self.response
                        else:
                            self.response[
                                'error'] = 'Old password doesn\'t match..'
                            return self.response
                    else:
                        try:
                            record = {'name': user_data['name'],
                                      'email': user_data['email'],
                                      'role': user_data['role']}
                            self.collection.update(
                                {'_id': user_data['_id']}, {'$set': record}, upsert=False, multi=False)
                            self.response['data'] = True
                        except Exception, e:
                            self.print_debug_info(e, self.debug_mode)
                            self.response['error'] = 'Update user error..'
                else:
                    self.response['error'] = 'User not found..'
                    return self.response
            else:
                if exist_user:
                    self.response['error'] = 'Username already exists..'
                    return self.response
                else:
                    if user_data['new_pass'] and user_data['new_pass'] == user_data['new_pass_again']:
                        password_hash = generate_password_hash(
                            user_data['new_pass'], method='pbkdf2:sha256')
                        record = {'_id': user_data['_id'], 'password': password_hash,
                                  'email': user_data['email'], 'name': user_data['name'],
                                  'role': user_data['role'], 'active': user_data['active']}
                        try:
                            self.collection.insert(record, safe=True)
                            self.response['data'] = True
                        except Exception, e:
                            self.print_debug_info(e, self.debug_mode)
                            self.response['error'] = 'Create user user error..'
                    else:
                        self.response[
                            'error'] = 'Password cannot be blank and must be the same..'
                        return self.response
        else:
            self.response['error'] = 'Error..'
        return self.response

    def save_participant(self, user_data):
        self.response['error'] = None
        if user_data:
            if not re.match(r"^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]*$", user_data['email']):
                self.response['error'] = 'Email is invalid..'
                return self.response

            exist_user = self.collection.find_one({'_id': user_data['_id']})
            if exist_user:
                self.response['error'] = 'Username already exists..'
                return self.response
            else:
                record = {'_id': user_data['_id'], 'email': user_data['email'],
                          'name': user_data['name'], 'active': user_data['active'],
                          'role': 'assistant'}

                try:
                    self.collection.insert(record, safe=True)
                    self.response['data'] = True
                except Exception, e:
                    self.print_debug_info(e, self.debug_mode)
                    self.response['error'] = 'Create user user error..'
        else:
            self.response['error'] = 'Error..'
            return self.response


    @staticmethod
    def print_debug_info(msg, show=False):
        if show:
            import sys
            import os

            error_color = '\033[32m'
            error_end = '\033[0m'

            error = {'type': sys.exc_info()[0].__name__,
                     'file': os.path.basename(sys.exc_info()[2].tb_frame.f_code.co_filename),
                     'line': sys.exc_info()[2].tb_lineno,
                     'details': str(msg)}

            print error_color
            print '\n\n---\nError type: %s in file: %s on line: %s\nError details: %s\n---\n\n'\
                  % (error['type'], error['file'], error['line'], error['details'])
            print error_end
