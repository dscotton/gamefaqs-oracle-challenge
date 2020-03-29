#!/usr/bin/python
#
# This script adds Oracle predictions to the oracle database.  Predictions
# come from message board posts.  Currently the message board topics are
# being saved to disc and fed into the program as files.
#
# This is a modified version of add_predictions.py for handling multiway
# polls.
#
# Copyright David Scotton, 2005-2007

import datetime
import getpass
import re
import sys

import oracle_db
import message_board

# Time difference (in minutes) between the user's GameFAQs timezone and
# Pacific time.  This was introduced to keep the database time consistent
# across contests.  0 for Pacific time, 180 for Eastern, etc.
# TIME_OFFSET = 1140
TIME_OFFSET = 0


def main():
  """This is the main prediction adding function.

  It starts by grabbing a file to open from standard in, which contains
  one message board page.  It processes each message contained in the page.

  NOTE: If there are multiple pages, they must be processed in order.
  However, after a page is complete (50 messages), it only needs to
  be processed once.

  """

  # db_user = raw_input('DB username: ')
  db_user = 'oraclech'
  pw = getpass.getpass()

  odb = oracle_db.OracleDb(db_user, pw, database='oraclech_new')

  contest_id = raw_input('Current Contest ID? ')
  round_num = raw_input('Current Round Number? ')
  round_nums = round_num.split(',')
  topic_num = raw_input('Current Topic Number? ')
  page_num = raw_input('Current Page Number? ')

  contest = odb.GetContest(contest_id)

  try:
    file_path = '%s/r%dt%dp%02d.html' % (contest['Name'].lower(),
                                         int(round_nums[-1]),
                                         int(topic_num),
                                         int(page_num))
    file_path = '/home/oraclech/topics/' + file_path
    print file_path
    file = open(file_path, 'r')
  except IOError:
    file_path = raw_input('File to open (in /home/oraclech/topics/): ')
    file_path = '/home/oraclech/topics/' + file_path
    file = open(file_path, 'r')
  page = file.read()
  parser = message_board.Parser()
  messages = parser.Parse(page)

  for message in messages:
    message['Timestamp'] -= datetime.timedelta(minutes=TIME_OFFSET)
    ParsePredictions(odb, message, contest, round_nums)

  odb.Commit()

def ParsePredictions(odb, message, contest, round_nums):
  """This function parses the predictions in one individual message.

  If the message contains predictions, they will be inserted into the
  oracle database.

  @param odb: A connection to the oracle database.
  @type  odb: c{oracle_db.OracleDB}

  @param message: The individual message to process.  The message should
                  be formatted as returned from a call to
                  c{message_board.Parser().Parse()}, with keys for the
                  'User', 'Timestamp', and 'Text' of the message.
  @type  message: dictionary

  @param contest: Info about the contest these predictions are for.
  @type  contest: dictionary

  @param round_nums: The round numbers these predictions are for.
  @type  round_nums: list

  @param duel: True if this is a 1 on 1 match (old contest style), or
               False if it's a multiway poll.
  @type  duel: boolean

  """

  duel = 0
  if contest['CompetitorsPerMatch'] == 2:
    duel = 1

  user_id = odb.GetUserId(message['User'])
  if user_id is None:
    user_id = GetUserId(odb, message['User'], add_alt=1)
  # This enables admins to enter predictions for other users.
  # TODO: Make this a flag or something
#  if user_id in (1,2):
#    user_id = PromptForId(odb, message, user_id)

  # Split the message into lines so we can examine each for predictions.

  pattern = ('^\s*(.*?)\s*'
             '(?:over .*?)?'
             '(?:with\s*)?'
             '(?:w/\s*)?'
             '(?:\W+\s*)?'
             '(\d{1,3}[,\.]?\d*)\s*%')
  prediction_re = re.compile(pattern)
  lines = re.split('(?:<br />)+', message['Text'])
  for line in lines:
    match = prediction_re.search(line)

    if match is not None:
      winner_name = match.group(1)

      # Eliminate double quotes because they will cause problems with MySQL.
      winner_name = winner_name.replace('"', '')
      
      percent = match.group(2)
      percent = percent.replace(',', '.')
      percent = float(percent)
      if percent > 100:
        percent = 100.0
      if duel and (float(percent) < 50):
        # This is an invalid prediction
        print 'Invalid prediction from %s: %s with %s' % (message['User'],
                                                          winner_name, percent)
        continue
      
      winner_id = DecipherName(odb, winner_name, line, contest['Type'],
                               contest['ContestId'], round_nums)
      if winner_id is None:
        continue

      match_id = odb.LookupMatchId(winner_id, round_nums, contest['ContestId'],
                                   message['Timestamp'])

      if match_id is None:
        print '\n%s predicted a competitors who isn\'t in this round:\n%s\n' \
              % (message['User'], line)
        continue

      if duel:
        old_prediction = odb.GetPredictions(user_id=user_id, match_id=match_id)
      else:
        old_prediction = odb.GetPredictions(user_id=user_id, match_id=match_id,
                                            character_id=winner_id)
      if not old_prediction or \
         old_prediction[0]['LastUpdated'] <= message['Timestamp']:
        # Check if the prediction is late.

        match_info = odb.GetMatches(match_id=match_id)
        time_margin = datetime.timedelta(minutes=0)
        if message['Timestamp'] + time_margin >= match_info[0]['MatchDate']:
          print '\nAccept late prediction from %s posted at %s?' \
              % (message['User'], message['Timestamp'])
          print '%s with %s' % (winner_name, percent)
          accept_late = raw_input('(y/n): ')
          if accept_late != 'y':
            continue

        odb.SetPrediction(user_id, match_id, winner_id, percent,
                          message['Timestamp'], duel=duel)
        print '%s predicts match %s: %s with %s' % (message['User'], match_id,
                                                    winner_name, percent)
      else:
        # We already have a newer prediction.
        print "Ignoring old prediction from %s at %s" % (message['User'],
                                                         message['Timestamp'])

    # TODO(dscotton): Check if the prediction is being submitted too late.


def GetUserId(odb, username, add_alt=0):
  """Get the user id of an unrecognized user.

  @param odb: A connection to the oracle database.
  @type  odb: c{oracle_db.OracleDB}

  @param username: The unrecognized GameFAQs username.
  @type  username: string

  @param add_alt: Whether or not to add this username as an alt. 1 or 0.
  @type  add_alt: integer
  
  @return: The database userid of the user.
  @rtype:  integer

  """

  print 'Unrecognized user %s.' % (username)
  alt = raw_input('Is this user in our DB (y/n)? ')
  if alt == 'y':
    main_name = raw_input('What is their primary username? ')
    user_id = odb.GetUserId(main_name)
    if user_id is None:
      user_id = GetUserId(odb, main_name)
    if add_alt:
      odb.AddAlt(user_id, username)
    return user_id

  else:
    return odb.AddUser(username)


def DecipherName(odb, winner_name, line, type, contest, round_nums):
  """Figure out a competitor id based on a user-input name.

  @param odb: A connection to the oracle database.
  @type  odb: c{oracle_db.OracleDb}

  @param winner_name: The name of the competitor to look up.
  @type  winner_name: string

  @param line: The full text line of the prediction.
  @type  line: string

  @param type: The type of competitor expected ('character', 'game', 'series').
  @type  type: string

  @param contest: The ID of the contest this competitor should be in.
  @type  contest: integer

  @param round_nums: The numbers of the rounds this competitor should be in.
  @type  round_nums: list of integers

  @return: The id of the competitor, or None if not a prediction.
  @rtype:  integer

  """

  competitor_id = None
  competitors = odb.GetCompetitors(winner_name, type=type)
  if competitors and len(competitors) > 1:
    comps_in_round = []
    for comp in competitors:
      if odb.IsCompetitorInRounds(comp['CompetitorId'], contest, round_nums):
        comps_in_round.append(comp)
    competitors = comps_in_round

  # Now try just with people in the round
  if not competitors:
    print 'Couldn\'t recognize competitor name for this prediction:'
    print '"', line, '"'
    comp_name = raw_input('Enter a name or leave blank to skip: ')
    if comp_name != '':
      competitor_id = DecipherName(odb, comp_name, line, type, contest,
                                   round_nums)
  elif len(competitors) > 1:
    for comp in competitors:
      if comp['Name'] == winner_name:
        return comp['CompetitorId']
    print 'Who is this prediction for?\n\n"%s"\n' % (line)
    for comp in competitors:
      print "%s, Id=%s" % (comp['Name'], comp['CompetitorId'])
    competitor_id = raw_input('\nEnter CompetitorId: ')
    if competitor_id == '':
      competitor_id = None
  else:
    competitor_id = competitors[0]['CompetitorId']

  if competitor_id is not None:
    competitor_id = int(competitor_id)

  return competitor_id


def PromptForId(odb, message, orig_id=1):
  """Prompt for user input to figure out who predictions are for.

  This function is written so that the Oracle host can post predictions
  in the topic for other users.

  @param odb: A connection to the Oracle database.
  @type  odb: c{oracle_db.OracleDB}

  @param message: The message containing the predictions to be added.  The
                  message should be formatted as returned from a call to
                  c{message_board.Parser().Parse()}, with keys for the
                  'User', 'Timestamp', and 'Text' of the message.
  @type  message: dictionary

  @param orig_id: The ID of the user that actually posted the message.
  @type orig_id: int

  """

  print 'Is this prediction for someone other than the poster?\n\n%s\n\n' % \
        (message['Text'])
  diff_user = raw_input('(y/n): ')

  if diff_user == 'n':
    return orig_id
  
  user_name = raw_input('Username this prediction is for? ')
  user_id = odb.GetUserId(user_name)

  if user_id is None:
    print 'Unrecognized username, try again.\n'
    return PromptForId(odb, message, orig_id)

  else:
    return user_id
  

if __name__ == "__main__":
  main()
