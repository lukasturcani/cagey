from collections.abc import Iterable
from itertools import product
from sqlite3 import Connection

from cagey._internal.queries import (
    Precursor,
    Reaction,
    insert_precursors,
    insert_reactions,
)


def add_precursors(connection: Connection, *, commit: bool = True) -> None:
    """Add initial precursor data to the database.

    Parameters:
        connection: The SQLite database connection.
        commit: Whether to commit the transaction.
    """
    precursors = {
        "Di1": "O=Cc1cccc(C=O)c1",
        "Di2": "CC(C)(C)c1cc(C=O)c(O)c(C=O)c1",
        "Di3": "O=Cc1cc2sc(C=O)cc2s1",
        "Di4": "O=Cc1ccc(C=O)cc1",
        "Di5": "O=Cc1c(F)c(F)c(C=O)c(F)c1F",
        "Di6": "O=Cc1ccc(-c2ccc(C=O)cc2)cc1",
        "Di7": "O=Cc1c2ccccc2c(C=O)c2ccccc12",
        "Di8": "O=Cc1ccc2ccc3ccc(C=O)nc3c2n1",
        "Di9": "O=Cc1ccsc1C=O",
        "Di10": "O=Cc1ccccc1C=O",
        "Di11": "Cn1nc(-c2ccc(C=O)cc2)cc1C=O",
        "Di12": "CC(C=O)=Cc1ccc(C=C(C)C=O)cc1",
        "Di13": "COc1cc(C=O)ccc1OCCOc1ccc(C=O)cc1OC",
        "Di14": "Cn1nc2c(C=O)cccc2c1C=O",
        "Di15": "O=Cc1ccc(OCCCOc2ccc(C=O)cc2)cc1",
        "Di16": "CCCCC(CC)COc1cc(C=O)c(OC)cc1C=O",
        "Di17": "NCCN",
        "Di18": "CC(C)(CN)CN",
        "Di19": "N[C@H]1CN(Cc2ccccc2)C[C@@H]1N",
        "Di20": "N[C@H]([C@H](C1=CC=CC=C1)N)C2=CC=CC=C2",
        "Di21": "Nc1ccc(Oc2ccc(N)cc2)cc1",
        "Di22": "NC1=NON=C1N",
        "Di23": "N[C@H]1CCC[C@H](C1)N",
        "Di24": "N[C@@H]1[C@H](CCCC1)N",
        "Di25": "NCCCCCCNCCCCCCN",
        "Di26": "NCCCCCCN",
        "Di27": "NCc1ccc(CN)cc1",
        "Di28": "NCC1CCC(CN)CC1",
        "Di29": "CN(CCCN)CCCN",
        "Di30": "NCCOCCN",
        "Di31": "NCC1=CC(CN)=CC=C1",
        "Di32": "NCC(CN)O",
        "Di33": "NCCCC[C@H](N)C(=O)O",
        "Di34": "N[C@H]1CC[C@H](N)CC1",
        "TriA": "Nc1nc(N)nc(N)n1",
        "TriB": "Cc1c(CN)c(C)c(CN)c(C)c1CN",
        "TriC": "NCCN(CCN)CCN",
        "TriD": "CCc1c(CN)c(CC)c(CN)c(CC)c1CN",
        "TriE": "NCCCN(CCCN)CCCN",
        "TriF": "NC1CC(N)CC(N)C1",
        "TriG": "O=Cc1cc(C=O)cc(C=O)c1",
        "TriH": "O=Cc1ccc(-c2cc(-c3ccc(C=O)cc3)cc(-c3ccc(C=O)cc3)c2)cc1",
        "TriI": "O=Cc1cc(C=O)c(O)c(C=O)c1",
        "TriJ": "O=Cc1ccc(N(c2ccc(C=O)cc2)c2ccc(C=O)cc2)cc1",
        "TriK": "O=Cc1ccc(-c2nc(-c3ccc(C=O)cc3)nc(-c3ccc(C=O)cc3)n2)cc1",
        "TriL": "O=Cc1ccc(C#Cc2cc(C#Cc3ccc(C=O)cc3)cc(C#Cc3ccc(C=O)cc3)c2)cc1",
        "TriM": "O=Cc1cccc(-c2cc(-c3cccc(C=O)c3)cc(-c3cccc(C=O)c3)c2)c1",
        "TriN": "O=Cc1ccccc1-c1cc(-c2ccccc2C=O)cc(-c2ccccc2C=O)c1",
        "TriO": "O=Cc1cc(-c2cc(-c3csc(C=O)c3)cc(-c3csc(C=O)c3)c2)cs1",
        "TriP": "O=Cc1ccc(-c2cc(-c3ccc(C=O)o3)cc(-c3ccc(C=O)o3)c2)o1",
        "TriQ": (
            "O=CC=Cc1ccc(-c2cc(-c3ccc(C=CC=O)cc3)"
            "cc(-c3ccc(C=CC=O)cc3)c2)cc1"
        ),
        "TriR": "O=Cc1ccc(OCc2cc(COc3ccc(C=O)cc3)cc(COc3ccc(C=O)cc3)c2)cc1",
        "TriS": "O=Cc1ccc(C#Cc2cc(C=O)cc(C=O)c2)cc1",
        "TriT": "O=Cc1c(O)c(C=O)c(O)c(C=O)c1O",
        "TriU": "O=Cc1ccc(C=Cc2cc(C=Cc3ccc(C=O)cc3)cc(C=Cc3ccc(C=O)cc3)c2)cc1",
    }
    insert_precursors(
        connection,
        precursors=(
            Precursor(name=name, smiles=smiles)
            for name, smiles in precursors.items()
        ),
        commit=commit,
    )


def add_ab_02_005_data(
    connection: Connection,
    *,
    commit: bool = True,
) -> None:
    """Add reaction data for experiment AB-02-005 to the database.

    Parameters:
        connection: The SQLite database connection.
        commit: Whether to commit the transaction.
    """
    _add_data_helper(
        dis=("Di1", "Di2", "Di3", "Di4", "Di5", "Di6", "Di7", "Di8"),
        tris=("TriA", "TriB", "TriC", "TriD", "TriE", "TriF"),
        experiment="AB-02-005",
        plate=1,
        connection=connection,
    )
    _add_data_helper(
        dis=("Di17", "Di18", "Di19", "Di20", "Di21", "Di22", "Di23", "Di24"),
        tris=("TriG", "TriH", "TriI", "TriJ", "TriK", "TriL"),
        experiment="AB-02-005",
        plate=2,
        connection=connection,
    )
    _add_data_helper(
        dis=("Di9", "Di10", "Di11", "Di12", "Di13", "Di14", "Di15", "Di16"),
        tris=("TriA", "TriB", "TriC", "TriD", "TriE", "TriF"),
        experiment="AB-02-005",
        plate=3,
        connection=connection,
    )
    _add_data_helper(
        dis=("Di17", "Di18", "Di19", "Di20", "Di21", "Di22", "Di23", "Di24"),
        tris=("TriM", "TriN", "TriO", "TriP", "TriQ", "TriR"),
        experiment="AB-02-005",
        plate=4,
        connection=connection,
    )
    if commit:
        connection.commit()


def add_ab_02_007_data(connection: Connection, *, commit: bool = True) -> None:
    """Add reaction data for experiment AB-02-007 to the database.

    Parameters:
        connection: The SQLite database connection.
        commit: Whether to commit the transaction.
    """
    _add_data_helper(
        dis=("Di18", "Di19", "Di20", "Di22", "Di23", "Di24", "Di25", "Di26"),
        tris=("TriG", "TriH", "TriI", "TriJ", "TriK", "TriR"),
        experiment="AB-02-007",
        plate=1,
        connection=connection,
    )
    _add_data_helper(
        dis=("Di27", "Di28", "Di29", "Di30", "Di31", "Di32", "Di33", "Di34"),
        tris=("TriG", "TriH", "TriI", "TriJ", "TriK", "TriR"),
        experiment="AB-02-007",
        plate=2,
        connection=connection,
    )
    _add_data_helper(
        dis=("Di18", "Di19", "Di20", "Di22", "Di23", "Di24", "Di25", "Di26"),
        tris=("TriS", "TriT", "TriU"),
        experiment="AB-02-007",
        plate=3,
        connection=connection,
    )
    _add_data_helper(
        dis=("Di27", "Di28", "Di29", "Di30", "Di31", "Di32", "Di33", "Di34"),
        tris=("TriS", "TriT", "TriU"),
        experiment="AB-02-007",
        plate=3,
        connection=connection,
        start_tri_index=3,
    )
    _add_data_helper(
        dis=("Di27", "Di28", "Di29", "Di30", "Di31", "Di32", "Di33", "Di34"),
        tris=("TriG", "TriH", "TriI", "TriJ", "TriK", "TriR"),
        experiment="AB-02-007",
        plate=4,
        connection=connection,
    )
    if commit:
        connection.commit()


def add_ab_02_009_data(connection: Connection, *, commit: bool = True) -> None:
    """Add reaction data for experiment AB-02-009 to the database.

    Parameters:
        connection: The SQLite database connection.
        commit: Whether to commit the transaction.
    """
    _add_data_helper(
        dis=("Di25", "Di26", "Di27", "Di28", "Di29", "Di30", "Di31", "Di32"),
        tris=("TriL", "TriM", "TriN", "TriO", "TriP", "TriQ"),
        experiment="AB-02-009",
        plate=1,
        connection=connection,
    )
    insert_reactions(
        connection,
        [
            Reaction(
                experiment="AB-02-009",
                plate=2,
                formulation_number=1,
                di_name="Di33",
                tri_name="TriL",
            ),
            Reaction(
                experiment="AB-02-009",
                plate=2,
                formulation_number=2,
                di_name="Di34",
                tri_name="TriL",
            ),
            Reaction(
                experiment="AB-02-009",
                plate=2,
                formulation_number=3,
                di_name="Di19",
                tri_name="TriS",
            ),
            Reaction(
                experiment="AB-02-009",
                plate=2,
                formulation_number=9,
                di_name="Di33",
                tri_name="TriM",
            ),
            Reaction(
                experiment="AB-02-009",
                plate=2,
                formulation_number=10,
                di_name="Di34",
                tri_name="TriM",
            ),
            Reaction(
                experiment="AB-02-009",
                plate=2,
                formulation_number=11,
                di_name="Di19",
                tri_name="TriT",
            ),
            Reaction(
                experiment="AB-02-009",
                plate=2,
                formulation_number=17,
                di_name="Di33",
                tri_name="TriN",
            ),
            Reaction(
                experiment="AB-02-009",
                plate=2,
                formulation_number=18,
                di_name="Di34",
                tri_name="TriN",
            ),
            Reaction(
                experiment="AB-02-009",
                plate=2,
                formulation_number=19,
                di_name="Di19",
                tri_name="TriU",
            ),
            Reaction(
                experiment="AB-02-009",
                plate=2,
                formulation_number=25,
                di_name="Di33",
                tri_name="TriO",
            ),
            Reaction(
                experiment="AB-02-009",
                plate=2,
                formulation_number=26,
                di_name="Di34",
                tri_name="TriO",
            ),
            Reaction(
                experiment="AB-02-009",
                plate=2,
                formulation_number=27,
                di_name="Di21",
                tri_name="TriS",
            ),
            Reaction(
                experiment="AB-02-009",
                plate=2,
                formulation_number=33,
                di_name="Di33",
                tri_name="TriP",
            ),
            Reaction(
                experiment="AB-02-009",
                plate=2,
                formulation_number=34,
                di_name="Di34",
                tri_name="TriP",
            ),
            Reaction(
                experiment="AB-02-009",
                plate=2,
                formulation_number=35,
                di_name="Di21",
                tri_name="TriT",
            ),
            Reaction(
                experiment="AB-02-009",
                plate=2,
                formulation_number=41,
                di_name="Di33",
                tri_name="TriQ",
            ),
            Reaction(
                experiment="AB-02-009",
                plate=2,
                formulation_number=42,
                di_name="Di34",
                tri_name="TriQ",
            ),
            Reaction(
                experiment="AB-02-009",
                plate=2,
                formulation_number=43,
                di_name="Di21",
                tri_name="TriU",
            ),
        ],
        commit=False,
    )
    if commit:
        connection.commit()


def _add_data_helper(  # noqa: PLR0913
    dis: Iterable[str],
    tris: Iterable[str],
    experiment: str,
    plate: int,
    connection: Connection,
    start_tri_index: int = 0,
) -> None:
    insert_reactions(
        connection,
        reactions=(
            Reaction(
                experiment=experiment,
                plate=plate,
                formulation_number=(di_index + 1) + (tri_index * 8),
                di_name=di,
                tri_name=tri,
            )
            for (di_index, di), (tri_index, tri) in product(
                enumerate(dis), enumerate(tris, start_tri_index)
            )
        ),
        commit=False,
    )
