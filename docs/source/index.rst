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
as input for your scripts which perform data analysis. You can install cagey with

.. code-block:: bash

  pip install cagey


Working with the database
=========================


Viewing precursors
------------------

.. testsetup:: viewing-precursors

  import os
  import tempfile
  from pathlib import Path

  intial_dir = Path.cwd()
  temp_dir = Path(tempfile.mkdtemp()).absolute()
  cagey_db = Path(os.environ["CAGEY_DB"]).absolute()
  os.chdir(temp_dir)
  target = temp_dir / "path" / "to" / "cagey.db"
  target.parent.mkdir(parents=True, exist_ok=True)

  target.symlink_to(cagey_db)

.. testcode:: viewing-precursors

  import sqlite3
  import polars as pl

  df = pl.read_database(
      """
      SELECT
          precursors.name,
          precursors.smiles
      FROM
          precursors
      ORDER BY
          precursors.name
      """,
      sqlite3.connect("path/to/cagey.db"),
  )
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

  intial_dir = Path.cwd()
  temp_dir = Path(tempfile.mkdtemp()).absolute()
  cagey_db = Path(os.environ["CAGEY_DB"]).absolute()
  os.chdir(temp_dir)
  target = temp_dir / "path" / "to" / "cagey.db"
  target.parent.mkdir(parents=True, exist_ok=True)

  target.symlink_to(cagey_db)

.. testcode:: viewing-reactions

  import sqlite3
  import polars as pl

  df = pl.read_database(
      """
      SELECT
          reactions.experiment,
          reactions.plate,
          reactions.formulation_number,
          di.name AS di_name,
          tri.name AS tri_name
      FROM
          reactions
      LEFT JOIN
          precursors AS di
          ON reactions.di_name = di.name
      LEFT JOIN
          precursors AS tri
          ON reactions.tri_name = tri.name
      ORDER BY
          reactions.experiment,
          reactions.plate,
          reactions.formulation_number,
          di.name,
          tri.name
      """,
      sqlite3.connect("path/to/cagey.db"),
  )
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

  intial_dir = Path.cwd()
  temp_dir = Path(tempfile.mkdtemp()).absolute()
  cagey_db = Path(os.environ["CAGEY_DB"]).absolute()
  os.chdir(temp_dir)
  target = temp_dir / "path" / "to" / "cagey.db"
  target.parent.mkdir(parents=True, exist_ok=True)

  target.symlink_to(cagey_db)

.. testcode:: viewing-aldehyde-peaks

  import sqlite3
  import polars as pl

  df = pl.read_database(
      """
      SELECT
          reactions.experiment,
          reactions.plate,
          reactions.formulation_number,
          nmr_aldehyde_peaks.ppm,
          nmr_aldehyde_peaks.amplitude
      FROM
          nmr_aldehyde_peaks
      LEFT JOIN
          nmr_spectra
          ON nmr_aldehyde_peaks.nmr_spectrum_id = nmr_spectra.id
      LEFT JOIN
          reactions
          ON nmr_spectra.reaction_id = reactions.id
      ORDER BY
          reactions.experiment,
          reactions.plate,
          reactions.formulation_number,
          nmr_aldehyde_peaks.ppm
      """,
      sqlite3.connect("path/to/cagey.db"),
  )
  print(df)

.. testoutput:: viewing-aldehyde-peaks

  shape: (751, 5)
  ┌────────────┬───────┬────────────────────┬───────────┬───────────────┐
  │ experiment ┆ plate ┆ formulation_number ┆ ppm       ┆ amplitude     │
  │ ---        ┆ ---   ┆ ---                ┆ ---       ┆ ---           │
  │ str        ┆ i64   ┆ i64                ┆ f64       ┆ f64           │
  ╞════════════╪═══════╪════════════════════╪═══════════╪═══════════════╡
  │ AB-02-005  ┆ 1     ┆ 1                  ┆ 10.124944 ┆ 5.4689e6      │
  │ AB-02-005  ┆ 1     ┆ 1                  ┆ 10.157341 ┆ 10014.054688  │
  │ AB-02-005  ┆ 1     ┆ 2                  ┆ 10.247195 ┆ 6.4216e6      │
  │ AB-02-005  ┆ 1     ┆ 3                  ┆ 10.047315 ┆ 8.3831e6      │
  │ AB-02-005  ┆ 1     ┆ 3                  ┆ 10.088269 ┆ 10120.1875    │
  │ …          ┆ …     ┆ …                  ┆ …         ┆ …             │
  │ AB-02-009  ┆ 2     ┆ 42                 ┆ 9.74719   ┆ 1.2567e7      │
  │ AB-02-009  ┆ 2     ┆ 42                 ┆ 9.804036  ┆ 112459.875    │
  │ AB-02-009  ┆ 2     ┆ 42                 ┆ 9.809537  ┆ 23061.015625  │
  │ AB-02-009  ┆ 2     ┆ 42                 ┆ 10.104773 ┆ 656725.390625 │
  │ AB-02-009  ┆ 2     ┆ 43                 ┆ 10.026532 ┆ 204503.21875  │
  └────────────┴───────┴────────────────────┴───────────┴───────────────┘

.. testcleanup:: viewing-aldehyde-peaks

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
          cagey.Precursor("DiBro", "BrCCBr"),
          cagey.Precursor("TriF", "FCC(F)CCF"),
          cagey.Precursor("TriI", "ICC(I)CCI"),
      ]
  )
  cagey.queries.insert_reactions(
      connection=connection,
      reactions=[
          cagey.Reaction(
              experiment="AB-03-example1",
              plate=1,
              formulation_number=3,
              di_name="DiBro",
              tri_name="TriF",
          ),
          cagey.Reaction(
              experiment="AB-03-example1",
              plate=1,
              formulation_number=4,
              di_name="DiBro",
              tri_name="TriI",
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
