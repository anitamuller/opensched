import datetime
import cgi
import event
from bson.objectid import ObjectId
from helper_functions import *


class Talk:

    def __init__(self, default_config):
        self.collection = default_config['TALKS_COLLECTION']
        self.response = {'error': None, 'data': None}
        self.debug_mode = default_config['DEBUG']

    def get_talks(self, limit, skip, tag=None, search=None):
        self.response['error'] = None
        cond = {}
        if tag is not None:
            cond = {'tags': tag}
        elif search is not None:
            cond = {'$or': [
                    {'name': {'$regex': search, '$options': 'i'}},
                    {'summary': {'$regex': search, '$options': 'i'}},
                    {'description': {'$regex': search, '$options': 'i'}},
                    {'speaker': {'$regex': search, '$options': 'i'}}]}

        try:
            cursor = self.collection.find(cond).sort(
                'date', direction=-1).skip(skip).limit(limit)
            self.response['data'] = []
            for talk in cursor:
                if 'tags' not in talk:
                    talk['tags'] = []

                if 'participants' not in talk:
                    talk['participants'] = []

                self.response['data'].append({'id': talk['_id'],
                                              'name': talk['name'],
                                              'summary': talk['summary'],
                                              'description': talk['description'],
                                              'date': talk['date'],
                                              'start': talk['start'],
                                              'end': talk['end'],
                                              'room': talk['room'],
                                              'speaker': talk['speaker'],
                                              'permalink': talk['permalink'],
                                              'tags': talk['tags'],
                                              'participants': talk['participants'],
                                              'attendance': len(talk['participants'])})
        except Exception, e:
            self.print_debug_info(e, self.debug_mode)
            self.response['error'] = 'Talks not found..'

        return self.response

    def get_talk_by_permalink(self, permalink):
        self.response['data'] = self.collection.find_one(
                {'permalink': permalink})

        return self.response

    def get_talk_by_id(self, talk_id):
        self.response['error'] = None
        try:
            self.response['data'] = self.collection.find_one(
                {'_id': ObjectId(talk_id)})
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
            self.response['error'] = 'Talk not found..'

        return self.response

    def get_total_count(self, tag=None, search=None):
        cond = {}
        if tag is not None:
            cond = {'tags': tag}
        elif search is not None:
            cond = {'$or': [
                    {'name': {'$regex': search, '$options': 'i'}},
                    {'summary': {'$regex': search, '$options': 'i'}},
                    {'description': {'$regex': search, '$options': 'i'}},
                    {'speaker': {'$regex': search, '$options': 'i'}}]}

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

    def create_new_talk(self, post_data):
        self.response['error'] = None
        try:
            self.response['data'] = self.collection.insert(post_data)
        except Exception, e:
            self.print_debug_info(e, self.debug_mode)
            self.response['error'] = 'Adding talk error..'

        return self.response

    def edit_talk(self, talk_id, talk_data):
        self.response['error'] = None
        del talk_data['permalink']
        talk_data = self.generate_permalink(talk_data)

        talk_participants = self.get_talk_by_id(talk_id)
        talk_participants_ = talk_participants['data']['participants']


        try:
            record = {'name': talk_data['name'],
                      'summary': talk_data['summary'],
                      'description': talk_data['description'],
                      'date': talk_data['date'],
                      'start': talk_data['start'],
                      'end': talk_data['end'],
                      'room': talk_data['room'],
                      'speaker': talk_data['speaker'],
                      'permalink': talk_data['permalink'],
                      'tags': talk_data['tags'],
                      'participants': talk_participants_}

            self.collection.update(
                {'_id': ObjectId(talk_id)}, {'$set': record}, upsert=False, multi=False)

            self.response['data'] = True
        except Exception, e:
            self.print_debug_info(e, self.debug_mode)
            self.response['error'] = 'Talk update error..'

        return self.response

    def delete_talk(self, talk_id):
        self.response['error'] = None
        try:
            if self.get_talk_by_id(talk_id) and self.collection.remove({'_id': ObjectId(talk_id)}):
                self.response['data'] = True

            else:
                self.response['data'] = False
        except Exception, e:
            self.print_debug_info(e, self.debug_mode)
            self.response['error'] = 'Deleting talk error..'

        return self.response



    @staticmethod
    def validate_talk_data(talk_data):

        talk_data['name'] = cgi.escape(talk_data['name'])
        talk_data['summary'] = cgi.escape(talk_data['summary'], quote=True)
        talk_data['description'] = cgi.escape(talk_data['description'], quote=True)
        talk_data['date'] = cgi.escape(talk_data['date'], quote=True)
        talk_data['start'] = cgi.escape(talk_data['start'], quote=True)
        talk_data['end'] = cgi.escape(talk_data['end'], quote=True)
        talk_data['room'] = cgi.escape(talk_data['room'], quote=True)


        return talk_data

    def generate_permalink(self, talk_data):
        cond = {'name': talk_data['name']}
        talks_samename = self.collection.find(cond).count()

        name_without_spaces=talk_data['name'].replace(" ", "_")
        name_lower_without_spaces = name_without_spaces.lower()

        if talks_samename == 0:
            permalink = name_lower_without_spaces
        else:
            newpermalink = talks_samename + 1
            permalink = name_lower_without_spaces + '-' + str(newpermalink)

        talk_data['permalink'] = permalink
        return talk_data


    def add_new_participant(self, permalink, username_participant):
        self.response['data'] = self.collection.find_one(
                     {'permalink': permalink})

        talk_participants = self.response['data']['participants']
        talk_participants.append(username_participant)

        new_talk = self.response['data']

        talk_name = new_talk['name']
        talk_summary = new_talk['summary']
        talk_description = new_talk['description']
        talk_speaker = new_talk['speaker']
        talk_permalink = new_talk['permalink']
        talk_room = new_talk['room']
        talk_date = new_talk['date']
        talk_start = new_talk['start']
        talk_end = new_talk['end']
        talk_tags = new_talk['tags']

        self.collection.update({'permalink': permalink},
                               {'name': talk_name, 'summary': talk_summary,
                                'description': talk_description, 'speaker': talk_speaker,
                                'permalink': talk_permalink, 'venue': talk_room,
                                'date': talk_date,'start': talk_start, 'end': talk_end,
                                'participants': talk_participants, 'tags': talk_tags
                                })



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
