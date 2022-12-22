from typing import Optional


def set_globals_locals(globals, locals)->tuple[dict, Optional[dict]]:
	#if both are originally None
	#return caller's parent frame's globals and locals
	import sys
	# because of a Python bug https://bugs.python.org/issue21161 let's pass both as globals
	out=sys._getframe(1).f_locals
	if globals is None and locals is None:
		f=sys._getframe(2)
		return {**f.f_globals, **f.f_locals}, None
	else:
		pass
	return globals, locals


def evalz(s: str, globals=None, locals=None, escape_char=None)->str:
	globals, locals=set_globals_locals(globals, locals)

	if escape_char is None:
		escape_char=next(ch for ch in "%!@" if ch in s)

	parts=s.split(escape_char)
	result=[]
	for i in range(len(parts)):
		if i%2==0:
			result.append(parts[i])
		elif parts[i]=="": # %% → %
			result.append(escape_char)
		else:
			try:
				item=eval(parts[i], globals, locals)
			except:
				import sys
				print("Error while executing code ========\n"+ parts[i] + "\n========", file=sys.stderr)
				raise
			result.append(
					item if isinstance(item, str) else
					str(item) if isinstance(item, int) else
					__import__("sympy").latex(item)
					)
	return "".join(result)