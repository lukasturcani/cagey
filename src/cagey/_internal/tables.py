from pathlib import Path

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


class MassSpecPeak(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
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
    id: int | None = Field(default=None, primary_key=True)
    mass_spec_peak_id: int = Field(foreign_key="massspecpeak.id")
    topology: str


def add_tables(database: Path) -> None:
    engine = create_engine(
        f"sqlite:///{database}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
