# MathPracAI - Product Vision & Current Direction

  ## Project Purpose

  MathPracAI is being built to solve a real tutoring problem.

  I currently tutor one Algebra 2 student. One of the biggest challenges is finding enough quality practice problems after introducing a new topic. Existing worksheets are often:

  * Paid
  * Difficult to find
  * Poorly formatted
  * Limited in quantity
  * Not personalized to the student's needs

  The goal of MathPracAI is **not** to become another worksheet website.

  The goal is to build a **practice engine** capable of generating unlimited, high-quality practice while tracking student learning over time.

  ---

  # Long-Term Vision

  The long-term vision is for MathPracAI to become an intelligent practice platform.

  A student should be able to log in every day (similar to the consistency of Wordle), complete a short personalized practice session, and gradually master Algebra 2 through consistent review and spaced
  repetition.

  Eventually the system should:

  * Generate unlimited valid practice problems.
  * Track every student interaction.
  * Identify strengths and weaknesses.
  * Recommend future review topics.
  * Help tutors understand exactly where a student is struggling.

  The engine should focus on helping students **learn**, not simply complete worksheets.

  ---

  # Current MVP

  The current version focuses on one student and three Algebra 2 topics:

  1. Evaluating Functions
  2. Domain and Range
  3. Parent Functions

  The UI is intentionally simple for now.

  Current development should prioritize:

  1. Clean problem presentation.
  2. Reliable problem generation.
  3. Expandability.

  UI polish can come later.

  ---

  # Core Design Philosophy

  The most important design principle is:

  **Generate infinite valid problems.**

  Instead of hardcoding hundreds of problems, MathPracAI should model the mathematics itself.

  Every problem should be generated from reusable templates and mathematical rules.

  This allows:

  * Unlimited practice
  * Reliable answer keys
  * Consistent difficulty
  * Easy expansion to new topics

  The engine should never depend on AI for mathematical correctness.

  ---

  # Future AI Philosophy

  AI will eventually improve the learning experience, but it should not determine mathematical correctness.

  Potential AI responsibilities:

  * Better explanations
  * Personalized hints
  * Review recommendations
  * Adaptive practice
  * Word problem generation

  The mathematical engine should remain deterministic and reliable.

  ---

  # Current Focus

  At this stage we are NOT designing graph assets yet.

  The current goal is to establish:

  * Problem templates
  * Text layout
  * Problem presentation
  * Engine architecture

  Graph assets will be designed afterward.

  ---

  # Problem Template Philosophy

  Every problem should have a consistent structure.

  Each problem contains:

  * Display content
  * Prompt
  * Student answer area
  * Metadata (topic, difficulty, etc.)

  This consistent structure will allow future graph assets to plug into the same system.

  ---

  # Topic 1 — Evaluating Functions

  Current display format:

  Example:

  f(x) = x² - 2x + 8

  Evaluate f(3).

  NOT:

  Evaluate f(3) if f(x) = x² - 2x + 8.

  The equation should always be displayed first.

  The prompt should appear underneath.

  This makes the problems cleaner, easier to scan, and more worksheet-like.

  Future versions may include:

  * Linear
  * Quadratic
  * Absolute value
  * Square root
  * Piecewise
  * Composition of functions

  For now, only linear and quadratic evaluation problems are required.

  ---

  # Topic 2 — Domain and Range

  Current display format:

  Example:

  f(x) = x² - 2x + 8

  Domain: __________

  Range: __________

  The equation should always appear first.

  The answer blanks should be underneath.

  No graph assets yet.

  Future versions will support:

  * Equation-based problems
  * Graph-based problems
  * Table-based problems

  Only equation-based problems are currently in scope.

  ---

  # Topic 3 — Parent Functions

  Parent Functions will be implemented later.

  The long-term vision is much larger than static graphs.

  Eventually the application should include a Desmos-like interactive graph.

  Desired future functionality:

  * Zoom
  * Pan
  * Grid
  * Plot points
  * Draw on graph
  * Interactive graph questions

  Because this requires significantly more infrastructure, Parent Functions will be implemented after the text-based engine is complete.

  ---

  # Current Development Priorities

  Priority 1:
  Create clean, reusable text-based problem templates.

  Priority 2:
  Design the underlying problem generation engine.

  Priority 3:
  Introduce graph assets.

  Priority 4:
  Build interactive graph functionality.

  Everything should be built with future expansion in mind while keeping the current implementation simple and maintainable.

  ---

  ## Architecture Decisions: Engine, Rendering, Serialization, and File Structure

  ### Core Engine Flow

  MathPracAI should follow this architecture:

  ```text
  ProblemType
  → generate mathematical data
  → build Problem object
  → generic renderer
  → student-facing HTML
  ```

  The engine should generate structured math first. The renderer should only display what already exists on the `Problem` object.

  The renderer should not decide what kind of problem it is rendering.

  Bad:

  ```python
  if problem.topic == "evaluating_functions":
      ...
  ```

  Good:

  ```python
  if problem.display_equation:
      render_equation()

  if problem.prompt:
      render_prompt()

  for asset in problem.assets:
      render_asset(asset)
  ```

  The renderer should be topic-agnostic.

  ---

  ### ProblemType Responsibility

  Each topic should eventually be represented by a `ProblemType`.

  A `ProblemType` owns:

  * available settings
  * mathematical generation rules
  * answer calculation
  * answer fields
  * hints and solution generation
  * valid asset types

  The UI should not hardcode topic-specific settings. Instead, each `ProblemType` should expose the settings it supports.

  Example future settings:

  ```text
  Domain & Range

  Question Target
  ☑ Domain
  ☑ Range

  Function Families
  ☑ Linear
  ☑ Quadratic
  ☑ Absolute Value
  ☑ Square Root

  Presentation
  ☑ Equation
  ☑ Graph
  ```

  ---

  ### Difficulty Direction

  The current `easy / medium / hard` difficulty system is temporary.

  Long-term, difficulty should be replaced by explicit topic settings.

  Reason:

  "Hard" means different things depending on the topic.

  For Evaluating Functions, difficulty might mean:

  * higher degree
  * negative inputs
  * larger coefficients
  * fractional values

  For Domain and Range, difficulty might mean:

  * transformed functions
  * graph interpretation
  * restricted domains
  * interval notation complexity

  Explicit settings give the tutor more control than a generic difficulty dropdown.

  ---

  ### Mathematical Source of Truth

  Do not use rendered equation strings as the source of truth.

  Bad:

  ```python
  equation = "f(x) = (x - 3)^2 + 2"
  ```

  as the only source of truth.

  Good:

  ```python
  {
      "family": "quadratic",
      "form": "vertex",
      "a": 1,
      "h": 3,
      "k": 2
  }
  ```

  The mathematical equation object should be the source of truth.

  From that structured object, the app should derive:

  * rendered equation text
  * graph asset
  * domain
  * range
  * answer key
  * hints
  * solutions

  This prevents parsing errors and keeps text problems and graph problems mathematically consistent.

  ---

  ### JSON Serialization

  Inside Python, the app should work with `Problem` objects.

  Outside Python, such as HTML forms or future APIs, the app should use serialized data.

  JSON is only a transport format.

  Flow:

  ```text
  Problem object
  → Problem.to_dict()
  → json.dumps(...)
  → problem_json hidden HTML field
  → form POST
  → json.loads(...)
  → Problem.from_dict(...)
  → Problem object
  ```

  The renderer should not use JSON directly.

  The renderer receives a `Problem` object and converts it into HTML.

  JSON exists only so the browser can send the problem data back to the server between requests.

  ---

  ### Problem Serialization Methods

  The `Problem` class should define:

  ```python
  Problem.to_dict()
  Problem.from_dict(data)
  ```

  Do not rely on:

  ```python
  problem.__dict__
  ```

  Reason:

  `to_dict()` lets the app explicitly choose which fields are part of the public serialized representation.

  Some future fields should not be serialized, such as:

  * validator objects
  * renderer objects
  * temporary cache values
  * runtime-only statistics
  * Python-only helper objects

  Serialization should include only the data needed to reconstruct the problem.

  ---

  ### File Organization

  `app.py` should not contain every responsibility.

  Recommended structure:

  ```text
  app.py
  models.py
  generators.py
  formatters.py
  validators.py
  renderers.py
  ```

  Responsibilities:

  ```text
  models.py
  - Problem dataclass
  - Problem.to_dict()
  - Problem.from_dict()
  - problem reconstruction helpers

  generators.py
  - ProblemType classes
  - deterministic problem generation
  - topic generator registry
  - temporary topic generators while topics are being migrated

  formatters.py
  - polynomial formatting
  - superscript formatting
  - equation formatting
  - substitution formatting

  validators.py
  - answer normalization
  - answer checking
  - future topic-specific validators

  renderers.py
  - render_problem_display()
  - render_asset()
  - render_control_panel()
  - render_answer_form()
  - render_problem_panel()
  - render_page()

  app.py
  - server setup
  - request routing
  - request parsing
  - high-level app flow
  ```

  The goal is not to split files for the sake of splitting files.

  The goal is to keep each file responsible for one clear job.

  ---

  ### Current Domain and Range Direction

  Domain and Range should be one `ProblemType`, not separate equation and graph problem types.

  Correct:

  ```text
  DomainRangeProblemType
  ```

  with settings that determine what gets generated and rendered.

  Incorrect:

  ```text
  DomainRangeEquationProblemType
  DomainRangeGraphProblemType
  ```

  The underlying math is the same. The presentation changes.

  Settings:

  ```text
  Question Target
  ☑ Domain
  ☑ Range

  Function Families
  ☑ Linear
  ☑ Quadratic
  ☑ Absolute Value
  ☑ Square Root

  Presentation
  ☑ Equation
  ☑ Graph
  ```

  If both Domain and Range are selected, ask for both every time.

  If both Equation and Graph are selected, randomly choose one presentation type per generated problem.

  If multiple function families are selected, randomly choose one selected family per generated problem.

  ---

  ### Domain and Range Answer Format

  Domain and Range answers should use interval notation only.

  Examples:

  ```text
  (-∞, ∞)
  [2, ∞)
  (-∞, 5]
  [3, 8]
  ```

  Do not use `x >= 3` or `y >= 2` as the primary answer format.

  Later, table-based problems may support set notation such as:

  ```text
  {1, 3, 5}
  ```

  but that is separate from interval-based domain and range problems.

  ---

  ### Domain and Range Input Buttons

  Because infinity and union symbols are not standard keyboard keys, the UI should eventually include helper buttons for:

  ```text
  ∞
  -∞
  ∪
  ```

  Do not add buttons for:

  ```text
  (
  )
  [
  ]
  ,
  ```

  because those are standard keyboard keys.

  ---

  ### Current Development Priorities

  Current completed/near-completed focus:

  ```text
  Evaluating Functions
  ```

  Evaluating Functions should follow:

  ```text
  ProblemType
  → generated math data
  → Problem object
  → generic renderer
  ```

  Current next focus:

  ```text
  Domain and Range
  ```

  Before implementing graph assets, implement equation-based Domain and Range using the same architecture.

  Graph problems should come after the structured mathematical source-of-truth model is clear.

  ---

  ### Non-Negotiable Architecture Rules

  * Do not let AI determine mathematical correctness.
  * Do not use rendered strings as the mathematical source of truth.
  * Do not make the renderer topic-specific.
  * Do not use JSON inside renderer logic.
  * Do not add graph assets before the math object model is stable.
  * Do not expand topics by hardcoding one-off problem strings.
  * Do not reintroduce the old single-sentence problem format.
  * UI changes should be separate from engine architecture changes.
