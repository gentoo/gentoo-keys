
#-*- coding:utf-8 -*-

"""
    Gentoo-keys - actions.py

    Primary api interface module

    @copyright: 2012-2015 by Brian Dolbec <dol-sen@gentoo.org>
    @copyright: 2014-2015 by Pavlos Ratis <dastergon@gentoo.org>
    @license: GNU GPL2, see COPYING for details.
"""

from __future__ import print_function

import itertools
import os
import sys

if sys.version_info[0] >= 3:
    py_input = input
    _unicode = str
else:
    py_input = raw_input
    _unicode = unicode


from collections import defaultdict

from gkeys.actionbase import ActionBase
from gkeys.gkey import GKEY
from gkeys.checks import SPECCHECK_SUMMARY, convert_pf, convert_yn
from gkeys.mail import Emailer

from snakeoil.demandload import demandload

demandload(
    "gkeys.base:Args",
    "json:load",
)

EXTENSIONS = ['.sig', '.asc', '.gpg','.gpgsig']


class Actions(ActionBase):
    '''Primary API actions'''

    def __init__(self, config, output=None, logger=None):
        ActionBase.__init__(self, config, output, logger)


    @staticmethod
    def SEED_COMMANDS(args):
        '''------< seed actions >-------'''
        pass


    @staticmethod
    def KEY_COMMANDS(args):
        '''-------< key actions >--------'''
        pass


    @staticmethod
    def GENERAL_COMMANDS(args):
        '''-----< general actions >------'''
        pass

    def listseed(self, args):
        '''Pretty-print the selected seed file'''
        kwargs = self.seedhandler.build_gkeydict(args)
        self.logger.debug(_unicode("ACTIONS: listseed; kwargs: %s")
            % _unicode(kwargs))
        if not self.seeds:
            try:
                self.seeds = self.seedhandler.load_seeds(args.category, args.nick)
            except ValueError:
                return (False, ['', "Failed to load seed file. Consider fetching seedfiles."])
        if self.seeds:
            results = self.seeds.list(**kwargs)
        else:
            results = ''
        return (True, ['', results])


    def fetchseed(self, args):
        '''Download the selected seed file(s)'''
        self.logger.debug(_unicode("ACTIONS: fetchseed; args: %s")
            % _unicode(args))
        if not args.category:
            return (False, ["Please specify seeds category."])
        self._set_category(self.config.get_key('verify-keyring'))
        verifyargs = Args()
        verifyargs.category=args.category
        success, messages = self.seedhandler.fetch_seeds(args.category, verifyargs, self.verify)
        messages.append("")
        messages.append("Fetch operation completed")
        return (False not in success, messages)

    def updateseed(self, args):
        '''Updates seeds of a selected file or all categories if no args are given'''
        self.logger.debug(_unicode("ACTIONS: updateseed; args: %s")
            % _unicode(args))
        messages = []
        success = True
        if not args.category:
            '''Update all available categories'''
            seed_categories = list(self.config.defaults['seeds'])
            category_msgs = []
            for seed_category in seed_categories:
                self.seeds = None
                custom_args = args
                custom_args.category = seed_category
                category_success, messages = self.updateseed(custom_args)
                category_msgs.extend(messages)
            return (True, category_msgs)
        print("Fetching seeds for %s category.\n" %args.category)
        success, old_gkeys = self.listseed(args)
        fetch_success, fetch_messages = self.fetchseed(args)
        self.seeds = None
        if fetch_success is not True:
            success = False
            messages = fetch_messages
            print("Fetch failed.\n")
        else:
            print("Fetch succeeded.\n")
            print("Installing or Refreshing keys for %s category." %args.category)
            install_success, install_messages = self.installkey(args)
            if install_success is not True:
                print("Update failed.\n")
                success = False
            else:
                print("Update succeeded.\n")
            messages = fetch_messages + [" Update operation:"] + [install_messages]
            success, new_gkeys = self.listseed(args)
            added_gkeys, changed_gkeys, removed_gkeys  = self.seedhandler.compare_seeds(old_gkeys, new_gkeys)
            print("Updated revoked GKeys:")
            for gkey in changed_gkeys:
                self.output(['', changed_gkeys])
            else:
                print("No GKeys were revoked")
            print("Added GKeys:")
            for gkey in added_gkeys:
                self.output(['', added_gkeys])
            else:
                print("No GKeys were added")
            print("Removed GKeys:")
            for gkey in removed_gkeys:
                self.output(['', added_gkeys])
            else:
                print("No GKeys were removed")
        return (success, messages)

    def addseed(self, args):
        '''Add or replace a key in the selected seed file'''
        success, data = self.listseed(args)
        gkeys = data[1]
        if not args.nick or not args.name or not args.keys or not args.keydir:
            return (False, ["Provide a nickname, a name and a public key fingerprint (-K, --keys)."])
        if not args.fingerprint:
            args.fingerprint = args.keys
        if args.uid is None:
            args.uid = []
        gkey = self.seedhandler.new(args, checkgkey=True)
        self._set_category(args.category)
        if not gkey:
            return (False, ["Failed to create a valid GKEY instance.",
                "Check for invalid data entries"])
        if len(gkeys) == 0:
            self.logger.debug(
                _unicode("ACTIONS: installkey; now adding gkey: %s")
                % _unicode(gkey))
            success = self.seeds.add(getattr(gkey, 'nick'), gkey)
            if success:
                success = self.seeds.save()
                messages = ["Successfully added new seed."]
        else:
            messages = ["Matching seeds found in seeds file",
                "Aborting... \nMatching seeds:", gkeys]
            success = False
        return (success, messages)


    def removeseed(self, args):
        '''Remove a seed from the selected seed file'''
        success, data = self.listseed(args)
        gkeys = data[1]
        if not gkeys:
            return (False, ["Failed to remove seed: No gkeys returned from listseed()",
                []])
        if len(gkeys) == 1:
            self.logger.debug(
                _unicode("ACTIONS: removeseed; now deleting gkey: %s")
                % _unicode(gkeys))
            success = self.seeds.delete(gkeys[0])
            if success:
                success = self.seeds.save()
            return (success, [_unicode("Successfully removed seed: %s")
                % _unicode(success), gkeys])
        elif len(gkeys):
            return (False, ["Too many seeds found to remove", gkeys])
        return (False, ["Failed to remove seed:", args,
            "No matching seed found"])


    def moveseed(self, args):
        '''Move keys between seed files'''
        searchkey = self.seedhandler.new(args, checkgkey=False)
        self.logger.debug(_unicode("ACTIONS: moveseed; gkey: %s")
            % _unicode(searchkey))
        if not self.seeds:
            self.seeds = self.seedhandler.load_seeds(args.category)
        kwargs = self.seedhandler.build_gkeydict(args)
        sourcekeys = self.seeds.list(**kwargs)
        dest = self.seedhandler.load_seeds(args.destination)
        destkeys = dest.list(**kwargs)
        messages = []
        if len(sourcekeys) == 1 and destkeys == []:
            self.logger.debug(
                _unicode("ACTIONS: moveseed; now adding destination gkey: %s")
                % _unicode(sourcekeys[0]))
            success = dest.add(sourcekeys[0])
            self.logger.debug("ACTIONS: moveseed; success: %s" % str(success))
            self.logger.debug(
                _unicode("ACTIONS: moveseed; now deleting sourcekey: %s")
                % _unicode(sourcekeys[0]))
            success = self.seeds.delete(sourcekeys[0])
            if success:
                success = dest.save()
                self.logger.debug("ACTIONS: moveseed; destination saved... %s"
                    % str(success))
                success = self.seeds.save()
            messages.extend([_unicode("Successfully Moved %s seed: %s")
                % (args.category, str(success)), sourcekeys[0]])
            return (success, messages)
        elif len(sourcekeys):
            messages = ["Too many seeds found to move"]
            messages.extend(sourcekeys)
            return (False, messages)
        messages.append("Failed to move seed:")
        messages.append(searchkey)
        messages.append('\n')
        messages.append("Source seeds found...")
        messages.extend(sourcekeys or ["None\n"])
        messages.append("Destination seeds found...")
        messages.extend(destkeys or ["None\n"])
        return (False, messages)


    def sendkey(self, args):
        '''Send selected key(s) to the server'''
        if not args.category:
            return (False, ["Please specify seeds type."])
        self.logger.debug(_unicode("ACTIONS: sendkey; args: %s")
            % _unicode(args))
        seeds = self.seedhandler.load_category(args.category, refresh=True)
        self._set_category(args.category)
        results = {}
        kwargs = self.seedhandler.build_gkeydict(args)
        keyresults = seeds.list(**kwargs)
        if keyresults:
            self.output('', '\n sending keys...')
        else:
            return (False, ["Key(s) not found"])
        for gkey in sorted(keyresults):
            self.logger.info(_unicode("Sending key %s, %s")
                % (gkey.nick, gkey.pub_keyid))
            self.output('', _unicode("  %s: %s")
                % (gkey.name, ', '.join(gkey.pub_keyid)))
            self.logger.debug(_unicode("ACTIONS: sendkey; gkey = %s")
                % _unicode(gkey))
            results[gkey.keydir] = self.gpg.send_keys(gkey)
        return (True, ['Completed'])



    def listkey(self, args):
        '''Pretty-print the selected gpg key'''
        # get confirmation
        # fill in code here
        if not args.category:
            args.category = 'gentoo'
        self._set_category(args.category)
        if args.keydir:
            self.gpg.set_keydir(args.keydir, "list-keys")
            self.gpg.set_keyseedfile()
            seeds = self.gpg.seedfile
        else:
            seeds = self.seedhandler.load_category(args.category)
        results = {}
        success = []
        messages = []
        kwargs = self.seedhandler.build_gkeydict(args)
        keyresults = seeds.list(**kwargs)
        for key in sorted(keyresults):
            if args.fingerprint:
                result = self.gpg.list_keys(key.keydir, kwargs['fingerprint'])
            else:
                result = self.gpg.list_keys(key.keydir)
            ls, lr = self._list_it(key, result.output)
            success.append(ls)
            results[key.name] = lr
            messages = ["Done."]

        if not messages:
            messages = ['No results found meeting criteria', "Did you specify -n foo or -n '*'"]
        return (False not in success, messages)


    def _list_it(self, key, result, print_key=True):
        self.logger.debug("ACTIONS: _list_it; listing key:" + str(key.nick))
        if self.config.options['print_results']:
            if print_key:
                print()
                print(_unicode("Nick.....: %s") % key.nick)
                print(_unicode("Name.....: %s") % key.name)
                print(_unicode("Keydir...: %s") % key.keydir)
            c = 0
            for line in result.split('\n'):
                if c == 0:
                    print(_unicode("Gpg info.: %s") % line)
                else:
                    print(_unicode("           %s") % line)
                c += 1
            self.logger.debug(_unicode("data output:\n") + _unicode(result))
        return (True, result)


    def installkey(self, args):
        '''Install a key from the seed(s)'''
        self.logger.debug("ACTIONS: installkey; args: %s" % str(args))
        success, data = self.listseed(args)
        gkeys = data[1]
        if gkeys:
            if gkeys and not args.nick == '*' and self.output:
                self.output(['', gkeys], "\n Found GKEY seeds:")
            elif gkeys and self.output:
                self.output(['all'], "\n Installing seeds:")
            else:
                self.logger.info("ACTIONS: installkey; "
                    "Matching seed entry not found")
                if args.nick:
                    return (False,
                        [_unicode("Search failed for: %s") % args.nick])
                elif args.name:
                    return (False,
                        [_unicode("Search failed for: %s") % args.name])
                else:
                    return (False, ["Search failed for search term"])
            # get confirmation
            # fill in code here
            self._set_category(args.category)
            for gkey in gkeys:
                self.gpg.set_keydir(gkey.keydir, "recv-keys")
                self.gpg.set_keyseedfile()
                seeds = self.gpg.seedfile.seeds
                if seeds:
                    self.logger.debug("ACTIONS: installkey; found installed seeds:"
                        "\n %s" % seeds)
                results = {}
                failed = []
                if gkey.nick in seeds and gkey.keys == seeds[gkey.nick].keys:
                    self.logger.debug("ACTIONS: installkey; refreshing key:")
                    if self.config.options['print_results']:
                        print(_unicode("Refreshing already installed key: %s, %s"
                            %(gkey.nick, gkey.keys)))
                    self.gpg.refresh_key(gkey)
                else:
                    self.logger.debug("ACTIONS: installkey; adding key:")
                    self.logger.debug("ACTIONS: " + str(gkey))
                    results[gkey.name] = self.gpg.add_key(gkey)
                    for result in results[gkey.name]:
                        self.logger.debug("ACTIONS: installkey; result.failed = " +
                                          str(result.failed))
                    if self.config.options['print_results']:
                        msg = _unicode("key desired: %(name)s, key added: %(key)s, succeeded:" +\
                            " %(success)s, fingerprint: %(fpr)s")
                        for result in results[gkey.name]:
                            umsg = msg % ({'name': gkey.name, 'key': result.username,
                                    'success': str(not result.failed),
                                    'fpr': result.fingerprint})
                            try:
                                print(umsg)
                            except UnicodeDecodeError:
                                print(_unicode("UnicodeDecodeError printing results for:"), gkey.name)
                                self.logger.debug(_unicode("installkey(); UnicodeDecodeError for:") + gkey.name)
                                self.logger.debug(_unicode("    result.username...:") + result.username)
                                self.logger.debug(_unicode("    result.failed.....:") + result.failed)
                                self.logger.debug(_unicode("    result.fingerprint:") + result.fingerprint)
                            self.logger.debug("stderr_out: " + str(result.stderr_out))
                            if result.failed:
                                failed.append(gkey)
            if failed and self.output:
                self.output([failed], "\n Failed to install:")
            if failed:
                success = False
            return (success, ["Completed"])
        return (success, ["No seeds to search or install"])


    def checkkey(self, args):
        '''Check keys actions
        Performs basic validity checks on the key(s), checks expiry,
        and presence of a signing sub-key'''
        if not args.category:
            return (False, [_unicode("Please specify seeds category.")])
        self.logger.debug(_unicode("ACTIONS: checkkey; args: %s") % _unicode(args))
        seeds = self.seedhandler.load_category(args.category)
        self._set_category(args.category)
        results = {}
        failed = defaultdict(list)
        kwargs = self.seedhandler.build_gkeydict(args)
        keyresults = seeds.list(**kwargs)
        self.output('', '\n Checking keys...')
        for gkey in sorted(keyresults):
            self.logger.info(_unicode("Checking key %s, %s")
                % (gkey.nick, gkey.pub_keyid))
            self.output('',
                _unicode("\n  %s, %s: %s" % (gkey.nick, gkey.name,
                _unicode(', ').join(gkey.pub_keyid))) +
                _unicode("\n  =============================================="))
            self.logger.debug(_unicode("ACTIONS: checkkey; gkey = %s") % _unicode(gkey))
            for key in gkey.pub_keyid:
                results[gkey.name] = self.gpg.check_keys(gkey.keydir, key)
                if results[gkey.name].expired:
                    failed['expired'].append(_unicode("%s <%s>: %s")
                        % (gkey.name, gkey.nick, key))
                if results[gkey.name].revoked:
                    failed['revoked'].append(_unicode("%s <%s>: %s")
                        % (gkey.name, gkey.nick, key))
                if results[gkey.name].invalid:
                    failed['invalid'].append(_unicode("%s <%s>: %s")
                        % (gkey.name, gkey.nick, key))
                if not results[gkey.name].sign:
                    failed['sign'].append(_unicode("%s <%s>: %s ")
                        % (gkey.name, gkey.nick, key))
        if failed['expired']:
            self.output([failed['expired']], '\n Expired keys:\n')
        if failed['revoked']:
            self.output([failed['revoked']], '\n Revoked keys:\n')
        if failed['invalid']:
            self.output([failed['invalid']], '\n Invalid keys:\n')
        if failed['sign']:
            self.output([failed['sign']], '\n No signing capable subkeys:\n')
        return (not any(itertools.chain.from_iterable(failed.values())),
            ['\nFound:\n-------', 'Expired: %d' % len(failed['expired']),
                'Revoked: %d' % len(failed['revoked']),
                'Invalid: %d' % len(failed['invalid']),
                'No signing capable subkeys: %d' % len(failed['sign'])
            ])


    def speccheck(self, args):
        '''Check if keys meet specifications requirements'''
        if not args.category:
            return (False, ["Please specify seeds category."])
        self.logger.debug(_unicode("ACTIONS: speccheck; args: %s")
            % _unicode(args))
        self._set_category(args.category)
        catdir, keyresults = self.keyhandler.determine_keys(args)
        self.logger.debug(_unicode("ACTIONS: speccheck; catdir = %s") % catdir)
        results = {}
        failed = defaultdict(list)
        self.output('', '\n Checking keys...')
        '''Login email'''
        if args.email in ['expiry']:
            if args.user:
                email_user = self.config.get_key(args.user)
            else:
                email_user = self.config.get_key('login_gentoo')
            emailer = Emailer(email_user, self.logger)
            template_path = os.path.join(self.config.get_key('template_path'), "expiry_template")
            message_template = self.keyhandler.set_template(template_path)
            self.logger.debug(_unicode('Emailer started with login: %s') \
                % _unicode(email_user['login_email']))
        for gkey in sorted(keyresults):
            self.logger.info(_unicode("Checking key %s, %s")
                % (gkey.nick, gkey.keys))
            self.output('',
                _unicode("\n  %s, %s: %s") % (gkey.nick, gkey.name,
                _unicode(', ').join(gkey.pub_keyid)) +
                _unicode("\n  =============================================="))
            self.logger.debug(_unicode("ACTIONS: speccheck; gkey = %s")
                % _unicode(gkey))
            for key in gkey.keys:
                results = self.gpg.speccheck(gkey.keydir, key)
                for g in results:
                    pub_pass = {}
                    key_print = ''
                    for key in results[g]:
                        self.output('', key.pretty_print())
                        key_print += '\n\n' + key.pretty_print()
                        if key.key is "PUB":
                            pub_pass = {
                                'key': key,
                                'pub': key.passed_spec,
                                'sign': False,
                                'encrypt': False,
                                'auth': False,
                                'signs': [],
                                'encrypts': [],
                                'authens': [],
                                'final': False,
                                'qualified_id_checks': [],
                                'qualified_id_passed': False
                            }
                        if key.key is "SUB":
                            if key.sign_capable and key.passed_spec:
                                pub_pass['signs'].append(key.passed_spec)
                                pub_pass['sign'] = True
                            if key.encrypt_capable:
                                pub_pass['encrypts'].append(key.passed_spec)
                                pub_pass['encrypt'] = True
                            if key.capabilities == 'a':
                                pub_pass['authens'].append(key.passed_spec)
                                if key.passed_spec:
                                    pub_pass['auth'] = True
                        if key.id:
                            pub_pass['qualified_id_checks'].append(key.id)
                            pub_pass['qualified_id_passed'] = True
                        validity = key.validity.split(',')[0]
                        if not key.expire and not 'r' in validity:
                            failed['expired'].append(_unicode("%s <%s>: %s")
                                % (gkey.name, gkey.nick, key.fingerprint))
                        if 'r' in validity:
                            failed['revoked'].append(_unicode("%s <%s>: %s")
                                % (gkey.name, gkey.nick, key.fingerprint))
                        if 'i' in validity:
                            failed['invalid'].append(_unicode("%s <%s>: %s")
                                % (gkey.name, gkey.nick, key.fingerprint))
                        if key.capabilities not in ['a', 'e']:
                            if not key.algo:
                                failed['algo'].append(_unicode("%s <%s>: %s")
                                    % (gkey.name, gkey.nick, key.fingerprint))
                            if not key.bits:
                                failed['bits'].append(_unicode("%s <%s>: %s")
                                    % (gkey.name, gkey.nick, key.fingerprint))
                        if "warning" in key.expire_reason.lower():
                            failed['warn'].append(_unicode("%s <%s>: %s ")
                                % (gkey.name, gkey.nick, key.fingerprint))
                    if True in pub_pass['signs']:
                        pub_pass['sign'] = True
                    if True in pub_pass['encrypts']:
                        pub_pass['encrypt'] = True
                    if not pub_pass['sign']:
                        failed['sign'].append(_unicode("%s <%s>: %s")
                            % (gkey.name, gkey.nick, pub_pass['key'].fingerprint))
                    if not pub_pass['qualified_id_passed']:
                        failed['qualified_id'].append(_unicode("%s <%s>: %s")
                            % (gkey.name, gkey.nick, pub_pass['key'].fingerprint))
                    if not pub_pass['encrypt']:
                        failed['encrypt'].append(_unicode("%s <%s>: %s")
                            % (gkey.name, gkey.nick, pub_pass['key'].fingerprint))
                    spec = _unicode("%s <%s>: %s") % (
                        gkey.name, gkey.nick, pub_pass['key'].fingerprint)
                    for k in ['pub', 'sign']:
                        if pub_pass[k]:
                            pub_pass['final'] = True
                        else:
                            pub_pass['final'] = False
                            break
                    if pub_pass['final']:
                        if spec not in failed['spec-approved']:
                            failed['spec-approved'].append(spec)
                    else:
                        if spec not in failed['spec']:
                            failed['spec'].append(spec)
                    sdata = convert_pf(pub_pass, ['pub', 'sign', 'final'])
                    sdata = convert_yn(sdata, ['auth', 'encrypt'])
                    self.output('', SPECCHECK_SUMMARY % sdata)
                    '''Email reminder code'''
                    if args.email in ['expiry']:
                        uid = ''
                        if gkey.uid:
                            uids = gkey.uid
                            uid = self.keyhandler.find_email(uids, self.config.get_key('prefered_address'))
                        self.logger.debug(_unicode('The valid uid is: %s') % uid)
                        days_limit = int(self.config.get_key('days_limit'))
                        self.logger.debug(_unicode('Days_limit for expiry is: %s') \
                            % _unicode(days_limit))
                        is_exp = self.keyhandler.is_expiring(results, days_limit)
                        if is_exp and uid:
                            self.logger.debug(_unicode('Process for emailing started'))
                            message = self.keyhandler.generate_template(message_template, \
                                key_print, SPECCHECK_SUMMARY % sdata)
                            emailer.send_email(uid, message)
        if args.email in ['expiry']:
            emailer.email_quit()
            self.logger.debug(_unicode('Emailer quit'))
        if failed['revoked']:
            self.output([sorted(set(failed['revoked']))], '\n Revoked keys:')
        if failed['invalid']:
            self.output([sorted(set(failed['invalid']))], '\n Invalid keys:')
        if failed['sign']:
            self.output([sorted(set(failed['sign']))], '\n No signing capable subkey:')
        if failed['encrypt']:
            self.output([sorted(set(failed['encrypt']))], '\n No Encryption capable subkey (Notice only):')
        if failed['algo']:
            self.output([sorted(set(failed['algo']))], '\n Incorrect Algorithm:')
        if failed['bits']:
            self.output([sorted(set(failed['bits']))], '\n Incorrect bit length:')
        if failed['expired']:
            self.output([sorted(set(failed['expired']))], '\n Expiry keys:')
        if failed['warn']:
            self.output([sorted(set(failed['warn']))], '\n Expiry Warnings:')
        if failed['qualified_id']:
            self.output([sorted(set(failed['qualified_id']))], '\n Qualified IDs:')
        if failed['spec']:
            self.output([sorted(set(failed['spec']))], '\n Failed to pass SPEC requirements:')
        if failed['spec-approved']:
            self.output([sorted(set(failed['spec-approved']))], '\n SPEC Approved:')

        return (len(failed) <1,
            ['\nFound Failures:\n-------',
                'Revoked................: %d' % len(set(failed['revoked'])),
                'Invalid................: %d' % len(set(failed['invalid'])),
                'No Signing subkey......: %d' % len(set(failed['sign'])),
                'No Encryption subkey...: %d' % len(set(failed['encrypt'])),
                'Algorithm..............: %d' % len(set(failed['algo'])),
                'Bit length.............: %d' % len(set(failed['bits'])),
                'Qualified IDs..........: %d' % len(set(failed['qualified_id'])),
                'Expiry.................: %d' % len(set(failed['expired'])),
                'Expiry Warnings........: %d' % len(set(failed['warn'])),
                'SPEC requirements......: %d' % len(set(failed['spec'])),
                '=============================',
                'SPEC Approved..........: %d' % len(set(failed['spec-approved'])),
            ])

    def removekey(self, args):
        '''Remove an installed key'''
        if not args.nick:
            return (False, ["Please provide a nickname or -n *"])
        kwargs = self.seedhandler.build_gkeydict(args)
        self.logger.debug(_unicode("ACTIONS: removekey; kwargs: %s")
            % _unicode(kwargs))
        seeds = self.seedhandler.load_category(args.category)
        self._set_category(args.category)
        messages = []
        if args.nick == '*':
            self.output([''],_unicode('Remove All keys in category: %s')
                % _unicode(args.category))
            ans = py_input ("Do you really want to remove ALL of the keys?[y/n]: ")
            while ans not in ["yes", "y", "no", "n"]:
                ans = py_input ("Do you really want to remove ALL keys?[y/n]: ")
            if ans in ["no", "n"]:
                messages.append("Key removal aborted... Nothing to be done.")
                return (True, messages)
            keyresults = seeds.seeds
        else:
            keyresults = seeds.list(**kwargs)
        self.output('', '\n Removing keys...')
        success = True
        for gkey in sorted(keyresults):
            if kwargs['nick'] != '*' and  kwargs['nick'] not in gkey.nick:
                messages.append(_unicode("%s does not seem to be a valid key.")
                    % _unicode(kwargs['nick']))
                success = False
            else:
                self.output(['', [gkey]], '\n Found GKEY seed:')
                ans = py_input (
                    _unicode("Do you really want to remove %s?[y/n]: ")
                    % _unicode(kwargs['nick'].lower()))
                while ans not in ["yes", "y", "no", "n"]:
                    ans = py_input (
                        _unicode("Do you really want to remove %s?[y/n]: ")
                        % _unicode(kwargs['nick'].lower()))
                if ans in ["no", "n"]:
                    messages.append("Key removal aborted... Nothing to be done.")
                else:
                    if len(gkey.keys) == 1 or args.keys == gkey.keys:
                        success, msgs = self.gpg.del_keydir(gkey)
                        messages.extend(msgs)
                    elif args.keys:
                        for key in args.keys:
                            success, msgs = self.gpg.del_key(gkey, key)
                            msgs.extend(msgs)
                    else:
                        for key in gkey.keys:
                            success, msgs = self.gpg.del_key(gkey, key)
                            msgs.extend(msgs)
        return (success, messages)


    def movekey(self, args):
        '''Rename an installed keydir'''
        return (False, [])


    def importkey(self, args):
        '''Add a specified key to a specified keyring'''
        if args.category:
            catdir = self._set_category(args.category)
            success, data = self.listseed(args)
            gkeys = data[1]
            results = {}
            failed = []
            print("Importing specified keys to keyring.")
            for gkey in gkeys:
                self.logger.debug(_unicode("ACTIONS: importkey; adding key: %s"), gkey.name)
                results[gkey.name] = self.gpg.add_key(gkey)
                if self.config.options['print_results']:
                    msg = _unicode("key desired: %(name)s, key added: %(key)s, " + \
                        "succeeded: %(success)s, fingerprint: %(fpr)s")
                    for result in results[gkey.name]:
                        print(msg % ({'name': gkey.name, 'key': result.username,
                            'success': str(not result.failed),
                            'fpr': result.fingerprint}))
                        self.logger.debug("stderr_out: " + str(result.stderr_out))
                        if result.failed:
                            self.logger.debug("ACTIONS: importkey; result.failed = "
                                + str(result.failed))
                            failed.append(gkey)
                if not results[gkey.name][0].failed:
                    print(_unicode("Importing: %s") % gkey.name)
                    self.logger.debug(
                        _unicode("ACTIONS: importkey; importing key: %s")
                        % gkey.name)
                    _keyring = os.path.join(catdir, args.keyring + '.gpg')
                    self.gpg.add_to_keyring(gkey, catdir, _keyring)
            if failed and self.output:
                self.output([failed], "\n Failed to install:")
            if len(failed):
                success = False
            return (success, ["Completed."])
        return (False, ["No seeds to search or install",
            "You must specify a category"])


    def installed(self, args):
        '''Lists the installed key directories'''
        if args.category:
            keyring = self.config.get_key('keyring')
        else:
            return (False, ["Please specify a category."])
        catdir = self._set_category(args.category)
        self.logger.debug("ACTIONS: installed; catdir = %s" % catdir)
        installed_keys = []
        try:
            if args.nick:
                keys = [args.nick]
            else:
                keys = os.listdir(catdir)
            for key in keys:
                seed_path = os.path.join(catdir, key)
                gkey_path = os.path.join(seed_path, 'gkey.seeds')
                seed = None
                try:
                    with open(gkey_path, 'r') as fileseed:
                        seed = load(fileseed)
                except IOError:
                    return ["No seed file found in %s." % gkey_path, ""]
                if seed:
                    for val in list(seed.values()):
                        installed_keys.append(GKEY(**val))
        except OSError:
            return (False, [_unicode("%s directory does not exist.") % catdir, ""])
        return (True, ['Found Key(s):', installed_keys])


    def user_confirm(self, message):
        '''Prompt a user to confirm an action

        @param message: string, user promt message to display
        @return boolean: confirmation to proceed or abort
        '''
        pass


    def verify(self, args, messages=None):
        '''File verification action.
        Note: If the specified key/keyring to verify against does not contain
        the key used to sign the file.  It will Auto-search for the correct key
        in the installed keys db. And verify against the matching key.'''

        '''
        @param args: argparse.parse_args instance
        @param messages: list, private internal option used for recursion only
        '''
        if messages == None:
            messages = []

        if not args.filename:
            return (False, ['Please provide a signed file.'])
        if not args.category:
            args.category = self.config.get_key('verify-keyring')
            self.logger.debug(_unicode(
                "ACTIONS: verify; keyring category not specified, using default: %s")
                % args.category)
        keys = self.seedhandler.load_category(args.category)
        if not keys:
            return (False, ['No installed keys found, try installkey action.'])
        key = self.seedhandler.seeds.nick_search(args.nick)
        if not key:
            if args.nick:
                messages.append(_unicode(
                    "Failed to find.........: %s in category: %s")
                    % (args.category, args.nick))
            args.category = self.config.get_key('verify-keyring')
            args.nick = self.config.get_key('verify-nick')
            messages.append(_unicode("Using config defaults..: %s %s")
                % (args.category, args.nick))
            return self.verify(args, messages)
        return self._verify(args, key, messages)


    def _verify(self, args, key, messages=None):
        if messages == None:
            messages = []
        self._set_category(args.category)
        filepath, signature  = args.filename, args.signature
        timestamp_path = None
        isurl = success = verified = False
        if filepath.startswith('http'):
            isurl = True
            url = filepath
            filepath = args.destination
            # a bit hackish, but save it to current directory
            # with download file name
            if not filepath:
                filepath = url.split('/')[-1]
                self.logger.debug(_unicode(
                    "ACTIONS: verify; destination filepath was "
                    "not supplied, using current directory ./%s") % filepath)
        if args.timestamp:
            timestamp_path = filepath + ".timestamp"
            climit = 60
        else:
            climit = 0
        sig_path = None
        if isurl:
            from sslfetch.connections import Connector
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
            fetcher = Connector(connector_output, None, "Gentoo Keys")
            self.logger.debug(
                _unicode("ACTIONS: verify; fetching %s signed file ") % filepath)
            self.logger.debug(
                _unicode("ACTIONS: verify; timestamp path: %s") % timestamp_path)
            success, signedfile, timestamp = fetcher.fetch_file(
                url, filepath, timestamp_path, climit=climit)
            if not success:
                messages.append(_unicode("File %s cannot be retrieved.") % filepath)
            elif '.' + url.rsplit('.', 1)[1] not in EXTENSIONS:
                if not signature:
                    success_fetch = False
                    for ext in EXTENSIONS:
                        sig_path = filepath + ext
                        if isurl:
                            signature = url + ext
                            self.logger.debug(
                                _unicode("ACTIONS: verify; fetching %s signature ")
                                % signature)
                            success_fetch, sig, timestamp = fetcher.fetch_file(signature, sig_path)
                        if success_fetch:
                            break
                        else:
                            signature = None
        elif signature is not None and os.path.exists(signature):
            sig_path = signature
        else:
            filepath = os.path.abspath(filepath)
            self.logger.debug(
                _unicode("ACTIONS: verify; local file %s") % filepath)
            success = os.path.isfile(filepath)
            if (not signature
                and '.' + filepath.rsplit('.', 1)[-1] not in EXTENSIONS):
                success_fetch = False
                for ext in EXTENSIONS:
                    sig_path = filepath + ext
                    sig_path = os.path.abspath(sig_path)
                    self.logger.debug(
                        _unicode("ACTIONS: verify; checking %s signature ")
                        % sig_path)
                    success_sig = os.path.isfile(sig_path)
                    if success_sig:
                        break
                    else:
                        sig_path = None
            elif signature:
                sig_path = os.path.abspath(signature)
        self.logger.info("Verifying file...")
        verified = False
        results = self.gpg.verify_file(key, sig_path, filepath)
        keyid = key.keyid[0]
        (valid, trust) = results.verified
        if valid:
            verified = True
            messages.extend(
                [_unicode("Verification succeeded.: %s") % (filepath),
                _unicode("Key info...............: %s <%s>, %s")
                % ( key.name, key.nick, keyid),
                _unicode("    category, nick.....: %s %s")
                % (args.category, args.nick)])
        else:
            messages.extend(
                [_unicode("Verification failed....: %s") % (filepath),
                _unicode("Key info...............: %s <%s>, %s")
                % ( key.name, key.nick, keyid)])
            found, args, new_msgs = self.keyhandler.autosearch_key(args, results)
            messages.extend(new_msgs)
            if found:
                return self.verify(args, messages)
        return (verified, messages)


    def listcats(self, args):
        '''List seed file definitions found in the config'''
        seeds = list(self.config.get_key('seeds'))
        return (True, {_unicode("Categories defined: %s\n")
            % (_unicode(",  ").join(seeds)): True})


    def listseedfiles(self, args):
        '''List seed files found in the configured seed directory'''
        seedsdir = self.config.get_key('seedsdir')
        seedfile = [f for f in os.listdir(seedsdir) if f[-5:] == 'seeds']
        return (True, {_unicode("Seed files found at path: %s\n  %s")
            % (seedsdir, _unicode("\n  ").join(seedfile)): True})


    def sign(self, args):
        '''Sign a file'''
        if not args.filename:
            return (False, ['Please provide a file to sign.'])

        if not args.nick:
            args.nick = self.config.get_key("sign", "nick")
        if isinstance(args.nick, str):
            nicks = [args.nick]
        else:
            nicks = args.nick
        args.category = 'sign'
        self._set_category(args.category)
        # load our installed signing keys db
        self.seeds = self.seedhandler.load_category('sign', nicks)
        if not self.seeds.seeds:
            return (False, ['No installed keys, try installkey action.', ''])
        keydir  = self.config.get_key("sign", "keydir")
        task = self.config.get_key("sign", "type")
        keyring = self.config.get_key("sign", "keyring")

        self.config.options['gpg_defaults'] = ['--status-fd', '2']

        self.logger.debug(_unicode("ACTIONS: sign; keydir = %s") % keydir)

        self.gpg.set_keydir(keydir, task)
        if keyring not in ['', None]:
            self.gpg.set_keyring(keyring, task)
        msgs = []
        success = []
        for fname in args.filename:
            results = self.gpg.sign(task, None, fname)
            verified, trust = results.verified
            if not results.verified[0]:
                msgs.extend(
                    [_unicode('Failed Signature for %s verified: %s, trust: %s')
                        % (fname, verified, trust),
                        _unicode('GPG output:', "\n").join(results.stderr_out)]
                )
                success.append(False)
            else:
                msgs.extend(
                    [_unicode(
                    'Signature result for: %s -- verified: %s, trust: %s')
                    % (fname, verified, trust)] #, 'GPG output:', "\n".join(results.stderr_out)]
                )
                success.append(True)
        return (False not in success, ['', msgs])


    def refreshkey(self, args):
        '''Calls gpg with the --refresh-keys option
        for in place updates of the installed keys'''
        if not args.category:
            return (False, ["Please specify seeds type."])
        self.logger.debug(_unicode("ACTIONS: refreshkey; args: %s")
            % _unicode(args))
        seeds = self.seedhandler.load_category(args.category, refresh=True)
        self._set_category(args.category)
        results = {}
        kwargs = self.seedhandler.build_gkeydict(args)
        keyresults = seeds.list(**kwargs)
        self.output('', '\n Refreshig keys...')
        for gkey in sorted(keyresults):
            self.logger.info(_unicode("Refreshig key %s, %s")
                % (gkey.nick, gkey.pub_keyid))
            self.output('', _unicode("  %s: %s")
                % (gkey.name, ', '.join(gkey.pub_keyid)))
            #self.output('', "  ===============")
            self.logger.debug(_unicode("ACTIONS: refreshkey; gkey = %s")
                % _unicode(gkey))
            results[gkey.keydir] = self.gpg.refresh_key(gkey)
        return (True, ['Completed'])


    def key_search(self, args, data_only=False):
        '''Search for a key's seed in the installed keys db'''
        keys = self.keyhandler.key_search(args)
        if data_only:
            return keys
        msgs = []
        for cat in list(keys):
            msgs.append(_unicode("Category.....: %s") % cat)
            msgs.append(keys[cat])
        del keys
        return (True, msgs)
