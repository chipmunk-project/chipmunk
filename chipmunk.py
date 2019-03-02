"""Chipmunk Compiler"""

from pathlib import Path
import pickle
import re
import subprocess
import sys

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from chipmunk_pickle import ChipmunkPickle
from sketch_generator import SketchGenerator
from utils import get_num_pkt_fields_and_state_vars


def main(argv):
    if len(argv) < 8:
        print(
            "Usage: python3 " + argv[0] +
            " <program file> <alu file> <number of pipeline stages> " + \
            "<number of stateless/stateful ALUs per stage> " + \
            "<codegen/optverify> <sketch_name (w/o file extension)> " + \
            "<parallel/serial>"
        )
        exit(1)
    else:
        program_file = str(argv[1])
        (num_fields_in_prog,
         num_state_vars) = get_num_pkt_fields_and_state_vars(
             Path(program_file).read_text())
        alu_file = str(argv[2])
        num_pipeline_stages = int(argv[3])
        num_alus_per_stage = int(argv[4])
        num_phv_containers = num_alus_per_stage
        assert num_fields_in_prog <= num_phv_containers
        mode = str(argv[5])
        assert mode in ["codegen", "optverify"]
        sketch_name = str(argv[6])
        parallel_or_serial = str(argv[7])
        assert parallel_or_serial in ["parallel", "serial"]

    # Initialize jinja2 environment for templates
    env = Environment(
        loader=FileSystemLoader('./templates'), undefined=StrictUndefined)

    # Create an object for sketch generation
    sketch_generator = SketchGenerator(
        sketch_name=sketch_name,
        num_pipeline_stages=num_pipeline_stages,
        num_alus_per_stage=num_alus_per_stage,
        num_phv_containers=num_phv_containers,
        num_state_vars=num_state_vars,
        num_fields_in_prog=num_fields_in_prog,
        jinja2_env=env,
        alu_file=alu_file)

    # Create stateless and stateful ALUs, operand muxes for stateful ALUs, and
    # output muxes.
    alu_definitions = sketch_generator.generate_alus()
    stateful_operand_mux_definitions = sketch_generator.generate_stateful_operand_muxes(
    )
    output_mux_definitions = sketch_generator.generate_output_muxes()

    # Create allocator to ensure each state var is assigned to exactly stateful ALU
    # and vice versa.
    sketch_generator.generate_state_allocator()

    # Now fill the appropriate template holes using the components created using
    # sketch_generator
    if mode == "codegen":
        codegen_code = sketch_generator.generate_sketch(
            program_file=program_file,
            alu_definitions=alu_definitions,
            stateful_operand_mux_definitions=stateful_operand_mux_definitions,
            mode=mode,
            output_mux_definitions=output_mux_definitions)

        # Create file and write sketch_harness into it.
        sketch_file_name = sketch_name + "_codegen.sk"
        with open(sketch_file_name, "w") as sketch_file:
            sketch_file.write(codegen_code)

        # Call sketch on it
        print("Total number of hole bits is",
              sketch_generator.total_hole_bits_)
        print("Sketch file is ", sketch_file_name)
        if parallel_or_serial == "parallel":
            (ret_code, output) = subprocess.getstatusoutput(
                "time sketch -V 12 --slv-seed=1 --slv-parallel " + \
                "--bnd-inbits=2 --bnd-int-range=50 " + sketch_file_name)
        else:
            (ret_code, output) = subprocess.getstatusoutput(
                "time sketch -V 12 --slv-seed=1 --bnd-inbits=2 " + \
                "--bnd-int-range=50 " + sketch_file_name)

        if ret_code != 0:
            with open(sketch_name + ".errors", "w") as errors_file:
                errors_file.write(output)
                print("Sketch failed. Output left in " + errors_file.name)
            sys.exit(1)
        else:
            for hole_name in sketch_generator.hole_names_:
                hits = re.findall("(" + hole_name + ")__" + r"\w+ = (\d+)",
                                  output)
                assert len(hits) == 1
                assert len(hits[0]) == 2
                print("int ", hits[0][0], " = ", hits[0][1], ";")
            with open(sketch_name + ".success", "w") as success_file:
                success_file.write(output)
                print(
                    "Sketch succeeded. Generated configuration is given " + \
                    "above. Output left in " + success_file.name)
            sys.exit(0)

    else:
        assert mode == "optverify"
        optverify_code = sketch_generator.generate_sketch(
            program_file=program_file,
            alu_definitions=alu_definitions,
            stateful_operand_mux_definitions=stateful_operand_mux_definitions,
            mode=mode,
            output_mux_definitions=output_mux_definitions)

        # Create file and write sketch_function into it
        with open(sketch_name + "_optverify.sk", "w") as sketch_file:
            sketch_file.write(optverify_code)
            print("Sketch file is ", sketch_file.name)

        # Put the rest (holes, hole arguments, constraints, etc.) into a .pickle
        # file.
        with open(sketch_name + ".pickle", "wb") as pickle_file:
            pickle.dump(
                ChipmunkPickle(
                    holes=sketch_generator.holes_,
                    hole_arguments=sketch_generator.hole_arguments_,
                    constraints=sketch_generator.constraints_,
                    num_fields_in_prog=num_fields_in_prog,
                    num_state_vars=num_state_vars), pickle_file)
            print("Pickle file is ", pickle_file.name)

        print("Total number of hole bits is",
              sketch_generator.total_hole_bits_)


if __name__ == "__main__":
    main(sys.argv)
