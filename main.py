import BeautifulSoup
import logging
import random
import re
import selenium.webdriver
import sqlite3
import time

from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

SCRAPE_TARGET_URL = 'http://www.livescores.com'
SQLITE_DB_NAME = 'livescores_event_urls.db'
POLL_FREQUENCY_SECS = 10
POLL_FREQUENCY_VARIANCE = 5

logging.basicConfig(
	level=logging.INFO,
	format='%(asctime)s %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

def create_browser():
	# Change our user agent so we don't look like PhantomJS.
	dcap = dict(DesiredCapabilities.PHANTOMJS)
	dcap["phantomjs.page.settings.userAgent"] = (
		"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_4) "
		"AppleWebKit/537.36 (KHTML, like Gecko) Chrome/29.0.1547.57 Safari/537.36"
	)

	return selenium.webdriver.PhantomJS(desired_capabilities=dcap)

def get_event_links(bs):
	return [
		elt['href'] for elt in bs.findAll('a', {'class':'scorelink'})
	]

def save_event_links(sqlite_conn, event_links):
	c = sqlite_conn.cursor()

	def extract_ev_id(event_link):
		return int(event_link.split('/')[-2].split('-')[1])

	c.executemany(
		"insert or replace into ev_urls(ev_id, url) values (?, ?)",
		[(extract_ev_id(event_link), event_link) for event_link in event_links]
	)

	sqlite_conn.commit()

def get_event_states(bs):
	states = []

	content = bs.find('div', {'class' : 'content'})
	rows = content.findAll('div', {'class' : re.compile('.*row.*')})

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
				start_date = fmt_date(start_date)

		if 'mt4' in row_class:
			left = row.find('div', {'class' : re.compile('.*left.*')})
			links = left.findAll('a')

			country = links[0].text
			league = links[1].text

		elif 'bt0' in row_class:
			country = None
			league = None

		else:
			ev_id = int(row['data-eid'])

			state = process_event_state(row)

			ev_info = {
				'ev_id' : ev_id,
				'start_date' : start_date,
				'country' : country,
				'league' : league
			}

			state.update(ev_info)

			states.append(state)

	return states

def fmt_date(date):
	localtime = time.localtime()

	cur_date = localtime.tm_mday
	cur_month = localtime.tm_mon
	cur_year = localtime.tm_year

	# We're not given the year, so just assume the current year.
	x = time.strptime(str(cur_year) + date, "%Y%B %d")

	# If assuming the year is this year means that the date is before today then
	# the year is probably next year, so assume that instead.
	if x < time.strptime(str(cur_year)+str(cur_month)+str(cur_date), '%Y%m%d'):
		x = time.strptime(str(cur_year + 1) + date, "%Y%B %d")

	return time.strftime("%Y-%m-%d", x)

def process_event_state(raw_state):
	secs = raw_state.find('div', {'class' : 'min'}).text

	scores = raw_state.find('div', {'class' : 'sco'})
	sl = scores.find('a', {'class' : 'scorelink'})

	if sl:
		home_score, away_score = sl.text.split(' - ')

	else:
		home_score, away_score = scores.text.split(' - ')

	home_score = int(home_score) if home_score != '?' else None
	away_score = int(away_score) if away_score != '?' else None

	teams = raw_state.findAll('div', {'class' : re.compile('.*ply.*')})
	home_team = teams[0].text
	away_team = teams[1].text

	state = {
		'home_team' : home_team,
		'away_team' : away_team,
		'home_score' : home_score,
		'away_score' : away_score
	}

	state['secs'] = None
	state['start_time'] = None

	if "'" in secs or secs in ('HT', 'FT'):
		state['secs'] = secs

	elif ':' in secs:
		state['start_time'] = secs

	return state

def save_event_states(sqlite_conn, event_states):
	c = sqlite_conn.cursor()

	ev_info = [
		'ev_id',
		'start_date',
		'start_time',
		'home_team',
		'away_team',
		'country',
		'league'
	]

	ev_info_sql = "insert or replace into ev_info(%s) values (%s)" % (
		','.join(ev_info),
		','.join(['?'] * len(ev_info))
	)

	c.executemany(
		ev_info_sql,
		[[event_state[x] for x in ev_info] for event_state in event_states]
	)

	ev_state = ['ev_id', 'home_score', 'away_score', 'secs']

	ev_state_sql = "insert or replace into ev_state(%s) values (%s)" % (
		','.join(ev_state),
		','.join(['?'] * len(ev_state))
	)

	c.executemany(
		ev_state_sql,
		[[event_state[x] for x in ev_state] for event_state in event_states]
	)

	sqlite_conn.commit()

def main():
	browser = create_browser()
	sqlite_conn = sqlite3.connect(SQLITE_DB_NAME)

	browser.get(SCRAPE_TARGET_URL)

	try:
		while True:
			logging.info("Loaded page %s", SCRAPE_TARGET_URL)

			bs = BeautifulSoup.BeautifulSoup(browser.page_source)

			event_links = get_event_links(bs)
			logger.info("Loaded %s event links", len(event_links))

			save_event_links(sqlite_conn, event_links)

			event_states = get_event_states(bs)
			save_event_states(sqlite_conn, event_states)

			sleep_duration = random.randint(
				POLL_FREQUENCY_SECS - POLL_FREQUENCY_VARIANCE,
				POLL_FREQUENCY_SECS + POLL_FREQUENCY_VARIANCE
			)

			time.sleep(sleep_duration)

	finally:
		browser.quit()
		sqlite_conn.close()

if __name__ == "__main__":
    main()
