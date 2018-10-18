#!/usr/bin/python
#
# This script enters the results from the latest match into the database.
# Copyright David Scotton, 2005

__author__ = 'dscotton@gmail.com'

import datetime
import getpass
import random
import re
import urllib2

import oracle_db

DB_USER = raw_input('DB username: ')
PW = getpass.getpass()


class ResultUpdater(object):
  """This class provides necessary methods for updating the results."""

  PROXY_SERVERS = (('38.96.193.61', 9090),
                   ('38.96.193.62', 9095),
                   ('38.96.193.63', 9100),
                   ('38.96.193.64', 9105),
                   ('38.96.193.65', 9110),
                   ('38.96.193.66', 9115),
                   ('38.96.193.67', 9120),
                   ('38.96.193.68', 9125),
                   ('38.96.193.69', 9130),
                   ('38.96.193.70', 9135),
                   ('38.96.193.71', 9140),
                   ('38.96.193.72', 9145),
                   ('38.96.193.73', 9150),
                   ('38.96.193.74', 9155),
                   ('38.96.193.75', 9160),
                   ('38.96.193.76', 9165),
                   ('38.96.193.77', 9170),
                   ('38.96.193.78', 9175))

  def __init__(self):
    """Class constructor."""

    self.__odb = oracle_db.OracleDb(DB_USER, PW,
                                    database='oraclech_oracle')

  def GetLastMatch(self):
    """Get information about the most recent GameFAQs match.

    @return: A dictionary containing information about the match.
    @rtype: dict

    """

    now = datetime.datetime.now()
    yesterday = now - datetime.timedelta(hours=12)
    return self.__odb.GetMatchByDate(yesterday)

  def GetPollResults(self, poll_id):
    """Get the results of a specific poll.

    @param poll_id: The number of the GameFAQs poll to get results for.
    @type poll_id: int

    @return: A tuple containing results for each entry.  Each entry has
             a dict with keys 'Name', 'Votes', and 'Percentage'.
    @rtype: tuple

    """

    # Set up proxy to defeat bacon's annoying blocking
    # proxy_url = 'http://kadri:privateproxy@%s:%s' % random.choice(self.PROXY_SERVERS)
    # proxy_handler = urllib2.ProxyHandler({'http': proxy_url})
    # opener = urllib2.build_opener(proxy_handler)
    # urllib2.install_opener(opener)

    url = 'http://www.gamefaqs.com/poll/index.html?poll=%d' % int(poll_id)
    page = urllib2.urlopen(url)
    text = page.read()

    results = []

    # One RE for all competitors, find all matches.
    result_re = re.compile(r'<th>([^<>]+)</th>\s*<td>(\d+\.?\d{0,2})%'
                           '.*?<td>(\d+)</td>', re.S)
    matches = result_re.findall(text)
    if not matches:
      raise Exception, 'no results'
    for match in matches:
      competitor_results = {'Name' : match[0],
                            'Percentage' : match[1],
                            'Votes' : match[2]}
      results.append(competitor_results)

    return results

  def AddResults(self):
    """Main function for recording the latest poll results."""

    match = self.GetLastMatch()
    contest = self.__odb.GetContest(match['ContestId'])
    results = self.GetPollResults(match['PollId'])

    total_votes = 0
    for res in results:
      total_votes += int(res['Votes'])
    for r in results:
      is_winner = 0
      if int(r['Votes']) > (total_votes / 2):
        is_winner = 1
      if contest['CompetitorsPerMatch'] > 2:
        is_winner = None
      comp = self.__odb.GetCompetitorIdInMatch(r['Name'], match['MatchId'])
      if not comp:
        raise ValueError, 'Couldn\'t find %s' % r['Name']
      self.__odb.AddResult(match['MatchId'], comp['CompetitorId'],
                           votes=r['Votes'], percentage=r['Percentage'],
                           is_winner=is_winner)


def main():
  ur = ResultUpdater()
  ur.AddResults()
  

if __name__ == "__main__":
  main()
