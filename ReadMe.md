# Whitespace Formatter

Python script for managing whitespace in a test files; source code files.

[TOC]

# Technologies

Python 3

# Test

> python UnitTest.py

# Changes

## Version 1

Supports trimming trailing whitespace; robust for any text file.

Supports de-tabbing leading text; robust for any text file.

Support de-tabbing the content of a text file without special handling for string literals. This is problematic for source files with tabs in string literals.

Supports de-tabbing code with string literals like C, C++ and Python. Dissimilar string literals are problematic.

Supports UTF-8 and UTF-16.

Detects binary (not UTF 8/16); error if specified as path or ignored for file matching.

## TODO

Support en-tabbing leading text.

Support en-tabbing text without special handling for string literals. Problematic for code that has tabs in string literals.

Support en-tabbing code; with special handling for string literals. Probably just ignore string literals; don't replace spaces with tabs since that could change behavior of the code.

For detab, allow leaving tabs in string literals

