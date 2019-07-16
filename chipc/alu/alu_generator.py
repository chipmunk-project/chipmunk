import sys

from alu_visitor import ALUVisitor
from aluLexer import aluLexer
from aluParser import aluParser
from antlr4 import CommonTokenStream
from antlr4 import FileStream


def main(argv):
    alu_file = argv[1]
    input_stream = FileStream(alu_file)
    lexer = aluLexer(input_stream)
    stream = CommonTokenStream(lexer)
    parser = aluParser(stream)
    tree = parser.alu()
    alu_gen_visitor = ALUVisitor(alu_file)
    alu_gen_visitor.visit(tree)
    print(alu_gen_visitor.mainFunction)


if __name__ == '__main__':
    main(sys.argv)
