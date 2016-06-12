#
#-*- coding:utf-8 -*-

"""
    Gentoo-keys - action_map.py

    Primary api interface module data

    @copyright: 2015 by Brian Dolbec <dol-sen@gentoo.org>
    @license: GNU GPL2, see COPYING for details.
"""


from collections import OrderedDict


Seed_Actions = ['----seeds----', 'add-seed', 'fetch-seed',
    'update-seed', 'list-seed', 'list-seedfiles', 'move-seed',
    'remove-seed']

Key_Actions = ['----keys-----', 'check-key', 'installed',
    'install-key', 'list-key', 'send-key', 'refresh-key', 'remove-key',
    'search-key', 'spec-check']

General_Actions = ['---general---', 'list-cats', 'sign','verify']

Available_Actions = General_Actions + Key_Actions + Seed_Actions

Action_Map = OrderedDict([
    ('---general---', {
        'func': 'GENERAL_COMMANDS',
        'options': [],
        'desc': '''-----< general actions >------''',
        'long_desc': '''''',
        'example': '''''',
        }),
    ('list-cats', {
        'func': 'listcats',
        'options': [],
        'desc': '''List seed file definitions (category names) found in the config''',
        'long_desc': '''List seed file definitions (category names) found in the config.
    These category names are used throughout the seed and key action operations.''',
        'example': '''$ gkeys list-cats

 Gkey task results:
    Categories defined: gentoo-devs,  gentoo,  sign

''',
        }),
    ('sign', {
        'func': 'sign',
        'options': ['nick', 'name', 'fingerprint', 'file', ],
        'desc': '''Sign a file''',
        'long_desc': '''Sign a file or files with the designated gpg key.
    The default sign settings can be set in gpg.conf.  These settings can be
    overridden on the command line using the 'nick', 'name', 'fingerprint' options''',
        'example': '''''',
        }),
    ('verify', {
        'func': 'verify',
        'options': ['category', 'nick', 'name', 'fingerprint', 'keydir', 'keys',
            '1file', 'signature', 'timestamp', 'dest', 'uid'],
        'desc': '''File automatic download and/or verification action.''',
        'long_desc': '''File automatic download and/or verification action.
    Note: If the specified key/keyring to verify against does not contain
    the key used to sign the file.  It will Auto-search for the correct key
    in the installed keys db. And verify against the matching key.
    It will report the success/failure along with the key information used for
    the verification''',
        'example': '''$ gkeys verify -F /home/brian/gpg-test/seeds/gentoo-devs.seeds

 Gkey task results:
    Using config defaults..: gentoo gkeys
    Verification succeeded.: /home/brian/gpg-test/seeds/gentoo-devs.seeds
    Key info...............: Gentoo-Linux Gentoo-keys Project Signing Key <gkeys>, 0xA41DBBD9151C3FC7
        category, nick.....: gentoo gkeys

''',
        }),
    ('----keys-----', {
        'func': 'KEY_COMMANDS',
        'options': [],
        'desc': '''-------< key actions >--------''',
        'long_desc': '',
        'example': '',
        }),
    ('check-key', {
        'func': 'checkkey',
        'options': ['category', 'nick', 'name', 'fingerprint', 'keyid', 'keys',
            'keydir', 'keyring'],
        'desc': '''Check key validity''',
        'long_desc': '''Check keys actions
    Performs basic validity checks on the key(s), checks expiry,
    and presence of a signing sub-key''',
        'example': '''$ gkeys check-key -C gentoo -n gkey

 Checking keys...


  gkeys, Gentoo-Linux Gentoo-keys Project Signing Key: 0xA41DBBD9151C3FC7, 0x825533CBF6CD6C97
  ==============================================


 Gkey task results:

Found:
-------
    Expired: 0
    Revoked: 0
    Invalid: 0
    No signing capable subkeys: 0
''',
        }),
    ('import-key', {
        'func': 'importkey',
        'options': ['category', 'nick', 'name', 'fingerprint', 'keys',
            'keydir', 'keyring'],
        'desc': '''Add a specified key to a specified keyring''',
        'long_desc': '''Add a specified key to a specified keyring''',
        'example': '''''',
        }),
    ('install-key', {
        'func': 'installkey',
        'options':  ['category', 'nick', 'name', 'fingerprint', 'keys',
            'keydir', 'keyring', '1file'],
        'desc': '''Install a key from the seed(s)''',
        'long_desc': '''Install a key from the seed(s).  The key will be
    installed to the pre-configured seed's keydir value within the category's directory.''',
        'example': '''''',
        }),
    ('installed', {
        'func': 'installed',
        'options': ['category', 'nick', 'name', 'fingerprint', 'keys',
            'keydir', 'keyring'],
        'desc': '''Lists the installed key directories''',
        'long_desc': '''Lists the installed key directories''',
        'example': '''$ gkeys installed -C gentoo

 Gkey task results:
    Found Key(s):
    ----------
    Name.........: Gentoo Tree Snapshot (Automated) Signing Key
    Nick.........: snapshot
    Keydir.......: release
    UID..........: Gentoo Portage Snapshot Signing Key (Automated Signing Key)
    Keyid........: 0xEC590EEAC9189250
      Fingerprint: E1D6ABB63BFCFB4BA02FDF1CEC590EEAC9189250
    Keyid........: 0xDB6B8C1F96D8BF6D
      Fingerprint: DCD05B71EAB94199527F44ACDB6B8C1F96D8BF6D

    ----------
    Name.........: Gentoo-Linux Gentoo-keys Project Signing Key
    Nick.........: gkeys
    Keydir.......: release
<snip> ...
''',
         }),
    ('list-key', {
        'func': 'listkey',
        'options': ['category', 'nick', 'name', 'fingerprint', 'keyid', 'keys',
            'keydir', 'keyring'],
        'desc': '''Pretty-print the selected gpg key''',
        'long_desc': '''Pretty-print the selected gpg key''',
        'example': '''gkeys list-key -C gentoo -n gkeys

Nick.....: gkeys
Name.....: Gentoo-Linux Gentoo-keys Project Signing Key
Keydir...: release
Gpg info.: pub   4096R/825533CBF6CD6C97 2014-10-03 [expires: 2017-09-17]
                 Key fingerprint = D2DE 1DBB A0F4 3EBA 341B  97D8 8255 33CB F6CD 6C97
           uid               [ unknown] Gentoo-keys Team <gkeys@gentoo.org>
           sub   4096R/A41DBBD9151C3FC7 2014-10-03 [expires: 2017-09-17]
                 Key fingerprint = C287 1675 69B3 C1F9 E9CE  D677 A41D BBD9 151C 3FC7

 Gkey task results:
    Done.''',
         }),
    ('send-key', {
        'func': 'sendkey',
        'options': ['category', 'nick', 'name', 'fingerprint', 'keyid', 'keys',
            'keydir', 'keyring'],
        'desc': '''Uploads the selected gpg key''',
        'long_desc': '''Uploads the selected gpg key''',
        'example': '''gkeys send-key -C gentoo -n gkeys''',
         }),

    ('move-key', {
        'func': 'movekey',
        'options': ['category', 'nick', 'name', 'fingerprint', 'keys',
            'keydir', 'keyring', 'dest'],
        'desc': '''Rename an installed keydir''',
        'long_desc': '''Rename an installed keydir''',
        'example': '''''',
         }),
    ('refresh-key', {
        'func': 'refreshkey',
        'options': ['category', 'nick', 'name', 'fingerprint', 'keyid', 'keys',
            'keydir', 'keyring'],
        'desc': '''Calls gpg with the --refresh-keys option
        for in place updates of the installed keys''',
        'long_desc': '''Calls gpg with the --refresh-keys option
    for in place updates of the installed keys.  To refresh all installed keys
    in the category, specify the category only.''',
        'example': '''$ gkeys refresh-key -C gentoo -n gkey

 Refreshig keys...

  Gentoo-Linux Gentoo-keys Project Signing Key: 0xA41DBBD9151C3FC7, 0x825533CBF6CD6C97


 Gkey task results:
    Completed
''',
         }),
    ('remove-key', {
        'func': 'removekey',
        'options': ['category', 'nick', 'name', 'fingerprint', 'keys',
            'keydir', 'keyring'],
        'desc': '''Remove (uninstall) an installed key''',
        'long_desc': '''Remove (uninstall) an installed key or keys''',
        'example': '''$ gkeys remove-key -C gentoo-devs -n dolsen

 Found GKEY seed:

    ----------
    Name.........: Brian Dolbec
    Nick.........: dolsen
    Keydir.......: dolsen
    UID..........: Brian Dolbec (Gentoo Developer) <dolsen@gentoo.org>
    UID..........: Brian Dolbec (Yes it's really me. Although which one of me is another question.) <brian.dolbec@gmail.com>
    UID..........: Brian Dolbec <brian.dolbec@gmail.com>
    UID..........: Brian Dolbec <dolsen@gentoo.org>
    Keyid........: 0x65E309F2189DB0B8
      Fingerprint: 76B63D6CCEC2FD160B0F5AC165E309F2189DB0B8
    Keyid........: 0xFBBD087275820ED8
      Fingerprint: A5D7C74E081CC70DB4A4AAF5FBBD087275820ED8
    Keyid........: 0xD80F5F1E1245142E
      Fingerprint: 262A829DFEAF9092A42C1C3ED80F5F1E1245142E
    Keyid........: 0x018682231B926E4F
      Fingerprint: 69FDA24269C8B5A7E9E231E9018682231B926E4F
    Keyid........: 0xD245831F292B1FFB
      Fingerprint: 93799ADE2C956B6553A23D8FD245831F292B1FFB
    Keyid........: 0x2214D90A014F17CB
      Fingerprint: 8688FD1CC71C1C04EAEA42372214D90A014F17CB


Do you really want to remove dolsen?[y/n]: y

 Gkey task results:
    Done removing dolsen key.
''',
         }),
    ('search-key', {
        'func': 'key_search',
        'options': ['category', 'nick', '1name', 'fingerprint', 'keyid', 'uid',
            'keys', 'keydir', 'exact', 'all'],
        'desc': '''Search for a key's seed in the installed keys db''',
        'long_desc': '''Search for a key's seed in the installed keys db''',
        'example': '''$ gkeys search-key  -n gkeys

 Gkey task results:
    Category.....: gentoo
    ----------
    Name.........: Gentoo-Linux Gentoo-keys Project Signing Key
    Nick.........: gkeys
    Keydir.......: release
    UID..........: Gentoo-keys Team <gkeys@gentoo.org>
    Keyid........: 0xA41DBBD9151C3FC7
      Fingerprint: C287167569B3C1F9E9CED677A41DBBD9151C3FC7
    Keyid........: 0x825533CBF6CD6C97
      Fingerprint: D2DE1DBBA0F43EBA341B97D8825533CBF6CD6C97

    Category.....: sign
    ----------
    Name.........: Gentoo-keys Team
    Nick.........: gkeys
    Keydir.......: gkeys
    UID..........: Gentoo-keys Team <gkeys@gentoo.org>
    Keyid........: 0x825533CBF6CD6C97
      Fingerprint: D2DE1DBBA0F43EBA341B97D8825533CBF6CD6C97
    Keyid........: 0xA41DBBD9151C3FC7
      Fingerprint: C287167569B3C1F9E9CED677A41DBBD9151C3FC7
''',
         }),
    ('spec-check', {
        'func': 'speccheck',
        'options': ['category', 'nick', 'name', 'fingerprint', 'keyid', 'keys',
            'keydir', 'keyring', 'email', 'user'],
        'desc': '''Check if keys meet specifications requirements''',
        'long_desc': '''Check if keys meet specifications requirements''',
        'example': '''$ gkeys spec-check -C gentoo -n gkeys

 Checking keys...

  gkeys, Gentoo-Linux Gentoo-keys Project Signing Key: 0x825533CBF6CD6C97
  ==============================================

    ----------
    Fingerprint......: D2DE1DBBA0F43EBA341B97D8825533CBF6CD6C97
    Key type ........: PUB    Capabilities.: cSC
    Algorithm........: Pass   Bit Length...: Pass
    Create Date......: Pass   Expire Date..: Pass
    Key Version......: Pass   Validity.....: -, Unknown
    Days till expiry.: 987
    Capability.......: Pass
    Qualified ID.....: Pass
    This primary key.: Pass

    ----------
    Fingerprint......: C287167569B3C1F9E9CED677A41DBBD9151C3FC7
    Key type ........: SUB    Capabilities.: s  sign
    Algorithm........: Pass   Bit Length...: Pass
    Create Date......: Pass   Expire Date..: Pass
    Key Version......: Pass   Validity.....: -, Unknown
    Days till expiry.: 987
    Capability.......: Pass
    Qualified ID.....: Pass
    This subkey......: Pass

    Key summary
    primary..........: Pass         signing subkey: Pass
    encryption subkey: No    authentication subkey: No
    SPEC requirements: Pass


 No Encryption capable subkey (Notice only):
     Gentoo-Linux Gentoo-keys Project Signing Key <gkeys>: D2DE1DBBA0F43EBA341B97D8825533CBF6CD6C97

 SPEC Approved:
     Gentoo-Linux Gentoo-keys Project Signing Key <gkeys>: D2DE1DBBA0F43EBA341B97D8825533CBF6CD6C97

 Gkey task results:

Found Failures:
-------
    Revoked................: 0
    Invalid................: 0
    No Signing subkey......: 0
    No Encryption subkey...: 1
    Algorithm..............: 0
    Bit length.............: 0
    Expiry.................: 0
    Expiry Warnings........: 0
    SPEC requirements......: 0
    =============================
    SPEC Approved..........: 1
''',
         }),
    ('----seeds----', {
        'func': 'SEED_COMMANDS',
        'options': [],
        'desc': '''------< seed actions >-------''',
        'long_desc': '',
        'example': '',
         }),
    ('add-seed', {
        'func': 'addseed',
        'options': ['category', 'nick', 'name', 'fingerprint', 'keys', 'keydir',
            'uid'],
        'desc': '''Add or replace a key in the selected seed file''',
        'long_desc': '''Add or replace a key in the selected seed file''',
        'example': '''$ gkeys add-seed -C mykeys -n foo -N "Foo Bar" -r foobar -K C287167569B3C1F9E9CED677A41DBBD9151C3FC7

 Gkey task results:
    Successfully added new seed.
''',
         }),
    ('fetch-seed', {
        'func': 'fetchseed',
        'options': ['category', 'nick', '1file', 'dest', 'signature',
            'timestamp'],
        'desc': '''Download the selected seed file(s)''',
        'long_desc': '''Download the selected seed file(s)''',
        'example': '''$ gkeys fetch-seed -C gentoo-devs

 Gkey task results:
     Verification succeeded.: /home/brian/gpg-test/seeds/gentoo-devs.seeds
     Key info...............: Gentoo-Linux Gentoo-keys Project Signing Key <gkeys>, 0xA41DBBD9151C3FC7
         category, nick.....: gentoo gkeys

    Fetch operation completed
''',
         }),
    ('update-seed', {
        'func': 'updateseed',
        'options': ['category', 'nick', '1file', 'dest', 'signature',
            'timestamp'],
        'desc': '''Update the selected seed file(s) or all categories if no arguments are given''',
        'long_desc': '''Update the selected seed file(s) or all categories if no arguments are given''',
        'example': '''$ gkeys update-seed -C gentoo-devs

 Gkey task results:
     Verification succeeded.: /home/brian/gpg-test/seeds/gentoo-devs.seeds
     Key info...............: Gentoo-Linux Gentoo-keys Project Signing Key <gkeys>, 0xA41DBBD9151C3FC7
         category, nick.....: gentoo gkeys

    Fetch operation completed
     Completed
''',
         }),
    ('list-seed', {
        'func': 'listseed',
        'options': ['category', 'nick', 'name', 'fingerprint', 'keys',
            'keydir', '1file'],
        'desc': '''Pretty-print the selected seed file''',
        'long_desc': '''Pretty-print the selected seed file''',
        'example': '''$ gkeys list-seed -C gentoo -n gkeys

 Gkey task results:

    ----------
    Name.........: Gentoo-Linux Gentoo-keys Project Signing Key
    Nick.........: gkeys
    Keydir.......: release
    UID..........: Gentoo-keys Team <gkeys@gentoo.org>
    Keyid........: 0xA41DBBD9151C3FC7
      Fingerprint: C287167569B3C1F9E9CED677A41DBBD9151C3FC7
    Keyid........: 0x825533CBF6CD6C97
      Fingerprint: D2DE1DBBA0F43EBA341B97D8825533CBF6CD6C97''',
         }),
    ('list-seedfiles', {
        'func': 'listseedfiles',
        'options': [],
        'desc': '''List seed files found in the configured seed directory''',
        'long_desc': '''List seed files found in the configured seed directory''',
        'example': '''$ gkeys list-seedfiles

 Gkey task results:
    Seed files found at path: /home/brian/gpg-test/seeds
  gentoo-devs.seeds
  gentoo.seeds
''',
         }),
    ('move-seed', {
        'func': 'moveseed',
        'options': ['category', 'nick', 'name', 'keydir', 'keys',
            'fingerprint', 'dest'],
        'desc': '''Move keys between seed files''',
        'long_desc': '''Move keys between seed files''',
        'example': '''''',
         }),
    ('remove-seed', {
        'func': 'removeseed',
        'options': ['category', 'nick', 'name', 'keys', 'fingerprint', 'keydir'],
        'desc': '''Remove a seed from the selected seed file''',
        'long_desc': '''Remove a seed from the selected seed file''',
        'example': '''$ gkeys remove-seed -C mykeys -n foo

 Gkey task results:
    Successfully removed seed: True
    ----------
    Name.........: Foo Bar
    Nick.........: foo
    Keydir.......: foobar
    Keyid........: 0xA41DBBD9151C3FC7
      Fingerprint: C287167569B3C1F9E9CED677A41DBBD9151C3FC7
''',
        }),
])
