
from sslfetch.connections import Connector, get_timestamp
from gkeys import _unicode

EXTENSIONS = ['.sig', '.asc', '.gpg','.gpgsig']


class Fetch(object):

    def __init__(self, logger):
        self.logger = logger
        connector_output = {
             'info': self.logger.info,
             'debug': self.logger.debug,
             'error': self.logger.error,
             'exception': self.logger.exception,
             # we want any warnings to be printed to the terminal
             # so assign it to logging.error
             'warning': self.logger.error,
             'kwargs-info': {},
             'kwargs-debug': {},
             'kwargs-error': {},
             'kwargs-exception': {},
             'kwargs-warning': {},
        }
        self.fetcher = Connector(connector_output, None, "Gentoo Keys")
        self.sig_path = None

    def fetch_url(self, url, filepath, signature=True, timestamp=None, timestamp_path=None, climit=60):
        if not timestamp_path:
            timestamp_path = filepath + ".timestamp"
        messages = []
        self.logger.debug(
            _unicode("FETCH: fetching %s signed file ") % filepath)
        self.logger.debug(
            _unicode("FETCH: timestamp path: %s") % timestamp_path)
        success, signedfile, timestamp = self.fetcher.fetch_file(
            url, filepath, timestamp_path, climit=climit, timestamp=timestamp)
        if timestamp is '':
            self.logger.debug("Fetch.fetch_url; file not downloaded")
            return (False, messages)
        elif not success:
            messages.append(_unicode("File %s cannot be retrieved.") % filepath)
        elif '.' + url.rsplit('.', 1)[1] not in EXTENSIONS:
            self.logger.debug("File %s successfully retrieved.", filepath)
            if signature:
                success_fetch = False
                for ext in EXTENSIONS:
                    sig_path = filepath + ext
                    signature = url + ext
                    self.logger.debug(
                        _unicode("FETCH: fetching %s signature ")
                        % signature)
                    success_fetch, sig, timestamp = self.fetcher.fetch_file(signature, sig_path)
                    if success_fetch:
                        self.sig_path = sig_path
                        break
                    else:
                        signature = None
        return (success, messages)

    def verify_cycle(self, tpath, climit=60):
        return self.fetcher.verify_cycle(tpath, climit=60)
