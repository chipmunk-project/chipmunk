"""Utilities for Chipmunk"""

from re import findall


def get_num_pkt_fields_and_state_vars(program):
    """Returns number of packet fields and state variables.
    Use a regex to scan the program and extract the largest packet field index
    and largest state variable index

    Args:
        program: The program to read

    Returns:
        A tuple of packet field numbers and state variables.
    """
    pkt_fields = [
        int(x) for x in findall(r'state_and_packet.pkt_(\d+)', program)
    ]
    state_vars = [
        int(x) for x in findall(r'state_and_packet.state_(\d+)', program)
    ]
    return (max(pkt_fields) + 1, max(state_vars) + 1)


def get_hole_dicts(sketch_output):
    """Returns a dictionary from hole names to hole values without spurious
    '__ANONYMOUS_s28' characters in between. The second \\w+ without parenthesis
    will capture this part and it's not grouped.
    """
    return {
        name: value
        for name, value in findall(r'(\w+)__\w+ = (\d+);', sketch_output)
    }
