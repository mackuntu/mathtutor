### Product Requirements Document: MathTutor System

#### Overview
The MathTutor system simplifies the creation and distribution of personalized math worksheets for families, enabling parents to provide consistent, quality math practice for their children. The system focuses on paper-based learning with efficient parent-guided feedback mechanisms.

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
   You can run the project in two ways:

   - **Web Interface** (Recommended):
     ```bash
     python -m src.web
     ```

   - **Command Line**:
     ```bash
     python -m src.main
     ```

---

### Goals
1. **Efficient Practice**: Generate daily customized worksheets with minimal parent effort.
2. **Paper-Based Learning**: Keep children engaged without screen time.
3. **Quick Feedback**: Enable immediate parent-guided feedback through answer overlays.
4. **Family-Friendly**: Support multiple children at different learning levels.

---

### Features

#### P1: Essential Features
1. **Simple Web Interface**:
   - One-click worksheet generation
   - Mobile-friendly design
   - Optional scheduled auto-generation
   - Basic configuration settings

2. **Enhanced Parent Guide**:
   - Clear answer overlay system
   - Common mistake indicators
   - Suggested hints for typical errors
   - Weekly progress checklist

3. **Core Worksheet Generation**:
   - Dynamic problem creation
   - Grade-appropriate content
   - Customizable difficulty levels
   - Print-ready formatting

4. **Multi-Child Support**:
   - Individual student profiles
   - Color-coded worksheets per child
   - Batch printing options
   - Progress tracking per student

5. **Educational Enhancements**:
   - Mini-tutorials on worksheets
   - Visual guides for concepts
   - Reference sections
   - Progressive difficulty system

#### P2: Important Features
1. **Basic Achievement System**:
   - Weekly tracker
   - Designated sticker spots
   - Challenge problems
   - Progress visualization

2. **Simplified Distribution**:
   - Single-file executable
   - Desktop shortcuts
   - Auto-update mechanism
   - Configuration persistence

3. **Resource Management**:
   - Organized worksheet storage
   - Print history tracking
   - Content reuse optimization
   - Batch processing options

#### P3: Nice-to-Have Features
1. **Advanced Analytics**:
   - Learning pattern recognition
   - Progress reporting
   - Difficulty adjustment algorithms
   - Performance insights

2. **Content Expansion**:
   - Additional subject areas
   - Seasonal/themed content
   - Custom problem templates
   - Parent-created content support

---

### Functional Requirements

#### Core Requirements
1. **Worksheet Creation**:
   - Dynamic generation of age-appropriate problems
   - Clean, print-ready formatting
   - Parent guide overlay generation

2. **Web Interface**:
   - Simple, mobile-friendly design
   - One-click generation
   - Basic configuration options

3. **Multi-Child Support**:
   - Profile management
   - Individual progress tracking
   - Batch worksheet generation

4. **Content Management**:
   - Problem difficulty progression
   - Educational reference materials
   - Weekly achievement tracking

#### Secondary Requirements
1. **Distribution System**:
   - Packaged executable
   - Auto-update mechanism
   - Configuration persistence

2. **Resource Optimization**:
   - Print history tracking
   - Content reuse strategies
   - Storage organization

#### Non-Functional Requirements
1. **Performance**:
   - Worksheet generation under 5 seconds
   - Web interface response under 1 second

2. **Usability**:
   - No technical knowledge required
   - Intuitive interface
   - Minimal setup process

3. **Reliability**:
   - Consistent formatting
   - Error-free content generation
   - Stable web interface

---

### Roadmap

#### Phase 1: Core System Enhancement
- Implement web interface
- Create parent guide overlay system
- Develop multi-child support

#### Phase 2: Distribution
- Package as executable
- Add configuration system
- Create auto-update mechanism

#### Phase 3: Content Expansion
- Add mini-tutorials
- Implement progressive difficulty
- Create achievement system

#### Phase 4: Optimization
- Resource management
- Print optimization
- Storage organization

#### Phase 5: Analytics
- Progress tracking
- Performance insights
- Pattern recognition

---

### Deliverables
1. **Web Interface**: Simple, mobile-friendly worksheet generation system
2. **Worksheet Generator**: Enhanced content creation system
3. **Parent Guide**: Clear overlay system for grading
4. **Profile Manager**: Multi-child support system
5. **Achievement System**: Basic progress tracking
6. **Documentation**: User guides and setup instructions

