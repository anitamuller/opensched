from flask import session


class Settings:

    def __init__(self, default_config):
        self.collection = default_config['SETTINGS_COLLECTION']

        self.config = default_config
        self.config['PER_PAGE'] = 15
        self.config['SEARCH'] = False
        self.config['SITE_TITLE'] = 'OpenSched'
        self.config['SITE_DESCRIPTION'] = 'Open event scheduler and agenda builder app'

        self.response = {'error': None, 'data': None}
        self.debug_mode = default_config['DEBUG']

    def get_config(self):
        try:
            cursor = self.collection.find_one()
            if cursor:
                self.config['PER_PAGE'] = cursor.get(
                    'per_page', self.config['PER_PAGE'])
                self.config['SEARCH'] = cursor.get(
                    'use_search', self.config['SEARCH'])
                self.config['SITE_TITLE'] = cursor.get(
                    'title', self.config['SITE_TITLE'])
                self.config['SITE_DESCRIPTION'] = cursor.get(
                    'description', self.config['SITE_DESCRIPTION'])
            return self.config
        except Exception, e:
            self.print_debug_info(e, self.debug_mode)
            self.response['error'] = 'System error..'

    def is_installed(self):
        users_cnt = self.config['USERS_COLLECTION'].find().count()
        configs_cnt = self.config['SETTINGS_COLLECTION'].find().count()

        if users_cnt and configs_cnt:
            session['installed'] = True
            return True
        else:
            session['installed'] = False
            return False

    def install(self, site_data, user_data):
        import user

        userClass = user.User(self.config)

        self.response['error'] = None
        try:
            self.config['USERS_COLLECTION'].ensure_index([('date', 1)])

            self.config['EVENTS_COLLECTION'].ensure_index([('date', -1)])
            self.config['EVENTS_COLLECTION'].ensure_index(
                [('tags', 1), ('date', -1)])
            self.config['EVENTS_COLLECTION'].ensure_index([('permalink', 1)])
            self.config['EVENTS_COLLECTION'].ensure_index(
                [('query', 1), ('orderby', 1)])

            self.config['TALKS_COLLECTION'].ensure_index([('date', -1)])
            self.config['TALKS_COLLECTION'].ensure_index(
                [('tags', 1), ('date', -1)])
            self.config['TALKS_COLLECTION'].ensure_index([('permalink', 1)])
            self.config['TALKS_COLLECTION'].ensure_index(
                [('query', 1), ('orderby', 1)])

            # Create admin user
            user_create = userClass.save_user(user_data)

            # Init site properties
            self.collection.insert(site_data)

            if user_create['error']:
                self.response['error'] = []
                self.response['error'].append(user_create['error'])
                self.config['USERS_COLLECTION'].drop()
                self.config['EVENTS_COLLECTION'].drop()
                self.config['TALKS_COLLECTION'].drop()
                self.collection.drop()
            return self.response
        except Exception, e:
            self.print_debug_info(e, self.debug_mode)
            self.response['error'] = 'Installation error..'

    def update_settings(self, data):
        self.response['error'] = None
        try:
            cursor = self.collection.find_one()
            self.collection.update(
                {'_id': cursor['_id']}, {'$set': data}, upsert=False, multi=False)
            self.response['data'] = True
            return self.response
        except Exception, e:
            self.print_debug_info(e, self.debug_mode)
            self.response['error'] = 'Settings update error..'

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
