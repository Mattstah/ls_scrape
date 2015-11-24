import logging
import selenium.webdriver
import sqlite3
import time

SCRAPE_TARGET_URL = 'http://www.livescores.com'
SQLITE_DB_NAME = 'livescores_event_urls.db'
POLL_FREQUENCY_SECS = 5

def create_browser():
	return selenium.webdriver.PhantomJS()

def kill_browser(browser):
	browser.quit()

def get_event_links(browser):
	browser.get(SCRAPE_TARGET_URL)

	def get_href(elt):
		return elt.get_attribute('href')

	event_links = map(
		get_href,
		browser.find_elements_by_class_name('scorelink')
	)

	print "Loaded %s event links." % len(event_links)

	return event_links

def save_event_links(sqlite_conn, event_links):
	c = sqlite_conn.cursor()

	c.executemany(
		"insert or replace into event_urls(url) values (?)",
		[(event_link,) for event_link in event_links]
	)

	sqlite_conn.commit()

def main():
	browser = create_browser()
	sqlite_conn = sqlite3.connect(SQLITE_DB_NAME)

	try:
		while True:
			event_links = get_event_links(browser)
			save_event_links(sqlite_conn, event_links)
			time.sleep(POLL_FREQUENCY_SECS)

	finally:
		kill_browser(browser)
		sqlite_conn.close()

if __name__ == "__main__":
    main()
