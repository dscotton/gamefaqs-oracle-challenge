#!/usr/bin/python
#
# This is a script for importing all GameFAQs matches from sc2k5.com to our
# database.
# Copyright David Scotton, 2005

__author__ = 'dscotton@gmail.com'

import datetime
import getpass
import re
import urllib2

import oracle_db


def main():
  """Parse match history from sc2k5.com and store it in our database."""

  user = raw_input("Database username: ")
  pw = getpass.getpass("Database password: ")
  database = 'oraclech_oracletest'

  odb = oracle_db.OracleDb(user, pw, database=database)

  url = 'http://www.sc2k5.com/drupal/node/19?fields=1&sort=pollid&type=ASC'

  history_page = urllib2.urlopen(url)
  history_data = history_page.read()
  history_data = re.sub('\n', '', history_data)

  history = re.split('<table[^<>]*>', history_data)
  history_table = history[4]

  match_rows = re.split('(?:</?tr>)+', history_table)

  # Remove empty list elements created by the split.

  while '' in match_rows:
    match_rows.remove('')

  # Also get rid of the header row.

  match_rows = match_rows[1:]

  for row in match_rows:
    fields = re.split('(?:</?td>)+', row)

    while '' in fields:
      fields.remove('')

    # Field order:
    # 0 - matchnum
    # 1 - pollid (with link)
    # 2 - date
    # 3 - roundnum
    # 4 - division
    # 5 - matchnum
    # 6 - winner's seed (irrel)
    # 7 - winner
    # 8 - winner's votes
    # 9 - winner's %
    # 10 - loser's seed
    # 11 - loser
    # 12 - loser's votes
    # 13 - loser's %
    # 14 - total votes
    # 15 - vote difference
    # 16 - % difference

    print fields

    poll_str = fields[1]
    poll_id = int(re.search("<[^<>]+>([^<>]+)</a>", poll_str).group(1))
    date = fields[2]
    round_num = int(fields[3])
    division_name = fields[4]
    match_num = int(fields[5])
    winner_name = fields[7]
    winner_votes = int(fields[8])
    winner_percent = fields[9].replace('%', '')
    loser_name = fields[11]
    loser_votes = int(fields[12])
    loser_percent = fields[13].replace('%', '')
    
    # Now we need to get the competitors' ids, and if they aren't in our
    # database, add them.

    winner_id = odb.LookupCompetitorId(winner_name)
    if winner_id is None:
      odb.AddCompetitor(winner_name)
      winner_id = odb.LookupCompetitorId(winner_name)

    loser_id = odb.LookupCompetitorId(loser_name)
    if loser_id is None:
      odb.AddCompetitor(loser_name)
      loser_id = odb.LookupCompetitorId(loser_name)

    # Get the contest id for this match.  I'll use a lame hack because we're
    # only going to be importing old data once.  I don't think there's a
    # need in the abstract for a identifying the contest of an un-entered
    # match (what would the criterion be?)

    contest_id = 0
    if poll_id <= 1002:
      contest_id = 1
    elif poll_id <= 1367:
      contest_id = 2
    elif poll_id <= 1663:
      contest_id = 3
    elif poll_id <= 1780:
      contest_id = 4
    elif poll_id <= 2019:
      contest_id = 5
    else:
      contest_id = 6

    # Get the division id for the match.

    if '/' in division_name:
      division_name = "Final Four"

    division_id = odb.LookupDivisionId(division_name, contest_id)
    if division_id is None:
      odb.AddDivision(division_name, contest_id)
      division_id = odb.LookupDivisionId(division_name, contest_id)

    # Check if the match is in the database, just in case.

    match_id = odb.LookupMatchId(winner_id, round_num, contest_id)
    if match_id is None:
      match_id = odb.AddMatch(match_num, round_num, poll_id, contest_id,
                              division_id, date)

    odb.AddResult(match_id, winner_id, votes=winner_votes,
                  percentage=winner_percent, is_winner=1)
    odb.AddResult(match_id, loser_id, votes=loser_votes,
                  percentage=loser_percent, is_winner=0)
    

if __name__ == "__main__":
  main()
