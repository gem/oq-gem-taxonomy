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
from parsimonious.exceptions import ParseError as ParsimParseError
from parsimonious.exceptions import (IncompleteParseError as
                                     ParsimIncompleteParseError)
from openquake.gem_taxonomy_data import GemTaxonomyData
from openquake.gem_taxonomy_data import __version__ as GTD_vers
from .version import __version__
import json
import re

#
# Refact atom name + if there are args + if there are params with single
# grammar parse
#

# * Taxonomy scope
#   DONE - check attr dup
#   - attributes order
#   - difference between arguments
#
# * Attribute scope
#   DONE - check atom dup
#   DONE - check mutex atoms for the same group
#   - atoms order
#
# * Atom scope
#   - missing atom dependencies
#   - difference between arguments
#   DONE - arguments check if present
#   DONE - arguments as filtered_attributes
#   DONE - arguments as filtered_parameters
#   DONE  . are optional? if not check '(' character
#   DONE - if not arguments check syntax
#   - parameters check if present (include scope inheritance and visualizz.)
#   - parameters range validation (a < b)
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
                atom_params = ":" ~r"[A-Za-z0-9<>-][A-Za-z0-9.+-]*"
                """)

            # flo = ~r"[0-9]+"
            self.rangefloat_grammar = Grammar(r"""
                range = flo "-" flo
                flo = ~r"[0-9-]?" ~r"[0-9.]*" ( ~r"e[+-]?[0-9]+" )?
                """)
            self.rangeint_grammar = Grammar(r"""
                range = inte "-" inte
                inte = ~r"[0-9-]" ~r"[0-9]*"
                """)

        self.gtd = GemTaxonomyData()
        self.tax = self.gtd.load(vers)
        # new_dict = {}
        # for k in ['Attribute', 'AtomsGroup', 'Atom']:
        #     if 'name' in self.tax[k][0]:
        #         new_dict[k + 'Dict'] = {x['name']: x for x in self.tax[k]}
        # self.tax.update(new_dict)

    def extract_atoms(self, attr_tree):
        atoms_trees = []

        if attr_tree.expr.name == 'attr':
            if len(attr_tree.children) != 2:
                raise ValueError('Taxonomy: malformed attribute')
            for child in attr_tree.children:
                if child.expr.name == 'atom':
                    atoms_trees.append(child)
                else:
                    for gr_child in child.children:
                        for ggr_child in gr_child.children:
                            if ggr_child.expr.name == 'atom':
                                atoms_trees.append(ggr_child)
        return atoms_trees

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
        atom_args_orig_in: flattened hierarchy of current atom
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
                atom_name = tree_arg.children[0].children[0].text
                if atom_name not in self.tax['AtomDict']:
                    raise ValueError(
                        'Attribute [%s]: unknown atom [%s].' % (
                            attr_base, tree_arg.text))
                tax_atom = self.tax['AtomDict'][atom_name]

                # check if current atom group is what expected for these args
                if tax_atom['group'] != args_info['atomsgroup_name']:
                    raise ValueError(
                        'Attribute [%s], atom [%s], expected atomsgroup [%s],'
                        ' found atom [%s] of atomsgroup [%s].' % (
                            attr_base, tree_arg.text,
                            args_info['atomsgroup_name'],
                            atom_name, tax_atom['group']))
                if atom_name in args_info['filtered_atoms']:
                    raise ValueError(
                        'Attribute [%s], forbidden atom found [%s].' % (
                            attr_base, atom_name))

    def params_get(self, tax_params, attr):
        if attr not in tax_params:
            return None
        param_type_name = tax_params['type'].split('(')[0]
        if (param_type_name == 'float' or
                param_type_name == 'rangeable_float'):
            return float(tax_params[attr])
        elif (param_type_name == 'int' or
              param_type_name == 'rangeable_int'):
            return int(tax_params[attr])
        else:
            return None

    def check_single_value(self, atom_anc, param_type_name,
                           atom_param, tax_params):
        ty_form = '%f' if param_type_name == 'float' else (
            '%d' if param_type_name == 'int' else '%s')
        if param_type_name == 'float':
            try:
                v = float(atom_param)
            except ValueError:
                raise ValueError(
                    'Atom [%s]: value [%s] not valid float.' %
                    (atom_anc, atom_param))
        elif param_type_name == 'int':
            try:
                v = int(atom_param)
            except ValueError:
                raise ValueError(
                    'Atom [%s]: value %s not valid int.' %
                    (atom_anc, atom_param))

        if 'min' in tax_params:
            v_min = self.params_get(tax_params, 'min')
            m_incl = (tax_params['min_incl'] if 'min_incl' in tax_params
                      else True)
            if (m_incl and v < v_min) or (not m_incl and v <= v_min):
                # import pdb ; pdb.set_trace()
                raise ValueError(
                    ('Atom [%s]: value [%s] less%s then min value ('
                     + ty_form + ').') %
                    (atom_anc, atom_param,
                     (" or equal" if not m_incl else ""),
                     tax_params['min']))

        if 'max' in tax_params:
            v_max = self.params_get(tax_params, 'max')
            m_incl = (tax_params['max_incl'] if 'max_incl' in tax_params
                      else True)
            if (m_incl and v > v_max) or (not m_incl and v >= v_max):
                raise ValueError(
                    ('Atom [%s]: value [%s] greater%s'
                     ' then max value (' + ty_form + ').') %
                    (atom_anc, atom_param,
                     (" or equal" if not m_incl else ""),
                     tax_params['max']))

        return v

    def validate_parameters(self, attr_base, atom_tree, tax_params,
                            atom_params, atom_params_orig_in):
        """
        atom_args: list of arguments


        attr_base: attribute base
        atom_tree: atom tree included args and params
        tax_params: 'params' field of gem_tax['Atom'] element
        atom_params: list of parameters (strings)
        atom_params_orig_in: flattened hierarchy of current atom
        """
        # NOTE: currently not parameter types with args but we can foresee them
        param_type_name = tax_params['type'].split('(')[0]

        atom_anc = atom_tree.text
        atom_name = atom_tree.children[0].text
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
        elif param_type_name == 'float' or param_type_name == 'int':
            for atom_param in atom_params:
                self.check_single_value(atom_anc, param_type_name,
                                        atom_param, tax_params)
        elif (param_type_name == 'rangeable_float' or
              param_type_name == 'rangeable_int'):
            single_type_name = param_type_name[10:]
            for atom_param in atom_params:
                # inequality case
                if atom_param[0] in ['<', '>']:
                    val = self.check_single_value(
                        atom_anc, single_type_name,
                        atom_param[1:], tax_params)
                    if 'min' in tax_params:
                        if atom_param[0] == '<' and val <= tax_params['min']:
                            raise ValueError(
                                'Atom [%s]: incorrect %s inequality,'
                                ' no valid values below min value (%s).' %
                                (atom_anc, single_type_name,
                                 tax_params['min']))
                    if 'max' in tax_params:
                        if atom_param[0] == '>' and val >= tax_params['max']:
                            raise ValueError(
                                'Atom [%s]: incorrect %s inequality,'
                                ' no valid values above max value (%s).' %
                                (atom_anc, single_type_name,
                                 tax_params['max']))
                else:
                    if param_type_name == 'rangeable_float':
                        if re.findall("[^-]+-", atom_param):
                            rangefloat_tree = self.rangefloat_grammar.parse(
                                atom_param)
                            if (rangefloat_tree.expr.name != 'range' or
                                    len(rangefloat_tree.children) != 3):
                                raise ValueError(
                                    'Atom [%s]: incorrect floats range'
                                    ' syntax parameter found[%s].' %
                                    (atom_anc, atom_param))
                            flos = [rangefloat_tree.children[0],
                                    rangefloat_tree.children[2]]
                            if (flos[0].expr.name != 'flo' or
                                    flos[1].expr.name != 'flo'):
                                raise ValueError(
                                    'Atom [%s]: incorrect floats range'
                                    ' syntax parameter found[%s].' %
                                    (atom_anc, atom_param))
                            for flo_idx in range(0, 2):
                                self.check_single_value(
                                    atom_anc, 'float',
                                    flos[flo_idx].text, tax_params)
                            # check endpoints order
                            if float(flos[0].text) >= float(flos[1].text):
                                raise ValueError(
                                    'Atom [%s]: incorrect floats range:'
                                    ' first endpoint is greater then or'
                                    ' equal to the second (%s)' % (
                                        atom_anc, atom_param))
                        else:
                            # precise single value case
                            self.check_single_value(
                                atom_anc, 'float',
                                atom_param, tax_params)
                    elif param_type_name == 'rangeable_int':
                        if re.findall("[^-]+-", atom_param):
                            rangeint_tree = self.rangeint_grammar.parse(
                                atom_param)
                            if (rangeint_tree.expr.name != 'range' or
                                    len(rangeint_tree.children) != 3):
                                raise ValueError(
                                    'Atom [%s]: incorrect integers range'
                                    ' syntax parameter found[%s].' %
                                    (atom_anc, atom_param))
                            ints = [rangeint_tree.children[0],
                                    rangeint_tree.children[2]]
                            if (ints[0].expr.name != 'inte' or
                                    ints[1].expr.name != 'inte'):
                                raise ValueError(
                                    'Atom [%s]: incorrect integers range'
                                    ' syntax parameter found[%s].' %
                                    (atom_anc, atom_param))
                            for int_idx in range(0, 2):
                                self.check_single_value(
                                    atom_anc, 'int',
                                    ints[int_idx].text, tax_params)
                            # check endpoints order
                            if int(ints[0].text) >= int(ints[1].text):
                                raise ValueError(
                                    'Atom [%s]: incorrect integers range:'
                                    ' first endpoint is greater then or'
                                    ' equal to the second (%s)' % (
                                        atom_anc, atom_param))
                        else:
                            # precise single value case
                            self.check_single_value(
                                atom_anc, 'int',
                                atom_param, tax_params)

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

    def validate_attribute(self, attr_base, attr_tree, attr_scope,
                           attr_name, filtered_atoms):
        """
        attr_base:      full attribute (recursion invariant)
        attr_tree:      current evaluated attribute tree
        attr_scope:     linearized description of current atom scope
                        (e.g. if already argument...)
        attr_name:      already specified when call as arguments check
        filtered_atoms: list of prohibited atoms (from arguments check)
        """
        attr = attr_tree.text
        atoms_trees = self.extract_atoms(attr_tree)
        atom_names_in = []
        atoms_in = {}

        for atom_tree in atoms_trees:
            atom = atom_tree.text
            if len(atom_tree.children) != 3:
                raise ValueError(
                    'Attribute [%s], scope [%s]: malformed atom [%s]' % (
                        attr_base, attr_scope, atom))

            atom_name = atom_tree.children[0].text
            tree_args = []
            atom_tree_args = atom_tree.children[1]
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
            for param_child in atom_tree.children[2].children:
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
                    atom_tree, tax_params, params,
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
            attr_tree = self.attr_grammar.parse(attr)

            attr_name, attr_out = self.validate_attribute(
                attr, attr_tree, '', '', [])

            if attr_name in attr_in:
                raise ValueError(
                    'Attribute [%s] multiple declaration,'
                    ' previous: [%s], current [%s]' %
                    (attr_name, attr_in[attr_name],
                     attr))
            attr_name_in.append(attr_name)
            attr_in[attr_name] = attr
