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
from collections import OrderedDict
import json
import glob
import argparse
import subprocess
from argparse import RawTextHelpFormatter
from openquake.gem_taxonomy import GemTaxonomy, __version__
from parsimonious.exceptions import ParseError as ParsimParseError
from parsimonious.exceptions import (IncompleteParseError as
                                     ParsimIncompleteParseError)


def info():
    format_default = GemTaxonomy.INFO_OUT_TYPE.TEXT
    formats_str = ', '.join([
        ('"%s" (default)' if GemTaxonomy.INFO_OUT_TYPE.DICT[
            x] == format_default else '"%s"') % x for x in
        GemTaxonomy.INFO_OUT_TYPE.DICT.keys()])

    parser = argparse.ArgumentParser(
        description='Info about taxonomy string tools (version 3.3).')
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

    ret = GemTaxonomy.info(fmt=('dict' if args.format == 'json'
                                else args.format))
    if args.format == 'json':
        print(json.dumps(ret))
    else:
        print(ret)


def validate():
    parser = argparse.ArgumentParser(
        description='Validate taxonomy string (version 3.3).')
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

    gt = GemTaxonomy()

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
        description='Validate taxonomy string (version 3.3).')
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

    gt = GemTaxonomy()

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

    gt = GemTaxonomy()

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


def _graph_check_args(gt, atom, atom_tree):
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
        if args_title not in atom_tree:
            args_tree = OrderedDict()
            atom_tree[args_title] = args_tree
    elif atom_args_type == 'filtered_attribute':
        args_attr_name = atom_args_type_parts[1].split(
            ',')[0][1:-1]
        args_title = "(/%s/)" % gt.tax[
            'AttributeDict'][args_attr_name]['title']
        if args_title not in atom_tree:
            args_tree = OrderedDict()
            atom_tree[args_title] = args_tree


def _graph_dive_deps(gt, atom_anc, atom_anc_tree):
    for k, v in gt.tax['AtomsDeps'].items():
        if atom_anc['name'] in v:
            atom = gt.tax['AtomDict'][k]
            group_title = gt.tax['AtomsGroupDict'][
                atom['group']]['title']
            if group_title in atom_anc_tree:
                atom_tree = atom_anc_tree[group_title]
            else:
                atom_tree = OrderedDict()
                atom_anc_tree[group_title] = atom_tree

            _graph_dive_deps(gt, gt.tax['AtomDict'][k],
                             atom_tree)
    _graph_check_args(gt, atom_anc, atom_anc_tree)


def _graph_print(tree, spc=0):
    for key, el in tree.items():
        if spc == 0:
            print()
        print(" " * spc + key)
        if el:
            _graph_print(el, spc=(spc + 4))


def _graph_dot_el(tree, parent_key=None):
    rank = '    {rank = same;\n'
    rank_els = ''
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
                print('    "%s" -> "%s" [color="red"]' % (
                    parent_key, key))
            else:
                print('    "%s" -> "%s"' % (
                    parent_key, key))
        else:
            if rank_els != '':
                rank_els += ' -> '
            rank_els += '"%s"' % key
        _graph_dot_el(el, parent_key=key)

    if not parent_key:
        rank += rank_els
        rank += ' [ style=invis ]; rankdir = TB;\n'
        rank += '    }'
        print(rank)


def _graph_dot(tree):
    print('digraph {')
    print('    rankdir="LR"')
    print('')

    _graph_dot_el(tree)
    print('}')


def specs2graph():
    parser = argparse.ArgumentParser(
        description='Create graph of taxonomy specifications (version 3.3).')
    parser.add_argument(
        '-d', '--dot', action='store_true',
        help='generate a gragh in .dot format')
    parser.add_argument('-V', '--version', action='version',
                        version='%s' % __version__,
                        help='show application version and exit')

    args = parser.parse_args()
    out_tree = OrderedDict()

    gt = GemTaxonomy()
    for attr in gt.tax['Attribute']:
        attr_tree = OrderedDict()
        out_tree[("/%s/" % attr['title'])] = attr_tree

        for atom in gt.tax['Atom']:
            # print(atom['attr'])
            if atom['attr'] != attr['name']:
                continue

            if atom['name'] not in gt.tax['AtomsDeps']:
                group_title = gt.tax['AtomsGroupDict'][
                    atom['group']]['title']
                if group_title in attr_tree:
                    atom_tree = attr_tree[group_title]
                else:
                    atom_tree = OrderedDict()
                    attr_tree[group_title] = atom_tree

                _graph_dive_deps(gt, atom, atom_tree)

    if args.dot:
        _graph_dot(out_tree)
    else:
        _graph_print(out_tree)
