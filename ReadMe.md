# Whitespace Formatter

Python script for managing whitespace in a test files; source code files.

[TOC]

# Technologies

Python 3

# Test

Unit test:

> python UnitTest.py

End-to-end test:

> python EndToEndTest.py

# Changes

## Version 1

### Supported Operations

- Supports UTF-8 and UTF-16 and detects and handles other formats (including binary) by either failing if specified as path or ignoring if matched in directory search.
- Trimming trailing whitespace; robust for any text file
- De-tabbing or en-tabbing leading text; robust for any text file
- De-tabbing or en-tabbing the content of a text file without special handling for string literals which is problematic for source files with tabs in string literals
- De-tabbing code with (non-raw) string literals like C, C++, C# and Python but dissimilar string literals are problematic

### String Literals

Handling the text of a string literal is problematic for both de-tabbing and en-tabbing. The problem stem from the fact that the tab stops of the source in which the literal resides is almost surely different than the tab stops of the output from the application that uses the literal. Cannot treat the tabs in a literal the same as the tabs in the whitespace of the code.

Another challenge with string literals is that detecting them is challenging since this tool might be used on a variety of programming languages which have different syntax. At this point, this handles languages with literals like in C, C++, C# and Python. Since the string literal syntax is somewhat uniform throughout the pantheon of languages, the logic should work well for many languages, but surely not all. Seems impossible to solve the issue in a general sense; for all edge cases.

For de-tabbing, a each tab in a string literal is replaced with a tab *specifier* (\t).

For en-tabbing, the content of a string literal is left as-is.

## TODO

Support en-tabbing code; with special handling for string literals. Probably just ignore string literals; don't replace spaces with tabs since that could change behavior of the code.

For detab, allow leaving tabs in string literals; ignoring the content of string literals

For entab (line), currently too aggressive in that any space that happens to fall at end of a tab stop is replaced with a tab. This is often not desirable such as in a comment string or even in a line of code that is not formatted as columnized multiple lines. Could ignore comment text but that requires parsing comments. Could ignore replacing spaces with tab if code is not-columnized, but that seems hard to detect.

