from collections import Mapping

def make_method(func, args, kwargs):

    def test_method(self):
        func(self, *args, **kwargs)

    # Format the argument string
    arg_string = ', '.join(repr(a) for a in args)
    kwarg_string = ', '.join('{0}={1}'.format(item[0], repr(item[1])) for item in kwargs.items())
    arg_list = []
    if arg_string:
        arg_list.append(arg_string)
    if kwarg_string:
        arg_list.append(kwarg_string)

    test_method.__name__ = 'test_{0}({1})'.format(func.__name__, ', '.join(arg_list))
    return test_method


def add_method(func, *combined_args):
    """
    Add a test case via a class decorator.

    nose uses generators for this but doesn't work with unittest.TestCase
    subclasses.  So we have to write our own.

    The first argument to this decorator is a test function.  All subsequent
    arguments are the arguments to create each generated test function with in
    the following format:

    Each set of arguments is a two-tuple.  The first element is an iterable of
    positional arguments.  the second is a dict representing the kwargs.
    """
    def wrapper(cls):
        for combined_arg in combined_args:
            if len(combined_arg) == 2:
                args = combined_arg[0]
                kwargs = combined_arg[1]
            elif isinstance(combined_arg[0], Mapping):
                args = []
                kwargs = combined_arg[0]
            else:
                args = combined_arg[0]
                kwargs = {}
            test_method = make_method(func, args, kwargs)
            setattr(cls, test_method.__name__, test_method)
        return cls

    return wrapper
