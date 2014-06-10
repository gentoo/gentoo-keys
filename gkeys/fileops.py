import os
from gkeys.log import logger

def updatefiles(config, logger):
        filename = config['dev-seedfile']
        old = filename + '.old'
        try:
            logger.info("Backing up existing file...")
            if os.path.exists(old):
                logger.debug(
                    "MAIN: _action_updatefile; Removing 'old' seed file: %s"
                    % old)
                os.unlink(old)
            if os.path.exists(filename):
                logger.debug(
                    "MAIN: _action_updatefile; Renaming current seed file to: "
                    "%s" % old)
                os.rename(filename, old)
            logger.debug(
                "MAIN: _action_updatefile; Renaming '.new' seed file to: %s"
                % filename)
            os.rename(filename + '.new', filename)
        except IOError:
            raise
            return False
        return True
