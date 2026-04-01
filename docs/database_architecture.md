
# Database Architecture

The database is a Neon Postgres database with five tables:

- **Students:** Students in the ensemble
- **Music:** Sheet music to be played
- **Instruments:** Instruments that a student can play or appear in music
- **Instrument Family:** Category that instruments belong to (brass, woodwinds, string, percussion)
- **Instrument Inventory:** Inventory of instruments to be checked out to students

There are three associative entities, mapping relationships between the tables:

- **Plays:** Maps Students and Instruments (Which students play which instrument(s))
- **Arranged For:** Maps Music and the Instruments (The instruments arranged for the music piece)
- **Checkout History:** Maps Students and Instrument Inventory (Each instrument in the inventory keeps a history of each checkout, including the student, checkout date, and return date. A `NULL` return date indicates the instrument is currently checkout out to a student)

## Database ER Diagram

![ER Diagram](diagrams/er_diagram.svg)

## Database Schema

**students** (student_id, first_name, last_name, grade)
**music** (music_id, title, composer, difficulty)
**instruments** (instrument_name, family_id)
**instrument_family** (family_id, family_name)
**instrument_inventory** (serial_number, instrument_name, condition)
**plays** (student_id, instrument_name)
**arranged_for** (music_id, instrument_name, parts_needed)
**checkout_history** (checkout_id, student_id, serial_number, checkout_date, return_date)
