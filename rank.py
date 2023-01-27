class Rank:

    foundation = 1
    copper = 2
    iron = 3
    jade = 4
    low_gold = 5
    high_gold = 6
    true_gold = 7
    underlord = 8
    overlord = 9
    archlord = 10
    monarch = 11

    all_values = [
        foundation,
        copper,
        iron,
        jade,
        low_gold,
        high_gold,
        true_gold,
        underlord,
        overlord,
        archlord,
        monarch,
    ]

    name = {
        foundation: "foundation",
        copper: "copper",
        iron: "iron",
        jade: "jade",
        low_gold: "low-gold",
        high_gold: "high-gold",
        true_gold: "true-gold",
        underlord: "underlord",
        overlord: "overlord",
        archlord: "archlord",
        monarch: "monarch",
    }

    descriptions = {
        foundation: "New to the path",
        copper: "A first taste of the arts",
        iron: "Beginning to show strength",
        jade: "Awareness begins, last entry stage",
        low_gold: "The first true stage, embers burn",
        high_gold: "Nearing dangerous power",
        true_gold: "Highest rank before true mastery",
        underlord: "Revelation and control of soulpower",
        overlord: "Challenges are nothing",
        archlord: "Kneel only for the Monarch",
        monarch: "Maximum power",
    }

    def __init__(self, value: int):
        self.value = value

    def has_value(self, value: int):
        return self.value == value

    def __str__(self):
        return self.name[self.value]

    def get_rank_for_level(self, level):
        rank_bucket = int(level / 10) + 1
        return self.name[rank_bucket]

    def __ge__(self, other):
        return self.value >= other.value

    def __gt__(self, other):
        return self.value > other.value

    @classmethod
    def of_string(cls, s: str):
        for (value, name) in cls.name.items():
            if s == name:
                return cls(value)

    def to_string_hum(self):
        return " ".join([word.capitalize() for word in str(self).split("-")])

    @classmethod
    def of_string_hum(cls, s: str):
        for value in cls.name.keys():
            potential_match = cls(value)
            if s == potential_match.to_string_hum():
                return potential_match

    @classmethod
    def all(cls):
        for value in cls.all_values:
            yield cls(value)

    def description(self):
        return self.descriptions[self.value]
