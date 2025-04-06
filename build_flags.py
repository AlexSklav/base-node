# coding: utf-8
import sys
import argparse

from base_node import __version__ as VERSION

def parse_args(sys_args=None):
    if sys_args is None:
        sys_args = sys.argv[1:]
    parser = argparse.ArgumentParser()

    default_version = VERSION
    parser.add_argument('--software-version', default=default_version, help="BaseNode software version")
    parser.add_argument('--hardware-version', default=1.0, help="BaseNode hardware version")

    parser.add_argument('arg', nargs='*')

    return parser.parse_known_args(args=sys_args)


if __name__ == '__main__':
    args, extra_args = parse_args()
    
    # Add BaseNode constants - properly escape both versions as C string literals
    extra_args += [r'-D___SOFTWARE_VERSION___=\"{}\"'.format(args.software_version)]
    extra_args += [r'-D___HARDWARE_VERSION___=\"{}\"'.format(args.hardware_version)]


    print(' '.join(extra_args))
