# Comprehensive Data Collection Plan for Tree Runner Example Generation

## Table of Contents
1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Directory Structure](#directory-structure)
4. [File Formats and Conventions](#file-formats-and-conventions)
5. [Detailed Process Flow](#detailed-process-flow)
6. [Implementation Files Overview](#implementation-files-overview)
7. [Configuration and Command Line Arguments](#configuration-and-command-line-arguments)
8. [Web UI Specification](#web-ui-specification)
9. [Example Generation Details](#example-generation-details)
10. [Error Handling and Edge Cases](#error-handling-and-edge-cases)
11. [Implementation Phases](#implementation-phases)

## Overview

This system generates high-quality example data for the tree runner through an iterative process that combines automated generation with human expertise. The goal is to create better examples by:

1. Starting with seed examples
2. Using these examples to generate sample outputs
3. Having humans create parent examples through an interactive web UI
4. Automatically generating leaf examples through deep tree generation
5. Iterating with improved examples each round

The system is designed to be resumable, robust, and to produce increasingly better examples over multiple iterations.

## System Architecture

### Core Concepts

- **Experiment**: A complete data collection run with a unique ID (e.g., `fiction_0628`)
- **Iteration**: One round of example generation within an experiment
- **Sample Sessions**: Full tree generations from writing prompts used to source new example prompts
- **Parent Examples**: Human-created examples showing how to break down tasks
- **Leaf Examples**: Automatically generated examples showing final task completion
- **Seed Examples**: Initial examples used only in iteration 0, unless keep_seed_parent_examples is true

### Key Design Principles

1. **Separation of Concerns**: Data collection is completely separate from tree running
2. **Iterative Improvement**: Each iteration builds on the previous one
3. **Human-in-the-Loop**: Parent examples require human creativity and judgment
4. **Automation Where Possible**: Leaf examples are generated automatically
5. **Resumability**: Experiments can be stopped and resumed at any point
6. **Traceability**: Every generated example can be traced back to its source

## Directory Structure

```
experiment_data/
   {experiment_id}/                              # e.g., fiction_0628
       config.json                              # Experiment configuration (all flags)
       iteration_0/
          used_prompts.json                   # Prompts used in this iteration
          examples/
             leaf_examples.xml               # Copied from seed files
             parent_examples.xml             # Copied from seed files
          sample-sessions/                    # Full trees from writing prompts
             123-what-would-happen-if-the-presi.xml
             7564-you-walk-into-the-grocery-stor.xml
          parent-sessions/                    # Trees for parent example generation
             123-1-what-would-be-the-social-impli.xml
             7564-8-what-might-an-evil-clerk-at-a-.xml
          leaf-sessions/                      # Trees for leaf example generation
              123-5-come-up-with-a-political-sloga.xml
              7564-7-what-are-some-crazy-food-items.xml
       iteration_1/
          used_prompts.json                   # Cumulative prompts (iter 0 + iter 1)
          examples/
             leaf_examples.xml               # Generated from iteration_0/leaf-sessions/
             parent_examples.xml             # Accumulated from all previous parent-sessions/
          ... (same subdirectories)
       iteration_n/
           ... (continues until max iterations)
```

### Directory Details

- **config.json**: Stores all configuration flags used to start the experiment
- **used_prompts.json**: Array of prompt indices already used (cumulative across iterations)
- **examples/**: Contains the example XML files used for this iteration's generation
- **sample-sessions/**: Full tree outputs from writing prompts, used as source for examples
- **parent-sessions/**: Full trees generated from prompts selected for parent examples
- **leaf-sessions/**: Full trees generated from prompts selected for leaf examples

## File Formats and Conventions

### Writing Prompts File Format

The writing prompts file (`writing_prompts/train.txt` by default) contains one prompt per line:
```
You've finally managed to discover the secret to immortality...
The moon is actually a giant egg, and it has just started to hatch.
```

When using these prompts as root prompts, prepend: "Write a story using the following prompt: "

### File Naming Convention

#### Sample Sessions
Format: `{prompt_index}-{truncated_prompt}.xml`
- `prompt_index`: 1-based line number from writing prompts file
- `truncated_prompt`: First 30 characters, alphanumeric only, spaces as hyphens
- Example: `253-youre-shocked-to-discover-that.xml`

#### Parent/Leaf Sessions
Format: `{prompt_index}-{node_id}-{truncated_prompt}.xml`
- `prompt_index`: Original writing prompt index
- `node_id`: Session ID from the tree (0 for root, assigned in pre-order traversal)
- `truncated_prompt`: From the selected node's prompt
- Example: `253-3-what-could-you-do-with-a-third.xml`

### Session XML Format

```xml
<?xml version="1.0" encoding="UTF-8"?>
<session>
  <id>0</id>
  <prompt>Write a story about...</prompt>
  <notes>Internal thoughts about approach</notes>
  <ask>Generate a story with these requirements: ...</ask>
  <response-id>1</response-id>
  <response>The generated story content from child</response>
  <notes>More thoughts after seeing response</notes>
  <ask>Improve the ending with more drama</ask>
  <response-id>2</response-id>
  <response>The improved ending</response>
  <submit>Final combined and edited story</submit>
  <final-response>Final story with all placeholders resolved</final-response>
</session>
```

### Example XML Format

```xml
<?xml version="1.0" encoding="UTF-8"?>
<sessions>
  <session>
    <prompt>Write a story about...</prompt>
    <!-- For parent examples: full session structure -->
    <notes>...</notes>
    <ask>...</ask>
    <response>...</response>
    <submit>...</submit>
    <!-- For leaf examples: only prompt and submit -->
    <submit>...</submit>
  </session>
  <!-- More sessions -->
</sessions>
```

### Configuration JSON Format

```json
{
  "experiment_id": "fiction_0628",
  "start_time": "2024-06-28T10:30:00Z",
  "model": "claude-3-opus-20240229",
  "leaf_examples_per_iteration": 20,
  "parent_examples_per_iteration": 10,
  "max_parent_examples": 100,
  "max_iterations": 10,
  "sample_max_depth": 3,
  "parent_max_depth": 1,
  "leaf_max_depth": 3,
  "web_ui_response_max_depth": 0,
  "writing_prompts_path": "writing_prompts/train.txt",
  "seed_leaf_examples": "examples/fiction_leaf_examples.xml",
  "seed_parent_examples": "examples/fiction_parent_examples.xml",
  "temperature": 0.7,
  "max_tokens": 4000,
  "leaf_readme_path": "prompts/leaf_readme.md",
  "parent_readme_path": "prompts/parent_readme.md"
}
```

### Used Prompts JSON Format

```json
[123, 7564, 892, 1205]  // Indices of prompts used (1-based)
```

## Detailed Process Flow

### Experiment Initialization

1. **Validate Experiment ID**
   - Check format matches `^[a-zA-Z0-9_]+$`
   - Ensure directory doesn't exist (unless resuming)
   
2. **Create Directory Structure**
   - Create `experiment_data/{experiment_id}/`
   - Save `config.json` with all parameters
   
3. **Load Resources**
   - Load writing prompts from file
   - Load seed example files
   - Initialize empty used prompts list

### Iteration Process

For each iteration from 0 to max_iterations:

#### Step 1: Prepare Examples

**Iteration 0:**
- Copy seed leaf examples to `iteration_0/examples/leaf_examples.xml`
- Copy seed parent examples to `iteration_0/examples/parent_examples.xml`

**Subsequent Iterations:**
- Generate leaf examples from previous iteration's leaf-sessions
- Accumulate parent examples from all previous parent-sessions
  - This only includes the parent examples from iteration_0/examples/parent_examples.xml if --keep-seed-parent-examples=true
- Parent accumulation stops after reaching max_parent_examples

#### Step 2: Sample Writing Prompts

1. Load cumulative used prompts from all previous iterations
2. Calculate needed prompts: `max(parent_examples_per_iteration, leaf_examples_per_iteration)`
3. Sample that many prompts without replacement from unused prompts
4. Save updated used prompts list to current iteration

#### Step 3: Generate Sample Sessions

For each sampled writing prompt:
1. Prepend "Write a story using the following prompt: " to the prompt
2. Run tree generation with `sample_max_depth`
3. Save full tree to `sample-sessions/{index}-{truncated}.xml`
4. Use current iteration's examples for generation

#### Step 4: Select Nodes for Examples

1. **Parent Example Selection** (if not at max_parent_examples):
   - Randomly select `parent_examples_per_iteration` sessions from sample-sessions
   - For each selected session, randomly select ANY node (leaf or parent)
   - Extract the prompt from that node
   
2. **Leaf Example Selection**:
   - Randomly select `leaf_examples_per_iteration` sessions from sample-sessions
   - For each selected session, randomly select ANY node (leaf or parent)
   - Extract the prompt from that node

#### Step 5: Generate Parent Examples (Web UI)

For each selected parent prompt:
1. Launch web UI with the prompt
2. Human creates example interactively:
   - Writes notes at any point (optional)
   - Writes asks with placeholders ($PROMPT, $RESPONSE1, etc.)
   - System generates responses with tree depth of `parent_max_depth - 1`
     (since human is acting as root at depth 0)
   - Continues until submit
3. Save full tree to `parent-sessions/{index}-{node_id}-{truncated}.xml`
   - The tree includes the human's root session plus all AI-generated subtrees
   - Total tree depth will be `parent_max_depth`
4. If user skips, remove writing prompt from available pool

#### Step 6: Generate Leaf Examples (Automated)

For each selected leaf prompt:
1. Run tree generation with `leaf_max_depth`
2. Use current iteration's examples
3. Save full tree to `leaf-sessions/{index}-{node_id}-{truncated}.xml`
4. Only the prompt and final-response will be used for the example

#### Step 7: Prepare for Next Iteration

1. Extract examples from generated sessions
2. Format as pretty-printed XML
3. Ready for next iteration

### Example Extraction Process

#### Parent Example Extraction
From each file in parent-sessions:
1. Parse the tree XML
2. Find the root node (session_id=0)
3. Extract the complete session structure
4. Preserve all events in order
5. Add to accumulated parent examples

#### Leaf Example Extraction
From each file in leaf-sessions:
1. Parse the tree XML
2. Find the root node (session_id=0)
3. Extract only:
   - `<prompt>` (with placeholders resolved)
   - `<final-response>` as `<submit>`
4. Create new leaf examples (not accumulated)

## Implementation Files Overview

### Core Files

#### `src/data_collection_main.py`
- **Purpose**: Entry point for data collection experiments
- **Dependencies**: All data collection modules
- **Key Functions**:
  - `main()`: Parse args, create experiment, run iterations
  - `create_experiment()`: Initialize directory structure
  - `run_iteration()`: Execute one iteration of data collection

#### `src/data_collection/config.py`
- **Purpose**: Configuration management for data collection
- **Dependencies**: None
- **Key Classes**:
  - `DataCollectionConfig`: Dataclass with all parameters
  - `parse_data_collection_args()`: Argument parsing with validation

#### `src/data_collection/experiment.py`
- **Purpose**: Experiment lifecycle management
- **Dependencies**: config.py, prompt_sampler.py, session_generator.py
- **Key Classes**:
  - `Experiment`: Manages entire experiment state
  - `Iteration`: Manages single iteration state

#### `src/data_collection/prompt_sampler.py`
- **Purpose**: Handle prompt sampling without replacement
- **Dependencies**: None
- **Key Classes**:
  - `PromptSampler`: Manages prompt selection and tracking
  - `UsedPromptsTracker`: Tracks used prompts across iterations

#### `src/data_collection/session_generator.py`
- **Purpose**: Generate sample sessions using tree runner
- **Dependencies**: tree_runner.py, tree_runner_config.py
- **Key Functions**:
  - `generate_sample_sessions()`: Create full trees from prompts
  - `generate_parent_session()`: Create tree for parent example
  - `generate_leaf_session()`: Create tree for leaf example

#### `src/data_collection/node_selector.py`
- **Purpose**: Select nodes from trees for example generation
- **Dependencies**: tree_node.py
- **Key Functions**:
  - `select_random_nodes()`: Pick random nodes from sessions
  - `extract_prompt_from_node()`: Get prompt from specific node

#### `src/data_collection/example_aggregator.py`
- **Purpose**: Extract and format examples from sessions
- **Dependencies**: session.py, xml_formatter.py
- **Key Classes**:
  - `ExampleAggregator`: Manages example extraction and formatting
  - `ParentExampleExtractor`: Extract parent examples
  - `LeafExampleExtractor`: Extract leaf examples

#### `src/data_collection/file_manager.py`
- **Purpose**: Handle all file I/O operations
- **Dependencies**: None
- **Key Functions**:
  - `save_session()`: Save tree with proper naming
  - `load_examples()`: Load example XML files
  - `save_examples()`: Save formatted example XML

### Web UI Files

#### `src/data_collection/web_ui/app.py`
- **Purpose**: Flask application for parent example creation
- **Dependencies**: Flask, session_processor.py
- **Key Routes**:
  - `/`: Main UI page
  - `/api/start_session`: Initialize new session
  - `/api/add_event`: Add note/ask to session
  - `/api/generate_response`: Generate response for ask
  - `/api/submit`: Finalize session

#### `src/data_collection/web_ui/static/index.html`
- **Purpose**: Interactive UI for parent example creation
- **Dependencies**: styles.css, script.js
- **Key Features**:
  - Event timeline display
  - Placeholder highlighting
  - Character counters
  - Skip functionality

#### `src/data_collection/web_ui/static/script.js`
- **Purpose**: Client-side logic for web UI
- **Dependencies**: None
- **Key Functions**:
  - `highlightPlaceholders()`: Show placeholders with tooltips
  - `updateCharCount()`: Track character limits
  - `submitEvent()`: Send events to server

#### `src/data_collection/web_ui/static/styles.css`
- **Purpose**: Styling for web UI
- **Dependencies**: None

#### `src/data_collection/web_ui/session_builder.py`
- **Purpose**: Build parent sessions interactively
- **Dependencies**: session.py, tree_runner.py
- **Key Classes**:
  - `InteractiveSessionBuilder`: Manage session state
  - `ResponseGenerator`: Generate responses for asks

## Configuration and Command Line Arguments

### Required Arguments

```bash
--experiment-id EXPERIMENT_ID
    Unique identifier for this experiment (alphanumeric + underscore)
    
--leaf-examples-per-iteration N
    Number of leaf examples to generate each iteration
    
--parent-examples-per-iteration N
    Number of parent examples to collect each iteration
    
--max-parent-examples N
    Total parent examples to accumulate before stopping collection
    
--max-iterations N
    Maximum number of iterations to run
```

### Depth Configuration

```bash
--sample-max-depth N (default: 3, min: 0)
    Tree depth for generating sample sessions
    
--parent-max-depth N (default: 1, min: 1)
    Total tree depth for parent example generation
    The human acts as the root (depth 0), so this controls how many levels
    of AI-generated responses appear below. With parent-max-depth=1, each
    response the human sees is generated directly. With parent-max-depth=2,
    each response is generated using depth-1 subtrees for better quality.
    
--leaf-max-depth N (default: 3, min: 0)
    Tree depth for generating leaf examples
```

### Optional Arguments

```bash
--writing-prompts-path PATH (default: writing_prompts/train.txt)
    Path to file containing writing prompts
    
--seed-leaf-examples PATH (default: examples/fiction_leaf_examples.xml)
    Initial leaf examples for iteration 0
    
--seed-parent-examples PATH (default: examples/fiction_parent_examples.xml)
    Initial parent examples for iteration 0
    
--keep-seed-parent-examples
    Keep using seed parent examples in iterations past iteration 0 (default: False)
    By default, seed examples don't count toward the parent example total after iteration 0
    
--parent-total-char-limit N (default: 2000)
    Maximum characters for entire parent session
    
--parent-submit-char-limit N (default: 500)
    Maximum characters for parent submit text
    
--web-ui-port PORT (default: 5000)
    Port for Flask web UI
```

### Inherited from Tree Runner

```bash
--model MODEL_NAME
    Model to use for generation (required)
    
--temperature FLOAT
    Generation temperature 0.0-1.0 (required)
    
--max-tokens N
    Maximum tokens per generation (required)
    
--leaf-readme-path PATH
    Path to leaf generation instructions (required)
    
--parent-readme-path PATH
    Path to parent generation instructions (required)
```

### Example Command

```bash
python src/data_collection_main.py \
    --experiment-id fiction_0628 \
    --model claude-3-opus-20240229 \
    --leaf-examples-per-iteration 20 \
    --parent-examples-per-iteration 10 \
    --max-parent-examples 100 \
    --max-iterations 10 \
    --temperature 0.7 \
    --max-tokens 4000 \
    --leaf-readme-path prompts/leaf_readme.md \
    --parent-readme-path prompts/parent_readme.md
```

## Web UI Specification

### User Interface Flow

1. **Session Start**
   - Display prompt at top
   - Show empty event timeline
   - Enable notes/ask input

2. **Adding Events**
   - User can add notes at any time (optional)
   - User writes ask with placeholders
   - Placeholders highlighted in real-time
   - Tooltip shows placeholder values on hover

3. **Response Generation**
   - User clicks "Generate Response"
   - System runs tree with parent_max_depth
   - Response displayed in timeline
   - User can continue adding events

4. **Session Completion**
   - User writes final submit
   - Character limits enforced
   - User clicks "Complete Session"
   - Session saved to parent-sessions

5. **Skip Functionality**
   - User can skip bad prompts
   - Prompt removed from available pool
   - Next prompt loaded automatically

### Placeholder System

- **Format**: `$PROMPT`, `$RESPONSE1`, `$RESPONSE2`, etc.
- **Behavior**: 
  - Preserved in `<ask>` and `<submit>` tags
  - Resolved in `<response>` and `<prompt>` tags
- **Display**: Highlighted with distinctive color, tooltip on hover

### Character Limits

- **Total Session**: Configurable limit (default 2000)
- **Submit Only**: Configurable limit (default 500)
- **Display**: Live character count with visual warnings

## Example Generation Details

### Parent Example Generation Process

1. **Prompt Selection**
   - Can be from any node (leaf or parent) in the tree
   - Selected randomly from sample sessions
   
2. **Interactive Creation**
   - Human sees prompt and decides approach
   - Writes notes to capture thinking (optional, can happen anytime)
   - Creates asks to delegate subtasks
   - Reviews responses and iterates
   - Writes final submit
   
3. **Tree Depth Understanding**
   - Human acts as root node (depth 0)
   - Each response is generated with depth `parent_max_depth - 1`
   - Example: If `parent_max_depth = 2`:
     - Human is at depth 0
     - When human writes an ask, the response is generated with a depth-1 tree
     - This means the AI can break down the ask into sub-asks internally
   - The saved parent-sessions file contains the FULL tree (all depths)
   - But only the root node (depth 0) is extracted for the parent examples
   
4. **Quality Considerations**
   - Examples should show good task decomposition
   - Asks should be clear and specific
   - Submit should integrate responses effectively
   
5. **Accumulation Strategy**
   - All parent examples accumulate across iterations
   - Provides increasing variety and quality
   - Stops accumulating after max_parent_examples

### Leaf Example Generation Process

1. **Prompt Selection**
   - Can be from any node (leaf or parent) in the tree
   - Selected randomly from sample sessions
   
2. **Automated Generation**
   - Run full tree with leaf_max_depth
   - Deeper trees produce more thoughtful responses
   - Uses current iteration's examples
   
3. **Example Extraction**
   - Only extract prompt and final-response
   - Final-response ensures placeholders are resolved
   - Discard intermediate tree structure
   
4. **Reset Strategy**
   - Leaf examples reset each iteration
   - Always exactly leaf_examples_per_iteration
   - Allows continuous improvement

### Example Shuffling

When passing examples to the model:
1. Load examples from XML file
2. Randomly shuffle order
3. Pass shuffled examples to model
4. Increases generation diversity

## Error Handling and Edge Cases

### Experiment Management

- **Duplicate IDs**: Reject unless --resume flag is set
- **Missing Directories**: Create all required directories
- **Corrupted State**: Detect incomplete iterations and recover

### Prompt Sampling

- **Insufficient Prompts**: Error if can't sample enough unused prompts
- **Bad Prompts**: Allow skipping in web UI, track skipped prompts
- **Empty Prompts File**: Clear error message with file path

### Generation Failures

- **Model Errors**: Retry with exponential backoff
- **Failed Sessions**: Mark as FAILED, continue with others
- **Parsing Errors**: Log detailed error, skip that example

### Web UI Issues

- **Port Conflicts**: Configurable port with clear error
- **Session Timeouts**: Auto-save partial progress
- **Browser Compatibility**: Support modern browsers only

### File System

- **Write Permissions**: Check early, fail fast
- **Disk Space**: Estimate space needed, warn if low
- **Atomic Writes**: Use temp files and rename

### Data Validation

- **XML Parsing**: Validate all XML before saving
- **Character Limits**: Enforce in UI and backend
- **Placeholder Format**: Validate $VARIABLE format

## Implementation Phases

### Phase 1: Core Infrastructure (Essential)
1. Create `data_collection_main.py` with full argument parsing
2. Implement `DataCollectionConfig` with all parameters
3. Create `Experiment` class with directory management
4. Implement `PromptSampler` with cross-iteration tracking
5. Add basic iteration loop with resume capability
6. Create comprehensive logging system

### Phase 2: Sample Generation (Critical)
1. Integrate tree runner for sample session generation
2. Implement proper file naming for all session types
3. Create `NodeSelector` for random node selection
4. Add prompt prepending for writing prompts
5. Implement session saving with proper structure
6. Add generation retry logic

### Phase 3: Leaf Example Automation (Important)
1. Implement automated leaf example generation
2. Create `LeafExampleExtractor` with final-response handling
3. Add example XML formatting with pretty printing
4. Implement example shuffling for model calls
5. Create example file management
6. Add leaf generation progress tracking

### Phase 4: Parent Example Web UI (Important)
1. Create Flask application structure
2. Implement session state management
3. Add interactive event building
4. Create placeholder highlighting system
5. Implement response generation integration
6. Add character limit enforcement
7. Create skip functionality for bad prompts
8. Add session saving to correct directory

### Phase 5: Example Accumulation (Moderate)
1. Implement parent example accumulation logic
2. Create max parent examples enforcement
3. Add example quality validation
4. Implement proper example ordering
5. Create example deduplication if needed
6. Add accumulation progress tracking

### Phase 6: Polish and Finalization (Nice to Have)
1. Add comprehensive error handling
2. Implement progress visualization
3. Create experiment summary reports
4. Add final command generation for tree_runner_main
5. Implement experiment comparison tools
6. Add data export functionality

## Final Output

Upon experiment completion, the system outputs:

```bash
Experiment complete! Generated examples saved to:
- Leaf examples: experiment_data/fiction_0628/iteration_9/examples/leaf_examples.xml
- Parent examples: experiment_data/fiction_0628/iteration_9/examples/parent_examples.xml

To use these examples with tree_runner_main.py:

python src/tree_runner_main.py \
    --model claude-3-opus-20240229 \
    --max-depth 3 \
    --temperature 0.7 \
    --max-tokens 4000 \
    --leaf-readme-path prompts/leaf_readme.md \
    --parent-readme-path prompts/parent_readme.md \
    --leaf-examples-xml-path experiment_data/fiction_0628/iteration_9/examples/leaf_examples.xml \
    --parent-examples-xml-path experiment_data/fiction_0628/iteration_9/examples/parent_examples.xml \
    --prompt "Your prompt here"
```

## Resume Capability Details

### Automatic Detection
1. Check for existing experiment directory
2. Find highest iteration number
3. Detect incomplete iterations by missing files
4. Load cumulative used prompts
5. Resume from appropriate point

### State Recovery
- **Complete Iteration**: Start next iteration
- **Missing Examples**: Regenerate from sessions
- **Partial Sessions**: Continue from last saved
- **Corrupted Files**: Skip and log error

### Manual Resume
```bash
python src/data_collection_main.py \
    --experiment-id fiction_0628 \
    --resume
```

## Monitoring and Debugging

### Log Files
- `experiment_data/{id}/experiment.log`: Main experiment log
- `experiment_data/{id}/iteration_{n}/generation.log`: Per-iteration details
- `experiment_data/{id}/web_ui.log`: Parent example creation events

### Progress Tracking
- Console output shows current iteration/example
- Web UI shows session progress
- Log files contain detailed timing information

### Debug Mode
```bash
--debug: Enable verbose logging
--dry-run: Show what would be done without executing
```
