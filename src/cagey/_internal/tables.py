from enum import StrEnum, auto
from operator import attrgetter
from pathlib import Path

import polars as pl
from sqlmodel import (
    Field,
    Relationship,
    SQLModel,
    UniqueConstraint,
    create_engine,
)
from sqlmodel.pool import StaticPool


class Precursor(SQLModel, table=True):
    name: str = Field(primary_key=True)
    smiles: str


class Reaction(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("experiment", "plate", "formulation_number"),
    )

    id: int | None = Field(default=None, primary_key=True)  # noqa: A003
    experiment: str
    plate: int
    formulation_number: int
    di_name: str = Field(foreign_key="precursor.name")
    tri_name: str = Field(foreign_key="precursor.name")


class NmrSpectrum(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)  # noqa: A003
    reaction_id: int = Field(foreign_key="reaction.id")

    aldehyde_peaks: list["NmrAldehydePeak"] = Relationship(
        back_populates="nmr_spectrum",
    )
    imine_peaks: list["NmrIminePeak"] = Relationship(
        back_populates="nmr_spectrum"
    )

    def get_aldehyde_peak_df(self) -> pl.DataFrame:
        return pl.DataFrame(
            {
                "peak_id": list(map(attrgetter("id"), self.aldehyde_peaks)),
                "ppm": list(map(attrgetter("ppm"), self.aldehyde_peaks)),
                "amplitude": list(
                    map(attrgetter("amplitude"), self.aldehyde_peaks)
                ),
            }
        )

    def get_imine_peak_df(self) -> pl.DataFrame:
        return pl.DataFrame(
            {
                "peak_id": list(map(attrgetter("id"), self.imine_peaks)),
                "ppm": list(map(attrgetter("ppm"), self.imine_peaks)),
                "amplitude": list(
                    map(attrgetter("amplitude"), self.imine_peaks)
                ),
            }
        )


class NmrAldehydePeak(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)  # noqa: A003
    nmr_spectrum_id: int = Field(foreign_key="nmrspectrum.id")
    ppm: float
    amplitude: float

    nmr_spectrum: NmrSpectrum = Relationship(back_populates="aldehyde_peaks")


class NmrIminePeak(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)  # noqa: A003
    nmr_spectrum_id: int = Field(foreign_key="nmrspectrum.id")
    ppm: float
    amplitude: float

    nmr_spectrum: NmrSpectrum = Relationship(back_populates="imine_peaks")


class MassSpectrum(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)  # noqa: A003
    reaction_id: int = Field(foreign_key="reaction.id")

    peaks: list["MassSpecPeak"] = Relationship(back_populates="mass_spectrum")

    def get_peak_df(self) -> pl.DataFrame:
        return pl.DataFrame(
            {
                "mass_spec_peak_id": list(map(attrgetter("id"), self.peaks)),
                "di_count": list(map(attrgetter("di_count"), self.peaks)),
                "tri_count": list(map(attrgetter("tri_count"), self.peaks)),
                "adduct": list(map(attrgetter("adduct"), self.peaks)),
                "charge": list(map(attrgetter("charge"), self.peaks)),
                "calculated_mz": list(
                    map(attrgetter("calculated_mz"), self.peaks)
                ),
                "spectrum_mz": list(
                    map(attrgetter("spectrum_mz"), self.peaks)
                ),
                "separation_mz": list(
                    map(attrgetter("separation_mz"), self.peaks)
                ),
                "intensity": list(map(attrgetter("intensity"), self.peaks)),
            }
        ).with_columns(
            ppm_error=get_ppm_error(),
            separation=get_separation(),
        )


def get_ppm_error() -> pl.Expr:
    return (
        (pl.col("calculated_mz") - pl.col("spectrum_mz"))
        / pl.col("calculated_mz")
        * pl.lit(1e6)
    ).abs()


def get_separation() -> pl.Expr:
    return (pl.col("separation_mz") - pl.col("spectrum_mz")) - (
        1 / pl.col("charge")
    )


class MassSpecPeak(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)  # noqa: A003
    mass_spectrum_id: int = Field(foreign_key="massspectrum.id")
    di_count: int
    tri_count: int
    adduct: str
    charge: int
    calculated_mz: float
    spectrum_mz: float
    separation_mz: float
    intensity: float

    mass_spectrum: MassSpectrum = Relationship(back_populates="peaks")

    def get_ppm_error(self) -> float:
        return abs(
            (self.calculated_mz - self.spectrum_mz) / self.calculated_mz * 1e6
        )

    def get_separation(self) -> float:
        return self.separation_mz - self.spectrum_mz


class MassSpecTopologyAssignment(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)  # noqa: A003
    mass_spec_peak_id: int = Field(foreign_key="massspecpeak.id")
    topology: str


class TurbidState(StrEnum):
    DISSOLVED = auto()
    TURBID = auto()
    NOT_DETERMINED = auto()


class Turbidity(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)  # noqa: A003
    reaction_id: int = Field(foreign_key="reaction.id")
    state: TurbidState

    __table_args__ = (UniqueConstraint("reaction_id"),)


def add_tables(database: Path) -> None:
    engine = create_engine(
        f"sqlite:///{database}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
