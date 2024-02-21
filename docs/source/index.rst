.. cagey documentation master file, created by
   sphinx-quickstart on Thu Sep  7 15:41:49 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

=================================
Welcome to cagey's documentation!
=================================

.. toctree::
  :maxdepth: 2
  :caption: Contents:
  :hidden:

  Modules <modules>


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
=========================

Once you've used ``cagey`` to create a database, you can use the ``cagey.queries`` module
to extract data from it in your Python scripts. The following sections will show you how to do this.

Note that the examples in this section are pre-written SQL queries. If you know a bit of
SQL, you can write your own queries to extract the data you need.
If you're looking to learn SQL, I recommend https://www.codecademy.com/learn/learn-sql,
it takes about 5 hours to complete.

Viewing precursors
------------------

.. testsetup:: viewing-precursors

  import os
  import tempfile
  from pathlib import Path
  import polars as pl

  pl.Config.set_tbl_width_chars(170)

  intial_dir = Path.cwd()
  temp_dir = Path(tempfile.mkdtemp()).absolute()
  cagey_db = Path(os.environ["CAGEY_DB"]).absolute()
  os.chdir(temp_dir)
  target = temp_dir / "path" / "to" / "cagey.db"
  target.parent.mkdir(parents=True, exist_ok=True)

  target.symlink_to(cagey_db)

.. testcode:: viewing-precursors

  import sqlite3
  import cagey
  df  = cagey.queries.precursors_df(sqlite3.connect("path/to/cagey.db"))

.. testcode:: viewing-precursors
  :hide:

  print(df)

.. testoutput:: viewing-precursors

  shape: (55, 2)
  ┌──────┬───────────────────────────────────┐
  │ name ┆ smiles                            │
  │ ---  ┆ ---                               │
  │ str  ┆ str                               │
  ╞══════╪═══════════════════════════════════╡
  │ Di1  ┆ O=Cc1cccc(C=O)c1                  │
  │ Di10 ┆ O=Cc1ccccc1C=O                    │
  │ Di11 ┆ Cn1nc(-c2ccc(C=O)cc2)cc1C=O       │
  │ Di12 ┆ CC(C=O)=Cc1ccc(C=C(C)C=O)cc1      │
  │ Di13 ┆ COc1cc(C=O)ccc1OCCOc1ccc(C=O)cc1… │
  │ …    ┆ …                                 │
  │ TriQ ┆ O=CC=Cc1ccc(-c2cc(-c3ccc(C=CC=O)… │
  │ TriR ┆ O=Cc1ccc(OCc2cc(COc3ccc(C=O)cc3)… │
  │ TriS ┆ O=Cc1ccc(C#Cc2cc(C=O)cc(C=O)c2)c… │
  │ TriT ┆ O=Cc1c(O)c(C=O)c(O)c(C=O)c1O      │
  │ TriU ┆ O=Cc1ccc(C=Cc2cc(C=Cc3ccc(C=O)cc… │
  └──────┴───────────────────────────────────┘

.. testcleanup:: viewing-precursors

  import shutil
  shutil.rmtree(temp_dir)
  os.chdir(intial_dir)

Viewing reactions
-----------------

.. testsetup:: viewing-reactions

  import os
  import tempfile
  from pathlib import Path
  import polars as pl

  pl.Config.set_tbl_width_chars(170)

  intial_dir = Path.cwd()
  temp_dir = Path(tempfile.mkdtemp()).absolute()
  cagey_db = Path(os.environ["CAGEY_DB"]).absolute()
  os.chdir(temp_dir)
  target = temp_dir / "path" / "to" / "cagey.db"
  target.parent.mkdir(parents=True, exist_ok=True)

  target.symlink_to(cagey_db)

.. testcode:: viewing-reactions

  import sqlite3
  import cagey
  df = cagey.queries.reactions_df(sqlite3.connect("path/to/cagey.db"))

.. testcode:: viewing-reactions
  :hide:

  print(df)

.. testoutput:: viewing-reactions

  shape: (450, 5)
  ┌────────────┬───────┬────────────────────┬─────────┬──────────┐
  │ experiment ┆ plate ┆ formulation_number ┆ di_name ┆ tri_name │
  │ ---        ┆ ---   ┆ ---                ┆ ---     ┆ ---      │
  │ str        ┆ i64   ┆ i64                ┆ str     ┆ str      │
  ╞════════════╪═══════╪════════════════════╪═════════╪══════════╡
  │ AB-02-005  ┆ 1     ┆ 1                  ┆ Di1     ┆ TriA     │
  │ AB-02-005  ┆ 1     ┆ 2                  ┆ Di2     ┆ TriA     │
  │ AB-02-005  ┆ 1     ┆ 3                  ┆ Di3     ┆ TriA     │
  │ AB-02-005  ┆ 1     ┆ 4                  ┆ Di4     ┆ TriA     │
  │ AB-02-005  ┆ 1     ┆ 5                  ┆ Di5     ┆ TriA     │
  │ …          ┆ …     ┆ …                  ┆ …       ┆ …        │
  │ AB-02-009  ┆ 2     ┆ 34                 ┆ Di34    ┆ TriP     │
  │ AB-02-009  ┆ 2     ┆ 35                 ┆ Di21    ┆ TriT     │
  │ AB-02-009  ┆ 2     ┆ 41                 ┆ Di33    ┆ TriQ     │
  │ AB-02-009  ┆ 2     ┆ 42                 ┆ Di34    ┆ TriQ     │
  │ AB-02-009  ┆ 2     ┆ 43                 ┆ Di21    ┆ TriU     │
  └────────────┴───────┴────────────────────┴─────────┴──────────┘

.. testcleanup:: viewing-reactions

  import shutil
  shutil.rmtree(temp_dir)
  os.chdir(intial_dir)

Viewing aldehyde peaks
----------------------

.. testsetup:: viewing-aldehyde-peaks

  import os
  import tempfile
  from pathlib import Path
  import polars as pl

  pl.Config.set_tbl_width_chars(170)

  intial_dir = Path.cwd()
  temp_dir = Path(tempfile.mkdtemp()).absolute()
  cagey_db = Path(os.environ["CAGEY_DB"]).absolute()
  os.chdir(temp_dir)
  target = temp_dir / "path" / "to" / "cagey.db"
  target.parent.mkdir(parents=True, exist_ok=True)

  target.symlink_to(cagey_db)

.. testcode:: viewing-aldehyde-peaks

  import sqlite3
  import cagey
  df = cagey.queries.aldehyde_peaks_df(sqlite3.connect("path/to/cagey.db"))

.. testcode:: viewing-aldehyde-peaks
  :hide:

  print(df)

.. testoutput:: viewing-aldehyde-peaks

  shape: (751, 7)
  ┌────────────┬───────┬────────────────────┬─────────┬──────────┬───────────┬───────────────┐
  │ experiment ┆ plate ┆ formulation_number ┆ di_name ┆ tri_name ┆ ppm       ┆ amplitude     │
  │ ---        ┆ ---   ┆ ---                ┆ ---     ┆ ---      ┆ ---       ┆ ---           │
  │ str        ┆ i64   ┆ i64                ┆ str     ┆ str      ┆ f64       ┆ f64           │
  ╞════════════╪═══════╪════════════════════╪═════════╪══════════╪═══════════╪═══════════════╡
  │ AB-02-005  ┆ 1     ┆ 1                  ┆ Di1     ┆ TriA     ┆ 10.124944 ┆ 5.4689e6      │
  │ AB-02-005  ┆ 1     ┆ 1                  ┆ Di1     ┆ TriA     ┆ 10.157341 ┆ 10014.054688  │
  │ AB-02-005  ┆ 1     ┆ 2                  ┆ Di2     ┆ TriA     ┆ 10.247195 ┆ 6.4216e6      │
  │ AB-02-005  ┆ 1     ┆ 3                  ┆ Di3     ┆ TriA     ┆ 10.047315 ┆ 8.3831e6      │
  │ AB-02-005  ┆ 1     ┆ 3                  ┆ Di3     ┆ TriA     ┆ 10.088269 ┆ 10120.1875    │
  │ …          ┆ …     ┆ …                  ┆ …       ┆ …        ┆ …         ┆ …             │
  │ AB-02-009  ┆ 2     ┆ 42                 ┆ Di34    ┆ TriQ     ┆ 9.74719   ┆ 1.2567e7      │
  │ AB-02-009  ┆ 2     ┆ 42                 ┆ Di34    ┆ TriQ     ┆ 9.804036  ┆ 112459.875    │
  │ AB-02-009  ┆ 2     ┆ 42                 ┆ Di34    ┆ TriQ     ┆ 9.809537  ┆ 23061.015625  │
  │ AB-02-009  ┆ 2     ┆ 42                 ┆ Di34    ┆ TriQ     ┆ 10.104773 ┆ 656725.390625 │
  │ AB-02-009  ┆ 2     ┆ 43                 ┆ Di21    ┆ TriU     ┆ 10.026532 ┆ 204503.21875  │
  └────────────┴───────┴────────────────────┴─────────┴──────────┴───────────┴───────────────┘

.. testcleanup:: viewing-aldehyde-peaks

  import shutil
  shutil.rmtree(temp_dir)
  os.chdir(intial_dir)

Viewing imine peaks
-------------------

.. testsetup:: viewing-imine-peaks

  import os
  import tempfile
  from pathlib import Path
  import polars as pl

  pl.Config.set_tbl_width_chars(170)

  intial_dir = Path.cwd()
  temp_dir = Path(tempfile.mkdtemp()).absolute()
  cagey_db = Path(os.environ["CAGEY_DB"]).absolute()
  os.chdir(temp_dir)
  target = temp_dir / "path" / "to" / "cagey.db"
  target.parent.mkdir(parents=True, exist_ok=True)

  target.symlink_to(cagey_db)

.. testcode:: viewing-imine-peaks

  import sqlite3
  import cagey
  df = cagey.queries.imine_peaks_df(sqlite3.connect("path/to/cagey.db"))


.. testcode:: viewing-imine-peaks
  :hide:

  print(df)

.. testoutput:: viewing-imine-peaks

  shape: (8_897, 7)
  ┌────────────┬───────┬────────────────────┬─────────┬──────────┬──────────┬───────────────┐
  │ experiment ┆ plate ┆ formulation_number ┆ di_name ┆ tri_name ┆ ppm      ┆ amplitude     │
  │ ---        ┆ ---   ┆ ---                ┆ ---     ┆ ---      ┆ ---      ┆ ---           │
  │ str        ┆ i64   ┆ i64                ┆ str     ┆ str      ┆ f64      ┆ f64           │
  ╞════════════╪═══════╪════════════════════╪═════════╪══════════╪══════════╪═══════════════╡
  │ AB-02-005  ┆ 1     ┆ 1                  ┆ Di1     ┆ TriA     ┆ 7.19154  ┆ 182851.445312 │
  │ AB-02-005  ┆ 1     ┆ 1                  ┆ Di1     ┆ TriA     ┆ 7.199486 ┆ 10129.6875    │
  │ AB-02-005  ┆ 1     ┆ 1                  ┆ Di1     ┆ TriA     ┆ 7.200708 ┆ 20981.03125   │
  │ AB-02-005  ┆ 1     ┆ 1                  ┆ Di1     ┆ TriA     ┆ 7.202542 ┆ 10030.398438  │
  │ AB-02-005  ┆ 1     ┆ 1                  ┆ Di1     ┆ TriA     ┆ 7.351688 ┆ 78380.953125  │
  │ …          ┆ …     ┆ …                  ┆ …       ┆ …        ┆ …        ┆ …             │
  │ AB-02-009  ┆ 2     ┆ 43                 ┆ Di21    ┆ TriU     ┆ 7.705604 ┆ 185844.953125 │
  │ AB-02-009  ┆ 2     ┆ 43                 ┆ Di21    ┆ TriU     ┆ 7.726386 ┆ 191285.3125   │
  │ AB-02-009  ┆ 2     ┆ 43                 ┆ Di21    ┆ TriU     ┆ 7.910985 ┆ 1.6976e6      │
  │ AB-02-009  ┆ 2     ┆ 43                 ┆ Di21    ┆ TriU     ┆ 7.984335 ┆ 46808.234375  │
  │ AB-02-009  ┆ 2     ┆ 43                 ┆ Di21    ┆ TriU     ┆ 8.491675 ┆ 409445.09375  │
  └────────────┴───────┴────────────────────┴─────────┴──────────┴──────────┴───────────────┘

.. testcleanup:: viewing-imine-peaks

  import shutil
  shutil.rmtree(temp_dir)
  os.chdir(intial_dir)


Viewing mass spectrum peaks
---------------------------

.. testsetup:: viewing-mass-spectrum-peaks

  import os
  import tempfile
  from pathlib import Path
  import polars as pl

  pl.Config.set_tbl_width_chars(170)
  pl.Config.set_tbl_cols(-1)

  intial_dir = Path.cwd()
  temp_dir = Path(tempfile.mkdtemp()).absolute()
  cagey_db = Path(os.environ["CAGEY_DB"]).absolute()
  os.chdir(temp_dir)
  target = temp_dir / "path" / "to" / "cagey.db"
  target.parent.mkdir(parents=True, exist_ok=True)

  target.symlink_to(cagey_db)


.. testcode:: viewing-mass-spectrum-peaks

  import sqlite3
  import cagey
  df = cagey.queries.mass_spectrum_peaks_df(sqlite3.connect("path/to/cagey.db"))

.. testcode:: viewing-mass-spectrum-peaks
  :hide:

  print(df)

.. testoutput:: viewing-mass-spectrum-peaks

  shape: (710, 13)
  ┌────────────┬───────┬────────────────────┬─────────┬──────────┬───────────┬──────────┬────────┬────────┬───────────────┬─────────────┬───────────────┬───────────┐
  │ experiment ┆ plate ┆ formulation_number ┆ di_name ┆ tri_name ┆ tri_count ┆ di_count ┆ adduct ┆ charge ┆ calculated_mz ┆ spectrum_mz ┆ separation_mz ┆ intensity │
  │ ---        ┆ ---   ┆ ---                ┆ ---     ┆ ---      ┆ ---       ┆ ---      ┆ ---    ┆ ---    ┆ ---           ┆ ---         ┆ ---           ┆ ---       │
  │ str        ┆ i64   ┆ i64                ┆ str     ┆ str      ┆ i64       ┆ i64      ┆ str    ┆ i64    ┆ f64           ┆ f64         ┆ f64           ┆ f64       │
  ╞════════════╪═══════╪════════════════════╪═════════╪══════════╪═══════════╪══════════╪════════╪════════╪═══════════════╪═════════════╪═══════════════╪═══════════╡
  │ AB-02-005  ┆ 1     ┆ 9                  ┆ Di1     ┆ TriB     ┆ 2         ┆ 3        ┆ H2     ┆ 2      ┆ 355.204848    ┆ 355.20633   ┆ 355.70863     ┆ 4.345e6   │
  │ AB-02-005  ┆ 1     ┆ 9                  ┆ Di1     ┆ TriB     ┆ 2         ┆ 3        ┆ Na1    ┆ 1      ┆ 731.383815    ┆ 731.38679   ┆ 732.39014     ┆ 5.375e6   │
  │ AB-02-005  ┆ 1     ┆ 9                  ┆ Di1     ┆ TriB     ┆ 2         ┆ 3        ┆ K1     ┆ 1      ┆ 747.357752    ┆ 747.36147   ┆ 748.36423     ┆ 702500.0  │
  │ AB-02-005  ┆ 1     ┆ 10                 ┆ Di2     ┆ TriB     ┆ 2         ┆ 3        ┆ H3     ┆ 3      ┆ 309.196689    ┆ 309.1977    ┆ 309.5326      ┆ 4.321e6   │
  │ AB-02-005  ┆ 1     ┆ 10                 ┆ Di2     ┆ TriB     ┆ 2         ┆ 3        ┆ H2     ┆ 2      ┆ 463.291121    ┆ 463.29423   ┆ 463.79488     ┆ 1.061e7   │
  │ …          ┆ …     ┆ …                  ┆ …       ┆ …        ┆ …         ┆ …        ┆ …      ┆ …      ┆ …             ┆ …           ┆ …             ┆ …         │
  │ AB-02-009  ┆ 1     ┆ 46                 ┆ Di30    ┆ TriQ     ┆ 2         ┆ 3        ┆ H2     ┆ 2      ┆ 571.291121    ┆ 571.29316   ┆ 571.79578     ┆ 2.944e6   │
  │ AB-02-009  ┆ 1     ┆ 46                 ┆ Di30    ┆ TriQ     ┆ 2         ┆ 3        ┆ H1     ┆ 1      ┆ 1141.574416   ┆ 1141.57561  ┆ 1142.57955    ┆ 2.704e6   │
  │ AB-02-009  ┆ 1     ┆ 46                 ┆ Di30    ┆ TriQ     ┆ 2         ┆ 3        ┆ Na1    ┆ 1      ┆ 1163.556361   ┆ 1163.55862  ┆ 1164.55963    ┆ 209200.0  │
  │ AB-02-009  ┆ 1     ┆ 46                 ┆ Di30    ┆ TriQ     ┆ 4         ┆ 6        ┆ Na2    ┆ 2      ┆ 1163.556361   ┆ 1163.55862  ┆ 1164.0711     ┆ 209200.0  │
  │ AB-02-009  ┆ 2     ┆ 18                 ┆ Di34    ┆ TriN     ┆ 2         ┆ 3        ┆ H1     ┆ 1      ┆ 1015.542721   ┆ 1015.54603  ┆ 1016.54919    ┆ 156600.0  │
  └────────────┴───────┴────────────────────┴─────────┴──────────┴───────────┴──────────┴────────┴────────┴───────────────┴─────────────┴───────────────┴───────────┘

.. testcleanup:: viewing-mass-spectrum-peaks

  import shutil
  shutil.rmtree(temp_dir)
  os.chdir(intial_dir)

Viewing mass spectrum topology assignments
------------------------------------------

.. testsetup:: viewing-mass-spectrum-topology-assignments

  import os
  import tempfile
  from pathlib import Path
  import polars as pl

  pl.Config.set_tbl_width_chars(180)
  pl.Config.set_tbl_cols(-1)

  intial_dir = Path.cwd()
  temp_dir = Path(tempfile.mkdtemp()).absolute()
  cagey_db = Path(os.environ["CAGEY_DB"]).absolute()
  os.chdir(temp_dir)
  target = temp_dir / "path" / "to" / "cagey.db"
  target.parent.mkdir(parents=True, exist_ok=True)

  target.symlink_to(cagey_db)

.. testcode:: viewing-mass-spectrum-topology-assignments

    import sqlite3
    import cagey
    df = cagey.queries.mass_spectrum_topology_assignments_df(sqlite3.connect("path/to/cagey.db"))

.. testcode:: viewing-mass-spectrum-topology-assignments
  :hide:

  print(df)

.. testoutput:: viewing-mass-spectrum-topology-assignments

  shape: (541, 14)
  ┌────────────┬───────┬────────────────────┬─────────┬──────────┬───────────┬──────────┬────────┬────────┬───────────────┬─────────────┬───────────────┬───────────┬──────────┐
  │ experiment ┆ plate ┆ formulation_number ┆ di_name ┆ tri_name ┆ tri_count ┆ di_count ┆ adduct ┆ charge ┆ calculated_mz ┆ spectrum_mz ┆ separation_mz ┆ intensity ┆ topology │
  │ ---        ┆ ---   ┆ ---                ┆ ---     ┆ ---      ┆ ---       ┆ ---      ┆ ---    ┆ ---    ┆ ---           ┆ ---         ┆ ---           ┆ ---       ┆ ---      │
  │ str        ┆ i64   ┆ i64                ┆ str     ┆ str      ┆ i64       ┆ i64      ┆ str    ┆ i64    ┆ f64           ┆ f64         ┆ f64           ┆ f64       ┆ str      │
  ╞════════════╪═══════╪════════════════════╪═════════╪══════════╪═══════════╪══════════╪════════╪════════╪═══════════════╪═════════════╪═══════════════╪═══════════╪══════════╡
  │ AB-02-005  ┆ 1     ┆ 9                  ┆ Di1     ┆ TriB     ┆ 2         ┆ 3        ┆ H2     ┆ 2      ┆ 355.204848    ┆ 355.20633   ┆ 355.70863     ┆ 4.345e6   ┆ 2+3      │
  │ AB-02-005  ┆ 1     ┆ 9                  ┆ Di1     ┆ TriB     ┆ 2         ┆ 3        ┆ Na1    ┆ 1      ┆ 731.383815    ┆ 731.38679   ┆ 732.39014     ┆ 5.375e6   ┆ 2+3      │
  │ AB-02-005  ┆ 1     ┆ 9                  ┆ Di1     ┆ TriB     ┆ 2         ┆ 3        ┆ K1     ┆ 1      ┆ 747.357752    ┆ 747.36147   ┆ 748.36423     ┆ 702500.0  ┆ 2+3      │
  │ AB-02-005  ┆ 1     ┆ 10                 ┆ Di2     ┆ TriB     ┆ 2         ┆ 3        ┆ H2     ┆ 2      ┆ 463.291121    ┆ 463.29423   ┆ 463.79488     ┆ 1.061e7   ┆ 2+3      │
  │ AB-02-005  ┆ 1     ┆ 10                 ┆ Di2     ┆ TriB     ┆ 2         ┆ 3        ┆ H1     ┆ 1      ┆ 925.574416    ┆ 925.5803    ┆ 926.58282     ┆ 1.653e7   ┆ 2+3      │
  │ …          ┆ …     ┆ …                  ┆ …       ┆ …        ┆ …         ┆ …        ┆ …      ┆ …      ┆ …             ┆ …           ┆ …             ┆ …         ┆ …        │
  │ AB-02-009  ┆ 1     ┆ 46                 ┆ Di30    ┆ TriQ     ┆ 2         ┆ 3        ┆ H2     ┆ 2      ┆ 571.291121    ┆ 571.29316   ┆ 571.79578     ┆ 2.944e6   ┆ 2+3      │
  │ AB-02-009  ┆ 1     ┆ 46                 ┆ Di30    ┆ TriQ     ┆ 2         ┆ 3        ┆ H1     ┆ 1      ┆ 1141.574416   ┆ 1141.57561  ┆ 1142.57955    ┆ 2.704e6   ┆ 2+3      │
  │ AB-02-009  ┆ 1     ┆ 46                 ┆ Di30    ┆ TriQ     ┆ 2         ┆ 3        ┆ Na1    ┆ 1      ┆ 1163.556361   ┆ 1163.55862  ┆ 1164.55963    ┆ 209200.0  ┆ 2+3      │
  │ AB-02-009  ┆ 1     ┆ 46                 ┆ Di30    ┆ TriQ     ┆ 4         ┆ 6        ┆ Na2    ┆ 2      ┆ 1163.556361   ┆ 1163.55862  ┆ 1164.0711     ┆ 209200.0  ┆ 4+6      │
  │ AB-02-009  ┆ 2     ┆ 18                 ┆ Di34    ┆ TriN     ┆ 2         ┆ 3        ┆ H1     ┆ 1      ┆ 1015.542721   ┆ 1015.54603  ┆ 1016.54919    ┆ 156600.0  ┆ 2+3      │
  └────────────┴───────┴────────────────────┴─────────┴──────────┴───────────┴──────────┴────────┴────────┴───────────────┴─────────────┴───────────────┴───────────┴──────────┘


.. testcleanup:: viewing-mass-spectrum-topology-assignments

  import shutil
  shutil.rmtree(temp_dir)
  os.chdir(intial_dir)

Viewing turbidity dissolved references
--------------------------------------

.. testsetup:: viewing-turbidity-dissolved-references

  import os
  import tempfile
  from pathlib import Path
  import polars as pl

  pl.Config.set_tbl_width_chars(170)

  intial_dir = Path.cwd()
  temp_dir = Path(tempfile.mkdtemp()).absolute()
  cagey_db = Path(os.environ["CAGEY_DB"]).absolute()
  os.chdir(temp_dir)
  target = temp_dir / "path" / "to" / "cagey.db"
  target.parent.mkdir(parents=True, exist_ok=True)

  target.symlink_to(cagey_db)

.. testcode:: viewing-turbidity-dissolved-references

    import sqlite3
    import cagey
    df = cagey.queries.turbidity_dissolved_references_df(sqlite3.connect("path/to/cagey.db"))

.. testcode:: viewing-turbidity-dissolved-references
  :hide:

  print(df)

.. testoutput:: viewing-turbidity-dissolved-references

  shape: (402, 6)
  ┌────────────┬───────┬────────────────────┬─────────┬──────────┬─────────────────────┐
  │ experiment ┆ plate ┆ formulation_number ┆ di_name ┆ tri_name ┆ dissolved_reference │
  │ ---        ┆ ---   ┆ ---                ┆ ---     ┆ ---      ┆ ---                 │
  │ str        ┆ i64   ┆ i64                ┆ str     ┆ str      ┆ f64                 │
  ╞════════════╪═══════╪════════════════════╪═════════╪══════════╪═════════════════════╡
  │ AB-02-005  ┆ 1     ┆ 1                  ┆ Di1     ┆ TriA     ┆ 67.033458           │
  │ AB-02-005  ┆ 1     ┆ 2                  ┆ Di2     ┆ TriA     ┆ 67.033458           │
  │ AB-02-005  ┆ 1     ┆ 3                  ┆ Di3     ┆ TriA     ┆ 67.033458           │
  │ AB-02-005  ┆ 1     ┆ 4                  ┆ Di4     ┆ TriA     ┆ 67.033458           │
  │ AB-02-005  ┆ 1     ┆ 5                  ┆ Di5     ┆ TriA     ┆ 67.033458           │
  │ …          ┆ …     ┆ …                  ┆ …       ┆ …        ┆ …                   │
  │ AB-02-009  ┆ 2     ┆ 34                 ┆ Di34    ┆ TriP     ┆ 26.762018           │
  │ AB-02-009  ┆ 2     ┆ 35                 ┆ Di21    ┆ TriT     ┆ 26.762018           │
  │ AB-02-009  ┆ 2     ┆ 41                 ┆ Di33    ┆ TriQ     ┆ 26.762018           │
  │ AB-02-009  ┆ 2     ┆ 42                 ┆ Di34    ┆ TriQ     ┆ 26.762018           │
  │ AB-02-009  ┆ 2     ┆ 43                 ┆ Di21    ┆ TriU     ┆ 26.762018           │
  └────────────┴───────┴────────────────────┴─────────┴──────────┴─────────────────────┘

.. testcleanup:: viewing-turbidity-dissolved-references

  import shutil
  shutil.rmtree(temp_dir)
  os.chdir(intial_dir)

Viewing turbidity measurments
-----------------------------

.. testsetup:: viewing-turbidity-measurments

  import os
  import tempfile
  from pathlib import Path
  import polars as pl

  pl.Config.set_tbl_width_chars(170)

  intial_dir = Path.cwd()
  temp_dir = Path(tempfile.mkdtemp()).absolute()
  cagey_db = Path(os.environ["CAGEY_DB"]).absolute()
  os.chdir(temp_dir)
  target = temp_dir / "path" / "to" / "cagey.db"
  target.parent.mkdir(parents=True, exist_ok=True)

  target.symlink_to(cagey_db)

.. testcode:: viewing-turbidity-measurments

    import sqlite3
    import cagey
    df = cagey.queries.turbidity_measurements_df(sqlite3.connect("path/to/cagey.db"))


.. testcode:: viewing-turbidity-measurments
  :hide:

  print(df)


.. testoutput:: viewing-turbidity-measurments

  shape: (6_824, 7)
  ┌────────────┬───────┬────────────────────┬─────────┬──────────┬────────────────────────────────┬───────────┐
  │ experiment ┆ plate ┆ formulation_number ┆ di_name ┆ tri_name ┆ time                           ┆ turbidity │
  │ ---        ┆ ---   ┆ ---                ┆ ---     ┆ ---      ┆ ---                            ┆ ---       │
  │ str        ┆ i64   ┆ i64                ┆ str     ┆ str      ┆ datetime[μs, UTC]              ┆ f64       │
  ╞════════════╪═══════╪════════════════════╪═════════╪══════════╪════════════════════════════════╪═══════════╡
  │ AB-02-005  ┆ 1     ┆ 1                  ┆ Di1     ┆ TriA     ┆ 2023-02-21 14:25:40.435542 UTC ┆ 89.183431 │
  │ AB-02-005  ┆ 1     ┆ 1                  ┆ Di1     ┆ TriA     ┆ 2023-02-21 14:25:48.002712 UTC ┆ 89.393769 │
  │ AB-02-005  ┆ 1     ┆ 1                  ┆ Di1     ┆ TriA     ┆ 2023-02-21 14:25:55.469585 UTC ┆ 89.331678 │
  │ AB-02-005  ┆ 1     ┆ 1                  ┆ Di1     ┆ TriA     ┆ 2023-02-21 14:26:03.001628 UTC ┆ 89.180119 │
  │ AB-02-005  ┆ 1     ┆ 1                  ┆ Di1     ┆ TriA     ┆ 2023-02-21 14:26:10.503830 UTC ┆ 89.290944 │
  │ …          ┆ …     ┆ …                  ┆ …       ┆ …        ┆ …                              ┆ …         │
  │ AB-02-009  ┆ 2     ┆ 43                 ┆ Di21    ┆ TriU     ┆ 2022-12-02 11:08:48.249675 UTC ┆ 56.7523   │
  │ AB-02-009  ┆ 2     ┆ 43                 ┆ Di21    ┆ TriU     ┆ 2022-12-02 11:08:55.784507 UTC ┆ 57.586026 │
  │ AB-02-009  ┆ 2     ┆ 43                 ┆ Di21    ┆ TriU     ┆ 2022-12-02 11:09:03.349212 UTC ┆ 57.455789 │
  │ AB-02-009  ┆ 2     ┆ 43                 ┆ Di21    ┆ TriU     ┆ 2022-12-02 11:09:10.912763 UTC ┆ 57.70839  │
  │ AB-02-009  ┆ 2     ┆ 43                 ┆ Di21    ┆ TriU     ┆ 2022-12-02 11:09:18.481001 UTC ┆ 58.490625 │
  └────────────┴───────┴────────────────────┴─────────┴──────────┴────────────────────────────────┴───────────┘


.. testcleanup:: viewing-turbidity-measurments

  import shutil
  shutil.rmtree(temp_dir)
  os.chdir(intial_dir)

Viewing turbidity states
------------------------

.. testsetup:: viewing-turbidity-states

  import os
  import tempfile
  from pathlib import Path
  import polars as pl

  pl.Config.set_tbl_width_chars(170)

  intial_dir = Path.cwd()
  temp_dir = Path(tempfile.mkdtemp()).absolute()
  cagey_db = Path(os.environ["CAGEY_DB"]).absolute()
  os.chdir(temp_dir)
  target = temp_dir / "path" / "to" / "cagey.db"
  target.parent.mkdir(parents=True, exist_ok=True)

  target.symlink_to(cagey_db)

.. testcode:: viewing-turbidity-states

    import sqlite3
    import cagey
    df = cagey.queries.turbidity_states_df(sqlite3.connect("path/to/cagey.db"))

.. testcode:: viewing-turbidity-states
  :hide:

  print(df)

.. testoutput:: viewing-turbidity-states

  shape: (402, 6)
  ┌────────────┬───────┬────────────────────┬─────────┬──────────┬────────┐
  │ experiment ┆ plate ┆ formulation_number ┆ di_name ┆ tri_name ┆ state  │
  │ ---        ┆ ---   ┆ ---                ┆ ---     ┆ ---      ┆ ---    │
  │ str        ┆ i64   ┆ i64                ┆ str     ┆ str      ┆ str    │
  ╞════════════╪═══════╪════════════════════╪═════════╪══════════╪════════╡
  │ AB-02-005  ┆ 1     ┆ 1                  ┆ Di1     ┆ TriA     ┆ turbid │
  │ AB-02-005  ┆ 1     ┆ 2                  ┆ Di2     ┆ TriA     ┆ turbid │
  │ AB-02-005  ┆ 1     ┆ 3                  ┆ Di3     ┆ TriA     ┆ turbid │
  │ AB-02-005  ┆ 1     ┆ 4                  ┆ Di4     ┆ TriA     ┆ turbid │
  │ AB-02-005  ┆ 1     ┆ 5                  ┆ Di5     ┆ TriA     ┆ turbid │
  │ …          ┆ …     ┆ …                  ┆ …       ┆ …        ┆ …      │
  │ AB-02-009  ┆ 2     ┆ 34                 ┆ Di34    ┆ TriP     ┆ turbid │
  │ AB-02-009  ┆ 2     ┆ 35                 ┆ Di21    ┆ TriT     ┆ turbid │
  │ AB-02-009  ┆ 2     ┆ 41                 ┆ Di33    ┆ TriQ     ┆ turbid │
  │ AB-02-009  ┆ 2     ┆ 42                 ┆ Di34    ┆ TriQ     ┆ turbid │
  │ AB-02-009  ┆ 2     ┆ 43                 ┆ Di21    ┆ TriU     ┆ turbid │
  └────────────┴───────┴────────────────────┴─────────┴──────────┴────────┘

.. testcleanup:: viewing-turbidity-states

  import shutil
  shutil.rmtree(temp_dir)
  os.chdir(intial_dir)


Adding new precursors and reactions
-----------------------------------

.. testsetup:: adding-new-precursors-and-reactions

  import os
  import tempfile
  from pathlib import Path
  import shutil
  import polars as pl

  pl.Config.set_tbl_width_chars(170)

  intial_dir = Path.cwd()
  temp_dir = Path(tempfile.mkdtemp()).absolute()
  cagey_db = Path(os.environ["CAGEY_DB"]).absolute()
  os.chdir(temp_dir)
  target = temp_dir / "path" / "to" / "cagey.db"
  target.parent.mkdir(parents=True, exist_ok=True)

  shutil.copy(cagey_db, target)

.. testcode:: adding-new-precursors-and-reactions

  import cagey
  import sqlite3

  connection = sqlite3.connect("path/to/cagey.db")
  cagey.queries.insert_precursors(
      connection=connection,
      precursors=[
          cagey.Precursor("DiBromine", "BrCCBr"),
          cagey.Precursor("TriFluorine", "FCC(F)CCF"),
          cagey.Precursor("TriIodine", "ICC(I)CCI"),
      ]
  )
  cagey.queries.insert_reactions(
      connection=connection,
      reactions=[
          cagey.Reaction(
              experiment="AB-03-example1",
              plate=1,
              formulation_number=3,
              di_name="DiBromine",
              tri_name="TriFluorine",
          ),
          cagey.Reaction(
              experiment="AB-03-example1",
              plate=1,
              formulation_number=4,
              di_name="DiBromine",
              tri_name="TriIodine",
          ),
      ]
  )

.. testcleanup:: adding-new-precursors-and-reactions

  shutil.rmtree(temp_dir)
  os.chdir(intial_dir)


==================
Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
