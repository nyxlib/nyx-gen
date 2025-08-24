# -*- coding: utf-8 -*-
########################################################################################################################

import json
import argparse

########################################################################################################################

from . import generators, __version__

########################################################################################################################

def main():

    ####################################################################################################################

    parser = argparse.ArgumentParser(description = 'Generate an Nyx driver skeleton from a description file')

    parser.add_argument('--version', action = 'version', version = __version__, help = 'Print version information and exit')

    parser.add_argument('--profiles', action = 'version', version = ', '.join(generators.keys()), help = 'Print profile names and exit')

    parser.add_argument('--override-project', action = 'store_true', help = 'Override the project output folder')

    parser.add_argument('--override-device', action = 'store_true', help = 'Override the device files')

    parser.add_argument('--override-main', action = 'store_true', help = 'Override main.c')

    parser.add_argument('--override-cmake', action = 'store_true', help = 'Override CMake')

    parser.add_argument('--output', type = str, default = '.', help = 'Skeleton output path')

    parser.add_argument('--descr', type = str, required = True, help = 'Driver description file')

    args = parser.parse_args()

    ####################################################################################################################

    try:

        with open(args.descr, 'rt') as f:

            descr = json.load(f)

    except IOError:

        print('Invalid JSON')

        return 1

    ####################################################################################################################

    if descr['mode'] in generators:

        try:

            generator_instance = generators[descr['mode']](args, descr)

            generator_instance.create_directories()

            generator_instance.generate()

            return 0

        except Exception as e:

            print(f'Error running code generator: {e.__str__()}')

    else:

        print(f'Invalid code generator: {descr["mode"]}')

    ####################################################################################################################

    return 1

########################################################################################################################
