import os
import glob


def get_sketch_directory():
    '''
    Return directory containing the `base_node` Arduino sketch.
    '''
    import base_node
    return os.path.join(os.path.abspath(os.path.dirname(base_node.__file__)),
                        'Arduino', 'BaseNode')


def get_includes():
    '''
    Return directories containing the `base_node` Arduino header files.

    Modules that need to compile against `base_node` should use this function
    to locate the appropriate include directories.

    Notes
    =====

    For example:

        import base_node
        ...
        print ' '.join(['-I%s' % i for i in cyvpr.get_includes()])
        ...

    '''
    import base_node
    return [get_sketch_directory()]


def get_sources():
    '''
    Return `base_node` Arduino source file paths.

    Modules that need to compile against `base_node` should use this function
    to locate the appropriate source files to compile.

    Notes
    =====

    For example:

        import base_node
        ...
        print ' '.join(base_node.get_sources())
        ...

    '''
    import base_node
    return glob.glob(os.path.join(get_sketch_directory(), '*.c*'))
