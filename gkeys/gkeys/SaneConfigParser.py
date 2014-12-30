#
#-*- coding:utf-8 -*-


try:
    from configparser import ConfigParser
    from configparser import NoSectionError
except:
    from ConfigParser import ConfigParser, NoSectionError


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

