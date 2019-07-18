
from antlr4 import *
from aluLexer import aluLexer
from aluListener import aluListener
from aluParser import aluParser

#from chipc.stateful_alu_sketch_generator import StatefulAluSketchGenerator
from stateless_alu_sketch_generator import StatelessAluSketchGenerator
import sys


      
def main ():
  stateless_file_name = "simple-tests/stateless_test.alu"
  stateful_file_name = "simple-tests/stateful_test.alu"
  input_file = ""
  result_file = 'result'
  
  if len (sys.argv) > 1:
    input_file = sys.argv[1]
  else:
    print('Invalid file. Using simple-tests/stateful_test.alu by default ')
    input_file = stateful_file_name

  
  input_stream = FileStream (input_file)
  print(input_file, ' loaded')
  lexer = aluLexer (input_stream)
  stream = CommonTokenStream (lexer)
  parser = aluParser (stream)
  tree = parser.alu()
  generator = StatelessAluSketchGenerator(input_file, result_file)
  generator.visit(tree)
  # TODO: Store holes
  # TODO: Store hole args?
  code = generator.helperFunctionStrings + generator.mainFunction
  f = open (result_file + '.sk', 'w')
  f.write (code)
  f.close()

if __name__ == '__main__':
  main()
