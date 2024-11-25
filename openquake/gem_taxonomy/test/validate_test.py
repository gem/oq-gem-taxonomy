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
import unittest
from openquake.gem_taxonomy import GemTaxonomy
from parsimonious.exceptions import ParseError as ParsimParseError
taxonomy_strings = [
    ("!?", "Rule 'attr' didn't match at '!?' (line 1, column 1)."),
    ("S+S", "Attribute [S+S]: multiple occurrencies of [S] atom."),
    ("C+LO", "For attribute [C+LO] discordant [atom/argument]->[attribute]"
     " associations: [C]->[material] vs [LO]->[llrs]"),
    ("MDD(W)", "Attribute [MDD(W)]: atom MDD requires at"
     " least 2 arguments, 1 found [MDD(W)]."),
    ("MDD(W,Z)", "Rule 'attr' matched in its entirety, but it didn't"
     " consume all the text. The non-matching portion of"
     " the text begins with '(W,Z)' (line 1, column 4)."),

    ("HYB(C;S)", None),
    ("HYB(C;S;W)", None),
    ("MDD(C;LO)", "For attribute [LO] discordant [atom/argument]->[attribute]"
     " associations: [args MDD]->[material] vs [LO]->[llrs]"),
    ("MDD(C;S;W)", "Attribute [MDD(C;S;W)]: atom [MDD] requires a maximum of"
     " 2 arguments, 3 found [MDD(C;S;W)]."),
    ("MDD(HYB(C;HYB);S)", "Attribute [MDD(HYB(C;HYB);S)], scope [args MDD,"
     " args HYB]: forbidden atom recusion found [HYB]."),
    ("MDD(HYB(C;LO);S)", "For attribute [LO] discordant [atom/argument]->"
     "[attribute] associations: [args MDD, args HYB]->[material] vs [LO]->"
     "[llrs]"),
    ("MDD(HYB(C);S)", "Attribute [MDD(HYB(C);S)]: atom HYB requires at least"
     " 2 arguments, 1 found [HYB(C)]."),
    ("MDD(HYB(C;S);S)", None),
    ("MDD(HYB(C,S,W);S)", "Rule 'attr' matched in its entirety, but it didn't"
     " consume all the text. The non-matching portion of the text begins with"
     " '(HYB(C,S,W);S)' (line 1, column 4)."),
    ("MDD(HYB(C;S;W);S)", None),
    ("MDD(HYB(S;W(X;Y)))", "Attribute [MDD(HYB(S;W(X;Y)))]: atom MDD requires"
     " at least 2 arguments, 1 found [MDD(HYB(S;W(X;Y)))]."),
    ("MDD(HYB(S;W(X;Y)), S)", "Rule 'attr' matched in its entirety, but it"
     " didn't consume all the text. The non-matching portion of the text"
     " begins with '(HYB(S;W(X;Y)), S)' (line 1, column 4)."),
    ("MDD(HYB(S;W(X;Y));S)", "Attribute [MDD(HYB(S;W(X;Y));S)]: argument[s]"
     " not expected for atom [W]."),
    ("MDD(MDD(C;LO);S)", "Attribute [MDD(MDD(C;LO);S)], scope [args MDD]:"
     " forbidden atom recusion found [MDD]."),
    ("MDD(W)", "Attribute [MDD(W)]: atom MDD requires at least 2 arguments,"
     " 1 found [MDD(W)]."),
    ("MDD(W, Z)", "Rule 'attr' matched in its entirety, but it didn't consume"
     " all the text. The non-matching portion of the text begins with '(W, Z)'"
     " (line 1, column 4)."),
    ("MDD(W,Z)", "Rule 'attr' matched in its entirety, but it didn't consume"
     " all the text. The non-matching portion of the text begins with '(W,Z)'"
     " (line 1, column 4)."),
    ("MDD(W;Z)", "Attribute [MDD(W;Z)]: unknown atom [Z]."),
]


def to_log(s_exp):
    return (s_exp if s_exp[1] is not None else (s_exp[0], "Success"))


class ValidateTestCase(unittest.TestCase):
    def test(self):
        print()
        gt = GemTaxonomy()
        for tax in taxonomy_strings:
            print('Test: "%s", expected: "%s"' %
                  to_log(tax))
            try:
                gt.validate(tax[0])
                self.assertEqual(
                    tax[1], None,
                    msg='Expected "%s" but not detected' %
                    (tax[1],))
            except ValueError as exc:
                self.assertEqual(
                    str(exc), tax[1],
                    msg='Expected "%s" Found "%s"' %
                    (tax[1], str(exc)))
            except ParsimParseError as exc:
                self.assertEqual(
                    str(exc), tax[1],
                    msg='Expected "%s" Found "%s"' %
                        (tax[1], str(exc)))
