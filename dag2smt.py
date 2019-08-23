#! /opt/local/bin/python3
import sys

import z3


class UnaryOp:
    def __init__(self, output, operand, operation):
        self.output = '_n' + output
        self.operand = '_n' + operand
        self.operation = operation

    def __str__(self):
        return self.output + ' = ' + self.operation + '(' + self.operand + ')'

    def __repr__(self):
        return self.__str__()


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
    def __init__(self, output, constant, var_type):
        self.output = '_n' + output
        self.constant = constant
        self.var_type = var_type

    def __str__(self):
        return self.output + ' = ' + self.constant + '\n'

    def __repr__(self):
        return self.__str__()


class Source:
    # _type instead of type to avoid conflict with python internal type()
    # function. The name is needed to keep track of original source variable
    # and provide counterexamples.
    def __init__(self, output, var_type, name):
        self.output = output
        self.var_type = var_type
        assert(var_type == 'INT')
        self.name = name

    def __str__(self):
        return self.output + ' = ' + self.name

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
unaryop_nodes = []
binop_nodes = []
cond_nodes = []
const_nodes = []

# Data structures to create z3 formula
z3_vars = []
z3_asserts = []

for line in sys.stdin.readlines():
    records = line.split()
    start = records[0]
    if (start in ['dag', 'TUPLE_DEF']):
        continue
    else:
        output_var = records[0]
        operation = records[2]
        var_type = records[3]
        if operation == 'ASSERT':
            asserts += ['_n' + records[3]]
        elif operation == 'S':
            src_nodes += [Source('_n' + output_var, var_type, records[4])]
        elif operation in ['NEG']:
            unaryop_nodes += [UnaryOp(output_var, records[4], operation)]
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
            const_nodes += [Const(output_var, records[4], var_type)]
        else:
            print('unknown operation: ', line)

# Now create z3 formula
# First create z3_vars
for node in src_nodes:
    z3_vars += [z3.Int(node.output)]
for node in binop_nodes:
    if (node.operation in ['PLUS', 'TIMES', 'DIV', 'MOD']):
        z3_vars += [z3.Int(node.output)]
    elif (node.operation in ['AND', 'OR', 'XOR', 'LT', 'EQ']):
        z3_vars += [z3.Bool(node.output)]
    else:
        assert(False), 'unknown binop node ' + node.operation
for node in unaryop_nodes:
    if (node.operation in ['NEG']):
        z3_vars += [z3.Int(node.output)]
    else:
        assert(False), "can't handle " + node.operation
for node in const_nodes:
    if (node.var_type == 'INT'):
        z3_vars += [z3.Int(node.output)]
    else:
        assert(node.var_type == 'BOOL')
        z3_vars += [z3.Bool(node.output)]

print('asserts:\n', asserts)
print('src_nodes:\n', src_nodes)
print('unaryop_nodes:\n', unaryop_nodes)
print('binop_nodes:\n', binop_nodes)
print('cond_nodes:\n', cond_nodes)
print('const_nodes:\n', const_nodes)
print('z3_vars:\n', z3_vars)
