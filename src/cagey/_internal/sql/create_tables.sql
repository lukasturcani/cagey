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
CREATE INDEX IF NOT EXISTS reaction_index
ON reactions (experiment, plate, formulation_number);

CREATE TABLE IF NOT EXISTS nmr_spectra (
    id INTEGER PRIMARY KEY,
    reaction_id INTEGER NOT NULL,
    FOREIGN KEY (reaction_id) REFERENCES reactions (id)
);
CREATE INDEX IF NOT EXISTS nmr_spectrum_index
ON nmr_spectra (reaction_id);

CREATE TABLE IF NOT EXISTS nmr_aldehyde_peaks (
    id INTEGER PRIMARY KEY,
    nmr_spectrum_id INTEGER NOT NULL,
    ppm REAL NOT NULL,
    amplitude REAL NOT NULL,
    FOREIGN KEY (nmr_spectrum_id) REFERENCES nmr_spectra (id)
);
CREATE INDEX IF NOT EXISTS nmr_aldehyde_peak_index
ON nmr_aldehyde_peaks (nmr_spectrum_id);

CREATE TABLE IF NOT EXISTS nmr_imine_peaks (
    id INTEGER PRIMARY KEY,
    nmr_spectrum_id INTEGER NOT NULL,
    ppm REAL NOT NULL,
    amplitude REAL NOT NULL,
    FOREIGN KEY (nmr_spectrum_id) REFERENCES nmr_spectra (id)
);
CREATE INDEX IF NOT EXISTS nmr_imine_peak_index
ON nmr_imine_peaks (nmr_spectrum_id);

CREATE TABLE IF NOT EXISTS mass_spectra (
    id INTEGER PRIMARY KEY,
    reaction_id INTEGER NOT NULL,
    FOREIGN KEY (reaction_id) REFERENCES reactions (id)
);
CREATE INDEX IF NOT EXISTS mass_spectrum_index
ON mass_spectra (reaction_id);

CREATE TABLE IF NOT EXISTS mass_spectrum_peaks (
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
CREATE INDEX IF NOT EXISTS mass_spectrum_peak_index
ON mass_spectrum_peaks (mass_spectrum_id);

CREATE TABLE IF NOT EXISTS mass_spectrum_topology_assignments (
    id INTEGER PRIMARY KEY,
    mass_spectrum_peak_id INTEGER NOT NULL,
    topology TEXT NOT NULL,
    FOREIGN KEY (mass_spectrum_peak_id) REFERENCES mass_spectrum_peaks (id)
);
CREATE INDEX IF NOT EXISTS mass_spectrum_topology_assignment_index
ON mass_spectrum_topology_assignments (mass_spectrum_peak_id);

CREATE TABLE IF NOT EXISTS turbidity_dissolved_references (
    id INTEGER PRIMARY KEY,
    reaction_id INTEGER NOT NULL,
    dissolved_reference REAL NOT NULL,
    FOREIGN KEY (reaction_id) REFERENCES reactions (id),
    UNIQUE (reaction_id)
);
CREATE INDEX IF NOT EXISTS turbidity_dissolved_reference_index
ON turbidity_dissolved_references (reaction_id);

CREATE TABLE IF NOT EXISTS turbidity_measurements (
    id INTEGER PRIMARY KEY,
    reaction_id INTEGER NOT NULL,
    time DATETIME NOT NULL,
    turbidity REAL NOT NULL,
    FOREIGN KEY (reaction_id) REFERENCES reactions (id)
);
CREATE INDEX IF NOT EXISTS turbidity_measurement_index
ON turbidity_measurements (reaction_id);

CREATE TABLE IF NOT EXISTS turbidities (
    id INTEGER PRIMARY KEY,
    reaction_id INTEGER NOT NULL,
    state TEXT CHECK (state IN ('dissolved', 'turbid', 'unstable')) NOT NULL,
    FOREIGN KEY (reaction_id) REFERENCES reactions (id),
    UNIQUE (reaction_id)
);
CREATE INDEX IF NOT EXISTS turbidity_index
ON turbidities (reaction_id);

COMMIT;
