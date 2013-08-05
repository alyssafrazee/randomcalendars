## attempting to use the Google Calendar API to improve Hilary's 
## randomly-generated TA calendars for the 620s series

## AF 5 August 2013

#######################
###### API SETUP ######
#######################

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
from random import shuffle, randint
from time import sleep

FLAGS = gflags.FLAGS
# need this file to authenticate your stuff
CLIENT_SECRETS = 'client_secrets.json'

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

ta_names = ['Lorenzo', 'Gene', 'Don', 'Joan', 'Theo', 'Nikki',
 'Aaliyah', 'Tim', 'Terry', 'Jenny', 'Jess', 'Melissa', 'Maya']

# set up the office hour blocks (this setup will generate one sample week)
# TODO - figure out how to parse arguments (when entered in readable way)
year = 2012
months = [12]
days = range(10, 15)
times = [((12,15),(13,15)),((14,30),(15,20))] #12:15-1:15 and 2:30-3:20
double_days = [(12, 10)]

# I am making up some dates that TA's are not available
ta_info = dict.fromkeys(ta_names)
for k in ta_info.keys():
  ta_info[k] = {'conflicts': [], 'calendar': None, 'color': str(randint(1,11))}
ta_info['Lorenzo']['conflicts'].append(datetime(month=12, day=10, year=year))
ta_info['Lorenzo']['conflicts'].append(datetime(month=12, day=14, year=year))
ta_info['Gene']['conflicts'].append(datetime(month=12, day=13, year=year))
ta_info['Joan']['conflicts'].append(datetime(month=12, day=12, year=year))

# TODO: set color palette, either for calendar or for events.

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
def assign_TAs(ta_info, event_times):
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

  assert len(event_times)==len(assigned_TAs),'number of assigned TAs was not equal to number of office hours'
  return assigned_TAs


## main function that will get called when the script is run
def generate_calendars(argv, 
  ta_names, 
  ta_info, 
  year, 
  months, 
  days, 
  times, 
  double_days):


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
      for day in days:
        for time in times:
          start, end = time
          start_hour, start_minute = start
          end_hour, end_minute = end
          start_dt = datetime(month=month, day=day, year=year, hour=start_hour, minute=start_minute)
          end_dt = datetime(month=month, day=day, year=year, hour=end_hour, minute=end_minute)
          event_times.append((start_dt, end_dt))
          if (month, day) in double_days:
            event_times.append((start_dt, end_dt)) #append another slot to be filled

    # create calendar for each TA -- THIS EXCEEDS THE API LIMITS so just don't do it
    #print 'creating calendars'
    #for TA in ta_names:
    #  sleep(2)
    #  calendar = {'summary': TA, 'timeZone': timeZone}
    #  created_calendar = service.calendars().insert(body=calendar).execute()
    #  ta_info[TA]['calendar'] = created_calendar

    # assign a TA to each office hour
    print 'assigning TAs'
    ta_assignments = assign_TAs(ta_info, event_times)

    # add these office hours to the right calendar
    print 'adding calendar events'
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
      'colorId': ta_info[TA]['color']
      }
      #created_event = service.events().insert(calendarId=ta_info[TA]['calendar']['id'], body=event).execute()
      created_event = service.events().insert(calendarId='primary', body=event).execute()      
      i += 1

  except AccessTokenRefreshError:
    print ("The credentials have been revoked or expired, please re-run"
      "the application to re-authorize")


##########################
###### do it to it! ######
##########################

if __name__ == '__main__':
  generate_calendars(sys.argv, ta_names, ta_info, year, months, days, times, double_days)


