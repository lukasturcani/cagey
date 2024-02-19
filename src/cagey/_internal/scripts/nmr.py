a = """

def get_nmr_aldehyde_peaks_from_file(
    path: Path,
    engine: Engine,
) -> pl.DataFrame:
    reaction_data = ReactionData.from_nmr_title(path)
    with Session(engine) as session:
        reaction_query = select(Reaction).where(
            Reaction.experiment == reaction_data.experiment,
            Reaction.plate == reaction_data.plate,
            Reaction.formulation_number == reaction_data.formulation_number,
        )
        reaction = session.exec(reaction_query).one()
    spectrum = _get_nmr_spectrum(path.parent, reaction)
    for peak_id, peak in enumerate(spectrum.aldehyde_peaks, 1):
        peak.id = peak_id
    return spectrum.get_aldehyde_peak_df()


def get_nmr_imine_peaks_from_file(
    path: Path,
    engine: Engine,
) -> pl.DataFrame:
    reaction_data = ReactionData.from_nmr_title(path)
    with Session(engine) as session:
        reaction_query = select(Reaction).where(
            Reaction.experiment == reaction_data.experiment,
            Reaction.plate == reaction_data.plate,
            Reaction.formulation_number == reaction_data.formulation_number,
        )
        reaction = session.exec(reaction_query).one()
    spectrum = _get_nmr_spectrum(path.parent, reaction)
    for peak_id, peak in enumerate(spectrum.imine_peaks, 1):
        peak.id = peak_id
    return spectrum.get_imine_peak_df()
"""
