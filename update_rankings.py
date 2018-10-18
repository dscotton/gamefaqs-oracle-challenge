#!/usr/bin/python
#
# This script generates match rankings and overall rankings for
# each user and inserts them into the DailyStandings table.
#
# Copyright David Scotton, 2005

__author__ = 'dscotton@gmail.com'

import datetime
import getpass

import oracle_db


def main():
  """This is the main function for generating user standings.

  """

  start_match = 887
#  end_match = 569

  db_user = raw_input('DB username: ')
  pw = getpass.getpass()

  odb = oracle_db.OracleDb(db_user, pw, database='oraclech_oracle')

  # Get the id of the most recent match, and update up to that match.
  now = datetime.datetime.now()
  yesterday = now - datetime.timedelta(hours=12)
  end_match = odb.GetMatchByDate(yesterday)['MatchId']

  print start_match, end_match
  for i in range (start_match, end_match+1):
    match_scores = odb.GetMatchScores(i)
    for user in match_scores:
      odb.SetMatchRanking(user['UserId'], i, user['Ranking'])
      odb.SetMatchScore(user['UserId'], i, user['Score'])
    overall_scores = odb.GetContestScores(i)
    for user in overall_scores:
      odb.SetOverallRanking(user['UserId'], i, user['Ranking'])


if __name__ == "__main__":
  main()
