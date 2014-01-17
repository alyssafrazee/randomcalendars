## attempting to use the Google Calendar API to improve Hilary's 
## randomly-generated TA calendars for the 620s series

## AF 5 August 2013

#######################
###### API SETUP ######
#######################

# much of this comes directly from sample.py
# download link: https://developers.google.com/api-client-library/python/start/installation
#(for reference)

# setup proper libraries (in virtualenv)
import gflags
import httplib2
import logging
import os
import pprint
import sys

from apiclient.discovery import build
from oauth2client.file import Storage
from oauth2client.client import AccessTokenRefreshError
from oauth2client.client import flow_from_clientsecrets
from oauth2client.tools import run
from datetime import datetime
from random import shuffle, sample, choice
from copy import deepcopy

FLAGS = gflags.FLAGS
# need this file to authenticate your stuff
# CLIENT_SECRETS = 'client_secrets_af.json' ## for alyssa.frazee@gmail.com
CLIENT_SECRETS = 'client_secrets.json' ## for biostat.620s.TAs@gmail.com

# Helpful message to display if the CLIENT_SECRETS file is missing.
MISSING_CLIENT_SECRETS_MESSAGE = """
WARNING: Please configure OAuth 2.0

To make this sample run you will need to download the client_secrets.json file
and save it at:

   %s

""" % os.path.join(os.path.dirname(__file__), CLIENT_SECRETS)

# to use for authentication
FLOW = flow_from_clientsecrets(CLIENT_SECRETS,
  scope=[
      'https://www.googleapis.com/auth/calendar',
      'https://www.googleapis.com/auth/calendar.readonly',
    ],
    message=MISSING_CLIENT_SECRETS_MESSAGE)


# command-line arguments
gflags.DEFINE_enum('logging_level', 'ERROR',
    ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
    'Set the level of logging detail.')

###########################
###### end API setup ######
###########################

###############################
###### TA calendar setup ######
###############################
timeZone = "US/Eastern"

# for testing the code:
# ta_names = ['Lorenzo', 'Gene', 'Don', 'Joan', 'Theo', 'Nikki',
#  'Aaliyah', 'Tim', 'Terry', 'Jenny', 'Jess', 'Melissa', 'Maya']

# for real:
######## FIRST TERM
# ta_names = ['Leonardo', 'Jean-Phillipe', 'Yao', 'Nicole', 'Amanda', 'Tom',
#  'Therri', 'Yenny', 'Julia', 'Jeongyong', 'Yuting', 'Brian', 'Htet', 'Jonathan']
# new_TAs = ['Therri', 'Jean-Phillipe', 'Julia', 'Brian', 'Yao', 'Htet', 'Yuting', 'Jonathan', 'Nicole']
# experienced_TAs = ['Leonardo', 'Jeongyong', 'Tom', 'Yenny', 'Amanda']

######## SECOND TERM
# ta_names = ['Leonardo', 'Jean-Philippe', 'Yao', 'Nicole', 'Amanda', 
#     'Tom', 'Therri', 'Yenny', 'Julia', 'Jeongyong', 'Cheryl', 'Brian',
#     'Htet', 'Jonathan', 'Yi']

######## THIRD TERM
ta_names = ["Stephen", "Caroline", "Jean-Philippe", "Fang", "Emily", "Rayman",
    "Dan", "David", "Yao", "Yi", "Prasad", "Brian", "Shuo", "Juemin", "Chen",
    "Shilu", "Cheryl", "James"]
new_TAs = ["Stephen", "Caroline", "Fang", "Emily", "Dan", "David", "Prasad",
    "James", "Shuo", "Chen", "Shilu"]
experienced_TAs = ["Jean-Philippe", "Rayman", "Yao", "Yi", "Brian", "Juemin", "Cheryl"]

# set up the office hour blocks (this setup will generate one sample week)
# TODO - figure out how to parse arguments (when entered in readable way)
# (web app coming soon!)

year = 2014
months = [1, 2, 3]
days_in_months = dict.fromkeys(months)
days_in_months[1] = range(22, 32)
days_in_months[2] = range(1, 29)
days_in_months[3] = range(1, 13)
times = [((12,15),(13,15)),((14,30),(15,20))] #12:15-1:15 and 2:30-3:20
double_days = [(2,3),(2,4),(2,5),(2,6),(2,12),(2,13),(2,17),(2,26),(2,27),(3,3),(3,4),(3,10),(3,11),(3,12)]
new_exp_pair_days = [(1,22),(1,23),(1,24),(1,27),(1,28)]
days_off = [(2,18), (2,19)] 

# TA information
ta_info = dict.fromkeys(ta_names)
for k in ta_info.keys():
    ta_info[k] = {'conflicts': [], 'calendar': None, 'color': str(ta_names.index(k))}

# incorporate each TA's conflicts:
##### first create event_times (this is done, more complicatedly, inside the main function)
from datetime import datetime
event_times = []
for month in months:
    for day in days_in_months[month]:
        wd = datetime(month=month, day=day, year=year)
        if wd.weekday() in range(0,5) and (month, day) not in days_off:
            for time in times:
                start, end = time
                start_hour, start_minute = start
                start_dt = datetime(month=month, day=day, year=year, hour=start_hour, minute=start_minute)
                event_times.append(start_dt)

# David: no Monday/Wednesday/Friday
# Emily: no Mondays 12:15, Tuesdays 12:15, Friday 12:15
######## no Mondays 2:00, Fridays 2:00
# Prasad: no Monday noon or Friday
# Yao: no Monday/Wednesday
# Fang: no Wednesday/Thursday
# Brian: No Wednesday/Friday noon, no Tuesdays/Thursdays pm. 
# Rayman: No Monday, Thursday 2pm, Wednesday, Friday 2pm
# Chen: no Wednesday
# Juemin: no MWF
# Cheryl: no MWF 2pm
# Carrie: no wed 12pm

for slot in event_times:
    if slot.weekday() == 0:
        ## Mondays
        ta_info['David']['conflicts'].append(slot)
        ta_info['Emily']['conflicts'].append(slot)
        ta_info['Yao']['conflicts'].append(slot)
        ta_info['Rayman']['conflicts'].append(slot)
        ta_info['Juemin']['conflicts'].append(slot)
        if slot.hour == 12:
            ta_info['Prasad']['conflicts'].append(slot)
        elif slot.hour == 14:
            ta_info['Cheryl']['conflicts'].append(slot)
    elif slot.weekday() == 1:
        ## Tuesdays
        if slot.hour == 12:
            ta_info['Emily']['conflicts'].append(slot)
        elif slot.hour == 14:
            ta_info['Brian']['conflicts'].append(slot)
    elif slot.weekday() == 2:
        ## Wednesdays
        ta_info['David']['conflicts'].append(slot)
        ta_info['Yao']['conflicts'].append(slot)
        ta_info['Fang']['conflicts'].append(slot)
        ta_info['Brian']['conflicts'].append(slot)
        ta_info['Juemin']['conflicts'].append(slot)
        ta_info['Chen']['conflicts'].append(slot)
        if slot.hour == 12:
            ta_info['Brian']['conflicts'].append(slot)
            ta_info['Caroline']['conflicts'].append(slot)
        elif slot.hour == 14:
            ta_info['Cheryl']['conflicts'].append(slot)
    elif slot.weekday() == 3:
        ## Thursdays
        ta_info['Fang']['conflicts'].append(slot)
        if slot.hour == 14:
            ta_info['Brian']['conflicts'].append(slot)
            ta_info['Rayman']['conflicts'].append(slot)
    elif slot.weekday() == 4:
        ## Fridays
        ta_info['David']['conflicts'].append(slot)
        ta_info['Emily']['conflicts'].append(slot)
        ta_info['Prasad']['conflicts'].append(slot)
        ta_info['Juemin']['conflicts'].append(slot)
        if slot.hour == 12:
            ta_info['Brian']['conflicts'].append(slot)
        if slot.hour == 14:
            ta_info['Rayman']['conflicts'].append(slot)
            ta_info['Cheryl']['conflicts'].append(slot)            


# function to check availability:
def available(ta_info, assigned_TA, slot):
    """slot is tuple of 2 datetime objects, 
    one for slot start and one for slot end"""
    for conflict in ta_info[assigned_TA]['conflicts']:
        if conflict.month == slot[0].month and conflict.day == slot[0].day and conflict.hour == slot[0].hour:
            return False
    return True


# function to assign TA's to slots
# TODO: optimize for no errors
def assign_TAs(ta_info, event_times, grade_quizzes):
    ta_names_shuffled = ta_info.keys()
    shuffle(ta_names_shuffled)
    assigned_TAs = []
    for slot in event_times:

        if not ta_names_shuffled:
        # we have reached the end of the TA "deck" and need to re-shuffle
            ta_names_shuffled = ta_info.keys()
            shuffle(ta_names_shuffled)

        assigned_TA = ta_names_shuffled.pop(0)

        # confirm availability:
        pop_ind = 1
        checked_TAs = []
        while not available(ta_info, assigned_TA, slot):
            checked_TAs.append(assigned_TA)
            if pop_ind < len(ta_names_shuffled):
                assigned_TA = ta_names_shuffled.pop(pop_ind)
            else:
                if(len(checked_TAs) == len(ta_info.keys())):
                    raise ValueError("nobody is available for the office hour on "+str(slot[0]))
                assigned_TA = choice(ta_info.keys())
            pop_ind += 1
        ta_names_shuffled = checked_TAs+ta_names_shuffled

        assigned_TAs.append(assigned_TA)
        # make sure same TA doesn't get assigned to the same day again:
        ### TODO fix so that this doesn't depend on 12 and 14 as the possible hours
        ta_info[assigned_TA]['conflicts'].append(datetime(month=slot[0].month, day=slot[0].day, year=year, hour=12))
        ta_info[assigned_TA]['conflicts'].append(datetime(month=slot[0].month, day=slot[0].day, year=year, hour=14))

    assert len(event_times)==len(assigned_TAs),'number of assigned TAs was not equal to number of office hours'
  
    # assign TAs to grade quizzes, if needed:
    if grade_quizzes:
        graders = sample(ta_info.keys(), 4)
        print 'quiz graders:'
        print '-- quiz 1:',graders[0]+', '+graders[1]
        print '-- quiz 2:',graders[2]+', '+graders[3]

    return assigned_TAs



## main function that will get called when the script is run
def generate_calendars(argv, ta_names, ta_info, year, 
  months, days_in_months, times, double_days):

  # Let the gflags module process the command-line arguments
    try:
        argv = FLAGS(argv)
    except gflags.FlagsError, e:
        print '%s\\nUsage: %s ARGS\\n%s' % (e, argv[0], FLAGS)
        sys.exit(1)

    # Set the logging according to the command-line flag
    logging.getLogger().setLevel(getattr(logging, FLAGS.logging_level))

    # If the Credentials don't exist or are invalid, run through the native
    # client flow. The Storage object will ensure that if successful the good
    # Credentials will get written back to a file.
    storage = Storage('sample.dat')
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        credentials = run(FLOW, storage)

    # Create an httplib2.Http object to handle our HTTP requests and authorize it
    # with our good Credentials.
    http = httplib2.Http()
    http = credentials.authorize(http)

    # make the calendar
    service = build('calendar', 'v3', http=http)

    # here's where the magic happens
    try:
        print "authentication successful"

        # create office hour slots
        event_times = []
        for month in months:
            for day in days_in_months[month]:
                wd = datetime(month=month, day=day, year=year)
                if wd.weekday() in range(0,5) and (month, day) not in days_off:
                    for time in times:
                        start, end = time
                        start_hour, start_minute = start
                        end_hour, end_minute = end
                        start_dt = datetime(month=month, day=day, year=year, hour=start_hour, minute=start_minute)
                        end_dt = datetime(month=month, day=day, year=year, hour=end_hour, minute=end_minute)
                        event_times.append((start_dt, end_dt))
                        if (month, day) in double_days:
                            event_times.append((start_dt, end_dt)) #append another slot to be filled

        print event_times

        # check to make sure each TA has a calendar
        # the API can only create 24 calendars in a short time,
        # so calendars probably need to be created beforehand.
        # note: next block of code is directly from the example for the CalendarList 'list' method
        my_calendars = []
        page_token = None
        while True:
            calendar_list = service.calendarList().list(pageToken=page_token).execute()
            for calendar_list_entry in calendar_list['items']:
                my_calendars.append(calendar_list_entry)
            page_token = calendar_list.get('nextPageToken')
            if not page_token:
                break

        # put each TA's calendar in the ta_info dict
        my_calendars_names = [x['summary'] for x in my_calendars]
        for TA in ta_names:
            if TA not in my_calendars_names:
                calendar = {'summary': TA, 'timeZone': timeZone, 'colorId': str(ta_names.index(TA))}
                try:
                    created_calendar = service.calendars().insert(body=calendar).execute()
                    ta_info[TA]['calendar'] = created_calendar
                except apiclient.errors.HttpError:
                    msg = TA+' does not have a calendar, and the API has exceeded its calendar creation limits. Please make a calendar for '+TA+' and re-run the script.'
                    raise HttpError(msg)
            else:
                ta_info[TA]['calendar'] = my_calendars[my_calendars_names.index(TA)]

        # assign a TA to each office hour
        ta_assignments = assign_TAs(ta_info=ta_info, event_times=event_times, grade_quizzes=True)

        # add these office hours to the right calendar
        recordfile = open('office_hour_ids','w')
        recordfile.write('event_id'+'\t'+'calendar_id'+'\t'+'start_time'+'\t'+'assigned_TA'+'\n')
        i = 0
        for slot in event_times:
            start_dt, end_dt = slot
            TA = ta_assignments[i]
            event = {
                'summary': TA,
                'start':{
                    'dateTime': start_dt.isoformat(),
                    'timeZone': timeZone
                },
                'end':{
                    'dateTime': end_dt.isoformat(),
                    'timeZone': timeZone
                },
            }
            created_event = service.events().insert(calendarId=ta_info[TA]['calendar']['id'], body=event).execute()
            #created_event = service.events().insert(calendarId='primary', body=event).execute()

            recordfile.write(created_event['id']+'\t'+ta_info[TA]['calendar']['id']+'\t'+str(start_dt)+'\t'+TA+'\n')
            i += 1

#   pair up the new and experienced TAs in early office hours:
    #### FIRST AND THIRD TERMS ONLY
        pair_times = []
        for month, day in new_exp_pair_days:
            for time in times:
                start, end = time
                start_hour, start_minute = start
                end_hour, end_minute = end
                start_dt = datetime(month=month, day=day, year=year, hour=start_hour, minute=start_minute)
                end_dt = datetime(month=month, day=day, year=year, hour=end_hour, minute=end_minute)
                pair_times.append((start_dt, end_dt))

        print 'pair times:'
        print pair_times

        new_TAs_shuffled = deepcopy(new_TAs)
        shuffle(new_TAs_shuffled)
        experienced_TAs_shuffled = deepcopy(experienced_TAs)
        shuffle(experienced_TAs_shuffled)
    
        for slot in pair_times:
            current_TA = ta_assignments[event_times.index(slot)]
            experienced = current_TA in experienced_TAs
            if not new_TAs_shuffled: #we've run out.
                new_TAs_shuffled = deepcopy(new_TAs)
                shuffle(new_TAs_shuffled)
            if not experienced_TAs_shuffled:
                experienced_TAs_shuffled = deepcopy(experienced_TAs)
                shuffle(experienced_TAs_shuffled)
            if experienced:
                paired_TA = new_TAs_shuffled.pop(0)
            else:
                paired_TA = experienced_TAs_shuffled.pop(0)
            pop_ind = 1
            checked_TAs = []
            while not available(ta_info, paired_TA, slot):
                checked_TAs.append(paired_TA)
                if experienced:
                    if pop_ind < len(new_TAs_shuffled):
                        paired_TA = new_TAs_shuffled.pop(pop_ind)
                    else:
                        if len(checked_TAs) == len(new_TAs):
                            raise ValueError("no new TAs are available for the office hour on "+str(slot[0]))
                        else:    
                            paired_TA = choice(new_TAs)
                    pop_ind += 1
                else:
                    if pop_ind < len(experienced_TAs_shuffled):
                        paired_TA = experienced_TAs_shuffled.pop(pop_ind)
                    else:
                        if len(checked_TAs) == len(experienced_TAs):
                            raise ValueError('no experienced TAs are available for the office hour on '+str(slot[0]))
                        else:
                            paired_TA = choice(experienced_TAs)
                    pop_ind += 1
            if experienced:
                new_TAs_shuffled = checked_TAs+new_TAs_shuffled
            else:
                experienced_TAs_shuffled = checked_TAs+experienced_TAs_shuffled
            event = {
            'summary': paired_TA,
            'start':{
                'dateTime': slot[0].isoformat(),
                'timeZone': timeZone
            },
            'end':{
                'dateTime': slot[1].isoformat(),
                'timeZone': timeZone
            },
            }
            created_event = service.events().insert(calendarId=ta_info[paired_TA]['calendar']['id'], body=event).execute()
            recordfile.write(created_event['id']+'\t'+ta_info[TA]['calendar']['id']+'\t'+str(slot[0])+'\t'+paired_TA+'\n')
        
        recordfile.close()


    except AccessTokenRefreshError:
        print ("The credentials have been revoked or expired, please re-run the application to re-authorize")


##########################
###### do it to it! ######
##########################

if __name__ == '__main__':
  generate_calendars(sys.argv, ta_names, ta_info, year, months, days_in_months, times, double_days)


## to do: clean this code. refactor this code. fix leaky scope (e.g., new_exp_pair_days), etc.

