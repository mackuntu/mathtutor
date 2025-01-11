### Product Requirements Document: MathTutor System

#### Overview
The MathTutor system automates the creation, rendering, distribution, and grading of personalized math worksheets for students, enabling teachers and parents to customize learning experiences effectively. The system includes features for worksheet generation, answer key creation, grading automation, and data storage for tracking performance.

---

## Installation

To set up the MathTutor system and its dependencies:

1. **Clone the Repository**:
   ```bash
   git clone git@github.com:mackuntu/mathtutor.git
   cd mathtutor
   ```

2. **Set Up a Virtual Environment (Optional but Recommended)**:
   ```bash
   pyenv install 3.12
   pyenv local 3.12
   ```

3. **Install Dependencies**:
   Use the provided `requirements.txt` file to install all necessary Python packages:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Application**:
   Follow the instructions in the user guide to generate worksheets, grade submissions, and manage data.

---

### Goals
1. **Personalized Education**: Generate customized worksheets based on student age and proficiency.
2. **Automated Workflow**: Streamline the process from worksheet creation to grading.
3. **Data-driven Insights**: Store and analyze data to monitor and enhance student learning outcomes.
4. **Mistake-Centric Learning**: Ensure mistakes are treated as learning opportunities to enhance student understanding and resilience.

---

### Features

#### P1: Essential Features
1. **Highlight Mistakes**:
   - Clearly indicate incorrect answers without revealing the correct answer immediately.
   - Provide immediate visual feedback for errors.

2. **Encourage Reflection**:
   - Prompt students to reconsider their answers with a hint or suggestion.
   - Example: “Check your subtraction here. Did you carry over correctly?”

3. **Explanations After Multiple Attempts**:
   - Provide step-by-step solutions for problems after several incorrect tries.
   - Offer concise written explanations for better comprehension.

4. **Target Weak Areas**:
   - Identify patterns in mistakes (e.g., subtraction errors) and focus future practice sessions on those areas.
   - Customize practice worksheets dynamically based on common errors.

5. **Positive Reinforcement**:
   - Reward effort and improvement to encourage persistence.
   - Example: “You solved 10% more problems correctly than last week. Keep it up!”

#### P2: Important Features
1. **Hints for Incorrect Answers**:
   - Offer hints like breaking down the problem into smaller steps or providing visual aids for complex problems.

2. **Dynamic Problem Adjustments**:
   - Generate simpler or related problems to reinforce foundational concepts for struggling students.
   - Gradually increase complexity once confidence is built.

3. **Encourage Self-Correction**:
   - Provide opportunities for students to retry problems before revealing the solution.
   - Example: “Would you like to try solving this again?”

4. **Customized Reports for Teachers and Parents**:
   - Generate detailed mistake analyses and practice suggestions for educators and parents.
   - Include progress tracking with visual charts and improvement metrics.

5. **Celebrate Progress**:
   - Highlight improvement percentages over time to build confidence and motivation.

#### P3: Nice-to-Have Features
1. **Gamify Learning**:
   - Add badges, points, or unlocking hints for retrying and solving problems.
   - Example: “You earned a star for retrying all your mistakes!”

2. **Emotional Support Features**:
   - Use friendly messages, emojis, or animated characters to create a supportive environment.
   - Example: “Mistakes help us learn! Let’s try again.”

3. **Interactive Walkthroughs**:
   - Provide animated or interactive problem-solving explanations for deeper engagement.

---

### Functional Requirements

#### Core Requirements
1. **Worksheet Creation**:
   - Allow dynamic generation of math problems based on student attributes.
   - Include decorative elements for engagement.

2. **Answer Key Generation**:
   - Automate the creation of a corresponding answer key.

3. **Grading System**:
   - Support OCR-based recognition of handwritten answers.
   - Enable grading with detailed breakdowns of correct and incorrect answers.

4. **Mistake Handling**:
   - Highlight mistakes and encourage retries with hints or suggestions.
   - Provide step-by-step explanations for repeated mistakes.

5. **Data Management**:
   - Store metadata and content in an SQLite database for future reference.
   - Maintain ROI templates for consistent answer extraction.

#### Secondary Requirements
1. **Reports**:
   - Generate customized reports for teachers and parents, including mistake patterns and progress tracking.

2. **Adaptability**:
   - Adjust problem difficulty dynamically based on student performance.

#### Non-Functional Requirements
1. **Performance**:
   - Handle up to 1,000 worksheets and answer keys per batch.
   - OCR grading must process within 2 minutes per worksheet.

2. **Scalability**:
   - Database design should support the addition of new subjects and problem types.

3. **Usability**:
   - Provide a user-friendly interface for non-technical users to generate and grade worksheets.

4. **Security**:
   - Ensure QR code data is encrypted to prevent unauthorized access to worksheet metadata.

---

### Roadmap

#### Phase 1: Core System Development
- Implement worksheet generation and answer key rendering.
- Develop database schema and storage mechanisms.

#### Phase 2: Automation
- Integrate OCR for answer extraction.
- Develop grading algorithms.

#### Phase 3: Mistake-Centric Features
- Add mistake handling workflows, including hints, retries, and explanations.
- Generate adaptive learning content based on weak areas.

#### Phase 4: Optimization and Engagement
- Enhance database queries for faster performance.
- Introduce gamification and emotional support features to improve user experience.

#### Phase 5: User Feedback and Iteration
- Release a beta version for educators.
- Gather feedback to refine UI and features.

---

### Deliverables
1. **Math Worksheet Generator**: Fully functional worksheet creation system.
2. **Answer Key Creator**: Automated answer key generation.
3. **Grader**: OCR-based grading tool with mistake feedback.
4. **Database**: Centralized storage for worksheets and answer keys.
5. **Mistake-Centric Features**: Workflow for highlighting and resolving mistakes.
6. **Documentation**: User guides and API references.

