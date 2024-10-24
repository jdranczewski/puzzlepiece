try:
    from IPython.core.magic import cell_magic, Magics, magics_class
    from IPython import get_ipython
except ModuleNotFoundError:
    raise Exception("This module needs to be imported within an IPython environment.")
import traceback


@magics_class
class CustomMagics(Magics):
    @cell_magic
    def pzp_script(self, line, cell):
        puzzle = line if len(line) else "puzzle"
        self.shell.ex(f'{puzzle}.run("""{cell}""")')

    # The skeleton for this magic comes from https://stackoverflow.com/a/54890975
    @cell_magic
    def safe_run(self, line, cell):
        try:
            self.shell.ex(cell)  # This executes the cell in the current namespace
        except Exception as e:
            try:
                # Check the provided line is callable
                if len(line) and ip.ev(f"callable({line})"):
                    # Save the error to the global namespace and execute the provided handler
                    self.shell.user_ns["error"] = e
                    ip.ev(f"{line}(error)")
            except Exception as ee:
                print("The provided exception handler failed to run:", str(ee))
            # Re-raise the error
            raise e


# Register
ip = get_ipython()
ip.register_magics(CustomMagics)


def format_exception(error):
    return (
        "".join(traceback.format_tb(error.__traceback__))
        + f"\n{type(error).__name__}: {error}"
    )
