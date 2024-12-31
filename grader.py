class AnswerGrader:
    @staticmethod
    def grade_answers(student_answers, correct_answers):
        report = []
        for i, (student, correct) in enumerate(zip(student_answers, correct_answers)):
            if student == correct:
                report.append((i + 1, "Correct"))
            else:
                report.append((i + 1, "Incorrect"))
        return report
