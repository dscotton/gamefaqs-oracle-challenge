#!/usr/bin/python
#
# This file defines a library for interacting with the GameFAQs message boards.
# Copyright David Scotton, 2005

import datetime
import re
import time
import urllib
import urllib2


class Connection:
  """This class defines an interface to the GameFAQs message boards.

  It is used for getting the text of threads on the boards.

  """

  def __init__(self, email, pw):
    """Instantiate a connection object and log in to GameFAQs.

    @param email: The email address to log in with.
    @type  email: string

    @param pw: The password to connect with.
    @type  pw: string

    """

    login_url = 'http://www.gamefaqs.com/user/login.html'

    postdata = {'path' : 'http://www.gamefaqs.com/',
                'EMAILADDR' : email,
                'PASSWORD' : pw}

    req = urllib2.Request(login_url, urllib.urlencode(postdata))

    # Need to capture the login cookie, which is more trouble than it's worth
    # at the moment.


class Parser:
  """This class parses GameFAQs threads."""

  def __init__(self):
    """Instantiate a parser.

    The parser doesn't have a state - instead it will just parse text that
    is passed to its Parse() method.

    """

    pass

  def Parse(self, page):
    """Parse text passed in into a usable format.

    @param page: The text of one page of a GameFAQs topic, as returned
                    from a read() call.
    @type  page: string

    @return: An array of messages.  Each message will be represented as
             a dictionary with the keys 'User', 'Timestamp', and 'Text',
             'TopicId', and 'TopicTitle'.  TopicId and TopicTitle will
             be the same for every message in the array.
    @rtype:  array of dictionaries

    """

    # Start by getting the topic title and ID.

    page_re = re.compile(r'https://gamefaqs.gamespot.com/boards/8-gamefaqs-contests/(\d+)\page=(\d+)',
                         re.I + re.S)
    title_re = re.compile(r'<h1 class="page-title">\s*([^<>]+?)\s*</h1>',
                          re.I + re.S)

    if page_re.search(page) is not None:
      topic_id = page_re.search(page).group(1)
    else:
      topic_id = 0
    title = title_re.search(page).group(1)

    # It would be good to strip out the irrelevant part of the page, but
    # the server gives 'recursion limit exceeded' when I do this so for
    # now it's commented out.
    #
    # beginning_re = re.compile('.*?<div class="box">\s*', re.S)
    # end_re = re.compile('(?:\s*</div>){3}\s*<div class="footer">.*', re.S)
    #
    # page = beginning_re.sub('', page)
    # page = end_re.sub('', page)

    split_re = re.compile('<tr><td class="msg">')
    try:
      messages = split_re.split(page)
    except TypeError:
      print page
      raise

    # This gives us an array, with each message in one cell, plus garbage in
    # the first and last cells.  The first cell can be ignored completely.
    # The last cell contains both the last message of the page and the footer.
    # Here we'll strip out the footer.

    messages = messages[1:]
    last_re = re.compile('(.*?)\s*</table>', re.S)
    match = last_re.search(messages[-1])
    messages[-1] = match.group(1)

    # Now there's one worthwhile message in each cell, so we can parse them.

    retval = []

    # Regexp for extracting poster, date, and message text.
    field_pattern = (r'data-username="([^<>]+)".*?<span class="post_time" title="\s*([^"]+)">.*?<div class="msg_body newbeta" data-msgnum="(?:\d+)" name="(?:\d+)">(.+?)<div')
    field_re = re.compile(field_pattern, re.S + re.I)

    for message in messages:
      parsedm = {}
      match = field_re.search(message)
      if match is None:
        print "No matches found in:"
        print message
        break

      parsedm['User'] = match.group(1)
      parsedm['Timestamp'] = datetime.datetime(*(time.strptime(
        match.group(2).replace('&nbsp;', ' '),
        '%m/%d/%Y %I:%M:%S %p')[0:6]))
      parsedm['Text'] = re.sub(r'<blockquote>.*?</blockquote>',
        '', match.group(3))
      parsedm['Text'] = parsedm['Text'].replace('\n', '')

      parsedm['TopicId'] = topic_id
      parsedm['TopicTitle'] = title

      retval.append(parsedm)

    return retval
