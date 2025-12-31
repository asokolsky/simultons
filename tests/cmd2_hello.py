import sys

import cmd2


class FirstApp(cmd2.Cmd):
    """A simple cmd2 application."""

    def do_hello_world(self, _: cmd2.Statement) -> None:
        """Prints a simple greeting."""
        self.poutput('Hello World')


if __name__ == '__main__':
    c = FirstApp()
    sys.exit(c.cmdloop())
