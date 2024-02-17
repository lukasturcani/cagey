BEGIN;

CREATE TABLE IF NOT EXISTS precursors (
    name TEXT PRIMARY KEY,
    smiles TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reactions (
    id INTEGER PRIMARY KEY,
    experiment TEXT NOT NULL,
    plate INTEGER NOT NULL,
    formulation_number INTEGER NOT NULL,
    di_name TEXT NOT NULL,
    tri_name TEXT NOT NULL,
    FOREIGN KEY (di_name) REFERENCES precursors (name),
    FOREIGN KEY (tri_name) REFERENCES precursors (name),
    UNIQUE (experiment, plate, formulation_number)
);

CREATE TABLE IF NOT EXISTS nmr_spectra (
    id INTEGER PRIMARY KEY,
    reaction_id INTEGER NOT NULL,
    FOREIGN KEY (reaction_id) REFERENCES reactions (id)
);

CREATE TABLE IF NOT EXISTS nmr_aldehyde_peaks (
    id INTEGER PRIMARY KEY,
    nmr_spectrum_id INTEGER NOT NULL,
    ppm REAL NOT NULL,
    amplitude REAL NOT NULL,
    FOREIGN KEY (nmr_spectrum_id) REFERENCES nmr_spectra (id)
);

CREATE TABLE IF NOT EXISTS nmr_imine_peaks (
    id INTEGER PRIMARY KEY,
    nmr_spectrum_id INTEGER NOT NULL,
    ppm REAL NOT NULL,
    amplitude REAL NOT NULL,
    FOREIGN KEY (nmr_spectrum_id) REFERENCES nmr_spectra (id)
);

CREATE TABLE IF NOT EXISTS mass_spectra (
    id INTEGER PRIMARY KEY,
    reaction_id INTEGER NOT NULL,
    FOREIGN KEY (reaction_id) REFERENCES reactions (id)
);

CREATE TABLE IF NOT EXISTS mass_specrum_peaks (
    id INTEGER PRIMARY KEY,
    mass_spectrum_id INTEGER NOT NULL,
    di_count INTEGER NOT NULL,
    tri_count INTEGER NOT NULL,
    adduct TEXT NOT NULL,
    charge INTEGER NOT NULL,
    calculated_mz REAL NOT NULL,
    spectrum_mz REAL NOT NULL,
    separation_mz REAL NOT NULL,
    intensity REAL NOT NULL,
    FOREIGN KEY (mass_spectrum_id) REFERENCES mass_spectra (id)
);

CREATE TABLE IF NOT EXISTS mass_spectrum_topology_assignments (
    id INTEGER PRIMARY KEY,
    mass_spectrum_peak_id INTEGER NOT NULL,
    topology TEXT NOT NULL,
    FOREIGN KEY (mass_spectrum_peak_id) REFERENCES mass_specrum_peaks (id)
);

CREATE TABLE IF NOT EXISTS turbidity_dissolved_references (
    id INTEGER PRIMARY KEY,
    reaction_id INTEGER NOT NULL,
    dissolved_reference REAL NOT NULL,
    FOREIGN KEY (reaction_id) REFERENCES reactions (id),
    UNIQUE (reaction_id)
);

CREATE TABLE IF NOT EXISTS turbidity_measurements (
    id INTEGER PRIMARY KEY,
    reaction_id INTEGER NOT NULL,
    time REAL NOT NULL,
    turbidity REAL NOT NULL,
    FOREIGN KEY (reaction_id) REFERENCES reactions (id)
);

CREATE TABLE IF NOT EXISTS turbidities (
    id INTEGER PRIMARY KEY,
    reaction_id INTEGER NOT NULL,
    state TEXT CHECK (state IN ('dissolved', 'turbid', 'unstable')) NOT NULL,
    FOREIGN KEY (reaction_id) REFERENCES reactions (id),
    UNIQUE (reaction_id)
);

COMMIT;
