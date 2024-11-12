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
from openquake.gem_taxonomy_data import GemTaxonomyData
from openquake.gem_taxonomy_data import __version__ as GTD_vers
from .version import __version__


class GemTaxonomy:
    # method to test package infrastructure
    @staticmethod
    def info():
        taxonomy_version = '3.3'
        print('''
GemTaxonomy Info
----------------
''')
        print('  GemTaxonomy package     - v. %s' % __version__)
        print('  GemTaxonomyData package - v. %s' % GTD_vers)
        gtd = GemTaxonomyData()
        tax = gtd.load(taxonomy_version)
        print('  Loaded Taxonomy Data    - v. %s' % taxonomy_version)
        print('  Atoms number            -    %d' % len(tax['Atom']))
