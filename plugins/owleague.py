import dateutil.parser
import requests
import pytz
import botologist.plugin


def get_owl_data():
	resp = requests.get('https://overwatchleague.com/en-gb/api/live-match?locale=en-gb')
	resp.raise_for_status()
	return resp.json()


def get_match_info(match_data):
	teams = match_data['competitors']
	return '%s vs %s' % (teams[0]['name'], teams[1]['name'])


def get_match_time(match_data, tz=None):
	dt = dateutil.parser.parse(match_data['startDate'])
	return dt.astimezone(tz=tz).strftime('%Y-%m-%d %H:%M %z')


def get_current_match_info(data):
	match = data.get('data', {}).get('liveMatch', {})
	if not match or match['liveStatus'] != 'LIVE':
		return
	return 'Live now: %s' % get_match_info(match)


def get_next_match_info(data, tz=None):
	match = data.get('data', {}).get('nextMatch', {})
	if not match:
		match = data.get('data', {}).get('liveMatch', {})
		if not match['liveStatus'] == 'UPCOMING':
			return
	return 'Next match: %s at %s' % (
		get_match_info(match),
		get_match_time(match, tz=tz),
	)


class OwleaguePlugin(botologist.plugin.Plugin):
	def __init__(self, bot, channel):
		super().__init__(bot, channel)
		self.prev_state = None
		self.tz = pytz.timezone(self.bot.config.get('output_timezone', 'UTC'))

	def _get_info_str(self, ticker):
		data = get_owl_data()
		cur_match = get_current_match_info(data)
		next_match = get_next_match_info(data, tz=self.tz)

		skip = ticker and (cur_match == self.prev_state or not cur_match)
		self.prev_state = cur_match
		if skip:
			return

		match_infos = [m for m in (cur_match, next_match) if m] or \
			['No matches live or scheduled']
		return ' -- '.join(match_infos + ['https://overwatchleague.com'])

	@botologist.plugin.ticker()
	def ticker(self):
		return self._get_info_str(ticker=True)

	@botologist.plugin.command('owl')
	def command(self, msg):
		return self._get_info_str(ticker=False)