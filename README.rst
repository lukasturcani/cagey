Cagey
=====

``cagey`` analyses experimental data from generated during high-throughput
porous organic cage synthesis to determine if cages were successfully formed.

Installation
------------

.. code-block:: bash

  pip install cagey

This will give you a series of command line tools which we used in the
next section.

Usage
-----

``cagey`` creates a SQLite database holding all of our experimental data,
which is then used to perform additional analysis.

Creating a Database
...................

.. code-block:: bash

  cagey-add-reactions path/to/cagey.db

Adding NMR Data
...............

.. code-block:: bash

  cagey-add-nmr path/to/cagey.db path/to/nmr/data/*/title

Adding Mass Spectrometry Data
.............................

.. warning::

  This step requires you have Docker and MZMine version 3.4.27 installed.

.. code-block:: bash

  cagey-add-ms path/to/cagey.db path/to/ms/data/*.d

Viewing the Database
....................

You can see the data held in the database by opening the notebook in
:ref:`./notebooks/view_tables.ipynb`.
