def update_function_name(function, name):
    """
    Update the name of the function, including in its code object, so that it shows up correctly in profiling.
    This is useful for decorator wrappers, which normally re-use the same code object many times, and therefore
    confuse profiling traces massively.
    # see https://discuss.python.org/t/profiling-applications-with-decorators-how-to-improve-decorator-names/47885
    # see https://docs.python.org/3/reference/datamodel.html#codeobject.replace
    """
    # Update the function's display name
    function.__name__ = name
    # Recreate the code object with the new name
    function.__code__ = function.__code__.replace(co_name=name)
