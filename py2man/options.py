#
#-*- coding:utf-8 -*-

from collections import OrderedDict


LONG_OPTIONS = OrderedDict({
    'help': '''.IP "-h, --help"
show this help message and exit''',
    'status': '''.IP "-A, --status"
Toggles the active status of a member for LDAP searches''',
    'all': '''.IP "-a, --all"
Toggles matching all input arguments for searches''',
    'category': '''.IP "-C \\fICATEGORY\\fR, --category \\fICATEGORY"
The category name of the seed file being added to.
.br
This name must be listed in the gkeys.conf file's
[seeds], [seedurls] and [verify-seeds] sections''',
    'cleankey': '''.IP " --clean-key"
Clean the key from the keyring due to failures.''',
    'cleanseed': '''.IP " --clean-seed"
Clean the seed from the seedfile due to failures.
.br
Used during binary keyring release creation.''',
    'config': '''.IP "-c \\fICONFIG\\fR, --config \\fICONFIG\\fR"
The path to an alternate config file''',
    'debug': '''.IP "-D, --debug \\fI{WARNING,INFO,FATAL,NOTSET,WARN,DEBUG,ERROR,CRITICAL}\\fR"
The logging level to set for the logfile''',
    'dest': '''.IP "-d \\fIDESTINATION\\fR, --dest \\fIDESTINATION"
The category name of the seed file being added to.''',
    'exact': '''.IP "-e, --exact"
Use CASE matching in searches''',
    'file': '''.IP "-F \\fIFILENAME\\fR, --file \\fIFILENAME"
The path/URL to use for the (signed) file''',
    '1file': '''.IP "-F \\fIFILENAME\\fR, --file \\fIFILENAME"
The path/URL to use for the (signed) file''',
    'fingerprint': '''.IP "-f \\fIFINGERPRINT\\fR, --fingerprint \\fIFINGERPRINT"
The fingerprint(s) of the the key(s) or subkey(s)''',
    'gpgsearch': '''.IP "-g, --gpgsearch"
Do a gpg search operation, rather than a gkey search''',
    'homedir': '''.IP "-H \\fIHOMEDIR\\fR, --file \\fIHOMEDIR"
The destination for the generated key''',
    'keyid': '''.IP "-i \\fIKEYID\\fR, --keyid \\fIKEYID"
The long keyid of the gpg key to search for''',
    'keyring': '''.IP "-k \\fIKEYRING\\fR, --keyring \\fIKEYRING"
The name of the keyring to use for verification, etc.''',
    'keys': '''.IP "-K \\fIKEYS\\fR, --keys \\fIKEYS"
The fingerprint(s) of the primary keys in the keyring.''',
    'mail': '''.IP "-m \\fIEMAIL\\fR, --mail \\fIEMAIL"
The email address to search for or use.''',
    'nick': '''.IP "-n \\fINICK\\fR, --nick \\fINICK"
The nick of the user whose gkey seed is being added''',
    'name': '''.IP "-N \\fINAME\\fR, --name \\fINAME"
The name of the user whose gkey seed is being added''',
    'keydir': '''.IP "-r \\fIKEYDIR\\fR, --keydir \\fIKEYDIR"
The key directory the key is to be installed to''',
    'signature': '''.IP "-s \\fISIGNATURE\\fR, --signature \\fISIGNATURE"
The path/URL to use for the signature.''',
    'spec': '''.IP "-S \\fISPEC\\fR, --psec \\fISPEC"
The spec file to use from the gkeys-gen.conf file.''',
    'timestamp': '''.IP "-t, --timestamp"
Turn on timestamp use.''',
    'uid': '''.IP "-u \\fIUID\\fR, --uid \\fIUID"
The user id(s) (and email) of the key(s) being added (optional)''',
})

SHORT_OPTS = OrderedDict({
    'help': '[\\fB\\-h\\fR]',
    'status': '[\\fB\\-A\\fR]',
    'all': '[\\fB\\-a\\fR]',
    'category': '[\\fB\\-C\\fR \\fICATEGORY\\fR]',
    'cleankey': '[\\fB\\-\\-cleankey\\fR]',
    'cleanseed': '[\\fB\\-\\-cleanseed\\fR]',
    'dest': '[\\fB\\-d\\fR \\fIDESTINATION\\fR]',
    'exact': '[\\fB\\-e\\fR]',
    'file': '[\\fB\\-F\\fR \\fIFILENAME\\fR]',
    '1file': '[\\fB\\-F\\fR \\fIFILENAME\\fR]',
    'fingerprint': '[\\fB\\-f\\fR \\fIFINGERPRINT\\fR [\\fIFINGERPRINT\\fR ...]]',
    'gpgsearch': '[\\fB\\-g\\fR]',
    'homedir': '[\\fB\\-H\\fR \\fIHOMEDIR\\fR]',
    'keyid': '[\\fB\\-i\\fR \\fIKEYID\\fR [\\fIKEYID\\fR ...]]',
    'keyring': '[\\fB\\-k\\fR \\fIKEYRING\\fR]',
    'keys': '[\\fB\\-K\\fR [\\fIKEYS\\fR [\\fIKEYS\\fR ...]]]',
    'mail': '[\\fB\\-m\\fR \\fIEMAIL\\fR]',
    'nick': '[\\fB\\-n\\fR \\fINICK\\fR]',
    'name': '[\\fB\\-N\\fR [\\fINAME\\fR [\\fINAME\\fR ...]]]',
    '1name': '[\\fB\\-N\\fR \\fINAME\\fR]',
    'keydir': '[\\fB\\-r\\fR \\fIKEYDIR\\fR]',
    'signature': '[\\fB\\-s\\fR \\fISIGNATURE\\fR]',
    'spec': '[\\fB\\-S\\fR \\fISPEC\\fR]',
    'timestamp': '[\\fB\\-t\\fR]',
    'uid': '[\\fB\\-u\\fR [\\fIUID\\fR [\\fIUID\\fR ...]]]',
})
