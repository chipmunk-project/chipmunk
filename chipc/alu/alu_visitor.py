from aluVisitor import aluVisitor


class ALUVisitor(aluVisitor):
    def __init__(self, instruction_file):
        self.instruction_file = instruction_file
        self.alu_name = 'aatish_alu'  # temp
        self.mux3Count = 0
        self.mux2Count = 0
        self.relopCount = 0
        self.optCount = 0
        self.constantCount = 0
        self.helperFunctionStrings = '\n\n\n'
        self.globalholes = ''
        self.mainFunction = ''

    def visitState_indicator(self, ctx):
        print(ctx.getChildCount())
        print(ctx.getChild(0))

    def visitAlu_body(self, ctx):
        if(ctx.getChildCount() == 7):  # if statement
            self.mainFunction += 'if ('
            self.visit(ctx.getChild(2))
            self.mainFunction += ') {'
            self.visit(ctx.getChild(5))
            self.mainFunction += '}'

    def visitUpdates(self, ctx):
        self.visitChildren(ctx)

    def visitUpdate(self, ctx):
        self.mainFunction += ctx.getChild(0).getText() + ' = '
        self.visit(ctx.getChild(2))
        self.mainFunction += ';'

    def visitState_var(self, ctx):
        self.mainFunction += ctx.getChild(0).getText()

    def visitRelOp(self, ctx):
        self.mainFunction += 'rel_op('
        self.visit(ctx.getChild(2))
        self.mainFunction += ','
        self.visit(ctx.getChild(4))
        self.mainFunction += ')'

    def visitMux3(self, ctx):
        self.mainFunction += 'Mux3('
        self.visit(ctx.getChild(2))
        self.mainFunction += ','
        self.visit(ctx.getChild(4))
        self.mainFunction += ')'
