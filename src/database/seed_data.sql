-- Seed Data for Band Agent Database

-- Instrument Families
INSERT INTO instrument_family (family_name) VALUES
    ('Woodwinds'),
    ('Brass'),
    ('Strings'),
    ('Percussion');

-- Instruments
INSERT INTO instruments (instrument_name, family_id) VALUES
    ('Flute',          (SELECT family_id FROM instrument_family WHERE family_name = 'Woodwinds')),
    ('Clarinet',       (SELECT family_id FROM instrument_family WHERE family_name = 'Woodwinds')),
    ('Alto Saxophone', (SELECT family_id FROM instrument_family WHERE family_name = 'Woodwinds')),
    ('Trumpet',        (SELECT family_id FROM instrument_family WHERE family_name = 'Brass')),
    ('Trombone',       (SELECT family_id FROM instrument_family WHERE family_name = 'Brass')),
    ('Tuba',           (SELECT family_id FROM instrument_family WHERE family_name = 'Brass')),
    ('Violin',         (SELECT family_id FROM instrument_family WHERE family_name = 'Strings')),
    ('Cello',          (SELECT family_id FROM instrument_family WHERE family_name = 'Strings')),
    ('Snare Drum',     (SELECT family_id FROM instrument_family WHERE family_name = 'Percussion')),
    ('Marimba',        (SELECT family_id FROM instrument_family WHERE family_name = 'Percussion'));

-- Students (25 students, grades 9-12)
INSERT INTO students (first_name, last_name, grade) VALUES
    -- Grade 9
    ('Emma',      'Johnson',   9),
    ('Liam',      'Smith',     9),
    ('Olivia',    'Davis',     9),
    ('Noah',      'Wilson',    9),
    ('Ava',       'Martinez',  9),
    ('Ethan',     'Brown',     9),
    ('Elizabeth', 'King',      9),
    -- Grade 10
    ('Sophia',    'Garcia',    10),
    ('Mason',     'Taylor',    10),
    ('Isabella',  'Anderson',  10),
    ('Logan',     'Thomas',    10),
    ('Mia',       'Jackson',   10),
    ('Lucas',     'White',     10),
    -- Grade 11
    ('Charlotte', 'Harris',    11),
    ('James',     'Martin',    11),
    ('Amelia',    'Thompson',  11),
    ('Benjamin',  'Lee',       11),
    ('Harper',    'Moore',     11),
    ('Elijah',    'Clark',     11),
    -- Grade 12
    ('Evelyn',    'Lewis',     12),
    ('Alexander', 'Robinson',  12),
    ('Abigail',   'Walker',    12),
    ('William',   'Hall',      12),
    ('Emily',     'Young',     12),
    ('Michael',   'Allen',     12);


-- Plays (student plays instrument)
INSERT INTO plays (student_id, instrument_name) VALUES
    -- Grade 9
    ((SELECT student_id FROM students WHERE first_name = 'Emma'      AND last_name = 'Johnson'),  'Flute'),
    ((SELECT student_id FROM students WHERE first_name = 'Liam'      AND last_name = 'Smith'),    'Clarinet'),
    ((SELECT student_id FROM students WHERE first_name = 'Olivia'    AND last_name = 'Davis'),    'Trumpet'),
    ((SELECT student_id FROM students WHERE first_name = 'Noah'      AND last_name = 'Wilson'),   'Violin'),
    ((SELECT student_id FROM students WHERE first_name = 'Ava'       AND last_name = 'Martinez'), 'Alto Saxophone'),
    ((SELECT student_id FROM students WHERE first_name = 'Ethan'     AND last_name = 'Brown'),    'Trombone'),
    ((SELECT student_id FROM students WHERE first_name = 'Elizabeth' AND last_name = 'King'),     'Cello'),
    -- Grade 10
    ((SELECT student_id FROM students WHERE first_name = 'Sophia'    AND last_name = 'Garcia'),   'Flute'),
    ((SELECT student_id FROM students WHERE first_name = 'Mason'     AND last_name = 'Taylor'),   'Trumpet'),
    ((SELECT student_id FROM students WHERE first_name = 'Isabella'  AND last_name = 'Anderson'), 'Clarinet'),
    ((SELECT student_id FROM students WHERE first_name = 'Logan'     AND last_name = 'Thomas'),   'Tuba'),
    ((SELECT student_id FROM students WHERE first_name = 'Mia'       AND last_name = 'Jackson'),  'Violin'),
    ((SELECT student_id FROM students WHERE first_name = 'Lucas'     AND last_name = 'White'),    'Snare Drum'),
    -- Grade 11
    ((SELECT student_id FROM students WHERE first_name = 'Charlotte' AND last_name = 'Harris'),   'Alto Saxophone'),
    ((SELECT student_id FROM students WHERE first_name = 'James'     AND last_name = 'Martin'),   'Trombone'),
    ((SELECT student_id FROM students WHERE first_name = 'Amelia'    AND last_name = 'Thompson'), 'Flute'),
    ((SELECT student_id FROM students WHERE first_name = 'Benjamin'  AND last_name = 'Lee'),      'Trumpet'),
    ((SELECT student_id FROM students WHERE first_name = 'Harper'    AND last_name = 'Moore'),    'Cello'),
    ((SELECT student_id FROM students WHERE first_name = 'Elijah'    AND last_name = 'Clark'),    'Clarinet'),
    -- Grade 12
    ((SELECT student_id FROM students WHERE first_name = 'Evelyn'    AND last_name = 'Lewis'),    'Marimba'),
    ((SELECT student_id FROM students WHERE first_name = 'Alexander' AND last_name = 'Robinson'), 'Tuba'),
    ((SELECT student_id FROM students WHERE first_name = 'Abigail'   AND last_name = 'Walker'),   'Violin'),
    ((SELECT student_id FROM students WHERE first_name = 'William'   AND last_name = 'Hall'),     'Trumpet'),
    ((SELECT student_id FROM students WHERE first_name = 'Emily'     AND last_name = 'Young'),    'Snare Drum'),
    ((SELECT student_id FROM students WHERE first_name = 'Michael'   AND last_name = 'Allen'),    'Alto Saxophone');
