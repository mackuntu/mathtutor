import random


# Module: Problem Templates
class ProblemTemplates:
    @staticmethod
    def generate_arithmetic(level, progression_factor, count):
        """
        Generate arithmetic problems dynamically for the given level.
        """
        max_value = int(10 + 20 * progression_factor)
        problems = []

        def addition():
            a, b = random.randint(1, max_value), random.randint(1, max_value)
            return f"{a} + {b} = _______", a + b

        def subtraction():
            a, b = random.randint(1, max_value), random.randint(1, max_value)
            if a > b:
                return f"{a} - {b} = _______", a - b
            return f"{b} - {a} = _______", b - a

        def multiplication():
            a, b = random.randint(1, max_value // 2), random.randint(1, 10)
            return f"{a} × {b} = _______", a * b

        def division():
            b = random.randint(1, 10)
            a = b * random.randint(1, max_value // b)
            return f"{a} ÷ {b} = _______", a // b

        operations = {
            1: [addition, subtraction],
            2: [addition, subtraction, multiplication, division],
        }

        for _ in range(count):
            operation = random.choice(operations.get(level))
            result = operation()
            if result:
                problems.append(result)
            else:
                print(f"Skipping result: {result}")

        return problems

    @staticmethod
    def generate_geometry(level, count):
        """
        Generate geometry problems dynamically for the given level.
        """
        shapes = ["circle", "triangle", "square", "rectangle", "pentagon", "hexagon"]
        tasks = {
            1: [
                lambda: (f"Identify the shape: {random.choice(shapes)}", shapes[0]),
                lambda: ("Which shape has 4 equal sides?", "square"),
                lambda: ("Which shape has 3 sides?", "triangle"),
                lambda: ("Draw a triangle.", "triangle"),
                lambda: ("Which shape has no corners?", "circle"),
            ]
        }

        problems = []
        for _ in range(count):
            task = random.choice(tasks.get(level, []))
            problems.append(task())

        return problems
