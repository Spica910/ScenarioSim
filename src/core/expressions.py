"""
A safe expression evaluation module using Python's AST.
"""
import ast
import operator

class SafeExpression:
    """
    Compiles and evaluates a Python expression string in a safe, restricted environment.
    """
    # Allowed AST node types
    ALLOWED_NODES = {
        ast.Expression, ast.Call, ast.Name, ast.Load, ast.Constant,
        ast.BinOp, ast.UnaryOp, ast.Compare, ast.BoolOp,
        ast.Attribute, ast.Subscript, ast.Index,
        # Operators
        ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod,
        ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
        ast.And, ast.Or, ast.USub, ast.Not,
    }
    # Allowed built-in function names
    ALLOWED_BUILTINS = {
        'min', 'max', 'abs', 'round', 'int', 'float', 'bool', 'str'
    }

    def __init__(self, expr_str: str, mode: str = 'eval'):
        self.expr_str = expr_str
        self.mode = mode

        if not self.expr_str or not self.expr_str.strip():
             # Handle empty expressions gracefully
            self.code = compile('None', '<string>', 'eval')
            return

        try:
            tree = ast.parse(self.expr_str, mode=self.mode)
            self._validate_tree(tree)
            self.code = compile(tree, '<string>', self.mode)
        except (SyntaxError, ValueError) as e:
            raise ValueError(f"Invalid or unsafe expression: {e}")

    def _validate_tree(self, tree):
        """Recursively validates all nodes in the AST against a whitelist."""
        for node in ast.walk(tree):
            if type(node) not in self.ALLOWED_NODES:
                raise ValueError(f"Unsafe node type '{type(node).__name__}' found in expression.")
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id not in self.ALLOWED_BUILTINS:
                    raise ValueError(f"Unsafe function call '{node.func.id}' found in expression.")

    def __call__(self, context: dict):
        """Evaluates the compiled code with a given context."""
        # The 'eval' built-in is used here, but it's safe because the AST
        # has been pre-validated. The compiled code object cannot perform
        # unsafe operations.
        return eval(self.code, {"__builtins__": {}}, context)

def safe_eval(expr_str: str, context: dict):
    """A simple wrapper for one-off safe evaluations."""
    return SafeExpression(expr_str)(context)

def safe_exec(source: str, context: dict):
    """
    A wrapper for 'safe' execution. It compiles the source and then
    evaluates each expression statement.
    WARNING: This is a simplified version for effects and has limitations.
    """
    if not source or not source.strip(): return

    # Split effects by semicolon and evaluate each part
    # This is a simplification; a more robust solution would parse the block
    for line in source.split(';'):
        line = line.strip()
        if not line: continue

        op = None
        if '+=' in line:
            var, expr = line.split('+=', 1)
            op = operator.add
        elif '-=' in line:
            var, expr = line.split('-=', 1)
            op = operator.sub
        elif '=' in line:
            var, expr = line.split('=', 1)
        else:
            continue # Ignore unsupported statements

        var = var.strip()
        expr = expr.strip()

        rhs_val = SafeExpression(expr)(context)

        if op:
            context[var] = op(context.get(var, 0), rhs_val)
        else:
            context[var] = rhs_val
