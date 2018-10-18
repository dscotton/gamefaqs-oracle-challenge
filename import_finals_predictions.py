#!/usr/bin/python
#
# This is a script for importing past spreadsheets of predictions into
# the Oracle Challenge database.
# Copyright David Scotton, 2005

__author__ = 'dscotton@gmail.com'

import getpass
import re

import oracle_db
import add_predictions


def main():
  """This is the main function which imports user predictions.

  It reads in the prediction file from one contest and adds each
  prediction to the database.

  """

  contest_id = 7
  comp_type = 'series'

  db_user = raw_input('DB username: ')
  pw = getpass.getpass()

  odb = oracle_db.OracleDb(db_user, pw, database='oraclech_oracle')

  prediction_file = open('2k6_final_predictions.csv', 'r')
  predictions = prediction_file.read()
  lines = predictions.split('\n')

  for line in lines:
    # Read each line, which contains one user's predictions, and add them to
    # the database.

    cells = line.split(',')
    user = re.search('"([^"]+)"', cells[0]).group(1)
    user_id = odb.GetUserId(user)

    # Unlike the original predictions import, here we only have to deal
    # with one match in the whole page.

    winner_re = re.compile('"([^"]+)"')
    percent_re = re.compile(r'(\d+\.?\d*)%')

    winner_match = winner_re.search(cells[1])
    percent_match = percent_re.search(cells[2])

    if winner_match is not None and percent_match is not None:
      # Get the match_id and add the prediction to the database.

      winner_name = winner_match.group(1)
      percent = percent_match.group(1)

      match_id = 380
      winner_id = add_predictions.DecipherName(odb, winner_name, winner_name,
                                               comp_type)

      odb.SetPrediction(user_id, match_id, winner_id, percent, 0)

      print "Match %s" % (match_id)
      print "%s predicts %s with %s" % (user, winner_name, percent)        


if __name__ == "__main__":
  main()
