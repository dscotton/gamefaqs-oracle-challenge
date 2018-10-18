#!/usr/bin/python
#
# Script for copying the day's updates.php into a static file.
# Copyright David Scotton, 2009

__author__ = 'dscotton@gmail.com'

import datetime
import getpass
import re
import urllib2

import oracle_db

DB_USER = raw_input('DB username: ')
PW = getpass.getpass()


class UpdateCopier(object):
  """Class for copying the latest day's update to a file."""

  def __init__(self):
    """Class constructor."""

    self.__odb = oracle_db.OracleDb(DB_USER, PW,
                                    database='oraclech_oracle')

  def GetLastMatch(self):
    """Get information about the most recent GameFAQs match.

    @return: A (MatchNumber, ContestName) tuple.
    @rtype: tuple of (str, str)

    """

    now = datetime.datetime.now()
    yesterday = now - datetime.timedelta(hours=12)
    match_info = self.__odb.GetMatchByDate(yesterday)
    name = self.__odb.GetContest(match_info['ContestId'])['Name']
    return (match_info['MatchNumber'], name)

  def GetUpdatePage(self, match_num, contest_name):
    """Copy the update page to a specific location.

    TODO(dscotton): This should be a static method.

    @param match_num: The number match (within the contest), eg. 1-63.
    @type match_num: int

    @param contest_name: The short name of the contest, eg SpC2k9.
    @type contest_name: str

    """

    url = ('http://www.oraclechallenge.com/updates.php?contest=%s&match=%d'
           % (contest_name, int(match_num)))
    page = urllib2.urlopen(url)
    text = page.read()

    file_name = '/home/oraclech/www/%s-%02d.html' % (contest_name, match_num)
    print file_name
    target = open(file_name, 'w')
    target.write(text)
    target.close()


def main():
  copier = UpdateCopier()
  number, name = copier.GetLastMatch()
  copier.GetUpdatePage(number, name)


if __name__ == "__main__":
  main()
