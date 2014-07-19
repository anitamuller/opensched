import datetime
import cgi
from bson.objectid import ObjectId
from helper_functions import *


class Event:

    def __init__(self, default_config):
        self.collection = default_config['EVENTS_COLLECTION']
        self.response = {'error': None, 'data': None}
        self.debug_mode = default_config['DEBUG']

    def get_events(self, limit, skip, tag=None, search=None):
        self.response['error'] = None
        cond = {}
        if tag is not None:
            cond = {'tags': tag}
        elif search is not None:
            cond = {'$or': [
                    {'name': {'$regex': search, '$options': 'i'}},
                    {'description': {'$regex': search, '$options': 'i'}},
                    {'preview': {'$regex': search, '$options': 'i'}}]}
        try:
            cursor = self.collection.find(cond).sort(
                'date', direction=-1).skip(skip).limit(limit)
            self.response['data'] = []
            for event in cursor:
                if 'tags' not in event:
                    event['tags'] = []
                if 'comments' not in event:
                    event['comments'] = []
                if 'preview' not in event:
                    event['preview'] = ''

                self.response['data'].append({'id': event['_id'],
                                              'name': event['name'],
                                              'description' : event['description'],
                                              'dateInit': event['dateInit'],
                                              'dateEnd': event['dateEnd'],
                                              'preview': event['preview'],
                                              'permalink': event['permalink'],
                                              'tags': event['tags'],
                                              'author': event['author'],
                                              'comments': event['comments']})
        except Exception, e:
            self.print_debug_info(e, self.debug_mode)
            self.response['error'] = 'Events not found..'

        return self.response

    def get_event_by_permalink(self, permalink):
        self.response['error'] = None
        try:
            self.response['data'] = self.collection.find_one(
                {'permalink': permalink})
        except Exception, e:
            self.print_debug_info(e, self.debug_mode)
            self.response['error'] = 'Event not found..'

        return self.response

    def get_event_by_id(self, event_id):
        self.response['error'] = None
        try:
            self.response['data'] = self.collection.find_one(
                {'_id': ObjectId(event_id)})
            if self.response['data']:
                if 'tags' not in self.response['data']:
                    self.response['data']['tags'] = ''
                else:
                    self.response['data']['tags'] = ','.join(
                        self.response['data']['tags'])
                if 'preview' not in self.response['data']:
                    self.response['data']['preview'] = ''
        except Exception, e:
            self.print_debug_info(e, self.debug_mode)
            self.response['error'] = 'Event not found..'

        return self.response

    def get_total_count(self, tag=None, search=None):
        cond = {}
        if tag is not None:
            cond = {'tags': tag}
        elif search is not None:
            cond = {'$or': [
                    {'title': {'$regex': search, '$options': 'i'}},
                    {'body': {'$regex': search, '$options': 'i'}},
                    {'preview': {'$regex': search, '$options': 'i'}}]}

        return self.collection.find(cond).count()

    def get_tags(self):
        self.response['error'] = None
        try:
            self.response['data'] = self.collection.aggregate([
                {'$unwind': '$tags'},
                {'$group': {'_id': '$tags', 'count': {'$sum': 1}}},
                {'$sort': {'count': -1}},
                {'$limit': 10},
                {'$project': {'title': '$_id', 'count': 1, '_id': 0}}
            ])
            if self.response['data']['result']:
                self.response['data'] = self.response['data']['result']
            else:
                self.response['data'] = []

        except Exception, e:
            self.print_debug_info(e, self.debug_mode)
            self.response['error'] = 'Get tags error..'

        return self.response

    def create_new_event(self, post_data):
        self.response['error'] = None
        try:
            self.response['data'] = self.collection.insert(post_data)
        except Exception, e:
            self.print_debug_info(e, self.debug_mode)
            self.response['error'] = 'Adding event error..'

        return self.response

    def edit_event(self, event_id, event_data):
        self.response['error'] = None
        del event_data['date']
        del event_data['permalink']

        try:
            self.collection.update(
                {'_id': ObjectId(event_id)}, {"$set": event_data}, upsert=False)
            self.response['data'] = True
        except Exception, e:
            self.print_debug_info(e, self.debug_mode)
            self.response['error'] = 'Event update error..'

        return self.response

    def delete_post(self, event_id):
        self.response['error'] = None
        try:
            if self.get_event_by_id(event_id) and self.collection.remove({'_id': ObjectId(event_id)}):
                self.response['data'] = True
            else:
                self.response['data'] = False
        except Exception, e:
            self.print_debug_info(e, self.debug_mode)
            self.response['error'] = 'Deleting event error..'

        return self.response

    @staticmethod
    def validate_event_data(event_data):
        permalink = random_string(12)

        event_data['title'] = cgi.escape(event_data['name'])
        event_data['preview'] = cgi.escape(event_data['preview'], quote=True)
        event_data['description'] = cgi.escape(event_data['description'], quote=True)
        event_data['date'] = datetime.datetime.utcnow()
        event_data['permalink'] = permalink

        return event_data

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