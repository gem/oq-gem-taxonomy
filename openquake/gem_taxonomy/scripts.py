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
from openquake.gem_taxonomy import GemTaxonomy
from parsimonious.exceptions import ParseError as ParsimParseError
from parsimonious.exceptions import (IncompleteParseError as
                                     ParsimIncompleteParseError)


def info():
    GemTaxonomy.info()


def validate():
    gt = GemTaxonomy()

    try:
        gt.validate(sys.argv[1])
    except (ValueError, ParsimParseError,
            ParsimIncompleteParseError) as exc:
        print(str(exc))
        sys.exit(1)
    sys.exit(0)


def validate_csv_usage(ret):
    print("""
SYNOPSIS
    %s CSVFILE [-n] FIELD1 [FIELD2 [...]]

DESCRIPTION
    Validates field[s] of csv file as valid taxonomy string.
    Fields are identified with lowercase names or indexes  if '-n'
    optional parameter is specified.

    Exit status:
    0          if all taxonomies are valid
    1          at least one taxonomy string is invalid

    Note:
    If some taxonomy string is valid but not in the canonical form
    a line will be printed in the form:
        original_string '|' canonical_form

""")
    sys.exit(ret)


def csv_validate():
    gt = GemTaxonomy()

    if len(sys.argv) < 2 or (
            sys.argv[1] == '-n' and len(sys.argv) < 3):
        validate_csv_usage(1)

    if sys.argv[1] == '-n':
        use_indexes = True
        csv_fields = sys.argv[2:]
    else:
        use_indexes = False
        csv_fields = sys.argv[1:]

    taxonomy_cols = []
    name_cols = {}
    csvfilename = sys.argv[1]
    with open(csvfilename) as csvfile:
        csvreader = csv.reader(csvfile)
        if not use_indexes:
            header = next(csvreader)
            for col, fieldname in enumerate(header):
                if fieldname.lower() in csv_fields:
                    taxonomy_cols.append(col)
                    name_cols[col] = fieldname
            if len(taxonomy_cols) == 0:
                print("No header fieldnames match fields passed as arguments",
                      file=sys.stderr)
        else:
            taxonomy_cols = [int(idx) for idx in csv_fields]

        ret_code = 0
        for idx, row in enumerate(csvreader):
            for col in taxonomy_cols:
                tax = row[col]
                try:
                    gt.validate(tax)
                except (ValueError, ParsimParseError,
                        ParsimIncompleteParseError) as exc:
                    ret_code = 1
                    if use_indexes:
                        # import pdb ; pdb.set_trace()
                        print('%s|%s|%d|%s|%s' % (
                            csvfilename, col, idx, tax, str(exc)),
                              file=sys.stderr)
                    else:
                        # import pdb ; pdb.set_trace()
                        print('%s|%s|%d|%s|%s' % (
                            csvfilename, name_cols[col], idx, tax,
                            str(exc)), file=sys.stderr)
        sys.exit(ret_code)
