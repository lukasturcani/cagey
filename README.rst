:Docs: https://cagey.readthedocs.io

Cagey
=====

First and foremost ``cagey`` is a command line tool for creating and managing a cage
database. With ``cagey`` you will extract a a range of experimental and computational
data in a variety of formats and place it into a single file. You can then use this file
as input for your scripts which perform data analysis. You can install ``cagey`` with:

.. code-block:: bash

  pip install cagey

Once installed you can use the command line tool to create a new database:

.. code-block:: bash

  cagey new path/to/data path/to/cagey.db

This will create a new database at ``path/to/cagey.db`` and populate it with data from
``path/to/data``. There are in fact a lot more things you can do with ``cagey``, and
the best way to learn about them is to use it interactively, starting with:

.. code-block:: bash

  cagey --help

::

   Usage: cagey [OPTIONS] COMMAND [ARGS]...

   A cage database tool.
   Run cagey help intro for an introduction.

  ╭─ Options ───────────────────────────────────────────────────────────────────────────╮
  │ --install-completion          Install completion for the current shell.             │
  │ --show-completion             Show completion for the current shell, to copy it or  │
  │                               customize the installation.                           │
  │ --help                        Show this message and exit.                           │
  ╰─────────────────────────────────────────────────────────────────────────────────────╯
  ╭─ Commands ──────────────────────────────────────────────────────────────────────────╮
  │ help         Get help on how to use cagey.                                          │
  │ insert       Insert new data into the cagey database.                               │
  │ ms           Mass spectrum analysis.                                                │
  │ new          Create a new database.                                                 │
  │ nmr          Extract NMR peaks.                                                     │
  ╰─────────────────────────────────────────────────────────────────────────────────────╯

Working with the database
-------------------------

Once you've used ``cagey`` to create a database, you can use the ``cagey.queries`` module
to extract data from it in your Python scripts. This step is best understood by
reading our documentation, which you can find at https://cagey.readthedocs.io.
