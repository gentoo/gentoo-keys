import os
from snakeoil.osutils import (ensure_dirs as snakeoil_ensure_dirs)


def ensure_dirs(path, gid=-1, uid=-1, mode=0o700, minimal=True, failback=None, fatal=False):
    '''Wrapper to snakeoil.osutil's ensure_dirs()
    This additionally allows for failures to run
    cleanup or other code and/or raise fatal errors.

    @param path: directory to ensure exists on disk
    @param gid: a valid GID to set any created directories to
    @param uid: a valid UID to set any created directories to
    @param mode: permissions to set any created directories to
    @param minimal: boolean controlling whether or not the specified mode
        must be enforced, or is the minimal permissions necessary.  For example,
        if mode=0755, minimal=True, and a directory exists with mode 0707,
        this will restore the missing group perms resulting in 757.
    @param failback: function to run in the event of a failed attemp
        to create the directory.
    @return: True if the directory could be created/ensured to have those
        permissions, False if not.
    '''
    succeeded = snakeoil_ensure_dirs(path, gid=-1, uid=-1, mode=mode, minimal=True)
    if not succeeded:
        if failback:
            failback()
        if fatal:
            raise IOError(
                "Failed to create directory: %s" % path)
    return succeeded


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
            if os.path.exists(filename + '.new'):
                logger.debug(
                    "MAIN: _action_updatefile; Renaming '.new' seed file to: %s"
                    % filename)
                os.rename(filename + '.new', filename)
        except IOError:
            raise
            return False
        return True
