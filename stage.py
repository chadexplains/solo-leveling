class Stage:

    design = 1
    design_review = 2
    code = 3
    code_review = 4
    completed = 5
    gave_up = 6

    name = {
        design: "design",
        design_review: "design_review",
        code: "code",
        code_review: "code_review",
        completed: "completed",
        gave_up: "gave_up",
    }

    def __init__(self, value: int):
        self.value = value

    def has_value(self, value: int):
        return self.value == value

    def __str__(self):
        return self.name[self.value]

    @classmethod
    def of_string(cls, s: str):
        for (value, name) in cls.name.items():
            if s == name:
                return cls(value=value)

    def next(self):
        if self.has_value(self.completed):
            return None
        else:
            return Stage(value=self.value + 1)

    def previous(self):
        if self.has_value(self.design):
            return None
        else:
            return Stage(value=self.value - 1)

    def players_turn(self) -> bool:
        return self.has_value(self.design) or self.has_value(self.code)

    def in_design(self) -> bool:
        return self.has_value(self.design) or self.has_value(self.design_review)

    def in_code(self) -> bool:
        return self.has_value(self.code) or self.has_value(self.code_review)

    def in_review(self) -> bool:
        return self.has_value(self.design_review) or self.has_value(self.code_review)
