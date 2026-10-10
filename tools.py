import ast
import math
import operator
import datetime

# ---------- Tool 1: Safe calculator ----------
_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub,
    ast.Mult: operator.mul, ast.Div: operator.truediv,
    ast.Pow: operator.pow, ast.USub: operator.neg,
}

def _eval(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.operand))
    raise ValueError("Unsupported expression")

def calculator(expression: str) -> str:
    """Evaluate a math expression like '(25*4)/3'."""
    try:
        tree = ast.parse(expression, mode="eval")
        return str(_eval(tree.body))
    except Exception as e:
        return f"Error: {e}"

# ---------- Tool 2: Shaft shear stress ----------
def shaft_shear_stress(torque_Nm: float, diameter_mm: float) -> str:
    """Max shear stress in a solid circular shaft: tau = 16T / (pi d^3)."""
    try:
        d = float(diameter_mm) / 1000
        tau_pa = 16 * float(torque_Nm) / (math.pi * d ** 3)
        return f"{tau_pa / 1e6:.2f} MPa"
    except Exception as e:
        return f"Error: {e}"

# ---------- Tool 3: Unit converter ----------
_CONVERSIONS = {
    ("mpa", "psi"): 145.038, ("psi", "mpa"): 1 / 145.038,
    ("n", "kgf"): 0.101972, ("kgf", "n"): 9.80665,
    ("mm", "inch"): 1 / 25.4, ("inch", "mm"): 25.4,
    ("kw", "hp"): 1.34102, ("hp", "kw"): 0.745700,
}

def unit_convert(value: float, from_unit: str, to_unit: str) -> str:
    key = (from_unit.lower(), to_unit.lower())
    if key not in _CONVERSIONS:
        return f"Unsupported conversion. Supported: {sorted(set(k[0] for k in _CONVERSIONS))}"
    return f"{float(value) * _CONVERSIONS[key]:.4f} {to_unit}"

# ---------- Tool 4: Current time ----------
def current_time() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ---------- Tool 5 & 6: Memory (notes file) ----------
def save_note(text: str) -> str:
    with open("notes.txt", "a", encoding="utf-8") as f:
        f.write(text + "\n")
    return "Note saved."

def read_notes() -> str:
    try:
        with open("notes.txt", "r", encoding="utf-8") as f:
            return f.read() or "No notes yet."
    except FileNotFoundError:
        return "No notes yet."

# ---------- Registry: name -> (function, description) ----------
TOOLS = {
    "calculator": (calculator, 'Evaluate math. Input: {"expression": "2*(3+4)"}'),
    "shaft_shear_stress": (shaft_shear_stress, 'Input: {"torque_Nm": 500, "diameter_mm": 40}'),
    "unit_convert": (unit_convert, 'Input: {"value": 10, "from_unit": "MPa", "to_unit": "psi"}'),
    "current_time": (current_time, "No input needed: {}"),
    "save_note": (save_note, 'Input: {"text": "something to remember"}'),
    "read_notes": (read_notes, "No input needed: {}"),
}