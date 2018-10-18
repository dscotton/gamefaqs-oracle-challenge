#!/usr/bin/python
#
# This script adds message board posts to the oracle database.  This
# gives us an archive of every post in an oracle topic in our
# database.  Currently the message board topics are being saved to
# disc and fed into the program as files.
#
# Copyright David Scotton, 2005

import getpass
import re

import oracle_db
import message_board


def main():
  """This is the main prediction adding function.

  It starts by grabbing a file to open from standard in, which contains
  one message board page.  It processes each message contained in the page.

  NOTE: If there are multiple pages, they must be processed in order.
  However, after a page is complete (50 messages), it only needs to
  be processed once.

  """

  db_user = raw_input('DB username: ')
  pw = getpass.getpass()

  odb = oracle_db.OracleDb(db_user, pw, database='oraclech_oracle')

  contest_id = raw_input('Current Contest ID? ')
  round_num = raw_input('Current Round Number? ')
  round_nums = round_num.split(',')
  topic_num = raw_input('Current Topic Number? ')
#  page_num = raw_input('Current Page Number? ')

  contest = odb.GetContest(contest_id)

  for page_num in range(1, 10):
    try:
      file_path = '%s/r%st%dp%02d.html' % (contest['Name'].lower(),
                                           round_num[-1:],
                                           int(topic_num),
                                           int(page_num))
      file_path = '/home/oraclech/topics/' + file_path
      print file_path
      file = open(file_path, 'r')
    except IOError:
      print 'Failed to open %s' % file_path
      raise
      file_path = raw_input('File to open (in /home/oraclech/topics/): ')
      file_path = '/home/oraclech/topics/' + file_path
      file = open(file_path, 'r')
    page = file.read()
    InsertMessagesInPage(odb, page)


def InsertMessagesInPage(odb, page):
  """Insert all the messages from one page into the database.

  @param odb: A connection to the database.
  @type odb: oracle_db.OracleDb

  @param page: The text of the page to insert.
  @type page: str

  """
  
  parser = message_board.Parser()
  messages = parser.Parse(page)

  for message in messages:
    odb.AddMessage(message['TopicId'], message['TopicTitle'], message['User'],
                   message['Timestamp'], message['Text'])
  

if __name__ == "__main__":
  main()
