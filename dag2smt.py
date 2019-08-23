#! /opt/local/bin/python3
import sys


class BinOp:
    def __init__(self, output, operand1, operand2, operation):
        self.output = '_n' + output
        self.operand1 = '_n' + operand1
        self.operand2 = '_n' + operand2
        self.operation = operation

    def __str__(self):
        return self.output + ' = ' + self.operation + '(' + \
            self.operand1 + ',' + self.operand2 + ')\n'

    def __repr__(self):
        return self.__str__()


class CondOp:
    def __init__(self, output, predicate, yes_val, no_val):
        self.output = '_n' + output
        self.predicate = predicate
        self.yes_val = '_n' + yes_val
        self.no_val = '_n' + no_val

    def __str__(self):
        return self.output + ' = ' + self.predicate + ' ? ' + \
            self.yes_val + ' : ' + self.no_val + '\n'

    def __repr__(self):
        return self.__str__()


class Const:
    def __init__(self, output, constant):
        self.output = '_n' + output
        self.constant = constant

    def __str__(self):
        return self.output + ' = ' + self.constant + '\n'

    def __repr__(self):
        return self.__str__()

# borrowed from getSMTnode in BooleanNodes.h
# bool to int conversion routines


def bool_to_int(variable):
    return ' (ite ' + variable + ' 1 0 )'


def int_to_bool(variable):
    return ' (ite (> ' + variable + ' 0) true false)'


asserts = []
src_nodes = []
binop_nodes = []
cond_nodes = []
const_nodes = []

for line in sys.stdin.readlines():
    records = line.split()
    start = records[0]
    if (start in ['dag', 'TUPLE_DEF']):
        continue
    else:
        operation = records[2]
        output_var = records[0]
        if operation == 'ASSERT':
            asserts += ['_n' + records[3]]
        elif operation == 'S':
            src_nodes += ['_n' + output_var]
        elif operation in ['AND', 'OR', 'XOR', 'PLUS',
                           'TIMES', 'DIV', 'MOD', 'LT', 'EQ']:
            binop_nodes += [BinOp(output_var, records[4],
                                  records[5], operation)]
        elif operation in ['ARRACC']:
            cond_nodes += [CondOp(output_var, '_n' + records[4],
                                  records[7], records[6])]
        elif operation in ['ARRASS']:
            cond_nodes += [CondOp(output_var, '_n' + records[4] +
                                  ' == ' + records[6], records[8],
                                  records[7])]
        elif operation in ['CONST']:
            const_nodes += [Const(output_var, records[4])]
        else:
            print('unknown operation: ', line)

print('asserts:\n', asserts)
print('src_nodes:\n', src_nodes)
print('binop_nodes:\n', binop_nodes)
print('cond_nodes:\n', cond_nodes)
print('const_nodes:\n', const_nodes)
