#! /opt/local/bin/python3
import sys

from z3 import And
from z3 import BoolVal
from z3 import If
from z3 import Int
from z3 import IntVal
from z3 import Or
from z3 import Solver
from z3 import Xor

# Data structures to hold z3 variables and asserts
z3_vars = dict()
z3_asserts = []

for line in sys.stdin.readlines():
    records = line.split()
    start = records[0]
    if (start in ['dag', 'TUPLE_DEF']):
        continue
    else:
        output_var = '_n' + records[0]
        operation = records[2]
        if operation == 'ASSERT':
            z3_asserts += ['_n' + records[3]]
        elif operation == 'S':
            var_type = records[3]
            assert(var_type == 'INT')
            z3_vars[output_var] = Int(output_var)
        elif operation in ['NEG']:
            z3_vars[output_var] = - z3_vars['_n' + records[4]]
        elif operation in ['AND', 'OR', 'XOR', 'PLUS',
                           'TIMES', 'DIV', 'MOD', 'LT', 'EQ']:
            op1 = '_n' + records[4]
            op2 = '_n' + records[5]
            if operation == 'AND':
                z3_vars[output_var] = And(op1, op2)
            elif operation == 'OR':
                z3_vars[output_var] = Or(op1, op2)
            elif operation == 'XOR':
                z3_vars[output_var] = Xor(op1, op2)
            elif operation == 'PLUS':
                z3_vars[output_var] = z3_vars[op1] + z3_vars[op2]
            elif operation == 'TIMES':
                z3_vars[output_var] = z3_vars[op1] * z3_vars[op2]
            elif operation == 'DIV':
                z3_vars[output_var] = z3_vars[op1] / z3_vars[op2]
            elif operation == 'MOD':
                z3_vars[output_var] = z3_vars[op1] % z3_vars[op2]
            elif operation == 'LT':
                z3_vars[output_var] = z3_vars[op1] < z3_vars[op2]
            elif operation == 'EQ':
                z3_vars[output_var] = z3_vars[op1] == z3_vars[op2]
            else:
                assert(False)
        elif operation in ['ARRACC']:
            z3_vars[output_var] = If(z3_vars['_n' + records[4]],
                                     z3_vars['_n' + records[7]],
                                     z3_vars['_n' + records[6]])
        elif operation in ['ARRASS']:
            z3_vars[output_var] = If(z3_vars['_n' + records[4]] ==
                                     z3_vars['_n' + records[6]],
                                     z3_vars['_n' + records[8]],
                                     z3_vars['_n' + records[7]])
        elif operation in ['CONST']:
            var_type = records[3]
            if var_type == 'INT':
                z3_vars[output_var] = IntVal(int(records[4]))
            elif var_type == 'BOOL':
                z3_vars[output_var] = BoolVal(bool(records[4]))
            else:
                assert(False)
        else:
            print('unknown operation: ', line)

solver = Solver()
for constraint in z3_asserts:
    solver.add(z3_vars[constraint])
print(solver.check())