# The criteria for giving analyzer suggestions. These should be reasons FOR module to be split. AGAINST is considered by the decomposer. 
# Used by multiple analyzer agents. 
ANALYZER_CRITERIA = """
- Modules should only be split when they carry distinct responsibilities, has different reasons to change, or the complexity and lines of code grows such that it couples different responsibilites together. 
- Refactoring should be considered when there are significant duplication across modules, such that a likely change requires coordination. 
- The problems should be evidenced in the design or code today, and does not only make sense when something hypothetically changes in the future as we do not know the future requirements.
- Avoid previously suggested improvements again, to prevent running into loops. """

# The criteria for decomposer to accept / reject analyzer suggestions 
# Used by decomposer + refactor coder agents. 
DECOMPOSER_SUGGESTIONS_CRITERIA="""
- Whether the suggestions are splitting small modules, causes additional coupling, or make it more difficult to maintain the interface that outweigh the benefits. 
- Whether the nature and complexity of the problem, and still having single responsibility justify the code without refactoring. 
- Whether the suggestion conflict with issue requirements.
"""
