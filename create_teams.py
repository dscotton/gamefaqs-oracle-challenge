#!/usr/bin/python
#
# This script adds teams and team members to the oracle database.
#
# Copyright David Scotton, 2007

import re
import getpass
import sys
sys.path.append('/home/oraclech/src/lib/python/')

import oracle_db


def main():
  """This is the main method for adding team pairings.

  Pairings are read from a file with one team on each line.  The format
  is team name,username 1, username 2.

  """

  db_user = raw_input('DB username: ')
  pw = getpass.getpass()

  odb = oracle_db.OracleDb(db_user, pw, database='oraclech_oracle')

  contest_id = raw_input('Current Contest ID? ')
  contest_id = int(contest_id)

  file_path = '/home/oraclech/contest_%d_teams' % (contest_id)
  file = open(file_path, 'r')

#  team_pattern = re.compile('\s*\d+\.\s*([^/]+)/([^-]+?)\s+\-\s*Team\s*(.+)')
  team_pattern = re.compile('\s*([^,]+),([^,]+),(.+)')

  for line in file: # page.split('\r\n'):
    print line
    match = team_pattern.search(line)
    team_name, user1, user2 = match.groups()
    user_id1 = odb.GetUserId(user1)
    if user_id1 is None:
      user_id1 = GetUserId(odb, user1, add_alt=1)
    user_id2 = odb.GetUserId(user2)
    if user_id2 is None:
      user_id2 = GetUserId(odb, user2, add_alt=1)

    odb.CreateTeam(contest_id, user_id1, user_id2, team_name)
    

def GetUserId(odb, username, add_alt=0):
  """Get the user id of an unrecognized user.

  This method is copied from add_predictions.py, which is ugly - it
  should be put in a library.

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


if __name__ == "__main__":
  main()
