try:                    #Python 2
	from xmlrpclib import ServerProxy
	from settings import Settings
except ImportError:     #Python 3
	from xmlrpc.client import ServerProxy
	from .settings import Settings

from utils import get_gzip_base64_decoded

class Language:
	EN = 'eng'
	RU = 'rus'

class DownloadLimitReachedError(Exception): pass
class NoSessionError(Exception): pass
class UnauthorizedError(Exception): pass
class ServerMaintenanceError(Exception): pass
class ServiceUnavailableError(Exception): pass
class TooManyRequestsError(Exception): pass

class OpenSubtitles(object):
	'''OpenSubtitles API wrapper.

	Please check the official API documentation at:
	http://trac.opensubtitles.org/projects/opensubtitles/wiki/XMLRPC
	'''

	def __init__(self, user_agent=Settings.TEST_USER_AGENT, language=Settings.LANGUAGE):
		self.xmlrpc = ServerProxy(Settings.OPENSUBTITLES_SERVER, allow_none=True)
		self.language = language
		self.user_agent = user_agent
		self.token = None

	def _get_from_data_or_none(self, key):
		'''Return the key getted from data if the status is 200,
		otherwise return None.
		'''
		status = int(self.data.get('status').split()[0])
		if status == 200: return self.data.get(key)
		elif status == 401: raise UnauthorizedError
		elif status == 406: raise NoSessionError
		elif status == 407: raise DownloadLimitReachedError
		elif status == 429: raise TooManyRequestsError
		elif status == 503: raise ServiceUnavailableError
		elif status == 506: raise ServerMaintenanceError
		else: raise RuntimeError('Request failed: status: %s' % self.data.get('status'))

	def login(self, username, password):
		'''Returns token is login is ok, otherwise None.
		'''
		self.data = self.xmlrpc.LogIn(username, password, self.language, self.user_agent)
		token = self._get_from_data_or_none('token')
		if token:
			self.token = token
		return token

	def logout(self):
		'''Returns True is logout is ok, otherwise None.
		'''
		self.data = self.xmlrpc.LogOut(self.token)
		return '200' in self.data.get('status')

	def search_subtitles(self, imdbid=None, langs=[Language.EN], params=None):
		'''Returns a list with the subtitles info.
		'''
		all_params = {}
		if imdbid != None: all_params['imdbid'] = imdbid
		if langs != None: all_params['sublanguageid'] = ','.join(langs)
		if params != None: all_params.update(params)

		self.data = self.xmlrpc.SearchSubtitles(self.token, [all_params])
		return self._get_from_data_or_none('data')

	def try_upload_subtitles(self, params):
		'''Return True if the subtitle is on database, False if not.
		'''
		self.data = self.xmlrpc.TryUploadSubtitles(self.token, params)
		return self._get_from_data_or_none('alreadyindb') == 1

	def upload_subtitles(self, params):
		'''Returns the URL of the subtitle in case that the upload is OK,
		other case returns None.
		'''
		self.data = self.xmlrpc.UploadSubtitles(self.token, params)
		return self._get_from_data_or_none('data')

	def no_operation(self):
		'''Return True if the session is actived, False othercase.

		.. note:: this method should be called 15 minutes after last request to
				  the xmlrpc server.
		'''
		self.data = self.xmlrpc.NoOperation(self.token)
		return '200' in self.data.get('status')

	def auto_update(self, program):
		'''Returns info of the program: last_version, url, comments...
		'''
		self.data = self.xmlrpc.AutoUpdate(program)
		return self.data if '200' in self.data.get('status') else None

	def search_movies_on_imdb(self, params):
		self.data = self.xmlrpc.SearchMoviesOnIMDB(self.token, params)
		return self.data

	def search_to_mail(self):
		# array SearchToMail( $token, array( $sublanguageid, $sublanguageid, ...), array( array( 'moviehash' => $moviehash, 'moviesize' => $moviesize), array( 'moviehash' => $moviehash, 'moviesize' => $moviesize), ...) )'
		raise NotImplementedError

	def check_subtitle_hash(self):
		# array CheckSubHash( $token, array($subhash, $subhash, ...) )
		raise NotImplementedError

	def check_movie_hash(self):
		# array CheckMovieHash( $token, array($moviehash, $moviehash, ...) )
		raise NotImplementedError

	def check_movie_hash_2(self):
		# array CheckMovieHash2( $token, array($moviehash, $moviehash, ...) )
		raise NotImplementedError

	def insert_movie_hash(self):
		# array InsertMovieHash( $token, array( array('moviehash' => $moviehash, 'moviebytesize' => $moviebytesize, 'imdbid' => $imdbid, 'movietimems' => $movietimems, 'moviefps' => $moviefps, 'moviefilename' => $moviefilename), array(...) ) )
		raise NotImplementedError

	def detect_language(self):
		# array DetectLanguage( $token, array($text, $text, ...) )
		raise NotImplementedError

	def download_subtitles(self, subfileids):
		if isinstance(subfileids, basestring): subfileids = [subfileids]
		assert isinstance(subfileids, list)
		if len(subfileids) > 20: raise ValueError('Maximum number of subids is 20, given %d' % len(subfileids))
		self.data = self.xmlrpc.DownloadSubtitles(self.token, subfileids)
		subs = []
		for sub in self._get_from_data_or_none('data'):
			subs.append(get_gzip_base64_decoded(sub['data']))
		return subs
		
	def report_wrong_movie_hash(self):
		# array ReportWrongMovieHash( $token, $IDSubMovieFile )
		raise NotImplementedError

	def get_subtitle_languages(self):
		# array GetSubLanguages( $language = 'en' )
		raise NotImplementedError

	def get_available_translations(self):
		# array GetAvailableTranslations( $token, $program )
		raise NotImplementedError

	def get_translation(self):
		# array GetTranslation( $token, $iso639, $format, $program )
		raise NotImplementedError

	def get_imdb_movie_details(self):
		# array GetIMDBMovieDetails( $token, $imdbid )
		raise NotImplementedError

	def insert_movie(self):
		# array InsertMovie( $token, array('moviename' => $moviename, 'movieyear' => $movieyear) )
		raise NotImplementedError

	def subtitles_vote(self):
		# array SubtitlesVote( $token, array('idsubtitle' => $idsubtitle, 'score' => $score) )
		raise NotImplementedError

	def get_comments(self):
		# array GetComments( $token, array($idsubtitle, $idsubtitle, ...))
		raise NotImplementedError

	def add_comment(self):
		# array AddComment( $token, array('idsubtitle' => $idsubtitle, 'comment' => $comment, 'badsubtitle' => $int) )
		raise NotImplementedError

	def add_request(self):
		# array AddRequest( $token, array('sublanguageid' => $sublanguageid, 'idmovieimdb' => $idmovieimdb, 'comment' => $comment ) )
		raise NotImplementedError
