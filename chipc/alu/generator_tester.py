import sys

from aluLexer import aluLexer
from aluParser import aluParser
from antlr4 import CommonTokenStream
from antlr4 import FileStream

from chipc.alu.stateful_alu_sketch_generator import StatefulALUSketchGenerator


def main(argv):
    alu_file = argv[1]
    input_stream = FileStream(alu_file)
    lexer = aluLexer(input_stream)
    stream = CommonTokenStream(lexer)
    parser = aluParser(stream)
    tree = parser.alu()
    alu_gen_visitor = StatefulALUSketchGenerator(
        alu_file, 'simple_sub_stateless_alu_2_2_stateful_alu_1_0')
    alu_gen_visitor.visit(tree)
    print(alu_gen_visitor.helper_function_strings + '\n\n\n\n')
    print(alu_gen_visitor.main_function)


if __name__ == '__main__':
    main(sys.argv)
