import z3

z3.set_param(proof=True)
z3.set_param(unsat_core=True)
formula = z3.parse_smt2_file("cexgen.smt2")[0]

var_names = [formula.var_name(i) for i in range(0, formula.num_vars())]

f_str = str(formula)
implies_str = f_str[f_str.index("Implies"):]

var_names.sort(key=lambda c: implies_str.index(c))

print(var_names)

variables = [z3.Int(n) for n in var_names]

impl = formula.body()
print(impl)

new_f = z3.Not(z3.substitute_vars(impl, *variables))

z3_slv = z3.Solver()
z3_slv.add(new_f)
print(z3_slv.check())
print(z3_slv.model())
