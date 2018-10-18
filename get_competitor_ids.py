#!/usr/bin/python
#
# This is a script for getting a list of competitor IDs from the bracket,
# so that they can be added to the oracle database as new matches.
# Copyright David Scotton, 2008

__author__ = 'dscotton@gmail.com'

import getpass
import re

import oracle_db
import add_predictions

print "Running..."

CONTEST = 14
TYPE = 'rivalry'

# Paste the list of names in as a string - this is hacky, but we don't have to do it very often.
CHARACTER_LIST = """Pokemon Trainer Red vs. Pokemon Trainer Blue
Cloud Strife vs. Sephiroth
Mario vs. Bowser
Link vs. Ganondorf
""".strip().split('\n')

print "%d characters found..." % (len(CHARACTER_LIST))


def main():
  start_id = 949
  filename = '/tmp/sc2k11_matchups'
  sql_file = open(filename, 'w')
  db_user = raw_input('DB username: ')
  pw = getpass.getpass()
  odb = oracle_db.OracleDb(db_user, pw, database='oraclech_oracle')
  output_rows = []
  for i in xrange(len(CHARACTER_LIST)):
    char_name = CHARACTER_LIST[i].strip()
    competitor_id = odb.LookupCompetitorId(char_name, type=TYPE)
    if competitor_id is None:
      raise Exception("No competitor found for name: %s and type: %s" % (char_name, TYPE))
    output_rows.append("(%d, %d)" % (start_id + i / 2, competitor_id))

  query = ("INSERT INTO Results\n"
           "(MatchId, CompetitorId)\n"
           "VALUES\n%s;"
           % ",\n".join(output_rows))
  sql_file.write(query)
  print 'File generated.  Now run this command:'
  print 'db < ' + filename


if __name__ == "__main__":
  main()
