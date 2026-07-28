---
name: test-generator
version: 1.0.0
author: example-team
tags: [testing, pytest, unit-tests]
---

# Test Generator

## Description

Generate unit tests for source code. Use this skill when the user asks to write tests, generate a test suite, or add test coverage for a module or function. Trigger on phrasings like "write tests for this", "generate unit tests", "add test coverage", or "create a test suite". Do not trigger on requests to run tests or analyse test results.

## When to Use

**Trigger conditions:**
- "Write tests for this"
- "Generate unit tests for …"
- "Add test coverage to …"
- "Create a test suite for …"
- "I need tests for this function"

**Do not trigger when:**
- The user asks to run existing tests (use test-runner skill)
- The user asks to analyse test results or coverage reports
- The user asks to write integration or end-to-end tests (use e2e-test-generator skill)

## Instructions

1. Read the source code to understand what needs to be tested. Identify all public functions, methods, and classes.

2. For each testable unit, identify: the expected inputs, the expected outputs, and any side effects.

3. Identify edge cases: empty inputs, boundary values, invalid types, and error conditions.

4. Write tests using the testing framework already present in the project. If no framework is configured, default to `pytest` for Python, `jest` for JavaScript/TypeScript, and `JUnit` for Java.

5. Follow the Arrange-Act-Assert pattern: set up inputs, call the function, assert the result.

6. Give each test a descriptive name that states what is being tested and what the expected outcome is.

7. Group related tests in a class or describe block named after the function being tested.

8. Produce the output following the contract below.

## Output Contract

Produce a valid test file in the appropriate language and framework. The file must:

- Import the module under test
- Use the framework's test organisation conventions (classes for pytest, describe blocks for jest)
- Include a test for the happy path
- Include at least one edge case test
- Have no syntax errors
- Be directly runnable without modification

## Examples

**Example 1:**

Given a Python file named `utils.py` containing a single function `add_numbers(a: int, b: int) -> int` that adds two integers and raises `ValueError` if either argument is not an integer, write a pytest test file.

Expected output:
```python
import pytest
from utils import add_numbers

class TestAddNumbers:
    def test_adds_two_positive_integers(self):
        assert add_numbers(2, 3) == 5

    def test_adds_negative_integers(self):
        assert add_numbers(-1, -2) == -3

    def test_raises_value_error_for_float_input(self):
        with pytest.raises(ValueError):
            add_numbers(1.5, 2)

    def test_raises_value_error_for_string_input(self):
        with pytest.raises(ValueError):
            add_numbers("a", 1)
```

## Environment and Portability

Requires the testing framework to be installed in the project. If no framework is configured, default to `pytest` for Python.

Assumes the source file and test file will be in the same package or that the package is installed. If neither applies, add a `sys.path` insertion comment in the test file.

## References

No bundled files.
