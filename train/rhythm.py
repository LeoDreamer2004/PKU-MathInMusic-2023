from random import choice, randint, random
from .base import *
from copy import deepcopy


DEBUG = False
# the weight for strong beats
r1 = 8
# the weight for echo
r2 = 4
# the punishment for strong notes on weak beats
r3 = 0.3
# the punishment for long notes
r4 = 0.3
# the target value
rhythm_target = 1.2

# rate of four types of mutation
mutation_rate_1 = 4  # Swap two notes' length
mutation_rate_2 = 5  # Split a note into two notes
mutation_rate_3 = 4  # Merge two notes into one note
mutation_rate_4 = 1  # Copy a bar and paste it to another bar


class RhythmParameter(TrackParameterBase):
    def __init__(self, track: Track) -> None:
        super().__init__(track)
        self.strong_beats = 0
        self.echo = 0.0
        self.long_notes = 0.0
        self.neighboring_notes = 0.0
        self.strong_notes_on_weak_beats = 0.0
        self.update_parameters()

    def update_parameters(self):
        self._update_beats()
        self._update_echo()
        self._update_long_notes()
        self._update_neighboring_notes()

    def _update_beats(self):
        self.strong_beats = 0
        self.strong_notes_on_weak_beats = 0.0
        for bar in self.bars:
            bad_beats = 0
            for note in bar:
                if note.start_time % self.settings.half == 0:
                    self.strong_beats += 1
                # elif note.start_time % QUARTER == 0:
                # self.weak_beats += 1
                elif note.start_time % note.length != 0:
                    bad_beats += 1
            self.strong_notes_on_weak_beats += bad_beats / len(bar)

    def _update_echo(self):
        # Bar 0 and 2; 1 and 3; 4 and 6; 5 and 7 are echo, etc.
        # If they have the similar rhythm, the echo will be higher
        for bar in range(0, self.bar_number, 4):
            self.echo += self._rhythm_similarity_of_bars(
                self.bars[bar], self.bars[bar + 2]
            )
            self.echo += self._rhythm_similarity_of_bars(
                self.bars[bar + 1], self.bars[bar + 3]
            )
        self.echo /= self.bar_number

    def _update_long_notes(self):
        # Too many long notes are not welcomed
        self.long_notes = 0
        for bar in self.bars:
            for note in bar:
                if note.length == self.settings.half:
                    self.long_notes += 0.5
                elif note.length >= self.settings.quarter:
                    self.long_notes += 0.1

    def _update_neighboring_notes(self):
        # We don't want a quarter note followed by an eighth note, vice versa
        self.neighboring_notes = 0.0
        notes = self.track.note
        for idx in range(len(notes) - 1):
            if (
                abs(notes[idx].length - notes[idx + 1].length)
                == self.settings.half - self.settings.eighth
            ):
                self.neighboring_notes += 1

    def _rhythm_similarity_of_bars(self, bar1: Bar, bar2: Bar):
        """Calculate the similarity of the rhythm of two bars."""
        same = 0
        for note1 in bar1:
            for note2 in bar2:
                if (
                    note1.start_time - note2.start_time
                ) % self.settings.bar_length == 0:
                    same += 1
        return (same**2) / (len(bar1) * len(bar2))


class GAForRhythm(TrackGABase):
    def __init__(self, population: List[Track], mutation_rate: float):
        super().__init__(population, mutation_rate)
        self.update_fitness()

    @staticmethod
    def get_fitness(track: Track) -> float:
        param = RhythmParameter(track)
        f1 = (param.strong_beats - 2 * param.bar_number) * r1 / track.bar_number
        # give encouragement if echo is high
        f2 = param.echo * r2
        # give punishment if there are strong notes on weak beats
        f3 = -param.strong_notes_on_weak_beats * r3
        # give punishment if there are too many long notes
        f4 = -param.long_notes * r4
        if DEBUG and random() < 0.01:
            print(f"{f1} \t {f2} \t {f3} \t {f4}")
        return f1 + f2 + f3 + f4

    def crossover(self):
        for i in range(len(self.population)):
            index1 = self.best_index if randint(0, 1) else self.second_index
            index2 = self.best_index if randint(0, 1) else self.second_index
            bars1 = deepcopy(self.population[index1]).split_into_bars()
            bars2 = deepcopy(self.population[index2]).split_into_bars()
            cross_point = randint(0, self.bar_number // 2 - 1) * 2
            bars = bars1[:cross_point] + bars2[cross_point:]
            self.population[i] = self.population[i].join_bars(bars)

    def mutate(self):
        for i in range(len(self.population)):
            if random() > self.mutation_rate:
                continue
            track = deepcopy(
                self.population[choice([self.best_index, self.second_index])]
            )
            # When mutating, do not change the last note pitch,
            # because we want the last note to be the tonic.
            # Meanwhile, do not change the first note pitch in every bar,
            # in case of empty bars.
            mutate_type = choice_with_weight(
                [
                    self._mutate_1,
                    self._mutate_2,
                    self._mutate_3,
                    self._mutate_4,
                ],
                [
                    mutation_rate_1,
                    mutation_rate_2,
                    mutation_rate_3,
                    mutation_rate_4,
                ],
            )
            mutate_type(track)
            self.population[i] = track

    def _mutate_1(self, track: Track):
        # Swap two notes' length
        idx = randint(0, len(track.note) - 3)
        note1, note2 = track.note[idx], track.note[idx + 1]
        if (
            note2.start_time // self.settings.bar_length
            != note1.start_time // self.settings.bar_length
        ):
            # The two notes are in different bars, don't swap them
            return
        end = note2.end_time
        note1.length, note2.length = note2.length, note1.length
        note2.start_time = end - note2.length

    def _mutate_2(self, track: Track):
        # Split a note into two notes
        idx = randint(0, len(track.note) - 2)
        note = track.note[idx]
        if note.length <= self.settings.note_unit:  # We can't split it
            return
        while True:
            length = choice(self.settings.note_length)
            if length < note.length:
                end = note.end_time
                note.length -= length
                new_note = Note(note.pitch, length, end - length, note.velocity)
                track.note.insert(idx + 1, new_note)
                return

    def _mutate_3(self, track: Track):
        # merge two notes into one note
        idx = randint(0, len(track.note) - 3)
        note = track.note[idx]
        if track.note[idx + 1].start_time % self.settings.bar_length == 0:
            # The next note is at the beginning of a bar, we can't merge it
            return
        note.length = track.note[idx + 1].end_time - note.start_time
        track.note.pop(idx + 1)

    def _mutate_4(self, track: Track):
        # copy a bar and paste it to another bar
        idx = randint(2, track.bar_number - 1)
        bars = track.split_into_bars()
        bars[idx - 2] = deepcopy(bars[idx])
        for note in bars[idx - 2]:
            note.start_time -= self.settings.bar_length * 2
        track.join_bars(bars)

    def run(self, generation):
        print("--------- Start Rhythm Training ---------")
        succeed = False
        for i in range(generation):
            if i % 30 == 0:
                print(f"Rhythm generation {i}: " + self.train_info())
            self.epoch()
            if self.fitness[self.best_index] > rhythm_target:
                print(f"[!] Target reached at generation {i}")
                succeed = True
                break
        if not succeed:
            print(f"[!] Target not reached after {generation} generations")

        print(f"Final fitness for rhythm: {self.fitness[self.best_index]}")
        print("--------- Finish Rhythm Training ---------")
        return self.population[self.best_index]
