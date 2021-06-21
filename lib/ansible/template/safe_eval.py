# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import ast
import copy

from ansible.module_utils.common.text.converters import container_to_text, to_native
from ansible.module_utils.six import PY2, string_types
from ansible.utils.display import Display

display = Display()

# define certain JSON types
# eg. JSON booleans are unknown to python eval()
_OUR_GLOBALS = {
    '__builtins__': {},  # avoid global builtins as per eval docs
    'false': False,
    'null': None,
    'true': True,
}

if PY2:
    _OUR_GLOBALS.update({
        'True': True,
        'False': False,
    })

_CALL_ENABLED = frozenset(k for k, v in _OUR_GLOBALS.items() if callable(v))

_optional_nodes = []
# These node types are dependent on Python version
# Set - 3.7
# NameConstant - 3.4 - Deprecated in 3.8
# Constant - 3.6
# Str - Deprecated in 3.8
# Num - Deprecated in 3.8
for _name in ('Set', 'NameConstant', 'Constant', 'Str', 'Num'):
    try:
        _optional_nodes.append(getattr(ast, _name))
    except AttributeError:
        pass

# this is the list of AST nodes we are going to
# allow in the evaluation. Any node type other than
# those listed here will raise an exception in our custom
# visitor class defined below.
_SAFE_NODES = frozenset(
    (
        # ast.Add,
        # ast.BinOp,
        ast.Call,
        # ast.Compare,
        ast.Dict,
        # ast.Div,
        ast.Expression,
        ast.List,
        ast.Load,
        # ast.Mult,
        ast.Name,
        # ast.Sub,
        ast.UAdd,
        ast.USub,
        ast.Tuple,
        ast.UnaryOp,
    ) + tuple(_optional_nodes)
)


class CleansingNodeVisitor(ast.NodeVisitor):
    """ast.NodeVisitor subclass that will raise an exception on
    disallowed Nodes or disallowed callables
    """

    def __init__(self, expr):
        self._expr = expr
        self._inside_call = False

    def generic_visit(self, node):
        if type(node) not in _SAFE_NODES:
            raise Exception("invalid expression (%s)" % self._expr)
        super(CleansingNodeVisitor, self).generic_visit(node)

    def visit_Attribute(self, node):
        # ast.Attribute isn't in _SAFE_NODES, so this will never be called
        # added just for safety, and reference if we ever allow it
        if self._inside_call:
            # Disallow calls to any attribute
            raise Exception("invalid function: %s" % node.attr)
        self.generic_visit(node)

    def visit_Name(self, node):
        if self._inside_call and node.id not in _CALL_ENABLED:
            # Disallow calls to functions that we have not vetted
            # as safe.  Other functions are excluded by setting locals in
            # the call to eval() later on
            raise Exception("invalid function: %s" % node.id)
        self.generic_visit(node)

    def visit_Call(self, node):
        try:
            self._inside_call = True
            self.generic_visit(node)
        finally:
            self._inside_call = False


def safe_eval(expr, locals=None, include_exceptions=False):
    '''
    This is intended for converting Python string representations of data
    into Python objects but restricting the evaluation to specific operations
    and callables (outside of Jinja2, where the env is constrained).

    An example use is where a single templating operation of ``{{ foo }}`` returns a Python
    string representation that looks like the following, but we desire it to be an actual python
    dict:

        "{'bar': ['baz'], 'qux': True}"

    Based on:
    http://stackoverflow.com/questions/12523516/using-ast-and-whitelists-to-make-pythons-eval-safe
    '''
    locals = {} if locals is None else copy.deepcopy(locals)

    if not isinstance(expr, string_types):
        # already templated to a datastructure, perhaps?
        if include_exceptions:
            return (expr, None)
        return expr

    cnv = CleansingNodeVisitor(expr)
    try:
        parsed_tree = ast.parse(expr, mode='eval')
        cnv.visit(parsed_tree)
        compiled = compile(parsed_tree, '<expr %s>' % to_native(expr), 'eval')
        # Note: passing our own globals and locals here constrains what
        # callables (and other identifiers) are recognized.  this is in
        # addition to the filtering of callables done in CleansingNodeVisitor
        result = eval(compiled, copy.deepcopy(_OUR_GLOBALS), locals)
        if PY2:
            # On Python 2 u"{'key': 'value'}" is evaluated to {'key': 'value'},
            # ensure it is converted to {u'key': u'value'}.
            result = container_to_text(result)

        if include_exceptions:
            return (result, None)
        else:
            return result
    except SyntaxError as e:
        # special handling for syntax errors, we just return
        # the expression string back as-is to support late evaluation
        display.warning('Unable to safely evaluate %r: %s' % (expr, e))
        if include_exceptions:
            return (expr, None)
        return expr
    except Exception as e:
        display.warning('Unable to safely evaluate %r: %s' % (expr, e))
        if include_exceptions:
            return (expr, e)
        return expr
