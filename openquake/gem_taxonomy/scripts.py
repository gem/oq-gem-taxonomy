# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2024 GEM Foundation
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
import sys
import csv
import json
import glob
import argparse
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
        _, report = gt.validate(args.taxonomy_str)
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
        expl = gt.explain(args.taxonomy_str, fmt=args.format)
    except (ValueError, ParsimParseError,
            ParsimIncompleteParseError) as exc:
        print(str(exc), file=sys.stderr)

        sys.exit(1)
    print(json.dumps(expl))
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


def csv_validate():
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
        '-c', '--config', nargs='?', default=None,
        help=('configuration file where each line is'
              ' [!]<globbing-files>[:field1[:field2[...]]]'))
    parser.add_argument(
        'files_and_cols', type=str, nargs='*', default=None,
        help=(
            'Files and columns information in the form: \'filename1\''
            ' [<headers_N_of_rows> [\'f1col1\' [\'f1col2\' [...]]]] [\',\'',
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

    if args.debug:
        from pprint import pprint

    if args.config is None and (not args.files_and_cols):
        parser.print_help()
        sys.exit(1)

    files2check = []
    cols4files = {}

    if args.config:
        conf_rows = []
        fconf = open(args.config)
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

    ret_code = 0
    for filename in files2check:
        if args.verbose:
            print('csv_validate: %s' % filename, file=sys.stderr)
        cols4file = cols4files[filename]
        with open(filename) as csvfile:
            csvreader = csv.reader(csvfile)
            last_header = None
            for header in range(0, cols4file['header_rows']):
                last_header = next(csvreader, None)
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
                for col in cols4file['check_n']:
                    tax = row[col]
                    try:
                        _, report = gt.validate(tax)
                        if report['is_canonical'] is False:
                            print('%s|%d|%s|%s|%d|%s' % (
                                args.csvfile, row_idx,
                                (col if col not in cols4file['n_map']
                                 else cols4file['n_map'][col]), tax, 0,
                                report['canonical']))
                            if args.canonical is True:
                                ret_code = 1
                    except (ValueError, ParsimParseError,
                            ParsimIncompleteParseError) as exc:
                        ret_code = 1
                        print('%s|%d|%s|%s|%d|%s' % (
                            filename, row_idx,
                            (col if col not in cols4file['n_map']
                             else cols4file['n_map'][col]),
                            tax, 1, str(exc)))

    sys.exit(ret_code)
