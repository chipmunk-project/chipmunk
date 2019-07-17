from aluParser import aluParser
from aluVisitor import aluVisitor


class ALUVisitor(aluVisitor):
    def __init__(self, instruction_file):
        self.instruction_file = instruction_file
        self.alu_name = 'aatish_alu'  # temp
        self.num_state_slots = 0
        self.mux3_count = 0
        self.mux2_count = 0
        self.relop_count = 0
        self.arithop_count = 0
        self.opt_count = 0
        self.constant_count = 0
        self.helper_function_strings = '\n\n\n'
        self.alu_args = dict()
        self.global_holes = dict()
        self.main_function = ''

    # Copied From Taegyun's code
    def add_hole(self, hole_name, hole_width):
        prefixed_hole = self.alu_name + '_' + hole_name
        assert (prefixed_hole + '_global' not in self.global_holes)
        self.global_holes[prefixed_hole + '_global'] = hole_width
        assert (hole_name not in self.alu_args)
        self.alu_args[hole_name] = hole_width

    def visitAlu(self, ctx):
        self.main_function += ('|StateGroup|' + self.alu_name +
                               '(ref |StateGroup| state_group, ')

        self.visit(ctx.getChild(0, aluParser.Packet_fieldsContext))

        self.visit(ctx.getChild(0, aluParser.State_varsContext))

        self.main_function += \
            ', %s) {\n |StateGroup| old_state_group = state_group;'

        self.visit(ctx.getChild(0, aluParser.Alu_bodyContext))

        for slot in range(self.num_state_slots):
            self.main_function += '\nstate_group.state_' + str(
                slot) + ' = state_' + str(slot) + ';'
            self.main_function += '\nreturn old_state_group;\n}'
        argument_string = ','.join(
            ['int ' + hole for hole in sorted(self.alu_args)])
        self.main_function = self.main_function % argument_string

    def visitPacket_fields(self, ctx):
        self.main_function += 'int '
        self.main_function += ctx.getChild(
            0, aluParser.Packet_fieldContext).getText() + ','
        self.num_packet_fields = 1
        if (ctx.getChildCount() > 6):
            for i in range(5, ctx.getChildCount() - 1):
                print(i)
                self.visit(ctx.getChild(i))
                self.num_packet_fields += 1
        self.main_function = self.main_function[:-1]  # Trim out the last comma

    def visitPacket_field_with_comma(self, ctx):
        self.main_function += 'int '
        assert (ctx.getChild(0).getText() == ',')
        self.main_function += ctx.getChild(1).getText() + ','

    def visitState_vars(self, ctx):
        self.num_state_slots = ctx.getChildCount() - 5

    def visitState_indicator(self, ctx):
        print(ctx.getChildCount())
        print(ctx.getChild(0))

    def visitReturn_statement(self, ctx):
        # Stateful ALU's dont have return statements
        assert(ctx.getChildCount() == 0)

    def visitAlu_body(self, ctx):
        if (ctx.getChildCount() == 1):  # simple update
            self.visit(ctx.getChild(0))
        else:  # if-elif-else update
            self.main_function += 'if ('
            self.visit(ctx.if_guard)
            self.main_function += ') {'
            self.visit(ctx.if_body)
            self.main_function += '}'

            # if there is an elif
            if (ctx.getChildCount() > 7
                    and ctx.getChild(7).getText() == 'elif'):
                self.main_function += 'else if ('
                self.visit(ctx.elif_guard)
                self.main_function += ') {'
                self.visit(ctx.elif_body)
                self.main_function += '}'

            # if there is an else
            if ((ctx.getChildCount() > 7
                 and ctx.getChild(7).getText() == 'else')
                    or (ctx.getChildCount() > 14
                        and ctx.getChild(14).getText() == 'else')):
                self.main_function += 'else {'
                self.visit(ctx.else_body)
                self.main_function += '}'

    def visitUpdates(self, ctx):
        self.visitChildren(ctx)

    def visitUpdate(self, ctx):
        self.main_function += ctx.getChild(0).getText() + ' = '
        self.visit(ctx.getChild(2))
        self.main_function += ';'

    def visitState_var(self, ctx):
        self.main_function += ctx.getChild(0).getText()

    # def visitRelOp(self, ctx):
    #     self.main_function += self.alu_name + '_rel_op('
    #     self.visit(ctx.getChild(2))
    #     self.main_function += ','
    #     self.visit(ctx.getChild(4))
    #     self.main_function += ')'

    def visitMux3(self, ctx):
        self.main_function += self.alu_name + '_Mux3('
        self.visit(ctx.getChild(0, aluParser.ExprContext))
        self.main_function += ','
        self.visit(ctx.getChild(1, aluParser.ExprContext))
        self.main_function += ','
        self.visit(ctx.getChild(2, aluParser.ExprContext))
        self.main_function += ')'
        self.generateMux3()
        self.mux3_count += 1

    def visitMux2(self, ctx):
        self.main_function += self.alu_name + '_Mux2('
        self.visit(ctx.getChild(0, aluParser.ExprContext))
        self.main_function += ','
        self.visit(ctx.getChild(1, aluParser.ExprContext))
        self.main_function += ')'
        self.generateMux2()
        self.mux2_count += 1

    def visitRelOp(self, ctx):
        self.main_function += self.alu_name + '_' + 'rel_op_' + str(
            self.relop_count) + '('
        self.visit(ctx.getChild(0, aluParser.ExprContext))
        self.main_function += ','
        self.visit(ctx.getChild(1, aluParser.ExprContext))
        self.main_function += ',' + 'rel_op_' + \
            str(self.relop_count) + ') == 1'
        self.generateRelOp()
        self.relop_count += 1

    def visitOpt(self, ctx):
        self.main_function += self.alu_name + '_' + 'Opt_' + str(
            self.opt_count) + '('
        self.visitChildren(ctx)
        self.main_function += ',' + 'Opt_' + str(self.opt_count) + ')'
        self.generateOpt()
        self.opt_count += 1

    def visitConstant(self, ctx):
        self.main_function += self.alu_name + '_' + 'C_' + str(
            self.constant_count) + '('
        self.main_function += 'const_' + str(self.constant_count) + ')'
        self.generateConstant()
        self.constant_count += 1

    def generateMux3(self):
        self.helper_function_strings += 'int ' + self.alu_name + '_' + \
            'Mux3_' + str(self.mux3_count) + \
            """(int op1, int op2, int op3, int choice) {
    if (choice == 0) return op1;
    else if (choice == 1) return op2;
    else return op3;
    } \n\n"""
        self.add_hole('Mux3_' + str(self.mux3_count), 2)

    def generateMux2(self):
        self.helper_function_strings += 'int ' + self.alu_name + '_' + \
            'Mux2_' + str(self.mux2_count) + \
            """(int op1, int op2, int choice) {
    if (choice == 0) return op1;
    else return op2;
    } \n\n"""
        self.add_hole('Mux2_' + str(self.mux2_count), 1)

    def generateConstant(self):
        self.helper_function_strings += 'int ' + self.alu_name + '_' + \
            'C_' + str(self.constCount) + """(int const) {
    return const;
    }\n\n"""
        self.add_hole('const_' + str(self.constCount), 2)

    def generateRelOp(self):
        self.helper_function_strings += 'int ' + self.alu_name + '_' + \
            'rel_op_' + str(self.relop_count) + \
            """(int operand1, int operand2, int opcode) {
    if (opcode == 0) {
      return (operand1 != operand2) ? 1 : 0;
    } else if (opcode == 1) {
      return (operand1 < operand2) ? 1 : 0;
    } else if (opcode == 2) {
      return (operand1 > operand2) ? 1 : 0;
    } else {
      return (operand1 == operand2) ? 1 : 0;
    }
    } \n\n"""
        self.add_hole('rel_op_' + str(self.relop_count), 2)

    def generateArithOp(self):
        self.helper_function_strings += 'int ' + self.alu_name + '_' + \
            'arith_op_' + str(self.arithop_count) + \
            """(int operand1, int operand2, int opcode) {
    if (opcode == 0) {
      return operand1 + operand2;
    } else {
      return operand1 - operand2;
    }
    }\n\n"""
        self.add_hole('arith_op_' + str(self.arithop_count), 1)

    def generateOpt(self):
        self.helper_function_strings += 'int ' + self.alu_name + '_' + \
            'Opt_' + str(self.opt_count) + """(int op1, int enable) {
    if (enable != 0) return 0;
    return op1;
    } \n\n"""
        self.add_hole('Opt_' + str(self.opt_count), 1)
