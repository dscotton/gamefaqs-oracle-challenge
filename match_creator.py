#!/usr/bin/python
#
# Script for setting up the matches at the beginning of the contest.  
# This only populates the rounds, poll IDs, etc - not the characters that
# are in the match.

import datetime

contest_id = 12
rounds = 7
first_poll = 4069
first_match = datetime.datetime(2010, 10, 20)
first_div = 86
match_duration = datetime.timedelta(hours=12)

match_num = 1

for round in range(1, rounds + 1):
  for match_in_round in range(2 ** (rounds - round)):
    # Division math needs to be adjusted for the number of rounds
    div = first_div + 8
    if round <= 4:
      div = first_div + (match_in_round / (8 / 2 ** (round - 1)))
    print '(%d, %d, %d, %d, %d, "%s"),' % (
        match_num, round, first_poll + match_num - 1, contest_id, div,
        first_match + match_duration * (match_num - 1))
    match_num += 1
