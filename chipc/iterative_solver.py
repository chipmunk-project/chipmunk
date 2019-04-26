"""Repeated Solver"""
import argparse
import sys
from pathlib import Path

from chipc.compiler import Compiler
from chipc.utils import get_info_of_state_groups
from chipc.utils import get_num_pkt_fields_and_state_groups


# Create hole_elimination_assert from hole_assignments
# hole_assignments is in the format {'hole_name':'hole_value'},
# i.e., {'sample1_stateless_alu_0_0_mux1_ctrl': '0'}
def generate_hole_elimination_assert(hole_assignments):
    # The ! is to ensure a hole combination isn't present.
    hole_elimination_string = "!"
    for hole, value in hole_assignments.items():
        hole_elimination_string += "(" + hole + " == " + value + ") && "
    hole_elimination_string += "1"
    return [hole_elimination_string]


# Create multiple counterexamples in the range from 2 bits to 10 bits.
def generate_additional_testcases(hole_assignments, compiler,
                                  num_fields_in_prog, num_state_groups,
                                  state_group_info, count):
    counter_example_definition = ""
    counter_example_assert = ""
    for bits in range(2, 10):
        print("Trying to generate counterexample of " + str(bits) + " bits ")
        (pkt_group, state_group) = compiler.counter_example_generator(
            bits, hole_assignments, iter_cnt=count)

        # Check if all packet fields are included in pkt_group as part
        # of the counterexample.
        # If not, set those packet fields to a default (0) since they
        # don't matter for the counterexample.
        for i in range(int(num_fields_in_prog)):
            if ("pkt_" + str(i) in [
                    regex_match[0] for regex_match in pkt_group
            ]):
                continue
            else:
                pkt_group.append(("pkt_" + str(i), str(0)))

        # Check if all state vars are included in state_group as part
        # of the counterexample. If not, set those state vars to
        # default (0) since they don't matter for the counterexample

        for i in range(len(state_group_info)):
            if ("state_group_" + state_group_info[i][0] + "_state_" +
                    state_group_info[i][1] in [
                        regex_match[0] for regex_match in state_group
            ]):
                continue
            else:
                state_group.append(
                    ("state_group_" + state_group_info[i][0] + "_state_" +
                     state_group_info[i][1] + str(i), str(0)))
        counter_example_definition += "|StateAndPacket| x_" + str(
            count) + "_" + str(bits) + " = |StateAndPacket|(\n"
        for group in pkt_group:
            counter_example_definition += group[0] + " = " + str(
                int(group[1]) + 2**bits) + ',\n'
        for i, group in enumerate(state_group):
            counter_example_definition += group[0] + " = " + str(
                int(group[1]) + 2**bits)
            if i < len(state_group) - 1:
                counter_example_definition += ',\n'
            else:
                counter_example_definition += ");\n"
        counter_example_assert += "assert (pipeline(" + "x_" + str(
            count) + "_" + str(bits) + ")" + " == " + "program(" + "x_" + str(
                count) + "_" + str(bits) + "));\n"
    return counter_example_definition + counter_example_assert


def main(argv):
    parser = argparse.ArgumentParser(description="Iterative solver.")
    parser.add_argument(
        "program_file", help="Program specification in .sk file")
    parser.add_argument("stateful_alu_file", help="Stateful ALU file to use.")
    parser.add_argument(
        "stateless_alu_file", help="Stateless ALU file to use.")
    parser.add_argument(
        "num_pipeline_stages", type=int, help="Number of pipeline stages")
    parser.add_argument(
        "num_alus_per_stage",
        type=int,
        help="Number of stateless/stateful ALUs per stage")
    parser.add_argument(
        "--pkt-fields",
        type=int,
        nargs='+',
        help="Packet fields to check correctness")
    parser.add_argument(
        "-p",
        "--parallel",
        action="store_const",
        const="parallel_codegen",
        default="serial_codegen",
        help="Whether to run multiple sketches in parallel.")
    parser.add_argument(
        "--parallel-sketch",
        action="store_true",
        help="Whether sketch process uses parallelism")
    parser.add_argument(
        "--hole-elimination",
        action="store_const",
        const="hole_elimination_mode",
        default="cex_mode",
        help="Whether to iterate by eliminating holes or using counterexamples"
    )

    args = parser.parse_args(argv[1:])
    # Use program_content to store the program file text rather than use it
    # twice
    program_content = Path(args.program_file).read_text()
    (num_fields_in_prog,
     num_state_groups) = get_num_pkt_fields_and_state_groups(program_content)

    # Get the state vars information
    state_group_info = get_info_of_state_groups(program_content)
    sketch_name = args.program_file.split('/')[-1].split('.')[0] + \
        "_" + args.stateful_alu_file.split('/')[-1].split('.')[0] + \
        "_" + args.stateless_alu_file.split('/')[-1].split('.')[0] + \
        "_" + str(args.num_pipeline_stages) + \
        "_" + str(args.num_alus_per_stage)

    compiler = Compiler(args.program_file, args.stateful_alu_file,
                        args.stateless_alu_file,
                        args.num_pipeline_stages, args.num_alus_per_stage,
                        sketch_name, args.parallel_sketch, args.pkt_fields)

    # Repeatedly run synthesis at 2 bits and verification using all valid ints
    # until either verification succeeds or synthesis fails at 2 bits. Note
    # that the verification with all ints, might not work because sketch only
    # considers positive integers.
    # Synthesis is much faster at a smaller bit width, while verification needs
    # to run at a larger bit width for soundness.
    count = 1
    hole_elimination_assert = []
    additional_testcases = ""
    while 1:
        if args.hole_elimination == "hole_elimination_mode":
            (synthesis_ret_code, output, hole_assignments) = \
                compiler.serial_codegen(
                iter_cnt=count,
                additional_constraints=hole_elimination_assert) \
                if args.parallel == "serial_codegen" else \
                compiler.parallel_codegen(
                    additional_constraints=hole_elimination_assert)

        else:
            assert (args.hole_elimination == "cex_mode")
            (synthesis_ret_code, output, hole_assignments) = \
                compiler.serial_codegen(
                iter_cnt=count,
                additional_testcases=additional_testcases) \
                if args.parallel == "serial_codegen" else \
                compiler.parallel_codegen(
                    additional_testcases=additional_testcases)

        print("Iteration #" + str(count))
        if synthesis_ret_code == 0:
            print("Synthesis succeeded with 2 bits, proceeding to "
                  "verification.")
            verification_ret_code = compiler.sol_verify(
                hole_assignments, iter_cnt=count)
            if verification_ret_code == 0:
                print("SUCCESS: Verification succeeded.")
                return 0
            else:
                print("Verification failed. Trying again.")
                if args.hole_elimination == "hole_elimination_mode":
                    hole_elimination_assert = generate_hole_elimination_assert(
                        hole_assignments)
                else:
                    assert (args.hole_elimination == "cex_mode")
                    additional_testcases = generate_additional_testcases(
                        hole_assignments, compiler, num_fields_in_prog,
                        num_state_groups, state_group_info, count)
                count = count + 1
                continue
        else:
            # Failed synthesis at 2 bits.
            print("FAILURE: Failed synthesis at 2 bits.")
            return 1


def run_main():
    sys.exit(main(sys.argv))


if __name__ == "__main__":
    run_main()
