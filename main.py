import logging
import random
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

def get_event_links(browser):
	def get_href(elt):
		return elt.get_attribute('href')

	event_links = map(
		get_href,
		browser.find_elements_by_class_name('scorelink')
	)

	logger.info("Loaded %s event links.", len(event_links))

	return event_links

def save_event_links(sqlite_conn, event_links):
	c = sqlite_conn.cursor()

	def extract_ev_id(event_link):
		return int(event_link.split('/')[-2].split('-')[1])

	c.executemany(
		"insert or replace into ev_urls(ev_id, url) values (?, ?)",
		[(extract_ev_id(event_link), event_link) for event_link in event_links]
	)

	sqlite_conn.commit()

def get_event_states(browser):
	states = []

	rows = browser.find_element_by_class_name('content')
	children = rows.find_elements_by_xpath('./*')

	country = None
	league = None
	start_date = None

	for child in children:
		child_class = child.get_attribute('class')

		if 'row' not in child_class:
			continue

		elif 'mt4' in child_class:
			start_date = child.find_element_by_class_name('right').text
			start_date = fmt_date(start_date)

			left = child.find_element_by_class_name('left')
			left = left.find_elements_by_css_selector('a')

			country = left[0].text
			league = left[1].text

		else:
			ev_id = int(child.get_attribute('data-eid'))

			logger.info("Processing state for ev_id %s.", ev_id)

			state = process_event_state(child)

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
	secs = raw_state.find_element_by_class_name('min').text
	scores = raw_state.find_element_by_class_name('sco')

	sl = scores.find_elements_by_class_name('scorelink')

	if sl:
		home_score, away_score = sl[0].text.split(' - ')
	else:
		home_score, away_score = scores.text.split(' - ')

	home_score = int(home_score) if home_score != '?' else None
	away_score = int(away_score) if away_score != '?' else None

	teams = raw_state.find_elements_by_class_name('ply')
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

	try:
		while True:
			browser.get(SCRAPE_TARGET_URL)

			event_links = get_event_links(browser)
			save_event_links(sqlite_conn, event_links)

			event_states = get_event_states(browser)
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
