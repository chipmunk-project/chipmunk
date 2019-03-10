"""Parallel compiler"""
from pathlib import Path
import sys
import re
import itertools

from compiler import Compiler
from utils import get_num_pkt_fields_and_state_groups

def main(argv):
    """Main program."""
    if len(argv) != 6:
        print("Usage: python3 " + argv[0] +
              " <program file> <alu file> <number of pipeline stages> " +
              "<number of stateless/stateful ALUs per stage> " +
              "<sketch_name (w/o file extension)> ")
        sys.exit(1)

    program_file = str(argv[1])
    alu_file = str(argv[2])
    num_pipeline_stages = int(argv[3])
    num_alus_per_stage = int(argv[4])
    sketch_name = str(argv[5])

    (num_fields_in_prog,
     num_state_groups) = get_num_pkt_fields_and_state_groups(
         Path(program_file).read_text())

    # For each state_group, pick a pipeline_stage exhaustively.
    # Note that some of these assignments might be infeasible, but that's OK. Sketch will reject these anyway.
    count = 0
    compiler_results = []
    for assignment in itertools.product(list(range(num_pipeline_stages)), repeat=num_state_groups):
        additional_asserts = []
        count = count + 1
        print("Now in assignment # ", count, " assignment is ", assignment)
        for state_group in range(num_state_groups):
            assigned_stage = assignment[state_group]
            for stage in range(num_pipeline_stages):
                if (stage == assigned_stage):
                    additional_asserts += [sketch_name + "_salu_config_" + str(stage) + "_" + str(state_group) + " == 1"]
                else:
                    additional_asserts += [sketch_name + "_salu_config_" + str(stage) + "_" + str(state_group) + " == 0"]
        compiler = Compiler(program_file, alu_file, num_pipeline_stages,
                            num_alus_per_stage, sketch_name + "_" + str(count), "serial")
        compiler_results += [compiler.codegen(additional_asserts)]

    if all([x[0] != 0 for x in compiler_results]):
        with open(compiler.sketch_name + ".errors", "w") as errors_file:
            errors_file.write(compiler_results[count - 1][1])
            print("Sketch failed. Output left in " + errors_file.name)
        sys.exit(1)

    assert(not all([x[0] != 0 for x in compiler_results]))
    output =  next(x for x in compiler_results if x[0] == 0)[1]
    for hole_name in compiler.sketch_generator.hole_names_:
        hits = re.findall("(" + hole_name + ")__" + r"\w+ = (\d+)", output)
        assert len(hits) == 1
        assert len(hits[0]) == 2
        print("int ", hits[0][0], " = ", hits[0][1], ";")
    with open(compiler.sketch_name + ".success", "w") as success_file:
        success_file.write(output)
        print("Sketch succeeded. Generated configuration is given " +
              "above. Output left in " + success_file.name)
    sys.exit(0)

if __name__ == "__main__":
    main(sys.argv)
