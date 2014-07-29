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
                    {'summary': {'$regex': search, '$options': 'i'}},
                    {'description': {'$regex': search, '$options': 'i'}},
                    {'organizer': {'$regex': search, '$options': 'i'}}]}

        try:
            cursor = self.collection.find(cond).sort(
                'date', direction=-1).skip(skip).limit(limit)
            self.response['data'] = []
            for event in cursor:
                if 'tags' not in event:
                    event['tags'] = []
                if 'talks' not in event:
                    event['talks'] = []
                if 'participants' not in event:
                    event['participants'] = []

                self.response['data'].append({'id': event['_id'],
                                              'name': event['name'],
                                              'summary': event['summary'],
                                              'description': event['description'],
                                              'start': event['start'],
                                              'end': event['end'],
                                              'venue': event['venue'],
                                              'permalink': event['permalink'],
                                              'organizer': event['organizer'],
                                              'tags': event['tags'],
                                              'talks': event['talks'],
                                              'participants': event['participants'],
                                              'attendance': len(event['participants'])
                })
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


    def events_by_role(self, user_id):
        list_attendee = []

        events_attendee = []
        events_organizer = []

        try:
            cursor = self.collection.find()

            for event in cursor:
                if 'talks' not in event:
                    event['talks'] = []
                if 'participants' not in event:
                    event['participants'] = []
                else:
                    if user_id in event['participants']:
                        events_attendee.append({'permalink': event['permalink'],
                                                'talks': event['talks'],
                                                'participants': event['participants']
                                                })

                    if user_id == event['organizer']:
                        events_organizer.append(str(event['permalink']))

        except Exception, e:
            self.print_debug_info(e, self.debug_mode)


        return events_attendee, events_organizer

    def events_by_user_attendee2(self, user_id):
        list_attendee = []

        cursor = self.collection.find()
        for event in cursor:
            if user_id in event['participants']:
                list_attendee.append(event['permalink'])


        return list_attendee



    def get_total_count(self, tag=None, search=None):
        cond = {}
        if tag is not None:
            cond = {'tags': tag}
        elif search is not None:
            cond = {'$or': [
                    {'name': {'$regex': search, '$options': 'i'}},
                    {'summary': {'$regex': search, '$options': 'i'}},
                    {'description': {'$regex': search, '$options': 'i'}},
                    {'organizer': {'$regex': search, '$options': 'i'}}]}

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

    def add_new_talk(self, permalink, talk):
        self.response['data'] = self.collection.find_one(
                     {'permalink': permalink})

        event_talks = self.response['data']['talks']
        event_talks.append(talk['permalink'])

        new_event = self.response['data']

        event_name = new_event['name']
        event_summary = new_event['summary']
        event_description = new_event['description']
        event_organizer = new_event['organizer']
        event_permalink = new_event['permalink']
        event_venue = new_event['venue']
        event_start = new_event['start']
        event_end = new_event['end']
        event_participants = new_event['participants']
        event_tags = new_event['tags']

        self.collection.update({'permalink': permalink},
                               {'name': event_name, 'summary': event_summary,
                                'description': event_description, 'organizer': event_organizer,
                                'permalink': event_permalink, 'venue': event_venue,
                                'start': event_start, 'end': event_end,
                                'participants': event_participants, 'tags': event_tags,
                                'talks': event_talks
                                })

    def add_new_participant(self, permalink, username_participant):
        self.response['data'] = self.collection.find_one(
                     {'permalink': permalink})

        event_participants = self.response['data']['participants']
        event_participants.append(username_participant)

        new_event = self.response['data']

        event_name = new_event['name']
        event_summary = new_event['summary']
        event_description = new_event['description']
        event_organizer = new_event['organizer']
        event_permalink = new_event['permalink']
        event_venue = new_event['venue']
        event_start = new_event['start']
        event_end = new_event['end']
        event_talks = new_event['talks']
        event_tags = new_event['tags']

        self.collection.update({'permalink': permalink},
                               {'name': event_name, 'summary': event_summary,
                                'description': event_description, 'organizer': event_organizer,
                                'permalink': event_permalink, 'venue': event_venue,
                                'start': event_start, 'end': event_end,
                                'participants': event_participants, 'tags': event_tags,
                                'talks': event_talks
                                })

    def modify_talks_event(self, permalink, talks):
        self.response['data'] = self.collection.find_one(
                     {'permalink': permalink})
        new_event = self.response['data']

        event_name = new_event['name']
        event_summary = new_event['summary']
        event_description = new_event['description']
        event_organizer = new_event['organizer']
        event_permalink = new_event['permalink']
        event_venue = new_event['venue']
        event_start = new_event['start']
        event_end = new_event['end']
        event_participants = new_event['participants']
        event_tags = new_event['tags']
        event_talks = talks

        self.collection.update({'permalink': permalink},
                               {'name': event_name, 'summary': event_summary,
                                'description': event_description, 'organizer': event_organizer,
                                'permalink': event_permalink, 'venue': event_venue,
                                'start': event_start, 'end': event_end,
                                'participants': event_participants, 'tags': event_tags,
                                'talks': event_talks
                                })

    def edit_event(self, event_id, event_data):
        self.response['error'] = None
        del event_data['permalink']
        event_data = self.generate_permalink(event_data)


        try:
            self.collection.update(
                {'_id': ObjectId(event_id)}, {"$set": event_data}, upsert=False)
            self.response['data'] = True
        except Exception, e:
            self.print_debug_info(e, self.debug_mode)
            self.response['error'] = 'Event update error..'

        return self.response

    def delete_event(self, event_id):
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

        event_data['name'] = cgi.escape(event_data['name'])
        event_data['summary'] = cgi.escape(event_data['summary'], quote=True)
        event_data['description'] = cgi.escape(event_data['description'], quote=True)
        event_data['start'] = cgi.escape(event_data['start'], quote=True)
        event_data['end'] = cgi.escape(event_data['end'], quote=True)
        event_data['venue'] = cgi.escape(event_data['venue'], quote=True)

        return event_data

    def generate_permalink(self, event_data):
        cond = {'name': event_data['name']}
        events_samename = self.collection.find(cond).count()

        name_without_spaces=event_data['name'].replace(" ", "_")
        name_lower_without_spaces = name_without_spaces.lower()

        if events_samename == 0:
            permalink = name_lower_without_spaces
        else:
            newpermalink = events_samename + 1
            permalink = name_lower_without_spaces + '-' + str(newpermalink)

        event_data['permalink'] = permalink
        return event_data

    def get_talks_by_event(self, permalink):

        self.response['data'] = self.collection.find_one(
                {'permalink': permalink})


        talks = self.response['data']['talks']

        return talks


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
