a = """
def get_ms_spectrum_from_file(  # noqa: PLR0913
    path: Path,
    engine: Engine,
    *,
    calculated_peak_tolerance: float = 0.1,
    separation_peak_tolerance: float = 0.1,
    max_ppm_error: float = 10,
    max_separation: float = 0.02,
    min_peak_height: float = 1e4,
) -> MassSpectrum:
    reaction_key = ReactionKey.from_ms_path(path)
    with Session(engine) as session:
        Di = aliased(Precursor)  # noqa: N806
        Tri = aliased(Precursor)  # noqa: N806
        reaction_query = select(Reaction, Di, Tri).where(
            Reaction.experiment == reaction_key.experiment,
            Reaction.plate == reaction_key.plate,
            Reaction.formulation_number == reaction_key.formulation_number,
            Di.name == Reaction.di_name,
            Tri.name == Reaction.tri_name,
        )
        reaction, di, tri = session.exec(reaction_query).one()
        spectrum = _get_ms_spectrum(
            path=path,
            reaction=reaction,
            di=di,
            tri=tri,
            calculated_peak_tolerance=calculated_peak_tolerance,
            separation_peak_tolerance=separation_peak_tolerance,
            max_ppm_error=max_ppm_error,
            max_separation=max_separation,
            min_peak_height=min_peak_height,
        )
        for peak_id, peak in enumerate(spectrum.peaks, 1):
            peak.id = peak_id
    return spectrum

def get_ms_topology_assignments_from_file(  # noqa: PLR0913
    path: Path,
    engine: Engine,
    *,
    calculated_peak_tolerance: float = 0.1,
    separation_peak_tolerance: float = 0.1,
    max_ppm_error: float = 10,
    max_separation: float = 0.02,
    min_peak_height: float = 1e4,
) -> pl.DataFrame:
    spectrum = get_ms_spectrum_from_file(
        path=path,
        engine=engine,
        calculated_peak_tolerance=calculated_peak_tolerance,
        separation_peak_tolerance=separation_peak_tolerance,
        max_ppm_error=max_ppm_error,
        max_separation=max_separation,
        min_peak_height=min_peak_height,
    )
    topologies = tuple(get_topologies(spectrum))
    assignments = pl.DataFrame(
        {
            "mass_spec_peak_id": list(
                map(attrgetter("mass_spec_peak_id"), topologies)
            ),
            "topology": list(map(attrgetter("topology"), topologies)),
        }
    )
    return assignments.join(
        spectrum.get_peak_df(), on="mass_spec_peak_id", how="left"
    )

"""
