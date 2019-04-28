import re

import z3

z3.set_param(proof=True)
z3.set_param(unsat_core=True)
formula = z3.parse_smt2_file("cexgen.smt2")[0]

var_names = [formula.var_name(i) for i in range(0, formula.num_vars())]

# f_str = str(formula)
# implies_str = f_str[f_str.index("Implies"):]
#
# var_names.sort(key=lambda c: implies_str.index(c))
#
# print(var_names)

variables = [z3.Int(n) for n in var_names]

impl = formula.body()

new_f = z3.substitute_vars(impl, *reversed(variables))

print(new_f)
print(formula)

for l in str(new_f).split("\n"):
    assert l in str(formula)

new_f = z3.Not(new_f)


z3_slv = z3.Solver()
z3_slv.add(new_f)

pkt_vars = {}
state_vars = {}

result = z3_slv.check()

model = z3_slv.model()
for var in model.decls():
    var_str = re.sub(r"_\d+_\d+_\d+$", "", var.name(), count=1)
    value = model.get_interp(var).as_long()
    if var_str.startswith("pkt_"):
        pkt_vars[var_str] = value
    elif var_str.startswith("state_group_"):
        state_vars[var_str] = value

for i, (k, v) in enumerate(pkt_vars.items()):
    print(i, k, v)

print(pkt_vars, state_vars)
