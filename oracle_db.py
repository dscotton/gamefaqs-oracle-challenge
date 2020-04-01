#!/usr/bin/python
#
# This module defines an interface to the Oracle Challenge database.
# Copyright David Scotton, 2005

__author__ = 'dscotton@gmail.com'

import datetime

import MySQLdb


class OracleDb:
  """This class represents a connection to the Oracle database."""

  def __init__(self, user, pw, database='oraclech_new'):
    """Instantiate a connection to the database.

    @param user: The username to use when connecting to the MySQL server.
    @type  user: string

    @param pw: The password to use to log into the MySQL server.
    @type  pw: string

    @param database: The database to use.  Change this parameter if
                     you are testing.
    @type  database: string

    """

    self.__conn = MySQLdb.connect(db=database, user=user, passwd=pw)
    self.__dbh = self.__conn.cursor(cursorclass=MySQLdb.cursors.DictCursor)

  def Commit(self):
      self.__conn.commit()

  def AddUser(self, username):
    """Add a user to the database.

    This function should only be used for adding primary accounts.  To
    register a user's alt, use the AddAlt() method.

    @param username: The GameFAQs username of the user to add.
    @type  username: string

    @return: The Id number of the user added.
    @rtype:  integer

    """

    # First check if they are already in our database.

    # TODO(dscotton): Fix bug where if the user is already in the UserNames
    # table, but their name in the Users table is different from the
    # argument to this function, it creates a duplicate and crashes.
    # - Fixed?
    
    mysql = 'SELECT * FROM UserNames WHERE UserName="%s"' % (username)

    self.__dbh.execute(mysql)
    results = self.__dbh.fetchall()

    if len(results) > 0:
      return results[0]['UserId']

    mysql = """
      INSERT
      INTO Users
      (Name)
      VALUES ('%s')
    """ % (username)

    self.__dbh.execute(mysql)

    # Get the user's new user_id.

    mysql = 'SELECT * FROM Users WHERE Name="%s"' % (username)

    self.__dbh.execute(mysql)
    results = self.__dbh.fetchall()
    user_id = results[0]['UserId']

    mysql = """
      INSERT
      INTO UserNames
      (UserName, UserId)
      VALUES ('%s', %i)
    """ % (username, user_id)

    self.__dbh.execute(mysql)

    return user_id

  def AddAlt(self, user_id, username):
    """Register an alt (alternate username) for a user.

    The user must already appear in our Users table, preferably with their
    primary account.  If they don't, you first need to add them with AddUser().

    @param user_id: The id of the user, in the Users table.
    @type  user_id: integer

    @param username: The alternate username to register.
    @type  username: string

    """
        
    # Check to make sure this is a valid UserId

    mysql = 'SELECT * FROM Users WHERE UserId="%s"' % (user_id)

    self.__dbh.execute(mysql)
    results = self.__dbh.fetchall()

    if len(results) == 0:
      raise ValueError, "No user with UserId %s" % (user_id)

    mysql = """
      INSERT
      INTO UserNames
      (UserName, UserId)
      VALUES ('%s', %i)
    """ % (username, user_id)

    self.__dbh.execute(mysql)

  def CreateTeam(self, contest_id, user_id1, user_id2, team_name):
    """Create a new team.

    @param contest_id: The contest number this team existed for.
    @type  contest_id: integer

    @param user_id1: The ID of the first member of the team.
    @type  user_id1: integer

    @param user_id2: The ID of the second member of the team.
    @type  user_id2: integer

    @param team_name: The name of the team.
    @type  team_name: string

    """

    team_id = self.AddTeam(contest_id, team_name)
    self.AddUserToTeam(team_id, user_id1)
    self.AddUserToTeam(team_id, user_id2)

  def AddTeam(self, contest_id, team_name):
    """Add a new team to the database.

    Members need to be added to the team separately - this creates an
    empty team.

    @param contest_id: The contest number to create the team for.
    @type  contest_id: integer

    @param team_name: The name of the team.
    @type  team_name: string

    @return: The ID of the newly created team.
    @rtype:  integer

    """

    mysql = """
      INSERT 
      INTO Teams
      (Name)
      VALUES ('%s')
    """ % (self.EscapeString(team_name))

    self.__dbh.execute(mysql)
    team_id = self.__conn.insert_id()

    mysql = """
      INSERT
      INTO TeamContests
      (TeamId, ContestId, TeamName)
      VALUES (%d, %d, "%s")
    """ % (team_id, contest_id, self.EscapeString(team_name))

    self.__dbh.execute(mysql)

    return team_id

  def AddUserToTeam(self, team_id, user_id):
    """Add a user to a team.

    @param team_id: The ID of the team to add the user to.
    @type  team_id: integer

    @param user_id: The ID of the user.
    @type  user_id: integer

    """

    mysql = """
      INSERT
      INTO TeamMembers
      (TeamId, UserId)
      VALUES (%d, %d)
    """ % (team_id, user_id)

    self.__dbh.execute(mysql)

  def GetUserId(self, username):
    """Lookup a user's id by username.

    @param username: The user's GameFAQs message board username.
    @type  username: string

    @return: The user's id from the Users table.
    @rtype:  integer

    """

    mysql = 'SELECT * FROM UserNames WHERE UserName="%s"' % (username)

    self.__dbh.execute(mysql)
    results = self.__dbh.fetchall()

    if len(results) > 0:
      return results[0]['UserId']
    else:
      return None

  def SetPrediction(self, user_id, match_id, winner_id, percent, timestamp,
                    duel=1):
    """Set a user's prediction for a match.

    If the user already has a prediction, it will be updated.
    Otherwise, a new prediction will be inserted.  You should
    check whether the prediction was made before the deadline
    before calling this method.
    
    @param user_id: The UserId of the predictor, from the Users table.
    @type  user_id: integer
    
    @param match_id: The Id of the match, from the Matches table.
    @type  match_id: integer

    @param winner_id: The Id of the winner, from Competitors.
    @type  winner_id: integer

    @param percent: The winner's predicted percentage.
    @type  percent: string

    @param timestamp: The time that the prediction was made (GameFAQs
                      message board timestamp, Pacific Time.)
    @type  timestamp: datetime

    @param duel: Whether this is a 1v1 match.  If True only one prediction
                 for the match is kept, if False separate predictions will
                 be stored for each character in the match.
    @type  duel: boolean

    """

    user_id = int(user_id)
    match_id = int(match_id)
    winner_id = int(winner_id)
    duel = int(duel)

    mysql = """
      SELECT *
      FROM Predictions
      WHERE UserId=%d
      AND MatchId=%d
    """ % (user_id, match_id)

    if not duel:
      mysql += ' AND WinnerId=%d' % winner_id
    self.__dbh.execute(mysql)
    results = self.__dbh.fetchall()

    if results:
      # Update the existing row.

      mysql = """
        UPDATE Predictions
        SET
          WinnerId=%s,
          Percentage=%s,
          LastUpdated='%s'
        WHERE UserId=%s
        AND MatchId=%s
      """ % (winner_id, percent, timestamp, user_id, match_id)

      if not duel:
        mysql += ' AND WinnerId=%d' % winner_id

      self.__dbh.execute(mysql)

    else:
      # Insert a new prediction.

      mysql = """
        INSERT
        INTO Predictions
        (UserId, MatchId, WinnerId, Percentage, LastUpdated)
        VALUES (%s, %s, %s, %s, '%s')
      """ % (user_id, match_id, winner_id, percent, timestamp)

    try:
      self.__dbh.execute(mysql)
    except:
      print mysql
      raise

  def GetPredictions(self, user_id=None, match_id=None, character_id=None):
    """Get Predictions from the database.

    If user_id and match_id are specified, only predictions for that
    user or match will be returned.  Otherwise, all predictions will
    be returned.

    @param user_id: Look up predictions for this specific user.
    @type  user_id: integer

    @param match_id: Look up only predictions for this match.
    @type  match_id: integer

    @param character_id: Look up only predictions for this character.
    @type  character_id: integer

    @return: A list of predictions.  Each prediction is a dictionary
             with keys 'UserId', 'MatchId', 'WinnerId', 'Percentage',
             and 'LastUpdated'.
    @rtype:  list of dictionaries

    """

    conditions = []

    if user_id is not None:
      conditions.append('UserId=%s' % (user_id))
    if match_id is not None:
      conditions.append('MatchId=%s' % (match_id))
    if character_id is not None:
      conditions.append('WinnerId=%s' % (character_id))
    where_clause = ''
    if conditions:
      where_clause = 'WHERE %s' % ' AND '.join(conditions)

    mysql = """
      SELECT *
      FROM Predictions
      %s
    """ % where_clause

    self.__dbh.execute(mysql)
    results = self.__dbh.fetchall()
    return results

  def AddMatch(self, match_num, round_num, poll_id, contest_id, division_id,
               match_date):
    """Add a match to our database.

    @param match_num: The number of the match within its contest.
    @type  match_num: integer

    @param round_num: The round of the match.
    @type  round_num: integer

    @param poll_id: The gamefaqs poll number.
    @type  poll_id: integer

    @param contest_id: The contest this match occurred in.
    @type  contest_id: integer

    @param division_id: The division this match is in.
    @type  division_id: integer

    @param match_date: The date of the match, in YYYY-MM-DD format.
    @type  match_date: string

    @return: The Id of the match added.
    @rtype:  integer

    """

    mysql = """
      INSERT
      INTO Matches
      (MatchNumber,
       RoundNumber,
       PollId,
       ContestId,
       DivisionId,
       MatchDate)
      VALUES
      (%s, %s, %s, %s, %s, '%s')
    """ % (match_num, round_num, poll_id, contest_id, division_id, match_date)

    self.__dbh.execute(mysql)
    return self.__dbh.insert_id()

  def GetMatches(self, match_id=None):
    """Get info about a match or all matches.

    @param match_id: The match to get.
    @type  match_id: integer

    @return: A tuple of match info, where each item is a dict with keys
             matching the columns in the Matches table.
    @rtype:  tuple

    """

    mysql = 'SELECT * FROM Matches'

    if match_id is not None:
      mysql += ' WHERE MatchId=%s' % (match_id)

    self.__dbh.execute(mysql)
    results = self.__dbh.fetchall()
    return results

  def GetMatchByDate(self, timestamp):
    """Get info about a match held on a particular date.

    Since multiple matches can now occur on the same date, this method
    looks for the last one that started before the given timestamp.

    @param timestamp: The date to look for
    @type timestamp: datetime

    @return: A dictionary containing information about the requested match.
    @rtype: dict

    """

    mysql = """
      SELECT *
      FROM Matches
      WHERE MatchDate < "%s"
      ORDER BY MatchDate DESC
    """ % timestamp

    self.__dbh.execute(mysql)
    result = self.__dbh.fetchone()
    return result

  def GetPastUnrecordedMatches(self, duration=24):
    """Get all matches that happened in the past that don't have results.

    Used to determine which results pages to attempt to scrape.
    """
    
    timestamp = datetime.datetime.now() - datetime.timedelta(hours=duration)

    mysql = """
      SELECT *
      FROM Matches
      WHERE MatchDate < "%s"
      AND MatchId IN 
        (SELECT MatchId FROM Results WHERE Percentage IS NULL GROUP BY MatchId)
      ORDER BY MatchDate DESC
    """ % (timestamp)
    self.__dbh.execute(mysql)
    result = self.__dbh.fetchall()
    return result

  def AddNewMatch(self, match_num, round_num, contest_id, division_id,
                  match_date, name1, name2, poll_id=None):
    """Register a new match in our database.

    This function is meant for completely registering a new match,
    including adding lines to the Results table to record who the
    competitors are in the match.

    @param match_num: The number of the match within its contest.
    @type  match_num: integer

    @param round_num: The round of the match.
    @type  round_num: integer

    @param contest_id: The contest this match occurred in.
    @type  contest_id: integer

    @param division_id: The division this match is in.
    @type  division_id: integer

    @param match_date: The date of the match, in YYYY-MM-DD format.
    @type  match_date: string

    @param name1: The name of the first competitor.
    @type  name1: string

    @param name2: The name of the second competitor.
    @type  name2: string

    @param poll_id: The gamefaqs poll number.
    @type  poll_id: integer

    @return: The Id of the match added.
    @rtype:  integer

    """

    if poll_id is None:
      poll_id = "NULL"

    mysql = """
      INSERT
      INTO Matches
      (MatchNumber,
       RoundNumber,
       PollId,
       ContestId,
       DivisionId,
       MatchDate)
      VALUES
      (%s, %s, %s, %s, %s, '%s')
    """ % (match_num, round_num, poll_id, contest_id, division_id, match_date)

    self.__dbh.execute(mysql)
    match_id = self.__dbh.insert_id()

    competitor1_id = self.GetCompetitorIds(name1)[0]['CompetitorId']
    competitor2_id = self.GetCompetitorIds(name2)[0]['CompetitorId']

    self.AddResult(match_id, competitor1_id)
    self.AddResult(match_id, competitor2_id)

    return match_id

  def LookupMatchId(self, competitor_id, round_nums, contest_id, date):
    """Look up a MatchId based on the contest, round, and competitor.

    @param competitor_id: One of the competitors in the match, from
                          the competitors table.
    @type  competitor_id: integer

    @param round_nums: The range of round numbers to examine for the match
                      (will return the earliest one that hasn't happened yet).
    @type  round_nums: list of integers

    @param contest_id: The contest the match is in.
    @type  contest_id: integer

    @param date: The date the prediction was made.  Only matches occuring
                 after this timestamp will be considered.
    @type  date: datetime

    @return: The id of the match.
    @rtype:  integer

    """

    if type(round_nums) is int:
      round_num = [round_nums]

    # Turn the round numbers into strings so we can join them.

    for i in range(len(round_nums)):
      round_nums[i] = str(round_nums[i])

    round_str = ', '.join(round_nums)

    mysql = """
      SELECT *
      FROM Matches, Results
      WHERE Matches.MatchId = Results.MatchId
      AND Matches.RoundNumber IN (%s)
      AND Matches.ContestId = %s
      AND Results.CompetitorId = %s
      AND Matches.MatchDate > '%s'
      ORDER BY MatchDate
    """ % (round_str, contest_id, competitor_id, date)

    self.__dbh.execute(mysql)
    results = self.__dbh.fetchall()

    if len(results) > 0:
      return results[0]['MatchId']
    else:
      return None

  def LookupMatchIdByNumber(self, contest_id, match_num):
    """Look up a match id based on the contest and match number.

    @param contest_id: The contest the match takes place in.
    @type  contest_id: integer

    @param match_num: The number of the match within the contest.
    @type  match_num: integer

    @return: The match id of the specified match.
    @rtype:  integer

    """

    mysql = """
      SELECT MatchId
      FROM Matches
      WHERE ContestId=%s
      AND MatchNumber=%s
    """ % (contest_id, match_num)

    self.__dbh.execute(mysql)
    results = self.__dbh.fetchall()

    if results:
      return results[0]['MatchId']
    else:
      return None
    
  def AddDivision(self, name, contest_id):
    """Add a division to our divisions table.

    @param name: The name of the division.
    @type  name: string

    @param contest_id: The contest this division was in.
    @type  contest_id: integer

    """

    mysql = """
      INSERT
      INTO Divisions
      (Name, ContestId)
      VALUES ("%s", %s)
    """ % (name, contest_id)

    self.__dbh.execute(mysql)

  def LookupDivisionId(self, name, contest_id):
    """If a division is already in our database, look up its id.

    @param name: The name of the division.
    @type  name: string

    @param contest_id: The contest this division was in.
    @type  contest_id: integer

    @return: The DivisionId from the divisions table.
    @rtype:  integer

    """

    mysql = """
      SELECT *
      FROM Divisions
      WHERE Name="%s"
      AND ContestId=%s
    """ % (name, contest_id)

    self.__dbh.execute(mysql)
    results = self.__dbh.fetchall()

    if results:
      return results[0]['DivisionId']
    else:
      return None

  def GetDivision(self, division_id):
    """Get a specific division."""
    query = """
      SELECT *
      FROM Divisions
      WHERE Id=%s
    """ % (division_id)

    self.__dbh.execute(query)
    results = self.__dbh.fetchall()

    if results:
      return results[0]
    else:
      return None

  def AddResult(self, match_id, competitor_id, votes=None, percentage=None,
                is_winner=None):
    """Add a result to our results table.

    This function does not necessarily have to add a final result.  A
    "result" also merely indicates who the competitors in a match are.

    @param match_id: The id of the match in our database.
    @type  match_id: integer

    @param competitor_id: The competitor this result is for.
    @type  competitor_id: integer

    @param votes: The number of votes this competitor got.
    @type  votes: integer

    @param percentage_id: This competitor's percentage of the vote.
    @type  percentage_id: string

    @param is_winner: Whether this competitor won.  None if the match
                      isn't over, 1 for winner, 0 for loser.
    @type  is_winner: integer

    """

    if votes is None:
      votes = 'NULL'
    if percentage is None:
      percentage = 'NULL'
    if is_winner is None:
      is_winner = 'NULL'

    # This shouldn't be necessary, but the DB started throwing Integrity errors on
    # INSERT, UPDATE, and INSERT ON DUPLICATE KEY UPDATE statements. The only way
    # around it seems to be delete and then insert.
    delete_statement = 'DELETE FROM Results WHERE MatchId=%d AND CompetitorId=%d' % (
      match_id, competitor_id)
    self.__dbh.execute(delete_statement)

    mysql = """
      INSERT
      INTO Results
      (MatchId, CompetitorId, Votes, Percentage, IsWinner)
      VALUES
      (%s, %s, %s, %s, %s)
    """ % (match_id, competitor_id, votes, percentage, is_winner)

    try:
      self.__dbh.execute(mysql)
    except:
      print('Error executing: ' + mysql)
      raise

  def AddCompetitor(self, name, description=None):
    """Add a competitor to the Competitors table.

    @param name: The competitor's name.
    @type  name: string

    @param description: An optional description of the character.
    @type  description: string

    """

    if description is None:
      description = 'NULL'

    mysql = """
      INSERT
      INTO Competitors
      (Name, Description)
      VALUES ('%s', '%s')
    """ % (name, description)

    self.__dbh.execute(mysql)

  def LookupCompetitorId(self, name, type='character'):
    """Look up a character's CompetitorId.

    @param name: The competitor's name.
    @type  name: string

    @return: The competitor id of the character.
    @rtype:  integer

    """

    mysql = 'SELECT * From Competitors WHERE (Name="%s" OR ShortName="%s") AND Type="%s"' % (
      name, name, type)

    self.__dbh.execute(mysql)
    results = self.__dbh.fetchall()

    if results:
      return results[0]['CompetitorId']
    else:
      return None
    
  def GetCompetitors(self, name, type='character'):
    """Look up a competitor's info.

    @param name: The competitor's name.
    @type  name: string

    @return: The competitor's DB record.
    @rtype:  dict

    """

    # TODO(dscotton): Get this to handle text with apostrophes and quotes.

    mysql = """
      SELECT *
      FROM Competitors
      WHERE Name LIKE "%%%s%%"
      AND Type='%s'
    """ % (name, type)

    self.__dbh.execute(mysql)
    results = self.__dbh.fetchall()

    if results:
      return results
    else:
      return None

  def GetCompetitorIdInMatch(self, name, match_id):
    """Get the ID of a competitor with a given name in a given match.

    This avoids problems where two competitors may match a given shortname (eg. Ryu and
    Stider Hiryu).

    @param name: The name of the competitor to look up.
    @type  name: string

    @param match_id: The ID of the match these results correspond to.
    @type  match_id: integer

    @return: The ID of the given competitor.
    @rtype:  integer

    """

    mysql = """
      SELECT *
      FROM
        Competitors c, Results r
      WHERE
        c.CompetitorId = r.CompetitorId
        AND c.Name LIKE "%%%s%%"
        AND r.MatchId = %d
    """ % (name, int(match_id))

    self.__dbh.execute(mysql)
    result = self.__dbh.fetchone()

    if result:
      return result
    else:
      return None

  def GetCompetitorsInMatch(self, match_id):
    """Get all competitors in a given match.

    @param match_id: The ID of the match these results correspond to.
    @type  match_id: integer

    @return: All competitors in the match.
    @rtype: List of dicts

    """

    mysql = """
      SELECT *
      FROM
        Competitors c, Results r
      WHERE
        c.CompetitorId = r.CompetitorId
        AND r.MatchId = %d
    """ % (name, int(match_id))

    self.__dbh.execute(mysql)
    result = self.__dbh.fetchall()

    if result:
      return result
    else:
      return None

  def IsCompetitorInRounds(self, competitor_id, contest_id, round_nums):
    """Check whether a competitor is in a given contest round.

    @param competitor_id: The competitor to check.
    @type  competitor_id: integer

    @param contest_id: The contest to test for inclusion in.
    @type  contest_id: integer

    @param round_nums: The rounds to look for the competitor in.
    @type  round_nums: list of integers

    @return: True if the competitor is in the contest and >=1 of the rounds given.
    @rtype:  boolean
    """

    mysql = """
      SELECT *
      FROM Competitors c, Results r, Matches m
      WHERE c.CompetitorId = r.CompetitorId
      AND r.MatchId = m.MatchId
      AND c.CompetitorId = %s
      AND m.ContestId = %s
      AND m.RoundNumber IN (%s)
    """ % (competitor_id, contest_id, ','.join([str(r) for r in round_nums]))

    self.__dbh.execute(mysql)
    result = self.__dbh.fetchone()

    if result:
      return True
    else:
      return False

  def GetMatchScores(self, match_id):
    """Generate a list of scores and rankings for one match.

    @param match_id: The match to get scores from.
    @type  match_id: integer

    @return: A list of dictionaries, each one containing the keys 'Name',
             'Score', and 'Ranking'
    @rtype:  list

    """

    match_info = self.GetMatches(match_id=match_id)[0]
    contest_info = self.GetContest(match_info['ContestId'])
    if contest_info['CompetitorsPerMatch'] == 2:
      return self.GetMatchScoresOneOnOne(match_id)
    elif contest_info['CompetitorsPerMatch'] == 4:
      return self.GetMatchScoresFourWay(match_id)

  def GetMatchScoresFourWay(self, match_id):
    """Generate a list of scores and rankings for one match.

    This is exactly like the GetMatchScoresOneOnOne method, except
    that it uses a different query for scoring matches with four
    options.

    @param match_id: The match to get scores from.
    @type  match_id: integer

    @return: A list of dictionaries, each one containing the keys 'Name',
             'Score', and 'Ranking'
    @rtype:  list

    """

    mysql = """
      SELECT
        Matches.MatchId As MatchId,
        Users.UserId As UserId,
        Users.Name,
        FLOOR(100 *
              ((50 - ABS(Predictions1.Percentage - Results1.Percentage)) +
               (50 - ABS(Predictions2.Percentage - Results2.Percentage)) +
               (50 - ABS(Predictions3.Percentage - Results3.Percentage)) +
               (50 - ABS(Predictions4.Percentage - Results4.Percentage))) / 4)
             / 100 As Score,
        Competitors1.ShortName As Competitor1,
        Predictions1.Percentage As Prediction1,
        Results1.Percentage As Result1,
        (50 - ABS( Predictions1.Percentage - Results1.Percentage)) As Score1,
        Competitors2.ShortName As Competitor2,
        Predictions2.Percentage As Prediction2,
        Results2.Percentage As Result2,
        50 - ABS( Predictions2.Percentage - Results2.Percentage) As Score2,
        Competitors3.ShortName As Competitor3,
        Predictions3.Percentage As Prediction3,
        Results3.Percentage As Result3,
        50 - ABS( Predictions3.Percentage - Results3.Percentage) As Score3,
        Competitors4.ShortName As Competitor4,
        Predictions4.Percentage As Prediction4,
        Results4.Percentage As Result4,
        50 - ABS( Predictions4.Percentage - Results4.Percentage) As Score4
      FROM
        Users,
        Matches,
        Competitors As Competitors1,
        Predictions As Predictions1,
        Results As Results1,
        Competitors As Competitors2,
        Predictions As Predictions2,
        Results As Results2,
        Competitors As Competitors3,
        Predictions As Predictions3,
        Results As Results3,
        Competitors As Competitors4,
        Predictions As Predictions4,
        Results As Results4
      WHERE
        Matches.MatchId = %d AND
        Results1.Percentage IS NOT NULL AND
        Users.UserId = Predictions1.UserId AND
        Predictions1.MatchId = Matches.MatchId AND
        Results1.MatchId = Matches.MatchId AND
        Competitors1.CompetitorId = Predictions1.WinnerId AND
        Results1.CompetitorId = Competitors1.CompetitorId AND
        Users.UserId = Predictions2.UserId AND
        Predictions2.MatchId = Matches.MatchId AND
        Results2.MatchId = Matches.MatchId AND
        Competitors2.CompetitorId = Predictions2.WinnerId AND
        Results2.CompetitorId = Competitors2.CompetitorId AND
        Users.UserId = Predictions3.UserId AND
        Predictions3.MatchId = Matches.MatchId AND
        Results3.MatchId = Matches.MatchId AND
        Competitors3.CompetitorId = Predictions3.WinnerId AND
        Results3.CompetitorId = Competitors3.CompetitorId AND
        Users.UserId = Predictions4.UserId AND
        Predictions4.MatchId = Matches.MatchId AND
        Results4.MatchId = Matches.MatchId AND
        Competitors4.CompetitorId = Predictions4.WinnerId AND
        Results4.CompetitorId = Competitors4.CompetitorId AND
        Competitors1.Name < Competitors2.Name AND
        Competitors2.Name < Competitors3.Name AND
        Competitors3.Name < Competitors4.Name
      ORDER BY
        Score DESC,
        Users.UserId ASC
    """ % (match_id)

    self.__dbh.execute(mysql)
    results = self.__dbh.fetchall()

    i = 0
    while i < len(results):
      if i == 0 or results[i]['Score'] < results[i - 1]['Score']:
        results[i]['Ranking'] = i + 1
      elif results[i]['Score'] == results[i - 1]['Score']:
        results[i]['Ranking'] = results[i - 1]['Ranking']
      else:
        raise Exception, "Something went wrong."
      
      i += 1

    return results

  def GetMatchScoresOneOnOne(self, match_id):
    """Generate a list of scores and rankings for one match.

    @param match_id: The match to get scores from.
    @type  match_id: integer

    @return: A list of dictionaries, each one containing the keys 'Name',
             'Score', and 'Ranking'
    @rtype:  list

    """

    mysql = """
      SELECT
        Users.Name as Name,
        Users.UserId,
        Competitors.Name as Pick,
        Predictions.WinnerId as WinnerId,
        Predictions.Percentage as Guess,
        if(Results.IsWinner = 1,
           50 - ABS(Predictions.Percentage - Results.Percentage),
           if(if(Matches.ContestId = 2,
                 25 - ABS(Predictions.Percentage - Results.Percentage),
                 if(Matches.ContestId >= 7,
                    45 - ABS(Predictions.Percentage - Results.Percentage),
                    45 - 2 * ABS(Predictions.Percentage - Results.Percentage))
                 ) < 0,
              0,
              if(Matches.ContestId = 2,
                 25 - ABS(Predictions.Percentage - Results.Percentage),
                 if(Matches.ContestId >= 7,
                    45 - ABS(Predictions.Percentage - Results.Percentage),
                    45 - 2 * ABS(Predictions.Percentage - Results.Percentage))
                 )
              )
           ) as Score
      FROM
        Users,
        Competitors,
        Predictions,
        Results,
        Matches
      WHERE Results.MatchId = Matches.MatchId
      AND Results.CompetitorId = Predictions.WinnerId
      AND Predictions.MatchId = Matches.MatchId
      AND Users.UserId = Predictions.UserId
      AND Predictions.MatchId = %s
      AND Predictions.WinnerId = Competitors.CompetitorId
      ORDER BY Score DESC
    """ % match_id

    self.__dbh.execute(mysql)
    results = self.__dbh.fetchall()

    i = 0
    while i < len(results):
      if i == 0 or results[i]['Score'] < results[i - 1]['Score']:
        results[i]['Ranking'] = i + 1
      elif results[i]['Score'] == results[i - 1]['Score']:
        results[i]['Ranking'] = results[i - 1]['Ranking']
      else:
        raise Exception, "Something went wrong."
      
      i += 1

    return results

  def GetContestScores(self, match_id):
    """Generate a list of scores and rankings for a contest.

    @param match_id: The last match to get scores from. (Returns total
                     scores through this day).
    @type  match_id: integer

    @return: A list of dictionaries, each one containing the keys 'Name',
             'Score', and 'Ranking'
    @rtype:  list

    """

    match = self.GetMatches(match_id=match_id)[0]
    contest_id = match['ContestId']
    contest_info = self.GetContest(contest_id)
    if contest_info['CompetitorsPerMatch'] == 2:
      return self.GetContestScoresOneOnOne(match_id, contest_id)
    elif contest_info['CompetitorsPerMatch'] == 4:
      return self.GetContestScoresFourWay(match_id, contest_id)

  def GetContestScoresFourWay(self, match_id, contest_id):
    """Helper function for total scores and rankings in a four way contest.

    @param match_id: The last match to get scores from. (Returns total
                     scores through this day).
    @type  match_id: integer

    @param contest_id: The contest to calculate scores for.
    @type  contest_id: integer

    @return: A list of dictionaries, each one containing the keys 'Name',
             'Score', and 'Ranking'
    @rtype:  list

    """

    mysql = """
      SELECT
        Users.UserId As UserId,
        Users.Name As Name,
        SUM(FLOOR(100*(
               (50 - ABS( Predictions1.Percentage - Results1.Percentage))+
               (50 - ABS( Predictions2.Percentage - Results2.Percentage))+
               (50 - ABS( Predictions3.Percentage - Results3.Percentage))+
               (50 - ABS( Predictions4.Percentage - Results4.Percentage)))/4)
               /100) As Score
      FROM
        Users,
        Matches As Matches1,
        Predictions As Predictions1,
        Results As Results1,
        Predictions As Predictions2,
        Results As Results2,
        Predictions As Predictions3,
        Results As Results3,
        Predictions As Predictions4,
        Results As Results4
      WHERE
        Matches1.ContestId = %d
        AND Matches1.MatchId <= %d
        AND Results1.Percentage IS NOT NULL
        AND Users.UserId = Predictions1.UserId
        AND Predictions1.MatchId = Matches1.MatchId
        AND Results1.MatchId = Matches1.MatchId
        AND Predictions1.WinnerId = Results1.CompetitorId
        AND Users.UserId = Predictions2.UserId
        AND Predictions2.MatchId = Matches1.MatchId
        AND Results2.MatchId = Matches1.MatchId
        AND Predictions2.WinnerId = Results2.CompetitorId
        AND Users.UserId = Predictions3.UserId
        AND Predictions3.MatchId = Matches1.MatchId
        AND Results3.MatchId = Matches1.MatchId
        AND Predictions3.WinnerId = Results3.CompetitorId
        AND Users.UserId = Predictions4.UserId
        AND Predictions4.MatchId = Matches1.MatchId
        AND Results4.MatchId = Matches1.MatchId
        AND Predictions4.WinnerId = Results4.CompetitorId
        AND Results1.CompetitorId < Results2.CompetitorId
        AND Results2.CompetitorId < Results3.CompetitorId
        AND Results3.CompetitorId < Results4.CompetitorId
      GROUP BY
        Users.UserId
      ORDER BY
        Score DESC,
        Users.UserId ASC;
    """ % (contest_id, match_id)

    self.__dbh.execute(mysql)
    results = self.__dbh.fetchall()

    i = 0
    while i < len(results):
      if i == 0 or results[i]['Score'] < results[i - 1]['Score']:
        results[i]['Ranking'] = i + 1
      elif results[i]['Score'] == results[i - 1]['Score']:
        results[i]['Ranking'] = results[i - 1]['Ranking']
      else:
        raise Exception, "Something went wrong."
      
      i += 1

    return results

  def GetContestScoresOneOnOne(self, match_id, contest_id):
    """Helper function for getting total scores and rankings in a 1v1 contest.

    @param match_id: The last match to get scores from. (Returns total
                     scores through this day).
    @type  match_id: integer

    @param contest_id: The contest to calculate scores for.
    @type  contest_id: integer

    @return: A list of dictionaries, each one containing the keys 'Name',
             'Score', and 'Ranking'
    @rtype:  list

    """

    mysql = """
      SELECT
        Users.Name as Name,
        Users.UserId,
        SUM(if(Results.IsWinner = 1,
               50 - ABS(Predictions.Percentage - Results.Percentage),
               if(if(Matches.ContestId = 2,
                     25 - ABS(Predictions.Percentage - Results.Percentage),
                     if(Matches.ContestId >= 7,
                        45 - ABS(Predictions.Percentage - Results.Percentage),
                        45 - 2 * ABS(Predictions.Percentage - Results.Percentage))
                     ) < 0,
                  0, 
                  if(Matches.ContestId = 2,
                     25 - ABS(Predictions.Percentage - Results.Percentage),
                     if(Matches.ContestId >= 7,
                        45 - ABS(Predictions.Percentage - Results.Percentage),
                        45 - 2 * ABS(Predictions.Percentage - Results.Percentage))
                     )
                  )
               )
            ) as Score
      FROM
        Users,
        Competitors,
        Predictions,
        Results,
        Matches
      WHERE Results.MatchId = Matches.MatchId
      AND Results.CompetitorId = Predictions.WinnerId
      AND Predictions.MatchId = Matches.MatchId
      AND Users.UserId = Predictions.UserId
      AND Matches.ContestId = %s
      AND Predictions.MatchId <= %s
      AND Predictions.WinnerId = Competitors.CompetitorId
      GROUP BY Users.UserId
      ORDER BY Score DESC
    """ % (contest_id, match_id)

    self.__dbh.execute(mysql)
    results = self.__dbh.fetchall()

    i = 0
    while i < len(results):
      if i == 0 or results[i]['Score'] < results[i - 1]['Score']:
        results[i]['Ranking'] = i + 1
      elif results[i]['Score'] == results[i - 1]['Score']:
        results[i]['Ranking'] = results[i - 1]['Ranking']
      else:
        raise Exception, "Something went wrong."
      
      i += 1

    return results

  def SetMatchRanking(self, user_id, match_id, match_rank):
    """Set one user's ranking for a specific match.

    @param user_id: The ID of the user whose record this is.
    @type  user_id: integer

    @param match_id: The match ID the result is for.
    @type  match_id: integer

    @param match_rank: The user's ranking in this match.
    @type  match_rank: integer

    """

    # Check whether there is already a result for this (user, match)
    # pair, and if so, update instead of inserting.

    mysql = """
      SELECT *
      FROM DailyStandings
      WHERE MatchId = %s
      AND UserId = %s
    """ % (match_id, user_id)

    self.__dbh.execute(mysql)
    results = self.__dbh.fetchall()

    if results:
      mysql = """
        UPDATE DailyStandings
        SET MatchRanking = %s
        WHERE MatchId = %s
        AND UserId = %s
      """ % (match_rank, match_id, user_id)

      self.__dbh.execute(mysql)

    else:
      mysql = """
        INSERT INTO DailyStandings
        (MatchId, UserId, MatchRanking)
        VALUES (%s, %s, %s)
      """ % (match_id, user_id, match_rank)

      self.__dbh.execute(mysql)

  def SetMatchScore(self, user_id, match_id, match_score):
    """Set one user's score in DailyStandings for a specific match.

    @param user_id: The ID of the user whose record this is.
    @type  user_id: integer

    @param match_id: The match ID the result is for.
    @type  match_id: integer

    @param match_rank: The user's score in this match.
    @type  match_rank: float

    """

    # Check whether there is already a result for this (user, match)
    # pair, and if so, update instead of inserting.

    mysql = """
      SELECT *
      FROM DailyStandings
      WHERE MatchId = %s
      AND UserId = %s
    """ % (match_id, user_id)

    self.__dbh.execute(mysql)
    results = self.__dbh.fetchall()

    if results:
      mysql = """
        UPDATE DailyStandings
        SET MatchScore = %s
        WHERE MatchId = %s
        AND UserId = %s
      """ % (match_score, match_id, user_id)

      self.__dbh.execute(mysql)

    else:
      mysql = """
        INSERT INTO DailyStandings
        (MatchId, UserId, MatchScore)
        VALUES (%s, %s, %s)
      """ % (match_id, user_id, match_score)

      self.__dbh.execute(mysql)

  def SetOverallRanking(self, user_id, match_id, overall_rank):
    """Set one user's ranking for a specific match.

    @param user_id: The ID of the user whose record this is.
    @type  user_id: integer

    @param match_id: The match ID the result is for.
    @type  match_id: integer

    @param overall_rank: The user's ranking in this match.
    @type  overall_rank: integer

    """

    # Check whether there is already a result for this (user, match)
    # pair, and if so, update instead of inserting.

    mysql = """
      SELECT *
      FROM DailyStandings
      WHERE MatchId = %s
      AND UserId = %s
    """ % (match_id, user_id)

    self.__dbh.execute(mysql)
    results = self.__dbh.fetchall()

    if results:
      mysql = """
        UPDATE DailyStandings
        SET OverallRanking = %s
        WHERE MatchId = %s
        AND UserId = %s
      """ % (overall_rank, match_id, user_id)

      self.__dbh.execute(mysql)

    else:
      mysql = """
        INSERT INTO DailyStandings
        (MatchId, UserId, OverallRanking)
        VALUES (%s, %s, %s)
      """ % (match_id, user_id, overall_rank)

      self.__dbh.execute(mysql)

  def GetContest(self, contest_id):
    """Look up information about a given contest.

    @param contest_id: The contest to look up.
    @type  contest_id: integer

    @return: Information about the specific contest, in a dict.
    @rtype:  dict

    """

    mysql = """
      SELECT *
      FROM Contests
      WHERE ContestId = %d
    """ % int(contest_id)

    self.__dbh.execute(mysql)
    results = self.__dbh.fetchone()
    return results

  def AddMessage(self, topic_id, topic_title, username, timestamp, text):
    """Add a new message to the database.

    @param topic_id: The ID of the topic the message was posted in.
    @type  topic_id: int

    @param topic_title: The name of the topic the message was posted in.
    @type  topic_title: str

    @param username: The user who posted the message.
    @type  username: str

    @param timestamp: The time the message was posted (Pacific Time).
    @type  timestamp: datetime

    @param text: The text of the message.
    @type  text: str

    """

    mysql = """
      INSERT INTO Messages
      (TopicId, TopicTitle, UserName, Timestamp, Body)
      VALUES (%s, "%s", "%s", "%s", "%s")
    """ % (topic_id, topic_title, username, timestamp, text)

    self.__dbh.execute(mysql)

  def EscapeString(self, text):
    """Wrapper for MySQLdb's escape_string method.

    @param text: The string to escape.
    @type  text: str

    @return: The escaped string.
    @rtype:  str

    """

    return MySQLdb.escape_string(text)
