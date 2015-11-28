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
	browser.get(SCRAPE_TARGET_URL)

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
		return event_link.split('/')[-2]

	c.executemany(
		"insert or replace into ev_urls(ev_id, url) values (?, ?)",
		[(extract_ev_id(event_link), event_link) for event_link in event_links]
	)

	sqlite_conn.commit()

def main():
	browser = create_browser()
	sqlite_conn = sqlite3.connect(SQLITE_DB_NAME)

	try:
		while True:
			event_links = get_event_links(browser)
			save_event_links(sqlite_conn, event_links)
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
