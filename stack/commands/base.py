"""The base command."""


class Base(object):
    """A base command."""

    def __init__(self, options, *args, **kwargs):
        self.options = options
        self.args = args
        self.kwargs = kwargs

    def run(self):
        raise NotImplementedError("You must implement the run() method yourself!")

    @staticmethod
    def yes_no(answer, default="yes"):
        yes = {"yes", "y", "ye", "", "ok", "k", "1"}
        no = {"no", "n", "0", "nope"}

        while True:
            if default:
                choice = input("{} ({}): ".format(answer, default)).lower()

                if choice in yes:
                    return True
                elif choice in no:
                    return False
                else:
                    return default in yes
            else:
                choice = input("{}: ".format(answer)).lower()

                if choice in yes:
                    return True
                elif choice in no:
                    return False
                else:
                    print("Please respond with 'yes' or 'no'\n")
