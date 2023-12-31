from random import randint
from .musicType import *

note_name_dict = {
    "C": 0,
    "C#": 1,
    "Cb": -1,
    "D": 2,
    "D#": 3,
    "Db": 1,
    "E": 4,
    "E#": 5,
    "Eb": 3,
    "F": 5,
    "Fb": 4,
    "G": 7,
    "G#": 8,
    "Gb": 6,
    "A": 9,
    "A#": 10,
    "Ab": 8,
    "B": 11,
    "B#": 12,
    "Bb": 10,
}


# offset of the notes in the major mode and minor mode
major_offset = (0, 2, 4, 5, 7, 9, 11)
minor_offset = (0, 2, 3, 5, 7, 8, 10)

# The range of notes to be generated
NOTE_MIN = 60  # C4
NOTE_MAX = 84  # C6


class Note:
    def __init__(self, pitch: Pitch_T, length: int, start_time: int, velocity: int):
        # Here the "time" is "tick" in mido actually
        self.pitch = pitch
        self.length = length
        self.start_time = start_time
        self.velocity = velocity

    def __str__(self):
        pitch = self.pitch_to_name(self.pitch)
        return f"{pitch}: length={self.length} start={self.start_time} velocity={self.velocity}"

    @property
    def end_time(self):
        return self.start_time + self.length

    @staticmethod
    def in_mode(pitch: Pitch_T, key: Key_T):
        """Judge if the note is in the given mode."""
        if key.endswith("m"):
            # minor mode
            base = note_name_dict[key[:-1]]
            return (pitch - base) % 12 in minor_offset
        else:
            # major mode
            base = note_name_dict[key]
            return (pitch - base) % 12 in major_offset

    @staticmethod
    def random_pitch_in_mode(
        key: Key_T, min_pitch: Pitch_T = NOTE_MIN, max_pitch: Pitch_T = NOTE_MAX
    ):
        """Generate a random note in the given mode
        with the pitch in the range [min_pitch, max_pitch]."""
        while True:
            pitch = randint(max(min_pitch, NOTE_MIN), min(max_pitch, NOTE_MAX))
            if Note.in_mode(pitch, key):
                return pitch

    @staticmethod
    def ord_in_mode(pitch: Pitch_T, key: Key_T):
        """Get the order of the note in the given mode.
        For example, in C major, C is 1, D is 2, E is 3, etc.
        Raise error if the note is not in the mode."""
        if key.endswith("m"):
            # minor mode
            base = note_name_dict[key[:-1]]
            return minor_offset.index((pitch - base) % 12) + 1
        else:
            # major mode
            base = note_name_dict[key]
            return major_offset.index((pitch - base) % 12) + 1

    @staticmethod
    def name_to_pitch(note_name: str) -> Pitch_T:
        """Convert a note name to a pitch.
        For example, "C4" -> 60.

        If you want to convert a key to a pitch,
        use `key_to_pitch()` instead."""
        octave = note_name[-1]
        name = note_name[:-1]
        pitch = note_name_dict[name]
        return (int(octave) + 1) * 12 + pitch

    @staticmethod
    def pitch_to_name(pitch: Pitch_T) -> str:
        """Convert a pitch to a note name.
        For example, 60 -> "C4"."""
        octave = pitch // 12 - 1
        note = pitch % 12
        for name, picth in note_name_dict.items():
            if note == picth:
                return name + str(octave)

    @staticmethod
    def key_to_pitch(key: Key_T) -> Pitch_T:
        """Convert a key to a pitch.
        For example, "C"/"Cm" -> 0, "Eb"/"Ebm" -> 3, and "B#" -> 11."""
        if key.endswith("m"):
            return note_name_dict[key[:-1]]
        else:
            return note_name_dict[key]
