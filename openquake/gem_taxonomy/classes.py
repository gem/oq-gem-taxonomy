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
import re
import json
import collections
import builtins
from parsimonious.grammar import Grammar
from parsimonious.exceptions import ParseError as ParsimParseError
from parsimonious.exceptions import (IncompleteParseError as
                                     ParsimIncompleteParseError)
from openquake.gem_taxonomy_data import GemTaxonomyData
from openquake.gem_taxonomy_data import __version__ as GTD_vers
from .version import __version__

#
#  TODO:
#
#    - complete code coverage with, possibly, fixtures where required
#


class GemTaxonomy:
    class EXPL_OUT_TYPE:
        SINGLELINE = 1
        MULTILINE = 2
        JSON = 3
        # HTML = 4

        DICT = {
            'textsingleline': SINGLELINE,
            'textmultiline': MULTILINE,
            'json': JSON,
            # 'html': HTML,
        }

    class INFO_OUT_TYPE:
        TEXT = 1
        JSON = 2

        DICT = {
            'text': TEXT,
            'json': JSON,
        }

    # method to test package infrastructure
    @staticmethod
    def info(fmt='text'):
        taxonomy_version = '3.3'
        gtd = GemTaxonomyData()
        tax = gtd.load(taxonomy_version)
        if fmt == 'text':
            s = '''GemTaxonomy Info
----------------
'''
            s += '  GemTaxonomy Package     - v. %s\n' % __version__
            s += '  GemTaxonomyData Package - v. %s\n' % GTD_vers
            s += '  Loaded Taxonomy Data    - v. %s\n' % taxonomy_version
            s += '  Atoms number            -    %d\n' % len(tax['Atom'])
            return s
        elif fmt == 'dict':
            return {
                'gem_taxonomy_version': __version__,
                'gem_taxonomy_data_version': GTD_vers,
                'gem_taxonomy_data_content_version': taxonomy_version,
                'gem_taxonomy_data_atoms_number': len(tax['Atom']),
            }

    def logic_print(self, attrs):
        self.LogicIndSet(0)
        return ''.join([x.__repr__() for x in attrs])

    def logic_explain(self, attrs, format=None):
        '''
            output_type should be:
                'textsingleline' - all the explanation in a single
                                   plain text line (default)
                'textmultiline'  - the explanation is splitted on
                                   many lines and indented to improve
                                   understandability
                'json'           - json tree version of the output
                (TODO 'html')    - hyperlinked version of the
                                   explanation
        '''
        try:
            output_type = self.EXPL_OUT_TYPE.DICT[
                'textsingleline' if format is None else format]
        except KeyError:
            raise ValueError('format %s unknown' % format)

        if output_type in [self.EXPL_OUT_TYPE.JSON]:
            ret = []
            for attr in attrs:
                ret.append(attr.explain(output_type=output_type))
            return output_type, ret
        else:
            self.LogicIndSet(0)
            s = ''
            for attr in attrs:
                s += attr.explain(output_type=output_type)
            if not attrs:
                s = "Completely unknown taxonomy."
            return output_type, s

    class LogicAttribute:
        def __init__(self, paself, attribute, atoms):
            self.paself = paself
            self.attribute = attribute
            self.atoms = atoms

        def explain(self, is_arg=False, output_type=None):
            if output_type is None:
                output_type = GemTaxonomy.EXPL_OUT_TYPE.SINGLELINE

            if output_type in [GemTaxonomy.EXPL_OUT_TYPE.JSON]:
                return {
                    'name': self.attribute['name'],
                    'title': self.attribute['title'],
                    'atoms': [atom.explain(
                        is_arg=is_arg, output_type=output_type)
                              for atom in self.atoms]
                    }

            s = ''
            if not is_arg:
                s += '%s: ' % self.attribute['title']
                if output_type == GemTaxonomy.EXPL_OUT_TYPE.MULTILINE:
                    s += '\n'
                    self.paself.LogicIndInc(4)

            if output_type == GemTaxonomy.EXPL_OUT_TYPE.MULTILINE:
                j_str = ',' + '\n'
            else:
                j_str = ', '

            for idx, atom in enumerate(self.atoms):
                if idx == 0:
                    s += atom.explain(output_type=output_type)
                    if output_type == GemTaxonomy.EXPL_OUT_TYPE.MULTILINE:
                        self.paself.LogicIndInc(4)
                else:
                    s += j_str + atom.explain(output_type=output_type)
            if output_type == GemTaxonomy.EXPL_OUT_TYPE.MULTILINE:
                self.paself.LogicIndDec(4)

            if not is_arg:
                s += '.'
                if output_type == GemTaxonomy.EXPL_OUT_TYPE.SINGLELINE:
                    s += ' '
                elif output_type == GemTaxonomy.EXPL_OUT_TYPE.MULTILINE:
                    s += '\n'

            if not is_arg:
                if output_type == GemTaxonomy.EXPL_OUT_TYPE.MULTILINE:
                    self.paself.LogicIndDec(4)
            return s

        def __repr__(self):
            indent = self.paself.LogicIndentation
            self.paself.LogicIndentation += 4
            ret = '%s<ATTR id="0x%xd" name="%s">\n%s%s</ATTR>\n' % (
                (' ' * indent),
                id(self), self.attribute['name'],
                ''.join([x.__repr__() for x in self.atoms]),
                (' ' * indent)
            )
            self.paself.LogicIndentation -= 4
            return ret

    class LogicAtom:
        def __init__(self, paself, text, atom, args, params, canonical):
            self.paself = paself
            self.text = text
            self.atom = atom
            self.args = args
            self.params = params
            self.canonical = canonical

        def explain(self, is_arg=False, output_type=None):
            if output_type is None:
                output_type = GemTaxonomy.EXPL_OUT_TYPE.SINGLELINE

            if output_type in [GemTaxonomy.EXPL_OUT_TYPE.JSON]:
                name = self.atom['name']
                ret = {
                    'name': name,
                    'title': self.paself.tax['AtomDict'][name][
                        'title'],
                }
                if self.args:
                    ret['args'] = [arg.explain(
                        is_arg=True,
                        output_type=GemTaxonomy.EXPL_OUT_TYPE.JSON) for
                                   arg in self.args]
                if self.params:
                    ret['params'] = [param.explain(
                        output_type=GemTaxonomy.EXPL_OUT_TYPE.JSON) for
                               param in self.params]

                return ret
            s = ''

            if output_type == GemTaxonomy.EXPL_OUT_TYPE.MULTILINE:
                indent = self.paself.LogicIndGet()
                s += ' ' * indent

            if ', ' in self.atom['title']:
                title = '"%s"' % self.atom['title']
            else:
                title = self.atom['title']
            s += title

            if self.args:
                s += ' ('
                if output_type == GemTaxonomy.EXPL_OUT_TYPE.MULTILINE:
                    s += '\n'
                    indent = self.paself.LogicIndInc(4)

                n_args = len(self.args)
                for idx, arg in enumerate(self.args):
                    s += arg.explain(is_arg=True, output_type=output_type)
                    # if idx < (n_args - 2):
                    if idx < (n_args - 1):
                        if (output_type ==
                                GemTaxonomy.EXPL_OUT_TYPE.SINGLELINE):
                            s += '; '
                        elif (output_type ==
                              GemTaxonomy.EXPL_OUT_TYPE.MULTILINE):
                            s += ';' + '\n'
                    # elif idx < (n_args - 1):
                    #     if (output_type ==
                    #         GemTaxonomy.EXPL_OUT_TYPE.SINGLELINE):
                    #         s += ' and '
                    #     elif (output_type ==
                    #           GemTaxonomy.EXPL_OUT_TYPE.MULTILINE):
                    #         s += ' and\n'
                if output_type == GemTaxonomy.EXPL_OUT_TYPE.MULTILINE:
                    s += '\n'
                    indent = self.paself.LogicIndDec(4)
                    s += ' ' * indent
                s += ')'
            if self.params:
                s += ': '
                s += ' '.join([param.explain(output_type=output_type) for
                               param in self.params])

            return s

        def __repr__(self):
            indent = self.paself.LogicIndentation
            self.paself.LogicIndentation += 4

            name = self.atom['name']
            if len(self.args) > 0:
                self.paself.LogicIndentation += 4
                args_list = [x.__repr__() for x in self.args]
                self.paself.LogicIndentation -= 4

                args = '%s<args>\n%s%s</args>\n' % (
                    ' ' * (indent + 4),
                    ''.join(args_list),
                    ' ' * (indent + 4))
            else:
                args = ''

            if len(self.params) > 0:
                params = '%s<params>\n%s%s</params>\n' % (
                    ' ' * (indent + 4),
                    ''.join(['%s' % x.__repr__() for x in self.params]),
                    ' ' * (indent + 4),
                )
            else:
                params = ''

            if len(self.args) == 0 and len(self.params) == 0:
                ret = ('%s<ATOM id="0x%xd" name="%s"'
                       ' title="%s"/>\n') % (
                           ' ' * indent, id(self), name,
                           self.paself.tax['AtomDict'][name]['title'])
            else:
                ret = ('%s<ATOM id="0x%xd" name="%s"'
                       ' title="%s">\n%s%s%s</ATOM>\n') % (
                           ' ' * indent, id(self), name,
                           self.paself.tax['AtomDict'][name]['title'],
                           args, params, ' ' * indent)

            self.paself.LogicIndentation -= 4

            return ret

    class LogicParam:
        TYPE_OPTION = 1
        TYPE_INT = 2
        TYPE_FLOAT = 3

        def type_s(self):
            return {
                self.TYPE_OPTION: 'option',
                self.TYPE_INT: 'int',
                self.TYPE_FLOAT: 'float'}[self.type]

        SUBTYPE_NONE = 0
        SUBTYPE_DIS_LT = 1
        SUBTYPE_DIS_GT = 2
        SUBTYPE_RANGE = 3
        SUBTYPE_EXACT = 4

        def subtype_s(self):
            return {
                self.SUBTYPE_NONE: 'none',
                self.SUBTYPE_DIS_LT: 'less_than',
                self.SUBTYPE_DIS_GT: 'greater_than',
                self.SUBTYPE_RANGE: 'range',
                self.SUBTYPE_EXACT: 'exact'}[self.subtype]

        UNIT_MEAS_SINGLE = 0
        UNIT_MEAS_PLURAL = 1

        def __init__(self, paself, atom, type, subtype,
                     title, value, unit_meas):
            self.paself = paself
            self.atom = atom
            self.type = type
            self.subtype = subtype
            self.title = title
            self.value = value
            self.unit_meas = unit_meas
            self.unit_meas_is_single = None

        def unit_meas_is_single_default(self, value_out):
            if value_out == '1':
                return True
            else:
                return False

        def unit_meas_out(self, value_out):
            is_single = (self.unit_meas_is_single(value_out)
                         if self.unit_meas_is_single is not None else
                         self.unit_meas_is_single_default(value_out))
            return (self.unit_meas[self.UNIT_MEAS_SINGLE if is_single else
                                   self.UNIT_MEAS_PLURAL])

        def explain(self, output_type=None):
            if output_type is None:
                output_type = GemTaxonomy.EXPL_OUT_TYPE.SINGLELINE
            if self.type not in [
                    self.TYPE_OPTION, self.TYPE_INT, self.TYPE_FLOAT]:
                raise ValueError('unknown param type %d' % self.type)

            if self.type == self.TYPE_OPTION:
                atom_name = self.atom.split(':')[0]
                opt_key = ':'.join(self.atom.split(':')[1:] + [self.value])
                param = [
                    x for x in self.paself.tax['Param'][atom_name]
                    if x['name'] == opt_key][0]
                if output_type in [GemTaxonomy.EXPL_OUT_TYPE.JSON]:
                    return {
                        'type': self.type_s(),
                        'subtype': self.subtype_s(),
                        'value': self.value,
                        'title': [param['title']]
                        }
                else:
                    return param['title']
            else:
                # add other if if other types '%f' if
                # self.type == self.TYPE_FLOAT)
                form = '%d' if self.type == self.TYPE_INT else '%s'
                fconv = getattr(builtins, (
                    'int' if self.type == self.TYPE_INT else 'float'))
                if output_type in [GemTaxonomy.EXPL_OUT_TYPE.JSON]:
                    if type(self.value) is list:
                        value = [fconv(v) for v in self.value]
                    else:
                        value = fconv(self.value)
                    return {
                        'type': self.type_s(),
                        'subtype': self.subtype_s(),
                        'value': value
                        }
                if self.subtype == self.SUBTYPE_DIS_LT:
                    value_out = form % fconv(self.value)
                    unit_meas_out = self.unit_meas_out(value_out)
                    ret = 'less than %s %s' % (value_out, unit_meas_out)
                elif self.subtype == self.SUBTYPE_DIS_GT:
                    value_out = form % fconv(self.value)
                    unit_meas_out = self.unit_meas_out(value_out)
                    ret = 'greater than %s %s' % (value_out, unit_meas_out)
                elif self.subtype == self.SUBTYPE_RANGE:
                    unit_meas_out = self.unit_meas[self.UNIT_MEAS_PLURAL]
                    ret = 'between %s and %s %s' % (
                        form % fconv(self.value[0]),
                        form % fconv(self.value[1]),
                        unit_meas_out)
                elif self.subtype == self.SUBTYPE_EXACT:
                    value_out = form % fconv(self.value)
                    unit_meas_out = self.unit_meas_out(value_out)
                    ret = '%s %s' % (value_out, unit_meas_out)
                else:
                    raise ValueError('unknown param subtype %d' % self.subtype)

            return ret

        def __repr__(self):
            form = '%d' if self.type == self.TYPE_INT else '%s'
            fconv = getattr(builtins, (
                'int' if self.type == self.TYPE_INT else 'float'))

            self.paself.LogicIndentation += 4
            indent = self.paself.LogicIndentation
            if self.type == self.TYPE_OPTION:
                # PAY ATTENTION:  currently TYPE_OPTION support
                #                 just 1 parameter, for multiple parameter
                # all the parents hierarchy must be available in the
                # tax['Param'][<ATOM>] list of partial elements

                self.paself.LogicIndentation += 4
                indent = self.paself.LogicIndentation
                v = '%s<value >%s</value>\n' % (
                    ' ' * indent, self.value)
                self.paself.LogicIndentation -= 4
                indent = self.paself.LogicIndentation
                ret = ('%s<param subtype="%s" title="%s" type="%s">'
                       '\n%s%s</param>\n') % (
                        (' ' * indent), self.subtype_s(),
                        self.title, self.type_s(), v,
                        (' ' * indent))
            else:
                self.paself.LogicIndentation += 4
                indent = self.paself.LogicIndentation
                if self.subtype == self.SUBTYPE_RANGE:
                    v = '%s<value>%s</value>\n%s<value>%s</value>\n' % (
                        ' ' * indent, form % fconv(self.value[0]),
                        ' ' * indent, form % fconv(self.value[1]))
                else:
                    v = '%s<value>%s</value>\n' % (
                        ' ' * indent, form % fconv(self.value))
                self.paself.LogicIndentation -= 4
                indent = self.paself.LogicIndentation

                ret = ('%s<param subtype="%s" type="%s"'
                       ' unit_meas_plural="%s"'
                       ' unit_meas_single="%s">\n%s%s</param>\n') % (
                           (' ' * indent), self.subtype_s(), self.type_s(),
                           self.unit_meas[1], self.unit_meas[0], v,
                           (' ' * indent))
            self.paself.LogicIndentation -= 4

            return ret

    def __init__(self, vers='3.3'):
        self.LogicIndentation = 0

        if vers == '3.3':
            self.taxo_grammar = Grammar(r'''
                taxo = "UNK" / ( attr ( "/" attr )* )
                attr = atom ( "+" atom )*
                atom = ~r"[A-Z][A-Z0-9]*" atom_args* atom_params*
                atom_args = "(" attr ( ";" attr )* ")"
                atom_params = ":" ~r"[A-Za-z0-9<>-][A-Za-z0-9.-]*"
                ''')

            # flo = ~r'[0-9]+'
            self.rangefloat_grammar = Grammar(r'''
                range = float_value "-" float_value
                float_value = ~r"[0-9-]?" ~r"[0-9.]*" ( ~r"e[+-]?[0-9]+" )?
                ''')
            self.rangeint_grammar = Grammar(r'''
                range = integer_value "-" integer_value
                integer_value = ~r"[0-9-]" ~r"[0-9]*"
                ''')

        self.gtd = GemTaxonomyData()
        self.tax = self.gtd.load(vers)
        # new_dict = {}
        # for k in ['Attribute', 'AtomsGroup', 'Atom']:
        #     if 'name' in self.tax[k][0]:
        #         new_dict[k + 'Dict'] = {x['name']: x for x in self.tax[k]}
        # self.tax.update(new_dict)

    def LogicIndSet(self, value):
        self.LogicIndentation = value

    def LogicIndGet(self):
        return self.LogicIndentation

    def LogicIndInc(self, delta):
        self.LogicIndentation += delta
        return self.LogicIndentation

    def LogicIndDec(self, delta):
        self.LogicIndentation -= delta
        return self.LogicIndentation

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
        '''
        attr_base: attribute base
        atom_anc: atom string included args and params
        tax_args: 'args' field of gem_tax['Atom'] element
        tree_args: list of tree arguments
        atom_args_orig_in: flattened hierarchy of current atom
        filtered_atoms: optional list of atoms not allowed as arguments

        RETURN:
        args_canon if arguments are filtered_attribute
        '''
        l_args = []
        arg_type_name = tax_args['type'].split('(')[0]

        if (arg_type_name == 'filtered_attribute'
                or arg_type_name == 'filtered_atomsgroup'):
            args_info = eval('self.args__' + tax_args['type'])
        else:
            raise ValueError(
                'Atom [%s]: unknown arguments type [%s].' %
                (atom_anc, tax_args['type']))

        if arg_type_name == 'filtered_attribute':
            args_list_canon = []
            for tree_arg in tree_args:
                # print('TREE_ARG: %s' % tree_arg.text)
                attr_name, attr_canon, l_arg = self.validate_attribute(
                    attr_base, tree_arg,
                    atom_args_orig_in, args_info['attribute_name'],
                    list(set(filtered_atoms).union(
                        set(args_info['filtered_atoms']))))
                args_list_canon.append(attr_canon)
                l_args.append(l_arg)
                # print('val_args: attr_canon: [%s]' % attr_canon)
            if 'must_be_diff' in tax_args and tax_args['must_be_diff']:
                same_elem = [item for item, count in collections.Counter(
                    args_list_canon).items() if count > 1]
                if same_elem:
                    raise ValueError(
                        'Attribute [%s]: for atom [%s] identical '
                        'arguments are denied [%s].' % (
                            attr_base, atom_anc, same_elem[0]))
            args_canon = ';'.join(args_list_canon)
            # print('val_args: args_canon: [%s]' % args_canon)
            return args_canon, l_args
        elif arg_type_name == 'filtered_atomsgroup':
            args_list_canon = []
            for tree_arg in tree_args:
                atom_name = tree_arg.children[0].children[0].text
                l_arg = self.LogicAtom(
                    self, tree_arg.text, self.tax['AtomDict'][atom_name],
                    [], [], None)

                args_list_canon.append(tree_arg.text)
                if len(tree_arg.children) > 1 and len(tree_arg.children[1].children) > 0:
                    raise ValueError(
                        'Attribute [%s]: composition of atoms not allowed [%s].' % (
                            attr_base, tree_arg.text))
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
                l_args.append(l_arg)
            args_canon = ';'.join(args_list_canon)
            return args_canon, l_args

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
                raise ValueError(
                    ('Atom [%s]: value [%s] less%s then min value ['
                     + ty_form + '].') %
                    (atom_anc, atom_param,
                     (' or equal' if not m_incl else ''),
                     tax_params['min']))

        if 'max' in tax_params:
            v_max = self.params_get(tax_params, 'max')
            m_incl = (tax_params['max_incl'] if 'max_incl' in tax_params
                      else True)
            if (m_incl and v > v_max) or (not m_incl and v >= v_max):
                raise ValueError(
                    ('Atom [%s]: value [%s] greater%s'
                     ' then max value [' + ty_form + '].') %
                    (atom_anc, atom_param,
                     (' or equal' if not m_incl else ''),
                     tax_params['max']))

        return v

    def validate_parameters(self, attr_base, atom_tree, tax_params,
                            atom_params, atom_params_orig_in):
        '''
        atom_args: list of arguments


        attr_base: attribute base
        atom_tree: atom tree included args and params
        tax_params: 'params' field of gem_tax['Atom'] element
        atom_params: list of parameters (strings)
        atom_params_orig_in: flattened hierarchy of current atom
        '''

        l_params = []
        # NOTE: currently not parameter types with args but we can foresee them
        param_type_name = tax_params['type'].split('(')[0]

        atom_anc = atom_tree.text
        atom_name = atom_tree.children[0].text
        if param_type_name == 'options':
            if tax_params['params_max'] > 0 and len(atom_params) > 0:
                if atom_name not in self.tax['Param']:
                    raise ValueError(
                        'Atom [%s]: parameters options not found.' %
                        (atom_anc,))
                atom_options = self.tax['Param'][atom_name]
                if len(atom_params) > 1:
                    raise ValueError(
                        'Atom [%s]: multiple parameters options'
                        ' not supported.' % (atom_anc,))
                for atom_param_idx, atom_param in enumerate(atom_params):
                    atom_param_key = ':'.join(atom_params[0:(
                        atom_param_idx + 1)])
                    atom_option_list = list(filter(
                        lambda option: option['name'] == atom_param_key,
                        atom_options))
                    if (len(atom_option_list) < 1):
                        raise ValueError(
                            'Atom [%s]: parameters option [%s] not found.' %
                            (atom_anc, atom_param_key))
                    l_params.append(self.LogicParam(
                        self, atom_name, self.LogicParam.TYPE_OPTION,
                        self.LogicParam.SUBTYPE_NONE,
                        atom_option_list[0]['title'],
                        atom_param, ''))
        elif param_type_name == 'float' or param_type_name == 'int':
            for atom_param in atom_params:
                self.check_single_value(atom_anc, param_type_name,
                                        atom_param, tax_params)
                l_params.append(self.LogicParam(
                    self, atom_name, (self.LogicParam.TYPE_FLOAT
                                      if param_type_name == 'float'
                                      else self.LogicParam.TYPE_INT),
                    self.LogicParam.SUBTYPE_EXACT, None,
                    atom_param, tax_params['unit_measure']))
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
                                ' no valid values below min value [%s].' %
                                (atom_anc, single_type_name,
                                 tax_params['min']))
                    if 'max' in tax_params:
                        if atom_param[0] == '>' and val >= tax_params['max']:
                            raise ValueError(
                                'Atom [%s]: incorrect %s inequality,'
                                ' no valid values above max value [%s].' %
                                (atom_anc, single_type_name,
                                 tax_params['max']))
                    l_params.append(self.LogicParam(
                        self, atom_name, (
                            self.LogicParam.TYPE_FLOAT
                            if param_type_name == 'rangeable_float'
                            else self.LogicParam.TYPE_INT),
                        (self.LogicParam.SUBTYPE_DIS_LT
                         if atom_param[0] == '<'
                         else self.LogicParam.SUBTYPE_DIS_GT), None,
                        atom_param[1:], tax_params['unit_measure']))
                else:
                    if param_type_name == 'rangeable_float':
                        if re.findall('[^-]+-', atom_param):
                            try:
                                rangefloat_tree = (
                                    self.rangefloat_grammar.parse(
                                        atom_param))
                            except (ParsimParseError,
                                    ParsimIncompleteParseError) as exc:
                                raise ValueError(
                                    'Atom [%s]: incorrect floats range'
                                    ' syntax parameter found [%s]: %s.' %
                                    (atom_anc, atom_param,
                                     str(exc).rstrip('.')))
                            if (rangefloat_tree.expr.name != 'range' or
                                    len(rangefloat_tree.children) != 3):
                                raise ValueError(
                                    'Atom [%s]: incorrect floats range'
                                    ' syntax parameter found [%s].' %
                                    (atom_anc, atom_param))
                            flos = [rangefloat_tree.children[0],
                                    rangefloat_tree.children[2]]
                            if (flos[0].expr.name != 'float_value' or
                                    flos[1].expr.name != 'float_value'):
                                raise ValueError(
                                    'Atom [%s]: incorrect floats range'
                                    ' syntax parameter found [%s].' %
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
                                    ' equal to the second [%s]' % (
                                        atom_anc, atom_param))
                            l_params.append(self.LogicParam(
                                self, atom_name, self.LogicParam.TYPE_FLOAT,
                                self.LogicParam.SUBTYPE_RANGE, None,
                                [float(flos[0].text), float(flos[1].text)],
                                tax_params['unit_measure']))
                        else:
                            # precise single value case
                            self.check_single_value(
                                atom_anc, 'float',
                                atom_param, tax_params)
                            l_params.append(self.LogicParam(
                                self, atom_name, self.LogicParam.TYPE_FLOAT,
                                self.LogicParam.SUBTYPE_EXACT,
                                None, float(atom_param),
                                tax_params['unit_measure']))
                    elif param_type_name == 'rangeable_int':
                        if re.findall('[^-]+-', atom_param):
                            try:
                                rangeint_tree = self.rangeint_grammar.parse(
                                    atom_param)
                            except (ParsimParseError,
                                    ParsimIncompleteParseError) as exc:
                                raise ValueError(
                                    'Atom [%s]: incorrect integers range'
                                    ' syntax parameter found [%s]: %s.' %
                                    (atom_anc, atom_param,
                                     str(exc).rstrip('.')))
                            if (rangeint_tree.expr.name != 'range' or
                                    len(rangeint_tree.children) != 3):
                                raise ValueError(
                                    'Atom [%s]: incorrect integers range'
                                    ' syntax parameter found [%s].' %
                                    (atom_anc, atom_param))
                            ints = [rangeint_tree.children[0],
                                    rangeint_tree.children[2]]
                            if (ints[0].expr.name != 'integer_value' or
                                    ints[1].expr.name != 'integer_value'):
                                raise ValueError(
                                    'Atom [%s]: incorrect integers range'
                                    ' syntax parameter found [%s].' %
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
                                    ' equal to the second [%s]' % (
                                        atom_anc, atom_param))
                            l_params.append(self.LogicParam(
                                self, atom_name, self.LogicParam.TYPE_INT,
                                self.LogicParam.SUBTYPE_RANGE, None,
                                [int(ints[0].text), int(ints[1].text)],
                                tax_params['unit_measure']))
                        else:
                            # precise single value case
                            self.check_single_value(
                                atom_anc, 'int',
                                atom_param, tax_params)
                            l_params.append(self.LogicParam(
                                self, atom_name, self.LogicParam.TYPE_INT,
                                self.LogicParam.SUBTYPE_EXACT, None,
                                int(atom_param), tax_params['unit_measure']))
        return l_params

    def validate_attribute(self, attr_base, attr_tree, attr_scope,
                           attr_name, filtered_atoms):
        '''
        attr_base:      full attribute (recursion invariant)
        attr_tree:      current evaluated attribute tree
        attr_scope:     linearized description of current atom scope
                        (e.g. if already argument...)
        attr_name:      already specified when call as arguments check
        attr_canon:     canonicalized version of string attribute
        filtered_atoms: list of prohibited atoms (from arguments check)

        RETURN:
        attr_name, l_attr
        '''
        attr = attr_tree.text
        atoms_trees = self.extract_atoms(attr_tree)
        atom_names_in = []
        atoms_in = []
        atoms_canon_in = []
        atoms_dict_in = {}
        l_attr = None
        l_atom = None
        l_atoms = []

        if attr_name is not None:
            l_attr = self.LogicAttribute(
                self, self.tax['AttributeDict'][attr_name], [])

        for atom_tree in atoms_trees:
            atom = atom_tree.text
            atoms_in.append(atom)
            if len(atom_tree.children) != 3:
                raise ValueError(
                    'Attribute [%s], scope [%s]: malformed atom [%s]' % (
                        attr_base, attr_scope, atom))

            atom_name = atom_tree.children[0].text
            args_canon = ''
            tree_args = []
            len_tree_args = 0
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
            l_params = []
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
                    ' atom recursion found [%s].' % (
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

            l_atom = self.LogicAtom(
                self, atom, self.tax['AtomDict'][atom_name],
                [], [], None)

            # check mutex atoms for the same group
            atoms_group_name = {k: v for k, v in atoms_dict_in.items() if
                                v['group'] == tax_atom['group']}
            if atoms_group_name:
                raise ValueError(
                    'Attribute [%s]: atoms group "%s"'
                    ' already present with member [%s],'
                    ' new atom [%s] not allowed.' %
                    (attr, self.tax['AtomsGroupDict'][
                        tax_atom['group']]['title'],
                     [x for x in atoms_group_name][0],
                     atom_name))

            atom_names_in.append(atom_name)
            atoms_dict_in[atom_name] = tax_atom

            if attr_name is None:
                # if atom_name in self.tax['AtomsDeps'].keys():
                #     print('Not independent atom [%s], at'
                #           ' least unsorted attribute atoms.' % atom_name)
                attr_name = tax_atom['attr']
                attr_scope = tax_atom['name']
                args_attr_scope = 'args ' + atom_name
                l_attr = self.LogicAttribute(
                    self, self.tax['AttributeDict'][attr_name], [])
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
                args_canon, l_args = self.validate_arguments(
                    attr_base,
                    atom, tax_args, tree_args,
                    args_attr_scope, filtered_atoms)
                l_atom.args = l_args
                # print('val_attr: args_canon: [%s]' % args_canon)
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

                l_params = self.validate_parameters(
                    attr_base,
                    atom_tree, tax_params, params,
                    attr_scope)
                l_atom.params = l_params
            else:
                if len(params) > 0:
                    raise ValueError(
                        'Attribute [%s]: no parameters expected'
                        ' for atom [%s], found [%s]' %
                        (attr_base, atom_name, params))

            if len_tree_args > 0:
                if len(params) > 0:
                    atoms_canon_in.append(
                        '%s(%s):%s' % (
                            atom_name, args_canon,
                            ':'.join(params)))
                else:
                    atoms_canon_in.append(
                        '%s(%s)' % (
                            atom_name, args_canon))
            else:
                if len(params) > 0:
                    atoms_canon_in.append(
                        '%s:%s' % (
                            atom_name, ':'.join(params)))
                else:
                    atoms_canon_in.append('%s' % (
                        atom_name))
            # print('val_attr: atoms_canon_in %s' % atoms_canon_in)
            l_atoms.append(l_atom)
            # end atoms loop

        for atom_name_in in atom_names_in:
            if atom_name_in not in self.tax['AtomsDeps']:
                continue
            else:
                for dep in self.tax['AtomsDeps'][atom_name_in]:
                    if dep in atom_names_in:
                        break
                else:
                    raise ValueError(
                        'Attribute [%s]: missing dependency for atom [%s]' %
                        (attr_base, atom_name))
        group_progs = [int(self.tax['AtomsGroupDict'][
            self.tax['AtomDict'][x]['group']]['prog']) for x in atom_names_in]
        attr_canon = '+'.join(
            [x for _, x in sorted(zip(group_progs, atoms_canon_in))])
        l_atoms_canon = [x for _, x in sorted(zip(group_progs, l_atoms))]
        if l_attr is not None:
            l_attr.atoms = l_atoms_canon
        return attr_name, attr_canon, l_attr

    def validate(self, tax_str):
        l_attrs = []
        attr_name_in = []
        attr_in = {}
        attr_canon_in = {}
        l_attrs_canon = []

        taxo_attrs = []
        tax_is_empty = False
        try:
            taxo_or_empty_tree = self.taxo_grammar.parse(tax_str)
            if len(taxo_or_empty_tree.children) == 1:
                single_child = taxo_or_empty_tree.children[0]
                if (single_child.expr.__class__.__name__ == 'Literal' and
                        single_child.text == 'UNK'):
                    tax_is_empty = True

            if not tax_is_empty:
                # extract list of grammar attributes and
                # place them in taxo_attrs list
                if len(taxo_or_empty_tree.children) > 0:
                    if (taxo_or_empty_tree.children[0].expr.__class__
                            .__name__ == 'Sequence'):
                        taxo_tree = taxo_or_empty_tree.children[0]
                        if len(taxo_tree.children) > 0:
                            taxo_attrs.append(taxo_tree.children[0])
                        if len(taxo_tree.children) > 1:
                            qta_tree = taxo_tree.children[1]
                            for seq_tree in qta_tree.children:
                                taxo_attrs.append(seq_tree.children[1])
            # print([x.expr.name for x in taxo_attrs])
            # print([x.text for x in taxo_attrs])
        except (ParsimParseError,
                ParsimIncompleteParseError) as exc:
            if len(tax_str) == 0:
                raise ValueError(
                    'Empty taxonomy string is not valid, use'
                    ' \'UNK\' string instead.')

            spec_info = ''
            if len(tax_str) > 0 and (not tax_str[0].isupper()):
                spec_info = (
                    'Taxonomy string [%s]: a taxonomy string must start with'
                    ' an uppercase alphabetic character.' % tax_str)
            elif len(tax_str) > 1 and (
                    (not tax_str[-1].isupper()) and
                    (tax_str[-1] not in ')0123456789.')):
                spec_info = (
                    'Taxonomy string [%s]: a taxonomy string must end with'
                    ' an uppercase alpha-numeric or a \')\' or a \'.\''
                    ' character.'
                    % tax_str)
            elif re.search(
                    'The non-matching portion of the'
                    ' text begins with \'\\(.+\\)\'',
                    exc.__str__()):
                spec_info = ('Atom arguments must be'
                             ' included in rounded brackets'
                             ' and separated by \';\' character.')
            elif re.search(
                    'The non-matching portion of the text'
                    ' begins with \'\\(\\)\'',
                    exc.__str__()):
                spec_info = ('Empty rounded brackets are not'
                             ' allowed for atoms with'
                             ' optional arguments.')

            raise ValueError(
                '%sTaxonomy string [%s] parsing error: %s.' %
                ((("%s " % spec_info) if spec_info else ''),
                 tax_str, str(exc).rstrip('.')))

        for attr_tree in taxo_attrs:
            attr = attr_tree.text

            attr_name, attr_canon, l_attr = self.validate_attribute(
                attr, attr_tree, '', None, [])
            l_attrs.append(l_attr)
            if attr_name in attr_in:
                raise ValueError(
                    'Attribute [%s] multiple declaration,'
                    ' previous: [%s], current [%s]' %
                    (attr_name, attr_in[attr_name],
                     attr))
            attr_name_in.append(attr_name)
            attr_in[attr_name] = attr
            attr_canon_in[attr_name] = attr_canon
        if tax_is_empty:
            tax_canon = 'UNK'
        else:
            attr_progs = [int(self.tax['AttributeDict'][x]['prog']) for x
                          in attr_name_in]
            attr_name_canon = [x for _, x in sorted(
                zip(attr_progs, attr_name_in))]
            tax_canon = '/'.join([attr_canon_in[x] for x in
                                  attr_name_canon])
            l_attrs_canon = [x for _, x in sorted(
                zip(attr_progs, l_attrs))]

        # self.logic_print(l_attrs_canon)
        # print(self.logic_explain(l_attrs_canon, 'textsingleline'))
        # print(self.logic_explain(l_attrs_canon, 'textmultiline'))
        # import pprint
        # pprint.pprint(self.logic_explain(l_attrs_canon, 'json'))

        if tax_str == tax_canon:
            return(attr_canon_in, l_attrs_canon, {'is_canonical': True})
        else:
            return(attr_canon_in, l_attrs_canon, {'is_canonical': False,
                                                  'original': tax_str,
                                                  'canonical': tax_canon})

    def split_by_attributes(self, *args):
        '''
        split_by_attributes(taxonomy_string)
        split_by_attributes(taxonomy_string, field_sep, taxonomy_field_idx,
                            key_name)
        '''
        n_args = len(args)
        if n_args not in [1, 4]:
            raise TypeError(
                '%s.get_attributes() takes'
                ' 1 or 4 positional arguments but %d'
                ' were given' % (self.__class__.__name__,
                                 n_args))
        if n_args == 1:
            tax = args[0]
            attrs, _, _ = self.validate(tax)
            return attrs
        else:
            fields = args[0]
            sep = args[1]
            fie_idx = args[2]
            key_name = args[3]
            subfields = fields.split(sep)
            tax = subfields[fie_idx]
            attrs, _, _ = self.validate(tax)
            n_subfields = len(subfields)

            if n_subfields == 1:
                return attrs
            elif n_subfields == 2:
                attrs[key_name] = subfields[1-fie_idx]
            elif n_subfields > 2:
                others = subfields[0:fie_idx] + subfields[fie_idx+1:]
                attrs[key_name] = others
            return attrs

    def explain(self, tax_str, fmt='textsingleline'):
        _, l_attrs, val_reply = self.validate(tax_str)

        return self.logic_explain(l_attrs, format=fmt) + (val_reply,)

    def dump_explain(self, fmt, expl):
        if fmt in [GemTaxonomy.EXPL_OUT_TYPE.SINGLELINE,
                   GemTaxonomy.EXPL_OUT_TYPE.MULTILINE]:
            print(expl)
        elif fmt in [GemTaxonomy.EXPL_OUT_TYPE.JSON]:
            print(json.dumps(expl))
        else:
            raise ValueError('Unknown explain format %d' % fmt)
