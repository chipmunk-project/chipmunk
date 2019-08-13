import subprocess


def check_syntax(sketch_file_name):
    # Check syntax of given sketch file.
    (return_code, output) = subprocess.getstatusoutput(
        'sketch ' + sketch_file_name + ' --slv-timeout=0.001')
    if (return_code == 0):
        print(sketch_file_name + ' passed syntax check. ')
        assert(output.rfind('Program Parse Error:') == -1)
    else:
        if (output.rfind('Program Parse Error:') != -1):
            raise Exception(
                sketch_file_name + ' contains a syntax error.' +
                'Output pasted below:\n\n' + output)


def synthesize(sketch_file_name, bnd_inbits, slv_seed, slv_parallel=False):
    assert(slv_parallel in [True, False])
    check_syntax(sketch_file_name)
    par_string = ' --slv-parallel' if slv_parallel else ''
    (return_code, output) = subprocess.getstatusoutput('time sketch -V 12 ' +
                                                       '--slv-nativeints ' +
                                                       sketch_file_name +
                                                       ' --bnd-inbits=' +
                                                       str(bnd_inbits) +
                                                       ' --slv-seed=' +
                                                       str(slv_seed) +
                                                       par_string +
                                                       ' --slv-timeout=60')
    assert(output.rfind('Program Parse Error:') == -1)
    return (return_code, output)


def generate_smt2_formula(sketch_file_name, smt_file_name, bit_range):
    check_syntax(sketch_file_name)
    # TODO: set the slv-timeout to 0.1 for now but need to think up
    # a better way to deal with it
    (return_code, output) = subprocess.getstatusoutput('sketch ' +
                                                       sketch_file_name +
                                                       ' --bnd-inbits=' +
                                                       str(bit_range) +
                                                       ' --slv-timeout=0.1' +
                                                       ' --beopt:writeSMT ' +
                                                       smt_file_name)
