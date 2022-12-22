#!/bin/python
from __future__ import annotations
import functools
from typing import Any, Callable, Sequence, Optional
from dataclasses import dataclass
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import ast
from pathlib import Path

#from .util import *
from util import evalz

from parse import parse_statement, parse_expr
exec("from pattern import *")  # TODO

formatter=get_ipython().display_formatter.formatters["text/plain"]  # type: ignore
formatter.for_type(ast.AST, 
		lambda obj, p, cycle: p.text(ast.dump(obj, indent=2) or "")
		)
import IPython


##


@dataclass
class O:
	prepare: str=""  # this part of code must be executed in advance. Global is okay. Idempotent.
	execute: str=""  # this part of code must be executed in advance, right next to the code itself
	expand: str=""  # after executing the 2 parts above this expands to the result
	def __add__(self, other: O)->O:
		return O(self.prepare+other.prepare, self.execute+other.execute, self.expand+other.expand)

	def __repr__(self)->str:
		return f"""
======== prepare ========
{self.prepare}
======== execute ========
{self.execute}
======== expand ========
{self.expand}
================
"""









pattern_replace_mutable(
	to_pattern_mutable(parse_expr("_last-1")), 
	{"last": parse_expr("1+2-1")}
	)


# ======== end pattern-matching part


def as_name(node: Any)->ast.Name:
	assert isinstance(node, ast.Name)
	return node

def TeXify_var(name: str)->str:
	"""
	return TeX identifier name without backslash.
	"""
	return "my__" + name


TeXify_type={"int": "int", "float": "fp", "str": "str"}.__getitem__



ReplaceList=list[tuple[Pattern, Callable[[Matching], Any]]]


@dataclass
class State:
	pass


# *args can optionally be state
def try_replace_all(replace_list: ReplaceList, node: ast.AST, *args)->Any:
	for pattern, replacement in replace_list:
		matching=pattern_match(pattern, node)
		if matching is not None: return replacement(matching, *args)
	assert False, (node, print(ast.dump(node, indent=2)))


int_replacements: ReplaceList=[
		(
			to_pattern_mutable(parse_expr("_a+_b")),
			lambda matching: f'{parse_int_wrapped(matching["a"])}+{parse_int_wrapped(matching["b"])}'
			),
		(
			to_pattern_mutable(parse_expr("_a-_b")),
			lambda matching: f'{parse_int_wrapped(matching["a"])}-{parse_int_wrapped(matching["b"])}'
			),
		(
			to_pattern_mutable(parse_expr("_a*_b")),
			lambda matching: f'{parse_int_wrapped(matching["a"])}*{parse_int_wrapped(matching["b"])}'
			),
		(
			#this one is actually not the same thing as Python //, it rounds (see \int_eval)
			to_pattern_mutable(parse_expr("_a//_b")),
			lambda matching: f'{parse_int_wrapped(matching["a"])}/{parse_int_wrapped(matching["b"])}'
			),
		(
			ast.Constant(value=Blank("value")),
			lambda matching: str(matching["value"])
			)
		]

def parse_int(node: ast.expr)->str:
	return try_replace_all(int_replacements, node)


def parse_int_wrapped(node: ast.expr)->str:
	return "("+parse_int(node)+")"



global_context_replacements: ReplaceList=[
	(
		to_pattern_mutable(parse_statement("_var: _type=_value")),
		lambda matching, state:
		O(
			execute=evalz(r'\%TeXify_type(matching["type"].id)%_set:Nn \%TeXify_var(matching["var"].id)% '
				r'{% parse_int(matching["value"]) %}'))
		),
	(
		to_pattern_mutable(parse_statement("print(_var)")),
		lambda matching, state:
		O(
				execute=evalz(
					r'\tl_show:N \%TeXify_var(as_name(matching["var"]).id)%'
				)
				)
		),
	(
		to_pattern_mutable(parse_statement("for _var in range(_first, _last): _body")),
		lambda matching, state: (
		(lambda matching, body:
			O(
					prepare=body.prepare,
					execute=
						evalz(
					r'\int_step_inline:nnn'
						r'''{%parse_int(matching["first"])%}'''
						r'''{%parse_int(
							pattern_replace_mutable(to_pattern_mutable(parse_expr("_last-1")), matching)
							)%}'''
						r'''{%body.execute+body.expand%}'''
					)
					)
			)(matching=matching, body=compile_body(matching["body"], state))
		)
		),
	]

# parses a "normal" statement node such as a+=1
def compile_statement_global_context(node, state):
	return try_replace_all(global_context_replacements, node, state)


def compile_body(body: Sequence[ast.AST], state: State)->O:
	result=O()
	for node in body:
		result+=compile_statement_global_context(node, state)
	return result


file="../examples/main.py"
tree=ast.parse(Path(file).read_text())
try:
	print(compile_body(tree.body, State()))
except: import traceback; traceback.print_exc()


##

def main():
	parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
	parser.add_argument("file")
	args=parser.parse_args()

	file=args.file

	file="../examples/main.py"
	tree=ast.parse(Path(file).read_text())

	



if __name__=="__main__":
	main()
