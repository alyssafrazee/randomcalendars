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
from random import shuffle, sample
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
ta_names = ['Leonardo', 'Jean-Phillipe', 'Yao', 'Nicole', 'Amanda', 'Tom',
 'Therri', 'Yenny', 'Julia', 'Jeongyong', 'Yuting', 'Brian', 'Htet', 'Jonathan']
new_TAs = ['Therri', 'Jean-Phillipe', 'Julia', 'Brian', 'Yao', 'Htet', 'Yuting', 'Jonathan', 'Nicole']
experienced_TAs = ['Leonardo', 'Jeongyong', 'Tom', 'Yenny', 'Amanda']

# set up the office hour blocks (this setup will generate one sample week)
# TODO - figure out how to parse arguments (when entered in readable way)
# (web app coming soon!)

year = 2013
months = [9, 10]
days_in_months = dict.fromkeys(months)
days_in_months[9] = range(5,31)
days_in_months[10] = range(1,25)
times = [((12,15),(13,15)),((14,30),(15,20))] #12:15-1:15 and 2:30-3:20
double_days = [(9,16),(9,18),(9,19),(9,23),(10,9),(10,10),(10,14),(10,21),(10,22),(10,23)]
new_exp_pair_days = [(9,5),(9,6),(9,9),(9,10),(9,11),(9,12)]
days_off = [(9,24),(9,25),(10,24)]

# here is where conflicts go: no conflicts yet
ta_info = dict.fromkeys(ta_names)
for k in ta_info.keys():
   ta_info[k] = {'conflicts': [], 'calendar': None, 'color': str(ta_names.index(k))}

# ta_info['Lorenzo']['conflicts'].append(datetime(month=12, day=10, year=year))
# ta_info['Lorenzo']['conflicts'].append(datetime(month=12, day=14, year=year))
# ta_info['Gene']['conflicts'].append(datetime(month=12, day=13, year=year))
# ta_info['Joan']['conflicts'].append(datetime(month=12, day=12, year=year))


# function to check availability:
def available(ta_info, assigned_TA, slot):
  """slot is tuple of 2 datetime objects, 
  one for slot start and one for slot end"""
  for conflict in ta_info[assigned_TA]['conflicts']:
    if conflict.month == slot[0].month and conflict.day == slot[0].day:
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
        raise ValueError('no TAs are available for the office hour on '+str(slot[0]))
      pop_ind += 1
    ta_names_shuffled = checked_TAs+ta_names_shuffled

    assigned_TAs.append(assigned_TA)
    # make sure same TA doesn't get assigned to the same day again:
    ta_info[assigned_TA]['conflicts'].append(datetime(month=slot[0].month, day=slot[0].day, year=year))

  assert len(event_times)==len(assigned_TAs),'number of assigned TAs was not equal to number of office hours'
  
  # assign TAs to grade quizzes, if needed:
  if grade_quizzes:
    graders = sample(ta_info.keys(), 4)
    print 'quiz graders:'
    print '-- quiz 1:',graders[0]+', '+graders[1]
    print '-- quiz 2:',graders[2]+', '+graders[3]

  return assigned_TAs



## main function that will get called when the script is run
def generate_calendars(argv, 
  ta_names, 
  ta_info, 
  year, 
  months, 
  days_in_months, 
  times, 
  double_days,
  new_exp_pair_days):


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

      recordfile.write(created_event['id']+'\t'+ta_info[TA]['calendar']['id']+'\t'
        +str(start_dt)+'\t'+TA+'\n')
      i += 1

    # pair up the new and experienced TAs in early office hours:
    pair_times = []
    for month, day in new_exp_pair_days:
      for time in times:
        start, end = time
        start_hour, start_minute = start
        end_hour, end_minute = end
        start_dt = datetime(month=month, day=day, year=year, hour=start_hour, minute=start_minute)
        end_dt = datetime(month=month, day=day, year=year, hour=end_hour, minute=end_minute)
        pair_times.append((start_dt, end_dt))

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
    print ("The credentials have been revoked or expired, please re-run "
      "the application to re-authorize")


##########################
###### do it to it! ######
##########################

if __name__ == '__main__':
  generate_calendars(sys.argv, ta_names, ta_info, year, months, days_in_months, times, double_days, new_exp_pair_days)



