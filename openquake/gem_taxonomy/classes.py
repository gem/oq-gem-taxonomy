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
import re
import json

#
# Refact atom name + if there are args + if there are params with single
# grammar parse
#

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
#   DONE - if not arguments check syntax
#   - parameters check if present (include scope inheritance and visualizz.)
#   DONE - if not parameters check syntax
#


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
                atom = ~r"[A-Z][A-Z0-9]*" atom_args* atom_params*
                atom_args = "(" attr ( ";" attr )* ")"
                atom_params = ":" ~r"[A-Z0-9<>][A-Z0-9-]*"
                """)

        self.gtd = GemTaxonomyData()
        self.tax = self.gtd.load(vers)
        # new_dict = {}
        # for k in ['Attribute', 'AtomsGroup', 'Atom']:
        #     if 'name' in self.tax[k][0]:
        #         new_dict[k + 'Dict'] = {x['name']: x for x in self.tax[k]}
        # self.tax.update(new_dict)

    def extract_atoms(self, tree_attr):
        tree_atoms = []

        if tree_attr.expr.name == 'attr':
            if len(tree_attr.children) != 2:
                raise ValueError('Taxonomy: malformed attribute')
            for child in tree_attr.children:
                if child.expr.name == 'atom':
                    tree_atoms.append(child)
                else:
                    for gr_child in child.children:
                        for ggr_child in gr_child.children:
                            if ggr_child.expr.name == 'atom':
                                tree_atoms.append(ggr_child)
        return tree_atoms

    def args__filtered_attribute(self, attribute_name, filtered_atoms):
        return {'args_type': 'filtered_attribute',
                'attribute_name': attribute_name,
                'filtered_atoms': filtered_atoms}

    def args__filtered_atomsgroup(self, atomsgroup_name, filtered_atoms):
        return {'args_type': 'filtered_atomsgroup',
                'atomsgroup_name': atomsgroup_name,
                'filtered_atoms': filtered_atoms}

    def validate_arguments(self, attr_base, atom_anc, tax_args, tree_args,
                           atom_args_orig_in, filtered_atoms):
        """
        attr_base: attribute base
        atom_anc: atom string included args and params
        tax_args: 'args' field of gem_tax['Atom'] element
        tree_args: list of tree arguments
        atom_args_orig_in: flattened hierarchy of current args
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
            for tree_arg in tree_args:
                self.validate_attribute(
                    attr_base, tree_arg,
                    atom_args_orig_in,
                    args_info['attribute_name'],
                    list(set(filtered_atoms).union(
                        set(args_info['filtered_atoms']))))
        elif arg_type_name == 'filtered_atomsgroup':
            # args_info['atomsgroup_name']
            # args_info['filtered_atoms']
            for tree_arg in tree_args:
                if tree_arg.children[0].text not in self.tax['AtomDict']:
                    raise ValueError(
                        'Attribute [%s]: unknown atom [%s].' % (
                            attr_base, tree_arg.text))
                atom_name = tree_arg.children[0].text
                tax_atom = self.tax['AtomDict'][atom_name]

                # check if current atom group is what expected for these args
                if tax_atom['group'] != args_info['atomsgroup_name']:
                    raise ValueError(
                        'Attribute [%s], atom [%s], expected atomsgroup [%s],'
                        ' found atom [%s] of atomsgroup [%s].' % (
                            attr_base, tree_arg.text,
                            args_info['atomsgroup_name'],
                            atom_name, tax_atom['group']))

    def validate_parameters(self, attr_base, atom_anc, tax_params, atom_params,
                            atom_params_orig_in):
        """
        atom_anc: atom string included args and params
        tax_args: 'args' field of gem_tax['Atom'] element
        atom_args: list of arguments
        """
        param_type_name = tax_params['type'].split('(')[0]
        atom_name = re.findall(r"[A-Za-z][A-Za-z0-9]*", atom_anc)[0]
        if param_type_name == 'options':
            if atom_name not in self.tax['Param']:
                raise ValueError(
                    'Atom [%s]: parameters options not found.' %
                    (atom_anc,))
            atom_options = self.tax['Param'][atom_name]

            for atom_param in atom_params:
                if (len(list(filter(
                        lambda option: option['name'] == atom_param,
                        atom_options))) < 1):
                    raise ValueError(
                        'Atom [%s]: parameters option [%s] not found.' %
                        (atom_anc, atom_param))

        # if (arg_type_name == 'filtered_attribute'
        #         or arg_type_name == 'filtered_atomsgroup'):
        #     args_info = eval('self.args__' + tax_args['type'])
        # else:
        #     raise ValueError(
        #         'Atom [%s]: unknown arguments type [%s].' %
        #         (atom_anc, tax_args['type']))

        # if arg_type_name == 'filtered_attribute':
        #     for attr_str in atom_args:
        #         self.validate_attribute(
        #             attr_base, attr_str,
        #             atom_args_orig_in,
        #             args_info['attribute_name'],
        #             list(set(filtered_atoms).union(
        #                 set(args_info['filtered_atoms']))))

    def validate_attribute(self, attr_base, tree_attr, attr_scope,
                           attr_name, filtered_atoms):
        """
        attr_base:      full attribute (recursion invariant)
        tree_attr:      current evaluated attribute tree
        attr_scope:     linearized description of current atom scope
                        (e.g. if already argument...)
        attr_name:      already specified when call as arguments check
        filtered_atoms: list of prohibited atoms (from arguments check)
        """
        attr = tree_attr.text
        tree_atoms = self.extract_atoms(tree_attr)
        atom_names_in = []
        atoms_in = {}

        for tree_atom in tree_atoms:
            atom = tree_atom.text
            if len(tree_atom.children) != 3:
                raise ValueError(
                    'Attribute [%s], scope [%s]: malformed atom [%s]' % (
                        attr_base, attr_scope, atom))

            atom_name = tree_atom.children[0].text
            tree_args = []
            atom_tree_args = tree_atom.children[1]
            nchs_args = len(atom_tree_args.children)
            if nchs_args > 0:
                atom_tree_args = atom_tree_args.children[0]
                nchs_args = len(atom_tree_args.children)

                if nchs_args > 2:
                    if atom_tree_args.children[0].text == '(':
                        if atom_tree_args.children[nchs_args - 1].text == ')':
                            tree_args.append(
                                atom_tree_args.children[1])
                            if nchs_args > 3:
                                other_args = (atom_tree_args.children[2]
                                              .children)
                                for arg_id in range(0, len(other_args)):
                                    tree_args.append(
                                        other_args[arg_id].children[1])

            # IN tree_args the trees for arguments
            params = []
            for param_child in tree_atom.children[2].children:
                if param_child.expr.name != 'atom_params':
                    raise ValueError(
                        'Attribute [%s], scope [%s]: for atom [%s]'
                        ' malformed parameters' % (
                            attr_base, attr_scope, atom))
                params.append(param_child.children[1].text)

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

            # search atom in the known list
            if atom_name not in self.tax['AtomDict']:
                raise ValueError(
                    'Attribute [%s]: unknown atom [%s].' %
                    (attr_base, atom_name))
            tax_atom = self.tax['AtomDict'][atom_name]

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
                len_tree_args = len(tree_args)
                # if args is defined check if are optional and
                # in the case present
                if ('args_min' in tax_args and
                        len_tree_args < tax_args['args_min']):
                        raise ValueError(
                            'Attribute [%s]: atom %s requires at least'
                            ' %d argument%s, %d found [%s].' %
                            (attr_base, atom_name, tax_args['args_min'],
                             's' if tax_args['args_min'] > 1 else '',
                             len_tree_args, atom))

                if ('args_max' in tax_args and
                        len_tree_args > tax_args['args_max']):
                    raise ValueError(
                        'Attribute [%s]: atom [%s] requires a maximum'
                        ' of %d argument%s, %d found [%s].' %
                        (attr_base, atom_name, tax_args['args_max'],
                         's' if tax_args['args_max'] > 1 else '',
                         len_tree_args, atom))
                self.validate_arguments(
                    attr_base,
                    atom, tax_args, tree_args,
                    args_attr_scope, filtered_atoms)
            else:
                # if not args check if arguments are present
                if len(tree_args) > 0:
                    raise ValueError(
                        'Attribute [%s]: argument[s] not expected'
                        ' for atom [%s].' % (attr_base, atom_name))

            if tax_atom['params']:
                len_params = len(params)
                tax_params = json.loads(tax_atom['params'])
                params_min = (tax_params['params_min'] if
                              'params_min' in tax_params else 1)

                if len_params < params_min:
                    raise ValueError(
                        'Attribute [%s]: atom %s requires at least'
                        ' %d parameter%s, %d found [%s].' %
                        (attr_base, atom_name, params_min,
                         's' if params_min > 1 else '',
                         len_params, atom))
                if ('params_max' in tax_params and
                        len_params > tax_params['params_max']):
                    raise ValueError(
                        'Attribute [%s]: atom [%s] requires a maximum'
                        ' of %d parameter%s, %d found [%s].' %
                        (attr_base, atom_name, tax_params['params_max'],
                         's' if tax_params['params_max'] > 1 else '',
                         len_params, atom))

                self.validate_parameters(
                    attr_base,
                    atom, tax_params, params,
                    attr_scope)
            else:
                if len(params) > 0:
                    raise ValueError(
                        'Attribute [%s]: no parameters expected'
                        ' for atom [%s], found (%s)' %
                        (attr_base, atom_name, params))

        # FIXME return properly values
        return 1, 2

    def validate(self, tax_str):
        attr_name_in = []
        attr_in = {}

        attrs = tax_str.split('/')
        for attr in attrs:
            tree_attr = self.attr_grammar.parse(attr)

            attr_name, attr_out = self.validate_attribute(
                attr, tree_attr, '', '', [])

            if attr_name in attr_in:
                raise ValueError(
                    'Attribute [%s] multiple declaration,'
                    ' previous: [%s], current [%s]' %
                    (attr_name, attr_in[attr_name],
                     attr))
            attr_name_in.append(attr_name)
            attr_in[attr_name] = attr
