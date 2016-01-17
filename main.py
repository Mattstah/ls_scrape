import random
import time

from football import get_db_session, Match, State
from livescores_parser import parse_page
from scraper import Scraper
from utils import get_logger, LogPrefix

logger = get_logger(__name__)

DB_NAME = 'sqlite:///matches.db'
MATCHES_FLUSH_AT = 1000
SCRAPE_TARGET = 'http://www.livescores.com'
POLL_FREQUENCY_SECS = 10
POLL_FREQUENCY_VARIANCE = 5


def emit_match(match):
	pass

def create_match(match):
	state = match.pop('state')

	if state is not None:
		state = State(**state)

	match = Match(**match)
	match.state = state

	return match

def update_obj(obj, data):
	changes = {}

	o = object()
	o_nvl = lambda x: '<Unset>' if x == o else x

	for k, v in data.iteritems():
		old_val = getattr(obj, k, o)
		setattr(obj, k, v)

		if old_val != v:
			changes[k] = (o_nvl(old_val), v)

	return changes

def run(scraper):
	db_session = get_db_session(DB_NAME)

	matches = db_session.query(Match).all()
	matches = {match.match_id : match for match in matches}

	while True:
		logger.info("Scraping...")

		html = scraper.scrape()
		parsed_matches = parse_page(html)

		for match in parsed_matches:
			match_id = match['match_id']

			prefix = '[%s]' % match_id

			with LogPrefix(logger, prefix):
				existing_match = matches.get(match_id)

				if existing_match is None:
					new_match = create_match(match)
					matches[match_id] = new_match
					db_session.add(new_match)
					logger.info("New match: %s", match)

				else:
					state = match.pop('state')
					match_changes = update_obj(existing_match, match)

					if match_changes:
						logger.info("Changed match: %s", match_changes)

					if state is None and existing_match.state is not None:
						existing_match.state = None
						logger.info("Removed match state.")

					elif state is not None and existing_match.state is None:
						existing_match.state = State(**state)
						logger.info("Added match state: %s", state)

					elif state is not None and existing_match.state is not None:
						state_changes = update_obj(existing_match.state, state)

						if state_changes:
							logger.info("Changed state: %s", state_changes)

					db_session.add(existing_match)

			emit_match(match)

		db_session.commit()

		# We don't really need to delete the matches, they're not that big,
		# but lets flush them when they get fairly large...
		if len(matches) >= MATCHES_FLUSH_AT:
			parsed_match_ids = set([match['match_id'] for match in parsed_matches])
			stored_match_ids = set(matches.keys())

			matches_to_del = stored_match_ids - parsed_matches

			for match_id in matches_to_del:
				del matches[match_id]

		sleep_duration = random.randint(
			POLL_FREQUENCY_SECS - POLL_FREQUENCY_VARIANCE,
			POLL_FREQUENCY_SECS + POLL_FREQUENCY_VARIANCE
		)

		time.sleep(sleep_duration)

try:
	s = Scraper(SCRAPE_TARGET)
	s.open()
	run(s)

finally:
	s.close()