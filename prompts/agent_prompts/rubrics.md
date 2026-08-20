# Readability

## Relevant Metrics

Lines of code per function, number of modules, naming conventions

## Scoring Rubric

1: Naming is inconsistent; function intent does not match what is described in its name; functions are often too long (60+ LOC for example) and it is due to poor design and not problem complexity; codebase is difficult to understand, such as having too many helper methods

2: Some function names and intents are clear; but there are multiple similar overly complex / god functions that makes a new developer difficult to read.

3: Codebase is understandable; some functions are too complex and can be simplified but that won't make new developers too difficult to pick up.

4: Function names clearly convey their intents; they are single purpose; control flow can be traced from start to end although with minor defects that makes them more complex than necessary.

5: Each function is well-written and can easily be picked up and explained by new developers; the good design makes it easy and makes the team willing to add new features later on.

# Simplicity

## Relevant Metrics

Cyclomatic complexity, function parameter count

## Scoring Rubric

1: Many deeply nested conditionals or loops; functions are only designed to achieve the current goal and often mixes multiple responsibilities together, making them complex to read and test.

2: Complexity is concentrated at a few methods and can be broken down; the complexity is due to poor design and not the overall problem complexity that causes difficulty in future development.

3: Most methods are readable and straightforward with complexity concentrated at a few methods or in main; the added complexity could slow down work but not necessarily cause difficulty in development.

4: Logic is clearly separated into lower branching steps; complexity is justified by the problem complexity; minor design flaws that make some areas require effort to maintain.

5: All functions have the minimal branching possible; all complexity is justified by the complexity of what the function does.

# Maintainability

## Relevant Metrics

Dependency graph and its visibility matrix, fan-in, fan-out, dependencies on less stable modules

## Scoring Rubric

1: Many modules are tightly coupled; changes to one module is likely to cause a ripple effect and affect many others; developers would be reluctant to make changes or introduce new features as a result.

2: Coupling is concentrated in a few modules; changing them would cause a ripple effect; many cross-file edits are required when introducing new features.

3: Most changes are localized; a few single logical change would require cross-file edits; it would take a longer time to introduce new features.

4: Mostly clear separation of concern; changes usually only affect modules closer in distance; changes are predictable and are less likely to introduce unwanted side effects.

5: New features can be introduced in isolation without affecting unwanted modules; codebase is organised efficiently with high cohesion low coupling between different concerns.

# Modularity

## Relevant Metrics

LCOM, number of public methods, feature envy, insufficient modularisation, protected access, circular dependency, isolated module, hub-like modularisation

## Scoring Rubric

1: Classes / modules regularly mixes multiple responsibilities together; they are only suitable for achieving the current goal and not suitable for any extension.

2: Most modules have one responsibility, but some of them mixes at least two major logic together or is tightly coupled with others.

3: Single responsibility is mostly held; some helper methods may belong to another class; some minor logic is coupled together.

4: Clean single responsibility is observed; some minor logic can be isolated and would only affect the future development by a minor scale.

5: Each module has its own distinct nameable responsibility; new features can be introduced and tested in isolation; follows high cohesion low coupling.

# Reusability

## Relevant Modules

Duplicated lines of code

## Scoring Rubric

1: Many duplicated code and logic across multiple modules with no shared abstraction; changing it requires edits to all these modules simultaneously.

2: Effort has been made to make some commonly used functions reusable; but there are still some key logic duplicated that would require changes to both.

3: Reusable logic is mostly factored out; certain code is duplicated but they may change less frequently

4: Reusable components are isolated with clear interfaces; some areas may require further breakdown of these reusable components.

5: Logic is factored out clearly; existing logic can be easily reused when introducing new features; the internal workings of these components can be changed without causing unwanted changes.
