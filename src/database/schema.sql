CREATE TABLE instrument_family (
    family_id   SERIAL PRIMARY KEY,
    family_name VARCHAR(50) NOT NULL UNIQUE  -- woodwinds, strings, brass, percussion
);

CREATE TABLE instruments (
    instrument_name VARCHAR(100) PRIMARY KEY,
    family_id       INT NOT NULL REFERENCES instrument_family(family_id)
);

CREATE TABLE students (
    student_id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name  VARCHAR(100) NOT NULL,
    grade      INT NOT NULL CHECK (grade BETWEEN 9 AND 12)
);

CREATE TABLE instrument_inventory (
    serial_number   VARCHAR(100) PRIMARY KEY,
    instrument_name VARCHAR(100) NOT NULL REFERENCES instruments(instrument_name),
    condition       VARCHAR(20)  NOT NULL DEFAULT 'good'
                    CHECK (condition IN ('good', 'fair', 'damaged', 'retired'))
);

-- NULL return_date means the instrument is currently checked out
CREATE TABLE checkout_history (
    checkout_id   SERIAL PRIMARY KEY,
    student_id    INT          NOT NULL REFERENCES students(student_id),
    serial_number VARCHAR(100) NOT NULL REFERENCES instrument_inventory(serial_number),
    checkout_date DATE         NOT NULL DEFAULT CURRENT_DATE,
    return_date   DATE
);

CREATE TABLE music (
    music_id   SERIAL PRIMARY KEY,
    title      VARCHAR(200) NOT NULL,
    composer   VARCHAR(100),
    difficulty INT CHECK (difficulty BETWEEN 1 AND 6)
);

-- Associative entity for music <-> instruments (many-to-many)
CREATE TABLE arranged_for (
    music_id        INT          NOT NULL REFERENCES music(music_id),
    instrument_name VARCHAR(100) NOT NULL REFERENCES instruments(instrument_name),
    parts_needed    INT          NOT NULL DEFAULT 1 CHECK (parts_needed > 0),
    PRIMARY KEY (music_id, instrument_name)
);

-- Junction table for students <-> instruments (many-to-many, the "plays" relationship)
CREATE TABLE plays (
    student_id      INT          NOT NULL REFERENCES students(student_id),
    instrument_name VARCHAR(100) NOT NULL REFERENCES instruments(instrument_name),
    PRIMARY KEY (student_id, instrument_name)
);
