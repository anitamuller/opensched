import base64
import cgi
from bson.objectid import ObjectId
from helper_functions import *


class Event:

    def __init__(self, default_config):
        self.collection = default_config['EVENTS_COLLECTION']
        self.response = {'error': None, 'data': None}
        self.debug_mode = default_config['DEBUG']

    def get_events(self, limit, skip, organizer=None, tag=None, search=None):
        self.response['error'] = None
        cond = {}
        if tag is not None:
            cond = {'tags': tag}
        elif organizer is not None:
            cond = {'organizer': organizer}
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
                if 'attendees' not in event:
                    event['attendees'] = []

                self.response['data'].append({'id': event['_id'],
                                              'name': event['name'],
                                              'summary': base64.b64decode(event['summary']),
                                              'description': base64.b64decode(event['description']),
                                              'start': date_to_string(event['start'], 'short'),
                                              'end': date_to_string(event['end'], 'short'),
                                              'venue': event['venue'],
                                              'permalink': event['permalink'],
                                              'organizer': event['organizer'],
                                              'tags': event['tags'],
                                              'talks': event['talks'],
                                              'attendees': event['attendees'],
                                              'attendance': len(event['attendees'])
                })
        except Exception, e:
            self.print_debug_info(e, self.debug_mode)
            self.response['error'] = 'Events not found..'

        return self.response

    def get_attendees(self):
        attendees = []
        try:
            cursor = self.collection.find()
            for event in cursor:
                list_attendees = event['attendees']
                for attendee in list_attendees:
                    if not attendee in attendees:
                        attendees.append(attendee)

        except Exception, e:
            self.print_debug_info(e, self.debug_mode)
        return attendees

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

    def events_organized_by(self, user_email):
        try:
            cursor = self.collection.find(
                {'organizer': user_email})

            self.response['data'] = []
            for event in cursor:
                self.response['data'].append({'id': event['_id'],
                                              'name': event['name'],
                                              'summary': base64.b64decode(event['summary']),
                                              'description': base64.b64decode(event['description']),
                                              'start': date_to_string(event['start'], 'short'),
                                              'end': date_to_string(event['end'], 'short'),
                                              'venue': event['venue'],
                                              'permalink': event['permalink'],
                                              'organizer': event['organizer'],
                                              'tags': event['tags'],
                                              'talks': event['talks'],
                                              'attendees': event['attendees'],
                                              'attendance': len(event['attendees'])
                })
        except Exception, e:
            self.print_debug_info(e, self.debug_mode)
            self.response['error'] = 'Event not found..'

        return self.response['data']

    def get_organizers(self):
        events_organizers = []
        try:
            cursor = self.collection.find()
            for event in cursor:
                if event['organizer'] not in events_organizers:
                    events_organizers.append(event['organizer'])
            return events_organizers
        except Exception, e:
            self.print_debug_info(e, self.debug_mode)

    def events_by_role(self, user_id):
        events_attendee = []

        try:
            cursor = self.collection.find()

            for event in cursor:
                if 'talks' not in event:
                    event['talks'] = []
                if 'attendees' not in event:
                    event['attendees'] = []
                else:
                    if user_id in event['attendees']:
                        events_attendee.append({'permalink': event['permalink'],
                                                'talks': event['talks'],
                                                'attendees': event['attendees']
                                                })

        except Exception, e:
            self.print_debug_info(e, self.debug_mode)

        return events_attendee

    def get_attendance_event(self, event_permalink):
        self.response['error'] = None
        try:
            self.response['data'] = self.collection.find_one(
                {'permalink': event_permalink})

        except Exception, e:
            self.print_debug_info(e, self.debug_mode)
            self.response['error'] = 'Event not found..'

        return self.response['data']['attendees']

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
        event_attendees = new_event['attendees']
        event_tags = new_event['tags']

        self.collection.update({'permalink': permalink}, {'name': event_name,
                                                          'summary': event_summary,
                                                          'description': event_description,
                                                          'organizer': event_organizer,
                                                          'permalink': event_permalink,
                                                          'venue': event_venue,
                                                          'start': event_start,
                                                          'end': event_end,
                                                          'attendees': event_attendees,
                                                          'tags': event_tags,
                                                          'talks': event_talks
        })

    def add_new_attendee(self, permalink, email_attendee):
        self.response['data'] = self.collection.find_one({'permalink': permalink})
        event_attendees = self.response['data']['attendees']

        if not email_attendee in event_attendees:
            event_attendees.append(email_attendee)

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

            self.collection.update({'permalink': permalink}, {'name': event_name,
                                                              'summary': event_summary,
                                                              'description': event_description,
                                                              'organizer': event_organizer,
                                                              'permalink': event_permalink,
                                                              'venue': event_venue,
                                                              'start': event_start,
                                                              'end': event_end,
                                                              'attendees': event_attendees,
                                                              'tags': event_tags,
                                                              'talks': event_talks
            })

    def modify_talks_event(self, permalink, talks):
        self.response['data'] = self.collection.find_one({'permalink': permalink})
        new_event = self.response['data']

        event_name = new_event['name']
        event_summary = new_event['summary']
        event_description = new_event['description']
        event_organizer = new_event['organizer']
        event_permalink = new_event['permalink']
        event_venue = new_event['venue']
        event_start = new_event['start']
        event_end = new_event['end']
        event_attendees = new_event['attendees']
        event_tags = new_event['tags']
        event_talks = talks

        self.collection.update({'permalink': permalink}, {'name': event_name,
                                                          'summary': event_summary,
                                                          'description': event_description,
                                                          'organizer': event_organizer,
                                                          'permalink': event_permalink,
                                                          'venue': event_venue,
                                                          'start': event_start,
                                                          'end': event_end,
                                                          'end': event_end,
                                                          'attendees': event_attendees,
                                                          'tags': event_tags,
                                                          'talks': event_talks
                                                          })
    def modify_attendees_event(self, permalink, attendees):
        self.response['data'] = self.collection.find_one({'permalink': permalink})
        new_event = self.response['data']

        event_name = new_event['name']
        event_summary = new_event['summary']
        event_description = new_event['description']
        event_organizer = new_event['organizer']
        event_permalink = new_event['permalink']
        event_venue = new_event['venue']
        event_start = new_event['start']
        event_end = new_event['end']
        event_tags = new_event['tags']
        event_talks = new_event['talks']
        event_attendees = attendees

        self.collection.update({'permalink': permalink}, {'name': event_name,
                                                          'summary': event_summary,
                                                          'description': event_description,
                                                          'organizer': event_organizer,
                                                          'permalink': event_permalink,
                                                          'venue': event_venue,
                                                          'start': event_start,
                                                          'end': event_end,
                                                          'end': event_end,
                                                          'attendees': event_attendees,
                                                          'tags': event_tags,
                                                          'talks': event_talks
                                                          })


    def edit_event(self, event_id, event_data):
        self.response['error'] = None

        event_name = event_data['name']
        name_without_spaces=event_name.replace(" ", "_")
        name_lower_without_spaces = name_without_spaces.lower()

        exist_event = self.collection.find_one({'_id': ObjectId(event_id)})
        exist_permalink = exist_event['permalink']

        if name_lower_without_spaces == exist_permalink:
            #the name didn't change, so permalink is the same
            event_data['permalink'] = exist_permalink
            try:
                self.collection.update(
                    {'_id': ObjectId(event_id)}, {"$set": event_data}, upsert=False)
                self.response['data'] = True
            except Exception, e:
                self.print_debug_info(e, self.debug_mode)
                self.response['error'] = 'Event update error..'

        else:
            del event_data['permalink']
            event_data = self.generate_permalink(event_data)

            try:
                self.collection.remove({'_id': ObjectId(event_id)})
                self.response['data'] = self.collection.insert(event_data)
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
