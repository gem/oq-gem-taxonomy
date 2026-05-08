# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2024-2025 GEM Foundation
#
# Openquake Gem Taxonomy is free software: you can redistribute it and/or
# modify it # under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.
import os
import sys
import csv
import json
import glob
import argparse
import subprocess
from argparse import RawTextHelpFormatter
from openquake.gem_taxonomy import GemTaxonomy, __version__
from parsimonious.exceptions import ParseError as ParsimParseError
from parsimonious.exceptions import (IncompleteParseError as
                                     ParsimIncompleteParseError)

def _tax_help():
    return ("use different taxonomy version than default (%s),"
            " acceptable values are %s" % (
                GemTaxonomy.default_tax_version, ", ".join(
                    [x for x in GemTaxonomy.available_tax_versions])))

def info():
    format_default = GemTaxonomy.INFO_OUT_TYPE.TEXT
    formats_str = ', '.join([
        ('"%s" (default)' if GemTaxonomy.INFO_OUT_TYPE.DICT[
            x] == format_default else '"%s"') % x for x in
        GemTaxonomy.INFO_OUT_TYPE.DICT.keys()])

    parser = argparse.ArgumentParser(
        description='Info about taxonomy string tools.')
    parser.add_argument(
        '-f', '--format',
        help=formats_str,
        default=list(
            GemTaxonomy.INFO_OUT_TYPE.DICT.keys())[
                list(GemTaxonomy.INFO_OUT_TYPE.DICT.values()).index(
                    format_default)]
    )
    parser.add_argument('-V', '--version', action='version',
                        version='%s' % __version__,
                        help='show application version and exit')

    args = parser.parse_args()

    ret = GemTaxonomy.info(fmt=args.format)
    print(ret)

# GemTaxonomy.default_version
def validate():
    parser = argparse.ArgumentParser(
        description='Validate taxonomy string.')
    parser.add_argument(
        '-t', '--taxonomy-vers', nargs=1,
        default=[GemTaxonomy.default_tax_version],
        choices=GemTaxonomy.available_tax_versions,
        metavar='<taxonomy_vers>', help=_tax_help())
    parser.add_argument(
        'taxonomy_str', type=str, help='The taxonomy string to validate')
    parser.add_argument(
        '-c', '--canonical', action='store_true',
        help='return 0 if taxonomy_str is a canonical taxonomy string only')
    parser.add_argument(
        '-r', '--report', action='store_true',
        help=('dump a json with information about canonicity of taxonomy_str:'
              ' {"is_canonical": true} if canonical, else {"is_canonical":'
              ' false, "canonical": "<canonical_taxonomy_str>"}'))
    parser.add_argument('-V', '--version', action='version',
                        version='%s' % __version__,
                        help='show application version and exit')

    args = parser.parse_args()

    gt = GemTaxonomy(vers=args.taxonomy_vers[0])

    try:
        _, _, report = gt.validate(args.taxonomy_str)
        if args.report:
            print(json.dumps(report))
    except (ValueError, ParsimParseError,
            ParsimIncompleteParseError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
    if args.canonical:
        sys.exit(0 if report['is_canonical'] else 1)
    else:
        sys.exit(0)


def explain():
    format_default = GemTaxonomy.EXPL_OUT_TYPE.MULTILINE
    formats_str = ', '.join([
        ('"%s" (default)' if GemTaxonomy.EXPL_OUT_TYPE.DICT[
            x] == format_default else '"%s"') % x for x in
        GemTaxonomy.EXPL_OUT_TYPE.DICT.keys()])

    parser = argparse.ArgumentParser(
        description='Validate taxonomy string (version %s).' %
        GemTaxonomy.default_tax_version)
    parser.add_argument(
        '-t', '--taxonomy-vers', nargs=1,
        default=[GemTaxonomy.default_tax_version],
        choices=GemTaxonomy.available_tax_versions,
        metavar='<taxonomy_vers>', help=_tax_help())
    parser.add_argument(
        'taxonomy_str', type=str, help='The taxonomy string to validate')
    parser.add_argument(
        '-f', '--format',
        help=formats_str,
        default=list(
            GemTaxonomy.EXPL_OUT_TYPE.DICT.keys())[
                list(GemTaxonomy.EXPL_OUT_TYPE.DICT.values()).index(
                    format_default)]
    )
    parser.add_argument('-V', '--version', action='version',
                        version='%s' % __version__,
                        help='show application version and exit')

    args = parser.parse_args()

    gt = GemTaxonomy(vers=args.taxonomy_vers[0])

    try:
        fmt, expl, val_reply = gt.explain(args.taxonomy_str, fmt=args.format)
    except (ValueError, ParsimParseError,
            ParsimIncompleteParseError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

    gt.dump_explain(fmt, expl)

    sys.exit(0)


def parse_conf_rows(files2check, cols4files, conf_rows):
    for is_load in (True, False):
        for conf_row in conf_rows:
            if len(conf_row) < 1:
                continue
            if conf_row[0][0] == '#':
                continue

            if (conf_row[0][0] != '!') != is_load:
                continue

            if conf_row[0][0] == '!':
                del_list = glob.glob(conf_row[0][1:])
                for del_item in del_list:
                    try:
                        files2check.remove(del_item)
                        del cols4files[del_item]
                    except ValueError:
                        pass
            else:
                filenames = glob.glob(conf_row[0])
                for filename in filenames:
                    files2check.append(filename)
                    col_info = {
                        'header_rows': 1,
                        'check': [],
                        'check_n': [],
                        'n_map': {},
                    }
                    if len(conf_row) > 1:
                        col_info['header_rows'] = int(conf_row[1])
                    if len(conf_row) > 2:
                        for field in conf_row[2:]:
                            if field[0:2] == 'N:':
                                col_info['check_n'].append(
                                    int(field[2:]))
                            else:
                                if col_info['header_rows'] == 0:
                                    raise ValueError(
                                        'misconfiguration for file \'%s\''
                                        ', headers rows number is set to 0 but'
                                        ' column named \'%s\' is defined'
                                        ' instead of an index.' % (
                                            filename, field))

                                col_info['check'].append(
                                    field)
                    elif len(conf_row) <= 2 and col_info['header_rows'] > 0:
                        # as default, if there is an header 'taxonomý' and
                        # 'TAXONOMY' are searched as taxonomy fields
                        col_info['check'].append('taxonomy')
                        col_info['check'].append('TAXONOMY')
                    else:
                        raise ValueError(
                            'misconfiguration for file \'%s\''
                            ', no header rows present and no column indexes'
                            ' are specified.' % filename)

                    cols4files[filename] = col_info


def _sniff_lineterm(fin):
    first_row = fin.readline()
    if first_row.endswith('\r\n'):
        ret = '\r\n'
    elif first_row.endswith('\r'):
        ret = '\r'
    elif first_row.endswith('\n'):
        ret = '\n'
    fin.seek(0)
    return ret


def csv_validate():
    PREPROC_SAFETY_FILE = 'PREPROCESS_SAFETY_FILE.run-once'
    parser = argparse.ArgumentParser(
        description='''Validates field[s] of csvfile as GEM taxonomy string.
A config file (-c|--config option) and/or at least one file must be specified.
''',
        epilog=(
            '''exit status:
    0          if all taxonomies are valid
    1          at least one taxonomy string is invalid

note:
    If some taxonomy string is valid but not in the canonical form a
        line will be printed in the form:
    "filename|row_num|column|original_taxonomy|0|canonical_taxonomy"

    If some taxonomy result not valid a line will be printed in the form:
    "filename|row_num|column|original_taxonomy|1|error_message"'''),
        formatter_class=RawTextHelpFormatter
    )
    parser.add_argument(
        '-t', '--taxonomy-vers', nargs=1,
        default=[GemTaxonomy.default_tax_version],
        choices=GemTaxonomy.available_tax_versions,
        metavar='<taxonomy_vers>', help=_tax_help())
    parser.add_argument(
        '-C', '--canonical', action='store_true',
        help='return 0 if taxonomy strings are all canonical GEM taxonomy'
        ' string only')
    parser.add_argument(
        '-d', '--debug', action='store_true',
        help='enable informations to debug the script and configuration file')
    parser.add_argument(
        '-v', '--verbose', action='store_true',
        help='increase verbosity')
    parser.add_argument(
        '-c', '--config', nargs=1, default=None,
        help=('configuration file where each line is'
              ' [!]<globbing-files>[:field1[:field2[...]]]'))
    parser.add_argument(
        '-s', '--sanitize', nargs=1, default=None,
        help=('try to sanitize non compliant column elements via an external'
              ' command (bufferized results will be used)'))
    parser.add_argument(
        '-S', '--subfield', nargs=2, metavar=('SEPARATOR', 'INDEX'),
        default=None, help=(
            'if field SEPARATOR is present try to split the field and get'
            ' the INDEX-nt sub-element as taxonomy string'))
    parser.add_argument(
        '-p', '--preprocess', nargs=1, default=None,
        help=('try to modify each column element via an external command, '
              'to avoid to run two times cousing destructive changes local'
              ' existence of a safety file (%s) is required (and removed by'
              ' the script itself' % PREPROC_SAFETY_FILE))
    parser.add_argument(
        'files_and_cols', type=str, nargs='*', default=None,
        help=(
            'Files and columns information in the form: \'filename1\''
            ' [<headers_N_of_rows> [\'f1col1\' [\'f1col2\' [...]]]] [\',\''
            '\'filename2\' [<headers_N_of_rows> [\'f2col1\'] [...]]]]\n'
            'filename support globbing expansion internally (use single'
            ' quote around it to avoid shell to expand it)\n'
            'column prefixed with \'N:<int>\' means identify the column by'
            ' it\'s index\n'
            'in the other cases column specify the column name (in a CSV with'
            ' header)\n'
            'if no columns are specified any lowercase column name equal to'
            ' \'taxonomy\' will be checked\n'
            '\',\' use comma to separate two different filenames descriptions')
        )
    parser.add_argument('-V', '--version', action='version',
                        version='%s' % __version__,
                        help='show application version and exit')

    args = parser.parse_args()

    if args.preprocess:
        if os.path.isfile(PREPROC_SAFETY_FILE):
            os.remove(PREPROC_SAFETY_FILE)
        else:
            print(
                'Preprocess option enabled but "%s" file doesn\'t exists, '
                'create it and run again the command to perform '
                'preprocessing ("%s" file will be deleted by the command)' %
                (PREPROC_SAFETY_FILE, PREPROC_SAFETY_FILE), file=sys.stderr)
            sys.exit(2)

    if args.debug:
        from pprint import pprint

    if args.config is None and (not args.files_and_cols):
        parser.print_help()
        sys.exit(1)

    files2check = []
    cols4files = {}

    if args.config:
        conf_rows = []
        fconf = open(args.config[0])
        for line in fconf:
            csv_reader = csv.reader([line])
            for row in csv_reader:
                conf_row = []
                for field in row:
                    conf_row.append(field)
            conf_rows.append(conf_row)

        parse_conf_rows(files2check, cols4files, conf_rows)

    if args.debug:
        print('\nAFTER CONFIG', file=sys.stderr)
        print("files2check", file=sys.stderr)
        pprint(files2check, stream=sys.stderr)
        print("cols4files", file=sys.stderr)
        pprint(cols4files, stream=sys.stderr)

    if args.files_and_cols:
        conf_rows = []
        is_first = True
        for item in args.files_and_cols:
            if is_first:
                conf_row = [item]
                conf_rows.append(conf_row)
                is_first = False
            elif item == ',':
                is_first = True
            else:
                conf_row.append(item)
        parse_conf_rows(files2check, cols4files, conf_rows)

    if args.debug:
        print('\nAFTER ARGS', file=sys.stderr)
        print("files2check", file=sys.stderr)
        pprint(files2check, stream=sys.stderr)
        print("cols4files", file=sys.stderr)
        pprint(cols4files, stream=sys.stderr)

    gt = GemTaxonomy(vers=args.taxonomy_vers[0])

    if args.preprocess:
        prep_proc = subprocess.Popen([args.preprocess[0]],
                                     stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE,
                                     universal_newlines=True)

    if args.sanitize:
        sani_proc = subprocess.Popen([args.sanitize[0]],
                                     stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE,
                                     universal_newlines=True)
        sani_cache = {}

    ret_code = 0
    for filename in files2check:
        if args.verbose:
            print('csv_validate: %s' % filename, file=sys.stderr)
        cols4file = cols4files[filename]
        with open(filename, newline='', encoding='utf-8-sig') as csvfile:
            if args.preprocess or args.sanitize:
                lineterm = _sniff_lineterm(csvfile)
                filename_out = "%s.taxs" % filename
                fout = open(filename_out, 'w')
                csvwriter = csv.writer(fout, lineterminator=lineterm)

            csvreader = csv.reader(csvfile)
            last_header = None
            for header in range(0, cols4file['header_rows']):
                last_header = next(csvreader, None)
                if args.preprocess or args.sanitize:
                    csvwriter.writerow(last_header)
            if last_header:
                for col2check in cols4file['check']:
                    try:
                        idx = last_header.index(col2check)
                        cols4file['check_n'].append(idx)
                        cols4file['n_map'][idx] = col2check
                    except ValueError as exc:
                        if args.debug:
                            print(
                                'For file \'%s\' column \'%s\' not found' % (
                                    filename, col2check),
                                file=sys.stderr)
                        continue
            if args.debug:
                print("\nBEFORE CSV LOOP", file=sys.stderr)
                pprint(cols4files, stream=sys.stderr)

            if args.verbose:
                print('  check cols: %s' % ', '.join([
                    (cols4file['n_map'][col] if col in
                     cols4file['n_map'] else col)
                    for col in cols4file['check_n']]), file=sys.stderr)
            for row_idx, row in enumerate(csvreader,
                                          start=cols4file['header_rows']):
                if args.preprocess or args.sanitize:
                    row_out = row[:]
                for col in cols4file['check_n']:
                    if args.preprocess:
                        prep_proc.stdin.write(row[col] + '\n')
                        prep_proc.stdin.flush()
                        tax = prep_proc.stdout.readline().strip()
                        row_out[col] = tax
                    else:
                        tax = row[col]

                    tax_list = None
                    if args.subfield:
                        if tax.find(args.subfield[0]):
                            tax_list = tax.split(args.subfield[0])
                            tax = tax_list[int(args.subfield[1])]
                    try:
                        _, _, report = gt.validate(tax)
                        if report['is_canonical'] is False:
                            print('%s|%d|%s|%s|%d|%s' % (
                                filename, row_idx,
                                (col if col not in cols4file['n_map']
                                 else cols4file['n_map'][col]), tax, 0,
                                report['canonical']))
                            if args.canonical is True:
                                ret_code = 1
                            if args.sanitize:
                                if tax_list:
                                    tax_list[int(args.subfield[1])] = report[
                                        'canonical']
                                    row_out[col] = args.subfield[0].join(
                                        tax_list)
                                else:
                                    row_out[col] = report['canonical']
                    except (ValueError, ParsimParseError,
                            ParsimIncompleteParseError) as exc:
                        ret_code = 1
                        print('%s|%d|%s|%s|%d|%s' % (
                            filename, row_idx,
                            (col if col not in cols4file['n_map']
                             else cols4file['n_map'][col]),
                            tax, 1, str(exc)))
                        if args.sanitize:
                            if tax not in sani_cache:
                                sani_proc.stdin.write(tax + '\n')
                                sani_proc.stdin.flush()
                                tax_new = sani_proc.stdout.readline().strip()
                                sani_cache[tax] = tax_new

                            if tax_list:
                                tax_list[int(args.subfield[1])] = sani_cache[
                                    tax]
                                row_out[col] = args.subfield[0].join(
                                    tax_list)
                            else:
                                row_out[col] = sani_cache[tax]
                if args.sanitize:
                    csvwriter.writerow(row_out)

        if args.preprocess or args.sanitize:
            fout.close()
            os.rename('%s.taxs' % filename, filename)

    if args.preprocess:
        prep_proc.terminate()
        prep_proc.wait()

    if args.sanitize:
        sani_proc.terminate()
        sani_proc.wait()

    sys.exit(ret_code)


def _graph_check_args(gt, atom, atom_leaf):
    if not atom['args']:
        return

    atom_args = json.loads(atom['args'])
    atom_args_type_parts = atom_args['type'].split('(')
    atom_args_type = atom_args_type_parts[0]
    if atom_args_type == 'filtered_atomsgroup':
        args_group_name = atom_args_type_parts[1].split(
            ',')[0][1:-1]
        args_title = "(%s)" % gt.tax[
            'AtomsGroupDict'][args_group_name]['title']
        if not atom_leaf.exists_child(args_title):
            args_leaf = OutLeaf()
            atom_leaf.add_child(args_title, args_leaf)
    elif atom_args_type == 'filtered_attribute':
        args_attr_name = atom_args_type_parts[1].split(
            ',')[0][1:-1]
        args_title = "(/%s/)" % gt.tax[
            'AttributeDict'][args_attr_name]['title']
        if not atom_leaf.exists_child(args_title):
            args_leaf = OutLeaf()
            atom_leaf.add_child(args_title, args_leaf)


def _graph_check_deny(gt, atom, atom_leaf):
    if atom['name'] not in gt.tax['AtomsDeny']:
        return

    for deny in gt.tax['AtomsDeny'][atom['name']]:
        deny_group = gt.tax['AtomsGroupDict'][gt.tax['AtomDict'][deny]['group']]['title']

        if not atom_leaf.exists_deny(deny_group):
            atom_leaf.add_deny(deny_group, OutLeaf(key=deny_group))


def _graph_dive_deps(gt, atom_anc, atom_anc_leaf):
    for k, v in gt.tax['AtomsDeps'].items():
        if atom_anc['name'] in v:
            atom = gt.tax['AtomDict'][k]
            group_title = gt.tax['AtomsGroupDict'][
                atom['group']]['title']
            if atom_anc_leaf.exists_child(group_title):
                atom_leaf = atom_anc_leaf.get_child(group_title)
            else:
                atom_leaf = OutLeaf()
                atom_anc_leaf.add_child(group_title, atom_leaf)

            _graph_check_deny(gt, atom, atom_leaf)
            _graph_dive_deps(gt, gt.tax['AtomDict'][k],
                             atom_leaf)
    _graph_check_args(gt, atom_anc, atom_anc_leaf)


def _graph_print(leaf, spc=0):
    for key, el in leaf.items():
        if spc == 0:
            print()
        if el.denies:
            denies = ', '.join(['[NOT IF %s]' % deny_key for deny_key in el.denies])
        else:
            denies = ''
        print(" " * spc + key + ' ' + denies)
        if el:
            _graph_print(el, spc=(spc + 4))

g_rank = []
g_rank_els = []

def _graph_dot_el(tree, parent_key=None, rank_level=0):
    global g_rank, g_rank_els  # noqa: F824

    try:
        g_rank[rank_level]
    except IndexError:
        g_rank.insert(rank_level, '\n    {\n        rank = same;\n        ')
        g_rank_els.insert(rank_level, '')

    for key, el in tree.items():
        is_arg = False
        is_attr = False
        if key[0] == '(':
            is_arg = True
            key = key[1:-1]
        if key[0] == '/':
            is_attr = True

        if is_attr:
            print('    "%s" [shape="rectangle"]' % key)
        else:
            print('    "%s"' % key)

        if parent_key:
            if is_arg:
                print('    "%s" -> "%s" [color="green"]' % (
                    parent_key, key))
            else:
                print('    "%s" -> "%s"' % (
                    parent_key, key))

        if not is_arg:
            if g_rank_els[rank_level] != '':
                g_rank_els[rank_level] += ' -> '
            g_rank_els[rank_level] += '"%s"' % key
        if el.denies:
            for deny in el.denies:
                print('    "%s" -> "%s" [color="red", arrowhead="box"]' % (
                    deny, key))
        _graph_dot_el(el, parent_key=key, rank_level=(rank_level + 1))

    if not parent_key:
        for i in range(0, len(g_rank)):
            if len(g_rank_els[i]) == 0:
                continue
            g_rank[i] += g_rank_els[i]
            if '->' in g_rank_els[i]:
                # NOTE: to show rank arrow uncomment the line below and comment the
                #       next one
                g_rank[i] += ' [ color=cyan ]'
                # g_rank[i] += ' [ style=invis ]'
            g_rank[i] += ';\n        rankdir = TB;\n'
            g_rank[i] += '    }'
            print(g_rank[i])


def _graph_dot(tree):
    print('digraph {')
    print('    rankdir="LR"')
    print('')

    _graph_dot_el(tree)
    print('}')


class OutLeaf:
    def __init__(self, key=None, child=None, deny=None):
        if key:
            self.key = key
        self.children = {}
        if child:
            self.children[child[0]] = child[1]

        self.denies = {}
        if deny:
            self.denies[deny[0]] = deny[1]

    def __iter__(self):
        for child in self.children:
            yield child

    def items(self):
        for key, child in self.children.items():
            yield (key, child)

    def __next__(self):
        if self.a <= 20:
            x = self.a
            self.a += 1
            return x
        else:
            raise StopIteration

    def set_name(self, name):
        self.name = name

    def add_child(self, name, child):
        child.set_name(name)
        self.children[name] = child

    def add_deny(self, name, deny):
        deny.set_name(name)
        self.denies[name] = deny

    def get_child(self, name):
        if name in self.children:
            return self.children[name]
        else:
            return None

    def get_deny(self, name):
        if name in self.denies:
            return self.denies[name]
        else:
            return None

    def exists_child(self, child_name):
        return (child_name in self.children)

    def exists_deny(self, deny_name):
        return (deny_name in self.denies)


def specs2graph():
    parser = argparse.ArgumentParser(
        description='Create graph of taxonomy specifications (version %s).' %
        GemTaxonomy.default_tax_version)
    parser.add_argument(
        '-t', '--taxonomy-vers', nargs=1,
        default=[GemTaxonomy.default_tax_version],
        choices=GemTaxonomy.available_tax_versions,
        metavar='<taxonomy_vers>', help=_tax_help())
    parser.add_argument(
        '-d', '--dot', action='store_true',
        help='generate a gragh in .dot format')
    parser.add_argument('-V', '--version', action='version',
                        version='%s' % __version__,
                        help='show application version and exit')

    args = parser.parse_args()
    out_leaf = OutLeaf()

    gt = GemTaxonomy(vers=args.taxonomy_vers[0])
    for attr in gt.tax['Attribute']:
        attr_leaf = OutLeaf()
        out_leaf.add_child(("/%s/" % attr['title']), attr_leaf)

        for atom in gt.tax['Atom']:
            # print(atom['attr'])
            if atom['attr'] != attr['name']:
                continue

            if atom['name'] not in gt.tax['AtomsDeps']:
                group_title = gt.tax['AtomsGroupDict'][
                    atom['group']]['title']
                if attr_leaf.exists_child(group_title):
                    atom_leaf = attr_leaf.get_child(group_title)
                else:
                    atom_leaf = OutLeaf()
                    attr_leaf.add_child(group_title, atom_leaf)

                _graph_dive_deps(gt, atom, atom_leaf)

    if args.dot:
        _graph_dot(out_leaf)
    else:
        _graph_print(out_leaf)
