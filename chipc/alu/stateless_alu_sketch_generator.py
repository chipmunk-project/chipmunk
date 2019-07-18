from textwrap import dedent

from aluParser import aluParser
from aluVisitor import aluVisitor
from overrides import overrides
#from chipc.aluParser import aluParser
#from chipc.aluVisitor import aluVisitor


class StatelessAluSketchGenerator (aluVisitor):
    def __init__(self, stateless_alu_file, stateless_alu_name):
        self.stateless_alu_name = stateless_alu_name
        self.stateless_alu_file = stateless_alu_file
        self.mux3Count = 0
        self.mux2Count = 0
        self.relopCount = 0
        self.arithopCount = 0
        self.optCount = 0
        self.constCount = 0
        self.helperFunctionStrings = '\n\n\n'
        self.globalholes = dict()
        self.stateless_alu_args = dict()
        self.mainFunction = ''
        self.num_packet_fields = 0
        # no num_state_slots

    def add_hole(self, hole_name, hole_width):
        prefixed_hole = self.stateless_alu_name + '-' + hole_name
        assert (prefixed_hole + '_global' not in self.globalholes)
        self.globalholes[prefixed_hole + '_global'] = hole_width
        assert (hole_name not in self.stateless_alu_args)
        self.stateless_alu_args[hole_name] = hole_width

    @overrides
    def visitAlu(self, ctx):

        self.visit(ctx.getChild(0, aluParser.State_indicatorContext))
        self.visit(ctx.getChild(0, aluParser.State_varsContext))

        self.mainFunction += 'int ' + self.stateless_alu_name + '('
        self.visit(ctx.getChild(0, aluParser.Packet_fieldsContext))
        self.visit(ctx.getChild(0, aluParser.Hole_varsContext))
        self.mainFunction += ' ){\n'
        self.visit(ctx.getChild(0, aluParser.Alu_bodyContext))
        self.mainFunction += '\n}'

    @overrides
    def visitState_indicator(self, ctx):

        try:
            assert ctx.getChildCount() == 3, 'Error: invalid state indicator argument provided for type. Insert \'stateful\' or \'stateless\''
            assert ctx.getChild(2).getText() == 'stateless', 'Error: type is declared as ' + \
                ctx.getChild(2).getText() + \
                ' and not \'stateless\' for stateless ALU '
        except AssertionError as e:
            raise

    @overrides
    def visitState_var(self, ctx):
        # TODO: When state_var is listed first in expr in
        # grammar file, hole_var and packet_field get
        # labeled as state_var. This is when there are
        # no state vars described
        self.mainFunction += ctx.getText()

    @overrides
    def visitState_vars(self, ctx):
        try:
            assert ctx.getChildCount() == 5, 'Error: state variables given to stateless ALU'
        except AssertionError as e:
            raise

    @overrides
    def visitState_var_with_comma(self, ctx):
        pass

    @overrides
    def visitHoleVar(self, ctx):
        self.mainFunction += ctx.getText()

    @overrides
    def visitHole_var(self, ctx):
        self.mainFunction += ctx.getText()

    @overrides
    def visitHole_vars(self, ctx):
        # Empty set of hole vars
        if (ctx.getChildCount() == 5):
            return
        self.mainFunction += 'int '
        self.mainFunction += ctx.getChild(4).getText() + ','
        if (ctx.getChildCount() > 5):
            for i in range(5, ctx.getChildCount()-1):
                pass
                self.visit(ctx.getChild(i))
        self.mainFunction = self.mainFunction[:-1]  # Trim out the last comma

    def visitHole_var_with_comma(self, ctx):
        assert (ctx.getChild(0).getText() == ',')
        self.mainFunction += ctx.getChild(1).getText() + ','

    @overrides
    def visitPacketField(self, ctx):
        self.mainFunction += ctx.getText()

    @overrides
    def visitPacket_field(self, ctx):
        self.mainFunction += ctx.getText()

    @overrides
    def visitPacket_fields(self, ctx):
        # Empty set of packet fields
        if (ctx.getChildCount() == 5):
            return
        self.mainFunction += 'int '
        self.mainFunction += ctx.getChild(4).getText() + ','
        self.num_packet_fields = 1
        if (ctx.getChildCount() > 1):
            for i in range(5, ctx.getChildCount()):
                self.visit(ctx.getChild(i))
                self.num_packet_fields += 1
        self.mainFunction = self.mainFunction[:-1]  # Trim out the last comma

    @overrides
    def visitPacket_field_with_comma(self, ctx):
        assert (ctx.getChild(0).getText() == ',')
        self.mainFunction += ctx.getChild(1).getText() + ','

    @overrides
    def visitAlu_body(self, ctx):
        if (ctx.getChildCount() == 1 and ctx.alu_update != None):  # simple update
            self.visit(ctx.alu_update)
        elif (ctx.getChildCount() == 1 and ctx.return_update != None):

            self.visit(ctx.return_update)
        else:  # if-elif-else update
            self.mainFunction += 'if ('
            self.visit(ctx.if_guard)
            self.mainFunction += ') {'
            print(ctx.if_body.getText())

            self.visit(ctx.if_body)
            self.mainFunction += '}'
            # if there is an elif
            count = 0
#            for c in ctx.getChildren():
#                print (count, ' : ',c.getText())
#                count+=1
            elif_index = 7
            alu_index = 0
            while (ctx.getChildCount() > elif_index and ctx.getChild(elif_index).getText() == 'elif'):

                self.mainFunction += 'else if ('
                self.visit(ctx.getChild(elif_index+2))
                self.mainFunction += ') {'
                self.visit(ctx.getChild(elif_index+5))

                self.mainFunction += '}'
                elif_index += 7

            # if there is an else
            if (ctx.getChildCount() > elif_index and ctx.getChild(elif_index).getText() == 'else'):
                self.mainFunction += 'else {'
                self.visit(ctx.else_body)
                self.mainFunction += '}'

    @overrides
    def visitNested(self, ctx):
        self.visit(ctx.getChild(0, aluParser.GuardContext))
        self.mainFunction += ctx.getChild(1).getText()
        self.visit(ctx.getChild(1, aluParser.GuardContext))

    @overrides
    def visitMux2(self, ctx):
        self.mainFunction += self.stateless_alu_name + '_' + 'Mux2_' + str(
            self.mux2Count) + '('
        self.visit(ctx.getChild(0, aluParser.ExprContext))
        self.mainFunction += ','
        self.visit(ctx.getChild(1, aluParser.ExprContext))
        self.mainFunction += ',' + 'Mux2_' + str(self.mux2Count) + ')'
        self.generateMux2()
        self.mux2Count += 1

    @overrides
    def visitMux3(self, ctx):
        self.mainFunction += self.stateless_alu_name + '_' + 'Mux3_' + str(
            self.mux3Count) + '('
        self.visit(ctx.getChild(0, aluParser.ExprContext))
        self.mainFunction += ','
        self.visit(ctx.getChild(1, aluParser.ExprContext))
        self.mainFunction += ','
        self.visit(ctx.getChild(2, aluParser.ExprContext))
        self.mainFunction += ',' + 'Mux3_' + str(self.mux3Count) + ')'
        self.generateMux3()
        self.mux3Count += 1

    @overrides
    def visitReturn_statement(self, ctx):
        self.mainFunction += 'return '
#        self.visit (ctx.getChild (0))
        self.visit(ctx.getChild(0, aluParser.ExprContext))
        self.mainFunction += ';'

    @overrides
    def visitMux3WithNum(self, ctx):
        self.mainFunction += self.stateless_alu_name + '_Mux3_' + str(
            self.mux3Count) + '('
        self.visit(ctx.getChild(0, aluParser.ExprContext))
        self.mainFunction += ','
        self.visit(ctx.getChild(1, aluParser.ExprContext))
        self.mainFunction += ',' + 'Mux3_' + str(self.mux3Count) + ')'
        # Here it's the child with index 6. The grammar parse for this
        # expression as whole is following, NUM '(' expr ',' expr ',' NUM ')'
        # Where NUM is not considered as an expr. Consider parsing NUM as expr
        # so we could simply do ctx.getChild(2, aluParser.ExprContext)
        # below.
#        self.generateMux3WithNum(ctx.getChild(6).getText())
        self.mux3Count += 1

    @overrides
    def visitOpt(self, ctx):
        self.mainFunction += self.stateless_alu_name + '_' + 'Opt_' + str(
            self.optCount) + '('
        self.visitChildren(ctx)
        self.mainFunction += ',' + 'Opt_' + str(self.optCount) + ')'
        self.generateOpt()
        self.optCount += 1

    @overrides
    def visitRelOp(self, ctx):
        self.mainFunction += self.stateless_alu_name + '_' + 'rel_op_' + str(
            self.relopCount) + '('
        self.visit(ctx.getChild(0, aluParser.ExprContext))
        self.mainFunction += ','
        self.visit(ctx.getChild(1, aluParser.ExprContext))
        self.mainFunction += ',' + 'rel_op_' + str(self.relopCount) + ') == 1'
        self.generateRelOp()
        self.relopCount += 1

    @overrides
    def visitEquals(self, ctx):

        self.visit(ctx.getChild(0, aluParser.ExprContext))
        self.mainFunction += '=='

        self.visit(ctx.getChild(1, aluParser.ExprContext))

    @overrides
    def visitGreater(self, ctx):

        self.visit(ctx.getChild(0, aluParser.ExprContext))
        self.mainFunction += '>'
        self.visit(ctx.getChild(1, aluParser.ExprContext))

    @overrides
    def visitGreaterEqual(self, ctx):

        self.visit(ctx.getChild(0, aluParser.ExprContext))
        self.mainFunction += '>='
        self.visit(ctx.getChild(1, aluParser.ExprContext))

    @overrides
    def visitLess(self, ctx):

        self.visit(ctx.getChild(0, aluParser.ExprContext))
        self.mainFunction += '<'
        self.visit(ctx.getChild(1, aluParser.ExprContext))

    @overrides
    def visitLessEqual(self, ctx):
        self.visit(ctx.getChild(0, aluParser.ExprContext))
        self.mainFunction += '<='
        self.visit(ctx.getChild(1, aluParser.ExprContext))

    @overrides
    def visitOr(self, ctx):

        self.visit(ctx.getChild(0, aluParser.ExprContext))
        self.mainFunction += '||'
        self.visit(ctx.getChild(1, aluParser.ExprContext))

    @overrides
    def visitAnd(self, ctx):

        self.visit(ctx.getChild(0, aluParser.ExprContext))
        self.mainFunction += '&&'
        self.visit(ctx.getChild(1, aluParser.ExprContext))

    @overrides
    def visitNotEqual(self, ctx):

        self.visit(ctx.getChild(0, aluParser.ExprContext))
        self.mainFunction += '!='
        self.visit(ctx.getChild(1, aluParser.ExprContext))

    @overrides
    def visitValue(self, ctx):
        self.mainFunction += ctx.getText()

    @overrides
    def visitArithOp(self, ctx):
        self.mainFunction += self.stateless_alu_name + '_' + 'arith_op_' + str(
            self.arithopCount) + '('
        self.visit(ctx.getChild(0, aluParser.ExprContext))
        self.mainFunction += ','
        self.visit(ctx.getChild(1, aluParser.ExprContext))
        self.mainFunction += ',' + 'arith_op_' + str(self.arithopCount) + ')'
        self.generateArithOp()
        self.arithopCount += 1

    @overrides
    def visitTrue(self, ctx):
        self.mainFunction += 'true'

    @overrides
    def visitConstant(self, ctx):
        self.mainFunction += self.stateless_alu_name + '_' + 'C_' + str(
            self.constCount) + '('
        self.mainFunction += 'const_' + str(self.constCount) + ')'
        self.generateConstant()
        self.constCount += 1

    @overrides
    def visitParen(self, ctx):
        pass

    @overrides
    def visitExprWithParen(self, ctx):
        self.mainFunction += ctx.getChild(0).getText()
        self.visit(ctx.getChild(1))

        self.mainFunction += ctx.getChild(2).getText()

    @overrides
    def visitUpdate(self, ctx):

        # Make sure every update ends with a semicolon
        assert ctx.getChild(ctx.getChildCount() - 1).getText() == ';', \
            'Every update must end with a semicolon.'

        self.visit(ctx.getChild(0, aluParser.State_varContext))
        self.mainFunction += ' = '
        self.visit(ctx.getChild(0, aluParser.ExprContext))
        self.mainFunction += ';'

    @overrides
    def visitExprWithOp(self, ctx):
        self.visit(ctx.getChild(0, aluParser.ExprContext))
        self.mainFunction += ctx.getChild(1).getText()
        self.visit(ctx.getChild(1, aluParser.ExprContext))

    def generateMux2(self):
        self.helperFunctionStrings += 'int ' + self.stateless_alu_name + '_' + \
            'Mux2_' + str(self.mux2Count) + \
            """(int op1, int op2, int choice) {
    if (choice == 0) return op1;
    else return op2;
    } \n\n"""
        self.add_hole('Mux2_' + str(self.mux2Count), 1)

    def generateMux3(self):
        self.helperFunctionStrings += 'int ' + self.stateless_alu_name + '_' + \
            'Mux3_' + str(self.mux3Count) + \
            """(int op1, int op2, int op3, int choice) {
    if (choice == 0) return op1;
    else if (choice == 1) return op2;
    else return op3;
    } \n\n"""
        self.add_hole('Mux3_' + str(self.mux3Count), 2)

    def generateMux3WithNum(self, num):
        # NOTE: To escape curly brace, use double curly brace.
        function_str = """\
            int {0}_Mux3_{1}(int op1, int op2, int choice) {{
                if (choice == 0) return op1;
                else if (choice == 1) return op2;
                else return {2};
            }}\n
        """
        self.helperFunctionStrings += dedent(
            function_str.format(self.stateless_alu_name, str(self.mux3Count),
                                num))
        # Add two bit width hole, to express 3 possible values for choice in
        # the above code.
        self.add_hole('Mux3_' + str(self.mux3Count), 2)

    def generateRelOp(self):
        self.helperFunctionStrings += 'int ' + self.stateless_alu_name + '_' + \
            'rel_op_' + str(self.relopCount) + \
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
        self.add_hole('rel_op_' + str(self.relopCount), 2)

    def generateArithOp(self):
        self.helperFunctionStrings += 'int ' + self.stateless_alu_name + '_' + \
            'arith_op_' + str(self.arithopCount) + \
            """(int operand1, int operand2, int opcode) {
    if (opcode == 0) {
      return operand1 + operand2;
    } else {
      return operand1 - operand2;
    }
    }\n\n"""
        self.add_hole('arith_op_' + str(self.arithopCount), 1)

    def generateConstant(self):
        self.helperFunctionStrings += 'int ' + self.stateless_alu_name + '_' + \
            'C_' + str(self.constCount) + """(int const) {
    return const;
    }\n\n"""
        self.add_hole('const_' + str(self.constCount), 2)

    def generateOpt(self):
        self.helperFunctionStrings += 'int ' + self.stateless_alu_name + '_' + \
            'Opt_' + str(self.optCount) + """(int op1, int enable) {
    if (enable != 0) return 0;
    return op1;
    } \n\n"""
        self.add_hole('Opt_' + str(self.optCount), 1)
