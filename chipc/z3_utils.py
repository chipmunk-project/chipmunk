import re

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
    assert z3.is_quantifier(formula), ('Formula is not a quantifier:\n',
                                       formula)
    var_names = [formula.var_name(i) for i in range(formula.num_vars())]
    vs = [z3.Int(n) for n in var_names]

    # Here simply doing z3.Not(formula.body()) doesn't work. formula.body()
    # returns an expression without any bounded variable, i.e., it refers
    # variables using indices in the order they appear instead of its names,
    # Var(0), Var(1), Var(2). Thus, we have to re-bind the variables using
    # substitute_vars. It is also necessary to reverse the list of variables.
    # See https://github.com/Z3Prover/z3/issues/402 for more details.
    return z3.Not(z3.substitute_vars(formula.body(), *reversed(vs)))


def generate_counterexamples(formula):
    """Given a z3 formula generated from a sketch, returns counterexample
    values for the formula.

    Returns:
        A tuple of two dicts from string to ints, where the first one
        represents counterexamples for packet variables and the second for
        state group variables.
    """
    # We negate the body of formula, and check whether the new formula is
    # satisfiable. If so, we extract the input values and they are
    # counterexamples for the original formula. Otherwise, the original formula
    # is satisfiable and there is no counterexample.
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


def check_sort(z3_var):
    assert (z3.is_bool(z3_var) or z3.is_int(z3_var)),\
        str(z3_var) + ' has unsupported type ' + str(type(z3_var))


def make_int(z3_var):
    if z3.is_bool(z3_var):
        return z3.If(z3_var, 1, 0)
    else:
        return z3_var


def make_bool(z3_var):
    if z3.is_int(z3_var):
        # Use > 0 to convert int to bool as per BooleanNodes.h
        # in the SKETCH code base.
        return z3_var > 0
    else:
        return z3_var


def get_z3_formula(sketch_ir: str, input_bits: int) -> z3.QuantifierRef:
    """Given an intermediate representation of a sketch file and returns a z3
    formula corresponding to that IR with the specified input bits for source
    variables."""

    z3_vars = dict()
    z3_asserts = []
    z3_srcs = []
    for line in sketch_ir.splitlines():
        records = line.split()
        start = records[0]
        if (start in ['dag', 'TUPLE_DEF']):
            continue
        else:
            # common processing across all nodes
            output_var = '_n' + records[0]
            operation = records[2]
            if operation in ['NEG', 'NOT']:
                operand1 = z3_vars['_n' + records[4]]
                check_sort(operand1)
            elif operation in ['AND', 'OR', 'XOR', 'PLUS',
                               'TIMES', 'DIV', 'MOD', 'LT',
                               'EQ']:
                operand1 = z3_vars['_n' + records[4]]
                operand2 = z3_vars['_n' + records[5]]
                check_sort(operand1)
                check_sort(operand2)

            # node-specific processing
            if operation == 'ASSERT':
                z3_asserts += ['_n' + records[3]]
            elif operation == 'S':
                var_type = records[3]
                source_name = records[4]
                assert var_type == 'INT', ('Unexpected variable type found in \
                        sketch IR:', line)
                z3_vars[source_name] = z3.Int(source_name)
                z3_vars[output_var] = z3.Int(source_name)
                z3_srcs += [source_name]
            elif operation in ['NEG']:
                z3_vars[output_var] = -make_int(operand1)
            elif operation in ['NOT']:
                z3_vars[output_var] = z3.Not(make_bool(operand1))
            elif operation in [
                    'AND', 'OR', 'XOR', 'PLUS', 'TIMES', 'DIV', 'MOD', 'LT',
                    'EQ'
            ]:
                if operation == 'AND':
                    z3_vars[output_var] = z3.And(
                        make_bool(operand1), make_bool(operand2))
                elif operation == 'OR':
                    z3_vars[output_var] = z3.Or(
                        make_bool(operand1), make_bool(operand2))
                elif operation == 'XOR':
                    z3_vars[output_var] = z3.Xor(
                        make_bool(operand1), make_bool(operand2))
                elif operation == 'PLUS':
                    z3_vars[output_var] = make_int(
                        operand1) + make_int(operand2)
                elif operation == 'TIMES':
                    z3_vars[output_var] = make_int(
                        operand1) * make_int(operand2)
                elif operation == 'DIV':
                    z3_vars[output_var] = make_int(
                        operand1) / make_int(operand2)
                elif operation == 'MOD':
                    z3_vars[output_var] = make_int(
                        operand1) % make_int(operand2)
                elif operation == 'LT':
                    z3_vars[output_var] = make_int(
                        operand1) < make_int(operand2)
                elif operation == 'EQ':
                    z3_vars[output_var] = make_int(
                        operand1) == make_int(operand2)
                else:
                    assert False, ('Invalid operation', operation)
            # One can consider ARRACC and ARRASS as array access and
            # assignment. For more details please refer this sketchusers
            # mailing list thread.
            # https://lists.csail.mit.edu/pipermail/sketchusers/2019-August/000104.html
            elif operation in ['ARRACC']:
                predicate = make_bool((z3_vars['_n' + records[4]]))
                yes_val = z3_vars['_n' + records[7]]
                no_val = z3_vars['_n' + records[6]]
                z3_vars[output_var] = z3.If(predicate, yes_val, no_val)
            elif operation in ['ARRASS']:
                var_type = type(z3_vars['_n' + records[4]])
                if var_type == z3.BoolRef:
                    assert records[6] in ['0', '1']
                    cmp_constant = records[6] == '1'
                elif var_type == z3.ArithRef:
                    cmp_constant = int(records[6])
                else:
                    assert False, ('Variable type', var_type, 'not supported')
                predicate = z3_vars['_n' + records[4]] == cmp_constant
                yes_val = z3_vars['_n' + records[8]]
                no_val = z3_vars['_n' + records[7]]
                z3_vars[output_var] = z3.If(predicate, yes_val, no_val)
            elif operation in ['CONST']:
                var_type = records[3]
                if var_type == 'INT':
                    z3_vars[output_var] = z3.IntVal(int(records[4]))
                elif var_type == 'BOOL':
                    assert records[4] in ['0', '1']
                    z3_vars[output_var] = z3.BoolVal(records[4] == '1')
                else:
                    assert False, ('Constant type', var_type, 'not supported')
            else:
                assert False, ('Unknown operation:', line)

    # To handle cases where we don't have any assert or source variable, add
    # a dummy bool variable.
    constraints = z3.BoolVal(True)
    for var in z3_asserts:
        constraints = z3.And(constraints, z3_vars[var])

    variable_range = z3.BoolVal(True)
    for var in z3_srcs:
        variable_range = z3.And(
            variable_range,
            z3.And(0 <= z3_vars[var], z3_vars[var] < 2**input_bits))

    final_assert = z3.ForAll([z3_vars[x] for x in z3_srcs],
                             z3.Implies(variable_range, constraints))
    # We could use z3.simplify on the final assert, however that could result
    # in a formula that is oversimplified and doesn't have a QuantfierRef which
    # is expected from the negated_body() function above.
    return final_assert


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
