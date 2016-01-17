import datetime
import functools
import logging

logging.basicConfig(
	level=logging.INFO,
	format='%(asctime)s %(levelname)s: %(prefix)s %(message)s'
)

def fmt_date_closest_year(date_str, fmt):
	cur_date = datetime.date.today()
	year = cur_date.year

	date = datetime.datetime.strptime(date_str, fmt).date()

	possible_dates = [
		date.replace(year=y)
		for y in (year -1, year, year + 1)
	]

	def day_difference(d1, d2):
		return abs((d1 - d2).days)

	day_difference_from_today = functools.partial(day_difference, cur_date)

	day_differences = map(day_difference_from_today, possible_dates)

	_, correct_date = min(zip(day_differences, possible_dates))

	return correct_date

def get_logger(module_name):
	return logging.LoggerAdapter(
		logging.getLogger(module_name),
		{'prefix' : ''},
	)

class LogPrefix(object):
	def __init__(self, logger, prefix):
		self.logger = logger
		self.prefix = str(prefix)

		self.inital_logger_prefix = self.logger.extra['prefix']

	def __enter__(self):
		self.logger.extra['prefix'] += self.prefix

	def __exit__(self, *args, **kwargs):
		self.logger.extra['prefix'] = self.inital_logger_prefix
