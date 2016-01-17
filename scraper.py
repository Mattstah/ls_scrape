from pyvirtualdisplay import Display
from selenium.webdriver import Firefox

# I would have liked to use PhantomJS for this but it keeps
# hanging on browser.get so I've resorted to using firefox
# in a virtual display which is set to be invisible.

class Scraper(object):
	def __init__(self, url):
		self.url = url
		self.browser = None
		self.display = Display(
			visible=0,
			size=(800, 600)
		)

	def open(self):
		self.display.start()
		self.browser = Firefox()

	def close(self):
		self.browser.quit()
		self.display.stop()

	def scrape(self):
		self.browser.get(self.url)
		self.browser.delete_all_cookies()
		return self.browser.page_source
