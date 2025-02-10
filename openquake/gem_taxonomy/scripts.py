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


def csv_validate():
    parser = argparse.ArgumentParser(
        description='''Validates field[s] of csvfile as GEM taxonomy string.
A config file (-c|--config option) exclusive-or at least one file must be specified.''',
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
        '-c', '--config', nargs='?', default=None,
        help=('configuration file where each line is'
              ' [!]<globbing-files>[:field1[:field2[...]]]'))
    parser.add_argument(
        'files_and_cols', type=str, nargs='*', default=None,
        help='''Files and columns information in the form: \'filename1\' [\'f1col1\' [\'f1col2\' [...]]] [\',\' \'filename2\' [\'f2col1\'] ...]
filename support globbing expansion internally (use single quote around it to avoid shell to expand it)
column prefixed with '!' means skip check of this field
column prefixed with 'N:<int>' means identify the column by it's index
in the other cases column specify the column name (in a CSV with header)
if no columns are specified any lowercase column name equal to 'taxonomy' will be checked
',' use comma to separate two different filenames descriptions''')
    parser.add_argument('-V', '--version', action='version',
                        version='%s' % __version__,
                        help='show application version and exit')

    args = parser.parse_args()

    if bool(args.config is None) == bool(not args.files_and_cols):
        parser.print_help()
        sys.exit(1)

    files2check = []
    files2skip = []
    cols4files = {}
    if args.config:
        fconf = open(args.config)
        for line in fconf:
            csv_reader = csv.reader( [ line ] )
            fields = None
            for row in csv_reader:
                fields = row
            if len(fields) < 1:
                continue
            if fields[0][0] == '#':
                continue
            if fields[0][0] == '!':
                files2skip.append(fields[0][1:])
            else:
                files2check.append(fields[0])
                cols4files[fields[0]] = fields[1:]
    import pdb ; pdb.set_trace()
    sys.exit(123)

    gt = GemTaxonomy()

    taxonomy_cols = []
    name_cols = {}
    with open(args.csvfile) as csvfile:
        csvreader = csv.reader(csvfile)
        if args.numerical:
            taxonomy_cols = [int(idx) for idx in args.field]
        else:
            header = next(csvreader)
            for col, fieldname in enumerate(header):
                if fieldname.lower() in args.field:
                    taxonomy_cols.append(col)
                    name_cols[col] = fieldname
            if len(taxonomy_cols) == 0:
                print("No header fieldnames match fields passed as arguments",
                      file=sys.stderr)

        ret_code = 0
        for idx, row in enumerate(csvreader):
            for col in taxonomy_cols:
                tax = row[col]
                try:
                    report = gt.validate(tax)
                    if report['is_canonical'] is False:
                        print('%s|%d|%s|%s|%d|%s' % (
                            args.csvfile, idx, col, tax, 0,
                            report['canonical']))
                        if args.canonical is True:
                            ret_code = 1
                except (ValueError, ParsimParseError,
                        ParsimIncompleteParseError) as exc:
                    ret_code = 1
                    if args.numerical:
                        print('%s|%d|%s|%s|%d|%s' % (
                            args.csvfile, idx, col, tax, 1,
                            str(exc)))
                    else:
                        print('%s|%d|%s|%s|%d|%s' % (
                            args.csvfile, idx, name_cols[col], tax, 1,
                            str(exc)))
        sys.exit(ret_code)
