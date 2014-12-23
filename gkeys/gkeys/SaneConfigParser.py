
import sys

# py3.2
if sys.hexversion >= 0x30200f0:
    from configparser import configparser as ConfigParser
    from configparser import NoSectionError
    py3 = True
else:
    from ConfigParser import ConfigParser, NoSectionError
    py3 = False


class SaneConfigParser(ConfigParser):
    '''This class overrides what I consider a buggy RawConfigParser.options()'''


    def options(self, section):
        """Return a list of option names for the given section name."""
        try:
            opts = self._sections[section].copy()
        except KeyError:
            raise NoSectionError(section)
        if '__name__' in opts:
            del opts['__name__']
        return list(opts.keys())

