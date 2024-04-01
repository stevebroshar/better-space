# Whitespace Formatter

Python command line tool for managing whitespace in a source code files: replacing tabs with spaces, tabs with spaces and removing whitespace at the end of lines.

TBO I hate tabs in code files. I would never replace spaces with tabs. But, I did try to make that feature usable none-the-less.

[TOC]

# Terms

- de-tab: replace tabs with spaces
- en-tab: replace spaces with tabs
- leading whitespace: space and tab characters before first non-whitespace char of a line
- trailing whitespace: space and tab characters after last non-whitespace char of a line
- code: source code

# Features

- Supports UTF-8 and UTF-16; for other formats (including binary) fails if specified by path (even via wildcard) or ignoring if matched in directory search.
- Trim trailing whitespace; robust for any text file
- De-tab or en-tab leading text; robust for any text file
- De-tab or en-tab the content of a text file without special handling for string literals which is problematic for source files with tabs in string literals
- De-tab code with (non-raw) string literals like C, C++, C# and Python but a dissimilar string literal would be problematic. What are other string literal syntax?

## String Literals

Handling the text of a string literal is problematic for both de-tabbing and en-tabbing. The problem stem from the fact that the tab stops of the source in which the literal resides is almost surely different than the tab stops of the output from the application that uses the literal. Cannot treat the tabs in a literal the same as the tabs in the whitespace of the code.

Another challenge with string literals is that detecting them is challenging since this tool might be used on a variety of programming languages which have different syntax. At this point, this handles languages with literals like in C, C++, C# and Python. Since the string literal syntax is somewhat uniform throughout the pantheon of languages, the logic should work well for many languages, but surely not all. Seems impossible to solve the issue in a general sense; for all edge cases.

For de-tabbing, a each tab in a string literal is replaced with a tab *specifier* (\t).

For en-tabbing, the content of a string literal is left as-is.

## New Line Character Sequence

The tool relies on Python's universal new line support that reads (splits lines) based any new line sequence (/n, /r, /r/n) and writes (joins lines) using the platform default sequence. This does mean that if the input does not use the platform default sequence, then an updated file will differ since it will use the platform default.

# Technologies

Python 3

# Test

Unit test:

> python UnitTest.py

End-to-end test:

> python EndToEndTest.py

# Changes

## Version 1

TBD

## TODO

Support en-tabbing code; with special handling for string literals. Probably just ignore string literals; don't replace spaces with tabs since that could change behavior of the code.

For detab, allow leaving tabs in string literals; ignoring the content of string literals

For entab (line), currently too aggressive in that any space that happens to fall at end of a tab stop is replaced with a tab. This is often not desirable such as in a comment string or even in a line of code that is not formatted as columnized multiple lines. Could ignore comment text but that requires parsing comments. Could ignore replacing spaces with tab if code is not-columnized, but that seems hard to detect.

Maybe: smart string literal handling based on file type. If file has certain extensions (.c, cpp, .cs and the many versions of C++ extensions) then use C-style string literal handling.

