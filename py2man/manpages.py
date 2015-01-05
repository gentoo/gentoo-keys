#
#-*- coding:utf-8 -*-


import os
from datetime import datetime

from options import LONG_OPTS, SHORT_OPTS


ActionStr = '.BR gkeys-%s (1),'

EXAMPLEHEADER = '''.SH Example'''

BreakStr = '''.br
%s'''

SubCmdStr = '''.IP %(cmd)s
%(cmd-desc)s'''

SubCmdHdr = '.SH \\  %s'

class ManPage(object):

    def __init__(self, prog, version, template, docpath, authors):
        self.prog = prog
        self.version = version
        self.template = template
        self.path = docpath
        self.authors = authors


    @staticmethod
    def gen_opts(options):
        _opts = list()
        for opt in options:
            _opts.append(SHORT_OPTS.get(opt))
        return _opts


    @staticmethod
    def gen_optsStr(firstline, data, opts):
        indent = '                                 '
        escapes = 15
        wrapl = 72 + escapes
        output = []
        line = firstline.rstrip('%(opts)s') % data
        line_len = len(line)
        l1 = True
        for opt in opts:
            if (line_len + len(SHORT_OPTS[opt])) < wrapl:
                line = line + '%s ' % SHORT_OPTS[opt]
                line_len = len(line)
            else:
                if l1:
                    output.append(line)
                    l1 = False
                else:
                    output.append(BreakStr % line)
                line = indent + '%s ' % SHORT_OPTS[opt]
                line_len = len(line)
        return '\n'.join(output)


    @staticmethod
    def gen_brlist(_list):
        output = []
        for member in _list:
            output.append(BreakStr % member)
        return '\n'.join(output)


    @staticmethod
    def gen_actions(actions):
        acts = []
        for act in actions:
            if not act.startswith("--"):
                acts.append(ActionStr % act)
        return '\n'.join(acts)


    @staticmethod
    def gen_options(options):
        _opts = []
        for opt in options:
            _opts.append(LONG_OPTS[opt])
        return '\n'.join(_opts)


    @staticmethod
    def gen_example(text):
        example = []
        if text:
            for line in text.split('\n'):
                if line and line[0] in [' ']:
                    example.append(line)
                else:
                    example.append(BreakStr % line)
        return '\n'.join(example)


    @staticmethod
    def gen_subcmd(cmds):
        output = []
        for cmd in list(cmds):
            if cmd.startswith('--'):
                output.append(SubCmdHdr % cmd.strip('-').upper())
            else:
                output.append(SubCmdStr % {'cmd': cmd, 'cmd-desc': cmds[cmd]})
        return '\n'.join(output)


    def make_subpage(self, action, Action_Map, actions):
        '''Create and saves one sub-command man page using the
        classes template definition setting'''
        actions.remove(action)
        # remove the help group separators
        actions = [x for x in actions if not x.startswith("---")]
        data = {}
        data['prog'] = self.prog
        data['version'] = self.version
        data['date'] = datetime.strftime(datetime.today(),'%B %d, %Y')
        data['authors'] = self.gen_brlist(self.authors)
        data['action'] = action
        data['actions'] = self.gen_actions(actions)
        data['options'] = self.gen_options(Action_Map[action]['options'])
        data['desc'] = Action_Map[action]['desc']
        data['long_desc'] = Action_Map[action]['long_desc']
        if Action_Map[action]['example']:
            data['example'] = self.gen_example(Action_Map[action]['example'])
            data['exampleheader'] = EXAMPLEHEADER
        else:
            data['example'] = ''
            data['exampleheader'] = ''
        doc = []
        for line in self.template.split('\n'):
            if '%(opts)s' in line:
                doc.append(self.gen_optsStr(
                    line, data, Action_Map[action]['options']))
            else:
                doc.append(line % data)
        filepath = os.path.join(self.path, "%s-%s.1" % (self.prog, action))
        with open(filepath, 'w', encoding='utf-8') as man:
            man.write('\n'.join(doc))


    def make_subpages(self, Action_Map, actions):
        '''Create man pages for all sub-commands listed

        @param prog: string of the base application command
        @param version: string to embed in the man pages
        @param Action_Map: Dictionary of sub-command actions and other data
        @param actions: list of keys in Action_Map to generate pages for
        @param location: string, path to save the newly created man pages
        '''
        for action in actions:
            self.make_subpage(action, Action_Map, actions)


    def make_prog(self, prog_map):
        data = {}
        data['prog'] = self.prog
        data['version'] = self.version
        data['date'] = datetime.strftime(datetime.today(),'%B %d, %Y')
        data['authors'] = self.gen_brlist(self.authors)
        data['actions'] = self.gen_actions(list(prog_map['sub-cmds']))
        data['options'] = self.gen_options(prog_map['options'])
        data['desc'] = prog_map['desc']
        data['long_desc'] = prog_map['long_desc']
        data['sub-cmds'] = self.gen_subcmd(prog_map['sub-cmds'])
        doc = []
        for line in self.template.split('\n'):
                doc.append(line % data)
        filepath = os.path.join(self.path, "%s.1" % (self.prog))
        with open(filepath, 'w', encoding='utf-8') as man:
            man.write('\n'.join(doc))

    def read_template(self, path, filename):
        filepath = os.path.join(path, filename)
        with open(filepath, 'r', encoding='utf-8') as template:
            self.template = template.read()
