import re
import sys

import z3


def parse_smt2_file(smt2_filename):
    """Reads a smt2 file and returns the first formula.

    Args:
        smt2_filename: smt2 file that was generated from Sketch.

    Raises:
        An assertion if the original smt2 file didn't contain any assert
        statements.
    """
    # parse_smt2_file returns a vector of ASTs, and each element corresponds to
    # one assert statement in the original file. The smt2 file generated by
    # sketch only has one assertions, simply take the first.
    formulas = z3.parse_smt2_file(smt2_filename)
    assert len(formulas) == 1, (smt2_filename,
                                'contains 0 or more than 1 asserts.')
    return formulas[0]


def negated_body(formula):
    """Given a z3.QuantiferRef formula with z3.Int variables,
    return negation of the body.

    Returns:
        A z3.BoolRef which is the negation of the formula body.
    """
    assert z3.is_quantifier(
        formula), ('Formula is not a quantifier:\n', formula)
    var_names = [formula.var_name(i) for i in range(formula.num_vars())]
    vs = [z3.Int(n) for n in var_names]
    return z3.Not(z3.substitute_vars(formula.body(), *reversed(vs)))


def generate_counter_examples(smt2_filename):
    """Given a smt2 file that was generated from sketch, returns counterexample
    values for input packet fields and state group variables.

    Returns:
        A tuple of two dicts from string to ints, where the first one
        represents counterexamples for packet variables and the second for
        state group variables.
    """
    formula = parse_smt2_file(smt2_filename)
    new_formula = negated_body(formula)

    z3_slv = z3.Solver()
    z3_slv.set(proof=True, unsat_core=True)
    z3_slv.add(new_formula)

    pkt_fields = {}
    state_vars = {}

    result = z3_slv.check()
    if result != z3.sat:
        print('Failed to generate counterexamples, z3 returned', result)
        return (pkt_fields, state_vars)

    model = z3_slv.model()
    for var in model.decls():
        value = model.get_interp(var).as_long()
        match_object = re.match(r'pkt_\d+', var.name())
        if match_object:
            var_name = match_object.group(0)
            pkt_fields[var_name] = value
            continue

        match_object = re.match(r'state_group_\d+_state_\d+', var.name())
        if match_object:
            var_name = match_object.group(0)
            state_vars[var_name] = value

    return (pkt_fields, state_vars)


def get_z3_formula(sketch_ir, verify_bit_width):
    """Given an intermediate representation of a sketch file, returns a z3
    formula corresponding to that."""

    z3_vars = dict()
    z3_asserts = []
    z3_srcs = []

    for line in sketch_ir.splitlines():
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
                assert var_type == 'INT', ('Unexpected variable type found in \
                        sketch IR:', line)
                z3_vars[output_var] = z3.Int(output_var)
                z3_srcs += [output_var]
            elif operation in ['NEG']:
                z3_vars[output_var] = - z3_vars['_n' + records[4]]
            elif operation in ['NOT']:
                z3_vars[output_var] = z3.Not(z3_vars['_n' + records[4]])
            elif operation in ['AND', 'OR', 'XOR', 'PLUS',
                               'TIMES', 'DIV', 'MOD', 'LT', 'EQ']:
                op1 = '_n' + records[4]
                op2 = '_n' + records[5]
                if operation == 'AND':
                    z3_vars[output_var] = z3.And(op1, op2)
                elif operation == 'OR':
                    z3_vars[output_var] = z3.Or(op1, op2)
                elif operation == 'XOR':
                    z3_vars[output_var] = z3.Xor(op1, op2)
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
                    assert False, ('Invalid operation', operation)

            elif operation in ['ARRACC']:
                z3_vars[output_var] = z3.If(z3_vars['_n' + records[4]],
                                            z3_vars['_n' + records[7]],
                                            z3_vars['_n' + records[6]])
            elif operation in ['ARRASS']:
                var_type = z3_vars['_n' + records[4]]
                if var_type == z3.BoolRef:
                    assert(records[6] in ['0', '1'])
                    cmp_constant = records[6] == '1'
                elif var_type == z3.ArithRef:
                    cmp_constant = int(records[6])
                else:
                    assert False, ('Variable type', var_type, 'not supported')
                z3_vars[output_var] = z3.If(z3_vars['_n' + records[4]] ==
                                            cmp_constant,
                                            z3_vars['_n' + records[8]],
                                            z3_vars['_n' + records[7]])
            elif operation in ['CONST']:
                var_type = records[3]
                if var_type == 'INT':
                    z3_vars[output_var] = z3.IntVal(int(records[4]))
                elif var_type == 'BOOL':
                    assert(records[4] in ['0', '1'])
                    z3_vars[output_var] = z3.BoolVal(records[4] == '1')
                else:
                    assert False, ('Constant type', var_type, 'not supported')
            else:
                assert False, ('Unknown operation:', line)

    # for var in z3_vars:
    #     print(var, ' = ', z3_vars[var])

    constraints = z3.BoolVal(True)
    for var in z3_asserts:
        constraints = z3.And(constraints, z3_vars[var])

    variable_range = z3.BoolVal(True)
    for var in z3_srcs:
        variable_range = z3.And(variable_range, z3.And(
            0 <= z3_vars[var], z3_vars[var] < 2**verify_bit_width))
    final_assert = z3.ForAll([z3_vars[x] for x in z3_srcs],
                             z3.Implies(variable_range, constraints))
    return z3.simplify(final_assert)


def simple_check(smt2_filename):
    """Given a smt2 file generated from a sketch, parses assertion from the
    file and checks with z3. We assume that the file already has input bit
    ranges defined by sketch.

    Returns:
        True if satisfiable else False.
    """
    formula = parse_smt2_file(smt2_filename)

    # The original formula's body is comprised of Implies(A, B) where A
    # specifies range of input variables and where B is a condition. We're
    # interested to check whether B is True within the range specified by A

    z3_slv = z3.Solver()
    z3_slv.add(formula)

    return z3_slv.check() == z3.sat
