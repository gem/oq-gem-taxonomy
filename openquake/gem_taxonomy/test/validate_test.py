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
from parsimonious.exceptions import (IncompleteParseError as
                                     ParsimIncompleteParseError)
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
    ("HYB(LFBR;LPB)", "For attribute [LFBR] discordant"
     " [atom/argument]->[attribute] associations: [args HYB]->[material] vs"
     " [LFBR]->[llrs]"),
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

    ("W()", "Rule 'attr' matched in its entirety, but it didn't consume all"
     " the text. The non-matching portion of the text begins with '()'"
     " (line 1, column 2)."),

    ("RES:2", None),
    ("RES:2:2A", "Attribute [RES:2:2A]: atom [RES] requires a maximum of 1"
     " parameter, 2 found [RES:2:2A]."),
    ("RES:2WWWWW", "Atom [RES:2WWWWW]: parameters option [2WWWWW] not found."),
    ("W:123", "Attribute [W:123]: no parameters expected for"
     " atom [W], found (['123'])"),
    ("H", "Attribute [H]: atom H requires at least 1 parameter, 0 found [H]."),
    ("H:3", None),
    ("H:3:5", "Attribute [H:3:5]: atom [H] requires a maximum of 1 parameter,"
     " 2 found [H:3:5]."),
    ("IRI+IRP(TOR;REC)", None),
    ("IRI+IRP(TOR;CHV)", "Attribute [IRI+IRP(TOR;CHV)], atom [CHV], expected"
     " atomsgroup [plan_irregularity], found atom [CHV] of atomsgroup"
     " [vertical_irregularity]."),
    ("MIX(RES;MIX(COM;GOV))", "Attribute [MIX(RES;MIX(COM;GOV))],"
     " forbidden atom found [MIX]."),
    ("MIX(RES;COM;GOV)", None),

    ("LFM+DCW:-0.5", "Atom [DCW:-0.5]: value [-0.5] less then min value"
     " (0.000000)."),
    ("LFM+DCW:0.5", None),
    ("LFM+DCW:1.5", "Atom [DCW:1.5]: value [1.5] greater then max value"
     " (1.000000)."),
    ("LFM+DCW:1.5.3.2", "Atom [DCW:1.5.3.2]: value [1.5.3.2] not valid"
     " float."),

    ("HBAPP:-1", "Atom [HBAPP:-1]: value [-1] less then min value"
     " (0)."),
    ("HBAPP:1", None),
    ("HBAPP:1000", None),
    ("HBAPP:11ss22", "Atom [HBAPP:11ss22]: value 11ss22 not valid int."),

    # float
    ("HD:0", None),
    ("HD:0.1", None),
    ("HD:45.5", None),
    ("HD:89.9", None),
    ("HD:90.0", "Atom [HD:90.0]: value [90.0] greater or equal then max value"
     " (90.000000)."),

    # rangeable_float
    ("HF:-3", "Atom [HF:-3]: value [-3] less then min value (0.000000)."),
    ("HF:<-3", "Atom [HF:<-3]: value [-3] less then min value (0.000000)."),
    ("HF:>-3", "Atom [HF:>-3]: value [-3] less then min value (0.000000)."),
    ("HF:<3", None),
    ("HF:>3", None),
    ("HF:<0", "Atom [HF:<0]: incorrect float inequality, no valid values below"
     " min value (0)."),
    ("HF:0-3", None),
    ("HF:3-6", None),
    ("HF:3-0", "Atom [HF:3-0]: incorrect floats range: first endpoint"
     " is greater then or equal to the second (3-0)"),

    # rangeable_int
    ("H:-3", "Atom [H:-3]: value [-3] less then min value (0)."),
    ("H:<-3", "Atom [H:<-3]: value [-3] less then min value (0)."),
    ("H:>-3", "Atom [H:>-3]: value [-3] less then min value (0)."),
    ("H:<3", None),
    ("H:>3", None),
    ("H:<0", "Atom [H:<0]: incorrect int inequality, no valid values below"
     " min value (0)."),
    ("H:0-3", None),
    ("H:3-6", None),
    ("H:3-0", "Atom [H:3-0]: incorrect integers range: first endpoint"
     " is greater then or equal to the second (3-0)"),
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
            except (ParsimParseError,
                    ParsimIncompleteParseError) as exc:
                self.assertEqual(
                    str(exc), tax[1],
                    msg='Expected "%s" Found "%s"' %
                        (tax[1], str(exc)))
