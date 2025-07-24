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
import re
import unittest
from openquake.gem_taxonomy import GemTaxonomy
from _pytest.assertion import truncate
truncate.DEFAULT_MAX_LINES = 9999
truncate.DEFAULT_MAX_CHARS = 9999

taxonomy_strings = [
    # Input taxonomy, Expected error, Canonical string (if orig isn't), Repr
    ('UNK', None, None, ''),
    ('', 'Empty taxonomy string is not valid, use \'UNK\' string'
     ' instead.', None, ''),
    ('/M', 'Taxonomy string [/M]: a taxonomy string must start with an'
     ' uppercase alphabetic character. Taxonomy string [/M] parsing'
     ' error: Rule \'taxo\' didn\'t match at \'/M\' (line 1, column 1).'),
    ('M/', 'Taxonomy string [M/]: a taxonomy string must end with an'
     ' uppercase alpha-numeric or a \')\' or a \'.\' character. Taxonomy'
     ' string [M/] parsing error: Rule \'taxo\' matched in its entirety,'
     ' but it didn\'t consume all the text. The non-matching portion of'
     ' the text begins with \'/\' (line 1, column 2).'),
    ('+M', 'Taxonomy string [+M]: a taxonomy string must start with an'
     ' uppercase alphabetic character. Taxonomy string [+M] parsing error:'
     ' Rule \'taxo\' didn\'t match at \'+M\' (line 1, column 1).'),
    ('!?', 'Taxonomy string [!?]: a taxonomy string must start with an'
     ' uppercase alphabetic character. Taxonomy string [!?] parsing error:'
     ' Rule \'taxo\' didn\'t match at \'!?\' (line 1, column 1).'),
    ('M/S', 'Attribute [material] multiple declaration, previous: [M],'
     ' current [S]'),
    ('S+S', 'Attribute [S+S]: multiple occurrencies of [S] atom.'),
    ('C+LO', 'For attribute [C+LO] discordant [atom/argument]->[attribute]'
     ' associations: [C]->[material] vs [LO]->[llrs]'),
    ('MDD(W)', 'Attribute [MDD(W)]: atom MDD requires at'
     ' least 2 arguments, 1 found [MDD(W)].'),
    ('MDD(W,Z)', 'Atom arguments must be included in rounded brackets and'
     ' separated by \';\' character. Taxonomy string [MDD(W,Z)] parsing error:'
     ' Rule \'taxo\' matched in its entirety, but it didn\'t'
     ' consume all the text. The non-matching portion of the text begins'
     ' with \'(W,Z)\' (line 1, column 4).'),
    ('HYB(C;S)', None, None,
     '<ATTR id="0xADDR" name="material">\n    <ATOM id="0xADDR" name="HYB"'
     ' title="Hybrid or composite (mixed) materials">\n        <args>\n'
     '            <ATTR id="0xADDR" name="material">\n                <ATOM'
     ' id="0xADDR" name="C" title="Concrete, unknown reinforcement"/>\n'
     '            </ATTR>\n            <ATTR'
     ' id="0xADDR" name="material">\n                <ATOM id="0xADDR"'
     ' name="S" title="Steel"/>\n            </ATTR>\n'
     '        </args>\n    </ATOM>\n</ATTR>\n'),
    ('HYB(C;S;W)', None, None,
     '<ATTR id="0xADDR" name="material">\n    <ATOM id="0xADDR" name="HYB"'
     ' title="Hybrid or composite (mixed) materials">\n        <args>\n'
     '            <ATTR id="0xADDR" name="material">\n                <ATOM'
     ' id="0xADDR" name="C" title="Concrete, unknown reinforcement"/>\n'
     '            </ATTR>\n            <ATTR'
     ' id="0xADDR" name="material">\n                <ATOM id="0xADDR"'
     ' name="S" title="Steel"/>\n            </ATTR>\n'
     '            <ATTR id="0xADDR" name="material">\n                <ATOM'
     ' id="0xADDR" name="W" title="Wood"/>\n'
     '            </ATTR>\n        </args>\n    </ATOM>\n</ATTR>\n'),
    ('HYB(LFBR;LPB)', 'For attribute [LFBR] discordant'
     ' [atom/argument]->[attribute] associations: [args HYB]->[material] vs'
     ' [LFBR]->[llrs]'),
    ('MDD(C;LO)', 'For attribute [LO] discordant [atom/argument]->[attribute]'
     ' associations: [args MDD]->[material] vs [LO]->[llrs]'),
    ('MDD(C;S;W)', 'Attribute [MDD(C;S;W)]: atom [MDD] requires a maximum of'
     ' 2 arguments, 3 found [MDD(C;S;W)].'),
    ('MDD(HYB(C;HYB);S)', 'Attribute [MDD(HYB(C;HYB);S)], scope [args MDD,'
     ' args HYB]: forbidden atom recursion found [HYB].'),
    ('MDD(HYB(C;LO);S)', 'For attribute [LO] discordant [atom/argument]->'
     '[attribute] associations: [args MDD, args HYB]->[material] vs [LO]->'
     '[llrs]'),
    ('MDD(HYB(C);S)', 'Attribute [MDD(HYB(C);S)]: atom HYB requires at least'
     ' 2 arguments, 1 found [HYB(C)].'),
    ('MDD(HYB(C;S);S)', None, None, '<ATTR id="0xADDR" name="material">\n'
     '    <ATOM id="0xADDR" name="MDD" title="Different materials in the two'
     ' directions">\n        <args>\n            <ATTR id="0xADDR"'
     ' name="material">\n                <ATOM id="0xADDR" name="HYB"'
     ' title="Hybrid or composite (mixed) materials">\n'
     '                    <args>\n                        <ATTR id="0xADDR"'
     ' name="material">\n                            <ATOM id="0xADDR"'
     ' name="C" title="Concrete, unknown reinforcement"/>\n'
     '                        </ATTR>\n'
     '                        <ATTR id="0xADDR" name="material">\n'
     '                            <ATOM id="0xADDR" name="S" title="Steel"/>\n'
     '                        </ATTR>\n'
     '                    </args>\n                </ATOM>\n'
     '            </ATTR>\n            <ATTR id="0xADDR" name="material">\n'
     '                <ATOM id="0xADDR" name="S" title="Steel"/>\n'
     '            </ATTR>\n        </args>\n'
     '    </ATOM>\n</ATTR>\n'),
    ('MDD(HYB(C,S,W);S)', 'Atom arguments must be included in rounded brackets'
     ' and separated by \';\' character. Taxonomy string [MDD(HYB(C,S,W);S)] parsing'
     ' error: Rule \'taxo\' matched in its entirety, but it didn\'t'
     ' consume all the text. The non-matching portion of the text begins with'
     ' \'(HYB(C,S,W);'
     'S)\' (line 1, column 4).'),
    ('MDD(HYB(C;S;W);S)', None, None, '<ATTR id="0xADDR" name="material">\n'
     '    <ATOM id="0xADDR" name="MDD" title="Different materials in the two'
     ' directions">\n        <args>\n            <ATTR id="0xADDR"'
     ' name="material">\n                <ATOM id="0xADDR" name="HYB"'
     ' title="Hybrid or composite (mixed) materials">\n'
     '                    <args>\n                        <ATTR id="0xADDR"'
     ' name="material">\n                            <ATOM id="0xADDR"'
     ' name="C" title="Concrete, unknown reinforcement"/>\n'
     '                        </ATTR>\n'
     '                        <ATTR id="0xADDR" name="material">\n'
     '                            <ATOM id="0xADDR" name="S" title="Steel"/>\n'
     '                        </ATTR>\n'
     '                        <ATTR id="0xADDR" name="material">\n'
     '                            <ATOM id="0xADDR" name="W" title="Wood"/>\n'
     '                        </ATTR>\n'
     '                    </args>\n                </ATOM>\n'
     '            </ATTR>\n            <ATTR id="0xADDR" name="material">\n'
     '                <ATOM id="0xADDR" name="S" title="Steel"/>\n'
     '            </ATTR>\n        </args>\n'
     '    </ATOM>\n</ATTR>\n'),
    ('MDD(HYB(S;W(X;Y)))', 'Attribute [MDD(HYB(S;W(X;Y)))]: atom MDD requires'
     ' at least 2 arguments, 1 found [MDD(HYB(S;W(X;Y)))].'),
    ('MDD(HYB(S;W(X;Y)), S)', 'Atom arguments must be included in rounded '
     'brackets and separated by \';\' character. Taxonomy string [MDD(HYB(S;W(X;Y)),'
     ' S)] parsing error: Rule \'taxo\' matched in its entirety, but it didn\'t'
     ' consume all the text. The non-matching portion of the text begins with'
     ' \'(HYB(S;W(X;Y)), S)\' (line 1, column 4).'),
    ('MDD(HYB(S;W(X;Y));S)', 'Attribute [MDD(HYB(S;W(X;Y));S)]: argument[s]'
     ' not expected for atom [W].'),
    ('MDD(MDD(C;LO);S)', 'Attribute [MDD(MDD(C;LO);S)], scope [args MDD]:'
     ' forbidden atom recursion found [MDD].'),
    ('MDD(W)', 'Attribute [MDD(W)]: atom MDD requires at least 2 arguments,'
     ' 1 found [MDD(W)].'),
    ('MDD(W, Z)', 'Atom arguments must be included in rounded brackets and'
     ' separated by \';\' character. Taxonomy string [MDD(W, Z)] parsing error:'
     ' Rule \'taxo\' matched in its entirety, but it didn\'t consume all the text.'
     ' The non-matching portion of the text begins with \'(W, Z)\' (line 1,'
     ' column 4).'),
    ('MDD(W,Z)', 'Atom arguments must be included in rounded brackets and'
     ' separated by \';\' character. Taxonomy string [MDD(W,Z)] parsing error: Rule'
     ' \'taxo\' matched in its entirety, but it didn\'t consume all the text.'
     ' The non-matching portion of the text begins with \'(W,Z)\' (line 1,'
     ' column 4).'),
    ('MDD(W;Z)', 'Attribute [MDD(W;Z)]: unknown atom [Z].'),

    ('W()', 'Empty rounded brackets are not allowed for atoms with optional'
     ' arguments. Taxonomy string [W()] parsing error: Rule \'taxo\' matched in its'
     ' entirety, but it didn\'t consume all the text. The non-matching portion'
     ' of the text begins with \'()\' (line 1, column 2).'),

    ('RES', None, None, '<ATTR id="0xADDR" name="occupancy">\n'
     '    <ATOM id="0xADDR" name="RES" title="Residential"/>\n</ATTR>\n'),
    ('RES:2', None, None, '<ATTR id="0xADDR" name="occupancy">\n'
     '    <ATOM id="0xADDR" name="RES" title="Residential">\n'
     '        <params>\n            <param subtype="none" title="Multi-unit,'
     ' unknown type" type="option">\n                <value >2</value>\n'
     '            </param>\n        </params>\n    </ATOM>\n</ATTR>\n'),
    ('RES:2:2A', 'Attribute [RES:2:2A]: atom [RES] requires a maximum of 1'
     ' parameter, 2 found [RES:2:2A].'),
    ('RES:2WWWWW', 'Atom [RES:2WWWWW]: parameters option [2WWWWW] not found.'),
    ('W:123', 'Attribute [W:123]: no parameters expected for'
     ' atom [W], found [[\'123\']]'),
    ('H', 'Attribute [H]: atom H requires at least 1 parameter, 0 found [H].'),
    ('H:3', None, None, '<ATTR id="0xADDR" name="height">\n'
     '    <ATOM id="0xADDR" name="H" title="Number of storeys above ground">\n'
     '        <params>\n            <param subtype="exact" type="int"'
     ' unit_meas_plural="storeys" unit_meas_single="storey">\n'
     '                <value>3</value>\n            </param>\n'
     '        </params>\n    </ATOM>\n</ATTR>\n'),
    ('H:3:5', 'Attribute [H:3:5]: atom [H] requires a maximum of 1 parameter,'
     ' 2 found [H:3:5].'),
    ('IRI+IRP(TOR+REC)', 'Attribute [IRI+IRP(TOR+REC)]: composition of atoms'
     ' not allowed [TOR+REC].'),
    ('IRI+IRP(TOR;REC)', None, None, '<ATTR id="0xADDR" name="irregularity">\n'
     '    <ATOM id="0xADDR" name="IRI" title="Irregular structure"/>\n'
     '    <ATOM id="0xADDR" name="IRP" title="Plan irregularities list'
     ' container">\n        <args>\n            <ATOM id="0xADDR" name="TOR"'
     ' title="Torsion eccentricity"/>\n            <ATOM id="0xADDR"'
     ' name="REC" title="Re-entrant corner"/>\n        </args>\n'
     '    </ATOM>\n</ATTR>\n'),
    ('IRI+IRP(TOR;CHV)', 'Attribute [IRI+IRP(TOR;CHV)], atom [CHV], expected'
     ' atomsgroup [plan_irregularity], found atom [CHV] of atomsgroup'
     ' [vertical_irregularity].'),
    ('MIX(RES;MIX(COM;GOV))', 'Attribute [MIX(RES;MIX(COM;GOV))],'
     ' forbidden atom found [MIX].'),
    ('MIX(RES;COM;GOV)', None, None, '<ATTR id="0xADDR" name="occupancy">\n'
     '    <ATOM id="0xADDR" name="MIX" title="Mixed">\n        <args>\n'
     '            <ATOM id="0xADDR" name="RES" title="Residential"/>\n'
     '            <ATOM id="0xADDR" name="COM" title="Commercial and'
     ' public"/>\n            <ATOM id="0xADDR" name="GOV"'
     ' title="Government"/>\n        </args>\n    </ATOM>\n</ATTR>\n'),
    ("LFINF", None, None, '<ATTR id="0xADDR" name="llrs">\n'
     '    <ATOM id="0xADDR" name="LFINF" title="Infilled frame"/>\n</ATTR>\n'),
    ("LFINF(MUR)", None, None, '<ATTR id="0xADDR" name="llrs">\n'
     '    <ATOM id="0xADDR" name="LFINF" title="Infilled frame">\n'
     '        <args>\n            <ATTR id="0xADDR" name="material">\n'
     '                <ATOM id="0xADDR" name="MUR" title="Masonry,'
     ' unreinforced"/>\n            </ATTR>\n        </args>\n'
     '    </ATOM>\n</ATTR>\n'),
    ('LFINF()', 'Empty rounded brackets are not allowed for atoms with optional'
     ' arguments. Taxonomy string [LFINF()] parsing error: Rule \'taxo\' matched'
     ' in its entirety, but it didn\'t consume all the text. The non-matching'
     ' portion of the text begins with \'()\' (line 1, column 6).'),

    ('LFM+DCW:-0.5', 'Atom [DCW:-0.5]: value [-0.5] less then min value'
     ' [0.000000].'),
    ('LFM+DCW:0.5', None, None, '<ATTR id="0xADDR" name="llrs">\n'
     '    <ATOM id="0xADDR" name="LFM" title="Moment frame"/>\n    <ATOM'
     ' id="0xADDR" name="DCW" title="Columns-Wall density">\n'
     '        <params>\n            <param subtype="exact" type="float"'
     ' unit_meas_plural="ratio" unit_meas_single="ratio">\n'
     '                <value>0.5</value>\n            </param>\n'
     '        </params>\n    </ATOM>\n</ATTR>\n'),
    ('LFM+DCW:1.5', 'Atom [DCW:1.5]: value [1.5] greater then max value'
     ' [1.000000].'),
    ('LFM+DCW:1.5.3.2', 'Atom [DCW:1.5.3.2]: value [1.5.3.2] not valid'
     ' float.'),

    ('HBAPP:-1', 'Atom [HBAPP:-1]: value [-1] less then min value'
     ' [0].'),
    ('HBAPP:1', None, None, '<ATTR id="0xADDR" name="height">\n'
     '    <ATOM id="0xADDR" name="HBAPP" title="Approximate number of storeys'
     ' below ground">\n        <params>\n            <param subtype="exact"'
     ' type="int" unit_meas_plural="storeys" unit_meas_single="storey">\n'
     '                <value>1</value>\n            </param>\n'
     '        </params>\n    </ATOM>\n</ATTR>\n'),
    ('HBAPP:1000', None, None, '<ATTR id="0xADDR" name="height">\n'
     '    <ATOM id="0xADDR" name="HBAPP" title="Approximate number of storeys'
     ' below ground">\n        <params>\n            <param subtype="exact"'
     ' type="int" unit_meas_plural="storeys" unit_meas_single="storey">\n'
     '                <value>1000</value>\n            </param>\n'
     '        </params>\n    </ATOM>\n</ATTR>\n'),
    ('HBAPP:11ss22', 'Atom [HBAPP:11ss22]: value 11ss22 not valid int.'),

    # float
    ('HD:0', None, None, '<ATTR id="0xADDR" name="height">\n'
     '    <ATOM id="0xADDR" name="HD" title="Slope of the ground">\n'
     '        <params>\n            <param subtype="exact" type="float"'
     ' unit_meas_plural="degrees" unit_meas_single="degree">\n'
     '                <value>0.0</value>\n            </param>\n'
     '        </params>\n    </ATOM>\n</ATTR>\n'),
    ('HD:0.1', None, None, '<ATTR id="0xADDR" name="height">\n'
     '    <ATOM id="0xADDR" name="HD" title="Slope of the ground">\n'
     '        <params>\n            <param subtype="exact" type="float"'
     ' unit_meas_plural="degrees" unit_meas_single="degree">\n'
     '                <value>0.1</value>\n            </param>\n'
     '        </params>\n    </ATOM>\n</ATTR>\n'),
    ('HD:45.5', None, None, '<ATTR id="0xADDR" name="height">\n'
     '    <ATOM id="0xADDR" name="HD" title="Slope of the ground">\n'
     '        <params>\n            <param subtype="exact" type="float"'
     ' unit_meas_plural="degrees" unit_meas_single="degree">\n'
     '                <value>45.5</value>\n            </param>\n'
     '        </params>\n    </ATOM>\n</ATTR>\n'),
    ('HD:89.9', None, None, '<ATTR id="0xADDR" name="height">\n'
     '    <ATOM id="0xADDR" name="HD" title="Slope of the ground">\n'
     '        <params>\n            <param subtype="exact" type="float"'
     ' unit_meas_plural="degrees" unit_meas_single="degree">\n'
     '                <value>89.9</value>\n            </param>\n'
     '        </params>\n    </ATOM>\n</ATTR>\n'),
    ('HD:90.0', 'Atom [HD:90.0]: value [90.0] greater or equal then max value'
     ' [90.000000].'),

    # rangeable_float
    ('HF:-3', 'Atom [HF:-3]: value [-3] less then min value [0.000000].'),
    ('HF:<-3', 'Atom [HF:<-3]: value [-3] less then min value [0.000000].'),
    ('HF:>-3', 'Atom [HF:>-3]: value [-3] less then min value [0.000000].'),
    ('HF:<3', None, None,
     '<ATTR id="0xADDR" name="height">\n    <ATOM id="0xADDR"'
     ' name="HF" title="Height of ground floor level above'
     ' grade">\n        <params>\n            <param'
     ' subtype="less_than" type="float" unit_meas_plural="meters"'
     ' unit_meas_single="meter">\n                <value>3.0</value>\n'
     '            </param>\n        </params>\n    </ATOM>\n</ATTR>\n'),
    ('HF:>3', None, None,
     '<ATTR id="0xADDR" name="height">\n    <ATOM id="0xADDR"'
     ' name="HF" title="Height of ground floor level above'
     ' grade">\n        <params>\n            <param'
     ' subtype="greater_than" type="float" unit_meas_plural="meters"'
     ' unit_meas_single="meter">\n                <value>3.0</value>\n'
     '            </param>\n        </params>\n    </ATOM>\n</ATTR>\n'),
    ('HF:<0', 'Atom [HF:<0]: incorrect float inequality, no valid values below'
     ' min value [0].'),
    ('HF:0-3', None, None,
     '<ATTR id="0xADDR" name="height">\n    <ATOM id="0xADDR"'
     ' name="HF" title="Height of ground floor level above'
     ' grade">\n        <params>\n            <param subtype="range"'
     ' type="float" unit_meas_plural="meters"'
     ' unit_meas_single="meter">\n                <value>0.0</value>\n'
     '                <value>3.0</value>\n            </param>\n'
     '        </params>\n    </ATOM>\n</ATTR>\n'),
    ('HF:3-6', None, None,
     '<ATTR id="0xADDR" name="height">\n    <ATOM id="0xADDR"'
     ' name="HF" title="Height of ground floor level above'
     ' grade">\n        <params>\n            <param subtype="range"'
     ' type="float" unit_meas_plural="meters"'
     ' unit_meas_single="meter">\n                <value>3.0</value>\n'
     '                <value>6.0</value>\n            </param>\n'
     '        </params>\n    </ATOM>\n</ATTR>\n'),
    ('HF:3-0', 'Atom [HF:3-0]: incorrect floats range: first endpoint'
     ' is greater then or equal to the second [3-0]'),

    # rangeable_int
    ('H:-3', 'Atom [H:-3]: value [-3] less then min value [0].'),
    ('H:<-3', 'Atom [H:<-3]: value [-3] less then min value [0].'),
    ('H:>-3', 'Atom [H:>-3]: value [-3] less then min value [0].'),
    ('H:<3', None, None,
     '<ATTR id="0xADDR" name="height">\n    <ATOM id="0xADDR"'
     ' name="H" title="Number of storeys above ground">\n'
     '        <params>\n            <param subtype="less_than"'
     ' type="int" unit_meas_plural="storeys"'
     ' unit_meas_single="storey">\n                <value>3</value>\n'
     '            </param>\n        </params>\n    </ATOM>\n</ATTR>\n'),
    ('H:>3', None, None,
     '<ATTR id="0xADDR" name="height">\n    <ATOM id="0xADDR"'
     ' name="H" title="Number of storeys above ground">\n'
     '        <params>\n            <param subtype="greater_than"'
     ' type="int" unit_meas_plural="storeys"'
     ' unit_meas_single="storey">\n                <value>3</value>\n'
     '            </param>\n        </params>\n    </ATOM>\n</ATTR>\n'),
    ('H:0-3', None, None,
     '<ATTR id="0xADDR" name="height">\n    <ATOM id="0xADDR"'
     ' name="H" title="Number of storeys above ground">\n'
     '        <params>\n            <param subtype="range" type="int"'
     ' unit_meas_plural="storeys" unit_meas_single="storey">\n'
     '                <value>0</value>\n '
     '               <value>3</value>\n            </param>\n'
     '        </params>\n    </ATOM>\n</ATTR>\n'),
    ('H:3-6', None, None,
     '<ATTR id="0xADDR" name="height">\n    <ATOM id="0xADDR"'
     ' name="H" title="Number of storeys above ground">\n'
     '        <params>\n            <param subtype="range" type="int"'
     ' unit_meas_plural="storeys" unit_meas_single="storey">\n'
     '                <value>3</value>\n '
     '               <value>6</value>\n            </param>\n'
     '        </params>\n    </ATOM>\n</ATTR>\n'),
    ('H:3-0', 'Atom [H:3-0]: incorrect integers range: first endpoint'
     ' is greater then or equal to the second [3-0]'),

    # check missing atom dependency
    ('HBAPP:1+HD:0', None, None,
     '<ATTR id="0xADDR" name="height">\n    <ATOM id="0xADDR"'
     ' name="HBAPP" title="Approximate number of storeys below'
     ' ground">\n        <params>\n            <param subtype="exact"'
     ' type="int" unit_meas_plural="storeys"'
     ' unit_meas_single="storey">\n                <value>1</value>\n'
     '            </param>\n        </params>\n    </ATOM>\n    <ATOM'
     ' id="0xADDR" name="HD" title="Slope of the ground">\n'
     '        <params>\n            <param subtype="exact"'
     ' type="float" unit_meas_plural="degrees"'
     ' unit_meas_single="degree">\n                <value>0.0</value>\n'
     '            </param>\n        </params>\n    </ATOM>\n</ATTR>\n'),
    ('S+CIP', 'Attribute [S+CIP]: missing dependency for atom [CIP]'),
    ('M+STRUB+SPSA', None, None,
     '<ATTR id="0xADDR" name="material">\n    <ATOM id="0xADDR"'
     ' name="M" title="Masonry, unknown reinforcement"/>\n    <ATOM'
     ' id="0xADDR" name="STRUB" title="Rubble (field stone) or'
     ' semi-dressed stone"/>\n    <ATOM id="0xADDR" name="SPSA"'
     ' title="Sandstone"/>\n</ATTR>\n'),
    ('M+SPSA', 'Attribute [M+SPSA]: missing dependency for atom [SPSA]'),
    ('HYB(S;M+SPSA)', 'Attribute [HYB(S;M+SPSA)]: missing dependency'
     ' for atom [SPSA]'),
    ('HYB(S;M+STRUB+SPSA)', None, None,
     '<ATTR id="0xADDR" name="material">\n    <ATOM id="0xADDR"'
     ' name="HYB" title="Hybrid or composite (mixed) materials">\n'
     '        <args>\n            <ATTR id="0xADDR"'
     ' name="material">\n                <ATOM id="0xADDR" name="S"'
     ' title="Steel"/>\n            </ATTR>\n            <ATTR'
     ' id="0xADDR" name="material">\n                <ATOM'
     ' id="0xADDR" name="M" title="Masonry, unknown'
     ' reinforcement"/>\n                <ATOM id="0xADDR"'
     ' name="STRUB" title="Rubble (field stone) or semi-dressed'
     ' stone"/>\n                <ATOM id="0xADDR" name="SPSA"'
     ' title="Sandstone"/>\n            </ATTR>\n        </args>\n'
     '    </ATOM>\n</ATTR>\n'),

    ('DCW:0.4+LFM/MDD(SL+S;HYB(ADO+M;WHE+W))', None,
     'MDD(S+SL;HYB(M+ADO;W+WHE))/LFM+DCW:0.4',
     '<ATTR id="0xADDR" name="material">\n    <ATOM id="0xADDR"'
     ' name="MDD" title="Different materials in the two'
     ' directions">\n        <args>\n            <ATTR id="0xADDR"'
     ' name="material">\n                <ATOM id="0xADDR" name="S"'
     ' title="Steel"/>\n                <ATOM id="0xADDR" name="SL"'
     ' title="Cold-formed steel members"/>\n            </ATTR>\n'
     '            <ATTR id="0xADDR" name="material">\n'
     '                <ATOM id="0xADDR" name="HYB" title="Hybrid or'
     ' composite (mixed) materials">\n                    <args>\n'
     '                        <ATTR id="0xADDR" name="material">\n'
     '                            <ATOM id="0xADDR" name="M"'
     ' title="Masonry, unknown reinforcement"/>\n'
     '                            <ATOM id="0xADDR" name="ADO"'
     ' title="Adobe blocks"/>\n                        </ATTR>\n'
     '                        <ATTR id="0xADDR" name="material">\n'
     '                            <ATOM id="0xADDR" name="W"'
     ' title="Wood"/>\n                            <ATOM id="0xADDR"'
     ' name="WHE" title="Heavy wood"/>\n'
     '                        </ATTR>\n                    </args>\n'
     '                </ATOM>\n            </ATTR>\n        </args>\n'
     '    </ATOM>\n</ATTR>\n<ATTR id="0xADDR" name="llrs">\n    <ATOM'
     ' id="0xADDR" name="LFM" title="Moment frame"/>\n    <ATOM'
     ' id="0xADDR" name="DCW" title="Columns-Wall density">\n'
     '        <params>\n            <param subtype="exact"'
     ' type="float" unit_meas_plural="ratio"'
     ' unit_meas_single="ratio">\n                <value>0.4</value>\n'
     '            </param>\n        </params>\n'
     '    </ATOM>\n</ATTR>\n'),
    ('MDD(S+SL;HYB(M+ADO;W+WHE))/LFM+DCW:0.4', None, None,
     '<ATTR id="0xADDR" name="material">\n    <ATOM id="0xADDR"'
     ' name="MDD" title="Different materials in the two'
     ' directions">\n        <args>\n            <ATTR id="0xADDR"'
     ' name="material">\n                <ATOM id="0xADDR" name="S"'
     ' title="Steel"/>\n                <ATOM id="0xADDR" name="SL"'
     ' title="Cold-formed steel members"/>\n            </ATTR>\n'
     '            <ATTR id="0xADDR" name="material">\n'
     '                <ATOM id="0xADDR" name="HYB" title="Hybrid or'
     ' composite (mixed) materials">\n                    <args>\n'
     '                        <ATTR id="0xADDR" name="material">\n'
     '                            <ATOM id="0xADDR" name="M"'
     ' title="Masonry, unknown reinforcement"/>\n'
     '                            <ATOM id="0xADDR" name="ADO"'
     ' title="Adobe blocks"/>\n                        </ATTR>\n'
     '                        <ATTR id="0xADDR" name="material">\n'
     '                            <ATOM id="0xADDR" name="W"'
     ' title="Wood"/>\n                            <ATOM id="0xADDR"'
     ' name="WHE" title="Heavy wood"/>\n'
     '                        </ATTR>\n                    </args>\n'
     '                </ATOM>\n            </ATTR>\n        </args>\n'
     '    </ATOM>\n</ATTR>\n<ATTR id="0xADDR" name="llrs">\n    <ATOM'
     ' id="0xADDR" name="LFM" title="Moment frame"/>\n    <ATOM'
     ' id="0xADDR" name="DCW" title="Columns-Wall density">\n'
     '        <params>\n            <param subtype="exact"'
     ' type="float" unit_meas_plural="ratio"'
     ' unit_meas_single="ratio">\n                <value>0.4</value>\n'
     '            </param>\n        </params>\n'
     '    </ATOM>\n</ATTR>\n'),

    ('LDD(DCW:0.4+LFM;DCW:0.8+LFM)', None, 'LDD(LFM+DCW:0.4;LFM+DCW:0.8)',
     '<ATTR id="0xADDR" name="llrs">\n    <ATOM id="0xADDR"'
     ' name="LDD" title="Different types of llrs in the two'
     ' directions">\n        <args>\n            <ATTR id="0xADDR"'
     ' name="llrs">\n                <ATOM id="0xADDR" name="LFM"'
     ' title="Moment frame"/>\n                <ATOM id="0xADDR"'
     ' name="DCW" title="Columns-Wall density">\n'
     '                    <params>\n                        <param'
     ' subtype="exact" type="float" unit_meas_plural="ratio"'
     ' unit_meas_single="ratio">\n '
     '                           <value>0.4</value>\n '
     '                       </param>\n                    </params>\n'
     '                </ATOM>\n            </ATTR>\n            <ATTR'
     ' id="0xADDR" name="llrs">\n                <ATOM id="0xADDR"'
     ' name="LFM" title="Moment frame"/>\n                <ATOM'
     ' id="0xADDR" name="DCW" title="Columns-Wall density">\n'
     '                    <params>\n                        <param'
     ' subtype="exact" type="float" unit_meas_plural="ratio"'
     ' unit_meas_single="ratio">\n '
     '                           <value>0.8</value>\n '
     '                       </param>\n                    </params>\n'
     '                </ATOM>\n            </ATTR>\n        </args>\n'
     '    </ATOM>\n</ATTR>\n'),
    ('LDD(DCW:0.4+LFM;LFM+DCW:0.4)', 'Attribute [LDD(DCW:0.4+LFM;LFM+'
     'DCW:0.4)]: for atom [LDD(DCW:0.4+LFM;LFM+DCW:0.4)] identical'
     ' arguments are denied [LFM+DCW:0.4].', '')
     ]


def to_log(s_exp):
    return ((s_exp[0], s_exp[1])
            if s_exp[1] is not None else (s_exp[0], 'Success'))


class InfoTestCase(unittest.TestCase):
    def test(self):
        self.maxDiff = None
        GemTaxonomy.info()
        GemTaxonomy.info(fmt='dict')
        GemTaxonomy.info(fmt='json')


class ValidateTestCase(unittest.TestCase):
    def test(self):
        self.maxDiff = None
        only_success = (os.getenv('ONLY_SUCCESS', 'False') == 'True')
        gt = GemTaxonomy()
        for tax_in in taxonomy_strings:
            tax = [None] * 6
            for idx, tax_val in enumerate(tax_in):
                tax[idx] = tax_val
            if only_success and tax[1] is not None:
                continue

            if tax[1] is not None and tax[2] is None:
                print('Test: "%s", expected: "%s"' %
                      to_log(tax))
            elif tax[1] is not None and tax[2] is not None:
                print('Test: "%s", expected: "%s", '
                      'suggested canonical: "%s"' %
                      (to_log(tax) + (tax[2],)))

            try:
                _, _, output = gt.validate(tax[0])
                self.assertEqual(
                    tax[1], None,
                    msg='Expected "%s" but not detected' %
                    (tax[1],))
                if output['is_canonical'] is False:
                    self.assertEqual(
                        output['canonical'], tax[2],
                        msg=('Expected canonical as '
                             '"%s" retrieved "%s"' %
                             (output['canonical'], tax[2])))
            except ValueError as exc:
                self.assertEqual(
                    str(exc), tax[1],
                    msg='Expected "%s" Found "%s"' %
                    (tax[1], str(exc)))


class ValidateSuccessOnlyTestCase(ValidateTestCase):
    @classmethod
    def setup_class(cls):
        os.environ['ONLY_SUCCESS'] = 'True'

    @classmethod
    def teardown_class(cls):
        del os.environ['ONLY_SUCCESS']

    def test(self):
        super().test()


class ReprTestCase(unittest.TestCase):
    # Use code like this to generate comparison strings
    # cat > temp.log ;  cut -c 19- < temp.log | sed 's/$/\\n/g' | \
    #     tr -d '\n' ; echo
    def test(self):
        self.maxDiff = None
        gt = GemTaxonomy()
        for tax in taxonomy_strings:
            if tax[1] is not None:
                continue

            _, l_attrs_canon, output = gt.validate(tax[0])
            repr = gt.logic_print(l_attrs_canon)
            repr = re.sub('0x[0-9a-f]+', '0xADDR', repr)
            # print('trepr: [%s]' % repr)
            self.assertEqual(repr, tax[3])


class ExplainTestCase(unittest.TestCase):
    # Use code like this to generate comparison strings
    # cat > temp.log ;  cut -c 19- < temp.log | sed 's/$/\\n/g' | \
    #     tr -d '\n' ; echo
    def test(self):
        self.maxDiff = None
        gt = GemTaxonomy()
        for tax in taxonomy_strings:
            if tax[1] is not None:
                continue
            # print('tzero: [%s]' % tax[0])

            gt.explain(tax[0])
            gt.explain(tax[0], fmt='textsingleline')
            gt.explain(tax[0], fmt='textmultiline')
            gt.explain(tax[0], fmt='json')
