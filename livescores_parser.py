import datetime
import re

import BeautifulSoup

from utils import fmt_date_closest_year, get_logger

logger = get_logger(__name__)

class ParseRowException(Exception):
	pass

def parse_page(page_html):
	bs = BeautifulSoup.BeautifulSoup(page_html)

	content = bs.find('div', {'class' : 'content'})
	rows = content.findAll('div', {'class' : re.compile('.*row.*')})

	return parse_rows(rows)

def parse_rows(rows):
	matches = []

	country = None
	league = None
	start_date = None

	for row in rows:
		row_class = row['class']

		if 'mt4' in row_class or 'bt0' in row_class:
			start_date = row.find(
				'div',
				{'class' : re.compile('.*right.*')}
			).text

			if start_date != '':
				start_date = fmt_date_closest_year(start_date, '%B %d')

			else:
				start_date = datetime.date.today()

		if 'mt4' in row_class:
			left = row.find('div', {'class' : re.compile('.*left.*')})
			links = left.findAll('a')

			country = links[0].text
			league = links[1].text

		elif 'bt0' in row_class:
			country = None
			league = None

		else:
			try:
				match = parse_match(row)

				if match is None:
					continue

				else:
					teams, state = match

			except ParseRowException, e:
				logger.error(e)
				continue

			match_id = int(row['data-eid'])			

			match = {
				'match_id' : match_id,
				'start_date' : start_date,
				'country' : country,
				'league' : league
			}

			match['state'] = state

			match.update(teams)

			matches.append(match)

	return matches

def parse_match(raw_match):
	teams = raw_match.findAll('div', {'class' : re.compile('.*ply.*')})

	home_team = teams[0].text
	away_team = teams[1].text

	match_info = {
		'home_team' : home_team,
		'away_team' : away_team,
	}

	mins = raw_match.find('div', {'class' : 'min'}).text

	if "'" in mins or mins in ('HT', 'FT'):
		scores = raw_match.find('div', {'class' : 'sco'})
		sl = scores.find('a', {'class' : 'scorelink'})

		if sl:
			home_score, away_score = sl.text.split(' - ')

		else:
			home_score, away_score = scores.text.split(' - ')

		home_score = int(home_score) if home_score != '?' else None
		away_score = int(away_score) if away_score != '?' else None

		state = {
			'home_score' : home_score,
			'away_score' : away_score,
			'mins' : mins,
		}

	elif ':' in mins:
		match_datetime = datetime.datetime.strptime(mins, '%H:%M')
		match_info['start_time'] = match_datetime.time()
		state = None

	elif any(x in mins.lower() for x in ('aaw', 'int', 'aban', 'postp')):
		# Away Awarded Win, Interrupted, Abandoned, Postponed
		return None

	else:
		raise ParseRowException(
			"Failed to parse row %s. Unknown mins: %s." % (raw_match, mins)
		)

	return match_info, state
