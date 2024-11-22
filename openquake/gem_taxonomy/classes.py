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
from parsimonious.grammar import Grammar
from openquake.gem_taxonomy_data import GemTaxonomyData
from openquake.gem_taxonomy_data import __version__ as GTD_vers
from .version import __version__
import json

# * Taxonomy scope
#   DONE - check attr dup
#   - attributes order
#
# * Attribute scope
#   DONE - check atom dup
#   DONE - check mutex atoms for the same group
#   - atoms order
#
# * Atom scope
#   DONE - arguments check if present
#   DONE  . are optional? if not check '(' character
#   - if not arguments check syntax
#   - parameters check if present
#   - if not parameters check syntax
#


def _find_node(node, name):
    if node.expr.name == name:
        return node
    for item in node.children:
        ret = _find_node(item, name)
        if ret:
            return ret
    return None


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

    def __init__(self, vers='3.3'):
        if vers == '3.3':
            self.attr_grammar = Grammar(r"""
                attr = atom ( "+" atom )*
                atom = ~r"[A-Z][A-Z0-9]*" atom_args* atom_pars*
                atom_args = "(" attr ( ";" attr )* ")"
                atom_pars = ":" ~r"[A-Z0-9<>][A-Z0-9-]*"
                """)

        self.gtd = GemTaxonomyData()
        self.tax = self.gtd.load(vers)
        # new_dict = {}
        # for k in ['Attribute', 'AtomsGroup', 'Atom']:
        #     if 'name' in self.tax[k][0]:
        #         new_dict[k + 'Dict'] = {x['name']: x for x in self.tax[k]}
        # self.tax.update(new_dict)

    def extract_atoms(self, attribute):
        atoms = []
        tree = self.attr_grammar.parse(attribute)

        if tree.expr.name == 'attr':
            if len(tree.children) != 2:
                raise ValueError('Taxonomy: malformed attribute')
            for child in tree.children:
                if child.expr.name == 'atom':
                    atoms.append(child.text)
                else:
                    for gr_child in child.children:
                        for ggr_child in gr_child.children:
                            if ggr_child.expr.name == 'atom':
                                atoms.append(ggr_child.text)
        return atoms

    def extract_arguments(self, atom):
        atom_args = []
        tree = self.attr_grammar.parse(atom)

        if tree.expr.name != 'attr':
            raise ValueError('Syntax error for atom'
                             ' list arguments [%s].' %
                             atom)

        # find the args_tree element
        args_tree = _find_node(tree, 'atom_args')

        stp = 0
        for child in args_tree.children:
            if stp == 0:  # check for open round bracket
                if child.expr.as_rule() == "'('":
                    stp = 1
            elif stp == 1:  # get first arg
                if child.expr.name == 'attr':
                    atom_args.append(child.text)
                    stp = 2
            elif stp == 2:  # get other args (zero or more)
                if child.expr.as_rule() == "(';' attr)*":
                    if len(child.children) > 0:
                        for gchild in child.children:
                            if gchild.expr.as_rule() != "';' attr":
                                raise ValueError(
                                    'Syntax error after first atom'
                                    ' list argument [%s].' %
                                    atom)
                            ggchild = gchild.children[1]
                            atom_args.append(ggchild.text)
                elif child.expr.as_rule() == "')'":
                    # properly closure of arguments list, return it.
                    return atom_args
                else:
                    raise ValueError(
                        'Syntax error for atom arguments'
                        ' list [%s].' % atom)
        raise ValueError(
            'Unexpected syntax argument after the first [%s].' % atom)

    def args__filtered_attribute(self, attribute_name, filtered_atoms):
        return {'args_type': 'filtered_attribute',
                'attribute_name': attribute_name,
                'filtered_atoms': filtered_atoms}

    def args__filtered_atomsgroup(self, atomsgroup_name, filtered_atoms):
        return {'args_type': 'filtered_atomsgroup',
                'atomsgroup_name': atomsgroup_name,
                'filtered_atoms': filtered_atoms}

    def validate_arguments(self, attr_base, atom_anc, tax_args, atom_args,
                           atom_args_orig_in, filtered_atoms):
        """
        atom_anc: atom string included args and params
        tax_args: 'args' field of gem_tax['Atom'] element
        atom_args: list of arguments
        filtered_atoms: optional list of atoms not allowed as arguments
        """
        arg_type_name = tax_args['type'].split('(')[0]

        if (arg_type_name == 'filtered_attribute'
                or arg_type_name == 'filtered_atomsgroup'):
            args_info = eval('self.args__' + tax_args['type'])
        else:
            raise ValueError(
                'Atom [%s]: unknown arguments type [%s].' %
                (atom_anc, tax_args['type']))

        if arg_type_name == 'filtered_attribute':
            for attr_str in atom_args:
                self.validate_attribute(
                    attr_base, attr_str,
                    atom_args_orig_in,
                    args_info['attribute_name'],
                    list(set(filtered_atoms).union(
                        set(args_info['filtered_atoms']))))

    def validate_attribute(self, attr_base, attr, attr_scope,
                           attr_name, filtered_atoms):
        """
        attr_base:      full attribute (recursion invariant)
        attr:           current evaluated attribute
        attr_scope:     linearized description of current atom scope
                        (e.g. if already argument...)
        attr_name:      already specified when call as arguments check
        filtered_atoms: list of prohibited atoms (from arguments check)
        """
        atoms = self.extract_atoms(attr)
        atom_names_in = []
        atoms_in = {}

        for atom in atoms:
            print("Atom:      %s" % atom)
            atom_name = atom.split('(')[0].split(':')[0]

            if atom_name in filtered_atoms:
                raise ValueError(
                    'Attribute [%s], scope [%s]: forbidden'
                    ' atom recusion found [%s].' % (
                        attr_base, attr_scope, atom_name))

            args_attr_scope = (attr_scope + ', ' + 'args ' + atom_name)

            # check multiple atom occurrencies
            if atom_name in atom_names_in:
                raise ValueError(
                    'Attribute [%s]: multiple occurrencies of [%s] atom.' %
                    (attr, atom_name))

            tax_atom = next(el for el in self.tax['Atom']
                            if el['name'] == atom_name)

            # check mutex atoms for the same group
            atoms_group_name = {k: v for k, v in atoms_in.items() if
                                v['group'] == tax_atom['group']}
            if atoms_group_name:
                raise ValueError(
                    'Attribute [%s]: atoms group "%s"'
                    ' already present with member [%s],'
                    ' new atom [%s] not allowed.' %
                    (attr, self.tax['AtomsGroupDict'][
                        tax_atom['group']]['desc'],
                     [x for x in atoms_group_name][0],
                     atom_name))

            atom_names_in.append(atom_name)
            atoms_in[atom_name] = tax_atom

            if attr_name == '':
                # if atom_name in self.tax['AtomsDeps'].keys():
                #     print('Not independent atom [%s], at'
                #           ' least unsorted attribute atoms.' % atom_name)
                attr_name = tax_atom['attr']
                attr_scope = tax_atom['name']
                args_attr_scope = 'args ' + atom_name
            else:
                if attr_name != tax_atom['attr']:
                    raise ValueError(
                        'For attribute [%s] discordant [atom/argument]->'
                        '[attribute] associations:'
                        ' [%s]->[%s] vs [%s]->[%s]' %
                        (attr, attr_scope, attr_name,
                         tax_atom['name'], tax_atom['attr']))
            if tax_atom['args']:
                tax_args = json.loads(tax_atom['args'])
                # if args is defined check if are optional and
                # in the case present
                if (tax_args['args_min'] > 0 or
                        len(atom.split('(')) > 1):
                    # get arguments if declared
                    atom_args = self.extract_arguments(atom)

                    # check number of arguments
                    len_atom_args = len(atom_args)
                    if ('args_min' in tax_args and
                            len_atom_args < tax_args['args_min']):
                        raise ValueError(
                            'Attribute [%s]: atom %s requires at least'
                            ' %d argument%s, %d found [%s].' %
                            (attr_base, atom_name, tax_args['args_min'],
                             's' if tax_args['args_min'] > 1 else '',
                             len_atom_args, atom))

                    if ('args_max' in tax_args and
                            len_atom_args > tax_args['args_max']):
                        raise ValueError(
                            'Attribute [%s]: atom [%s] requires a maximum'
                            ' of %d argument%s, %d found [%s].' %
                            (attr_base, atom_name, tax_args['args_max'],
                             's' if tax_args['args_max'] > 1 else '',
                             len_atom_args, atom))
                    self.validate_arguments(
                        attr_base,
                        atom, tax_args, atom_args,
                        args_attr_scope, filtered_atoms)
            else:
                # if not check if arguments are present
                pass

            if tax_atom['params']:
                # manage params if declared
                pass
            else:
                # if not check if parameters are present
                pass

            # import pdb ; pdb.set_trace()
            # print(atom_el)
        # FIXME return properly values
        return 1, 2

    def validate(self, tax_str):
        attr_name_in = []
        attr_in = {}

        attrs = tax_str.split('/')
        for attr in attrs:
            attr_name, attr_out = self.validate_attribute(
                attr, attr, '', '', [])

            if attr_name in attr_in:
                raise ValueError(
                    'Attribute [%s] multiple declaration,'
                    ' previous: [%s], current [%s]' %
                    (attr_name, attr_in[attr_name],
                     attr))
            attr_name_in.append(attr_name)
            attr_in[attr_name] = attr
