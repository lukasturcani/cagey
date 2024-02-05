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
    """Cage precursor molecules.

    Parameters:
        name: Human-usable name of the precursor molecule.
        smiles: SMILES representation of the precursor molecule.
    """

    name: str = Field(primary_key=True)
    """Human-usable of the precursor molecule."""
    smiles: str
    """SMILES representation of the precursor molecule."""


class Reaction(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("experiment", "plate", "formulation_number"),
    )

    id: int | None = Field(default=None, primary_key=True)
    experiment: str
    plate: int
    formulation_number: int
    di_name: str = Field(foreign_key="precursor.name")
    tri_name: str = Field(foreign_key="precursor.name")


class NmrSpectrum(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
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
    id: int | None = Field(default=None, primary_key=True)
    nmr_spectrum_id: int = Field(foreign_key="nmrspectrum.id")
    ppm: float
    amplitude: float

    nmr_spectrum: NmrSpectrum = Relationship(back_populates="aldehyde_peaks")


class NmrIminePeak(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    nmr_spectrum_id: int = Field(foreign_key="nmrspectrum.id")
    ppm: float
    amplitude: float

    nmr_spectrum: NmrSpectrum = Relationship(back_populates="imine_peaks")


class MassSpectrum(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
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
    """Peak in a mass spectrum.

    Parameters:
        id: Unique identifier of the peak.
        mass_spectrum_id:
            ID of the :class:`.MassSpectrum` this peak belongs to.
        di_count:
            Number of di-topic precursors in the cage responsible for the peak.
        tri_count:
            Number of tri-topic precursors in the cage responsible
            for the peak.
        adduct: Adduct of the peak.
        charge: Charge of the peak.
        calculated_mz: Predicted m/z of the cage responsible for the peak.
        spectrum_mz: The m/z of the cage peak in the spectrum.
        separation_mz: The m/z of the separation peak.
        intensity: Intensity of the peak.
    """

    id: int | None = Field(default=None, primary_key=True)
    """Unique identifier of the peak."""
    mass_spectrum_id: int = Field(foreign_key="massspectrum.id")
    """ID of the :class:`.MassSpectrum` this peak belongs to."""
    di_count: int
    """Number of di-topic precursors in the cage responsible for the peak."""
    tri_count: int
    """Number of tri-topic precursors in the cage responsible for the peak."""
    adduct: str
    """Adduct of the peak."""
    charge: int
    """Charge of the peak."""
    calculated_mz: float
    """Predicted m/z of the cage responsible for the peak."""
    spectrum_mz: float
    """The m/z of the cage peak in the spectrum."""
    separation_mz: float
    """The m/z of the separation peak."""
    intensity: float
    """Intensity of the peak."""
    mass_spectrum: MassSpectrum = Relationship(back_populates="peaks")
    """:class:`.MassSpectrum` this peak belongs to."""

    def get_ppm_error(self) -> float:
        """Get the ppm difference between the predicted and measured peaks."""
        return abs(
            (self.calculated_mz - self.spectrum_mz) / self.calculated_mz * 1e6
        )

    def get_separation(self) -> float:
        """Get the difference between the separation and cage peaks."""
        return self.separation_mz - self.spectrum_mz


class MassSpecTopologyAssignment(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    mass_spec_peak_id: int = Field(foreign_key="massspecpeak.id")
    topology: str


class TurbidityDissolvedReference(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    reaction_id: int = Field(foreign_key="reaction.id")
    dissolved_reference: float

    __table_args__ = (UniqueConstraint("reaction_id"),)


class TurbidityMeasurement(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    reaction_id: int = Field(foreign_key="reaction.id")
    time: str
    turbidity: float


class TurbidState(StrEnum):
    DISSOLVED = auto()
    TURBID = auto()
    UNSTABLE = auto()


class Turbidity(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    reaction_id: int = Field(foreign_key="reaction.id")
    state: TurbidState

    __table_args__ = (UniqueConstraint("reaction_id"),)


def add(database: Path) -> None:
    engine = create_engine(
        f"sqlite:///{database}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
