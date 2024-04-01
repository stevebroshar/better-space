# Whitespace Formatter

Python command line tool for managing whitespace in a source code files: replacing tabs with spaces, tabs with spaces and removing whitespace at the end of lines.

All you need is Python 3 installed and the `whitespace_formatter.py` script file.

[TOC]

# Terms

- de-tab: replace tabs with spaces
- en-tab: replace spaces with tabs
- leading whitespace: space and tab characters before first non-whitespace char of a line
- trailing whitespace: space and tab characters after last non-whitespace char of a line
- code: source code

# Features

## Platform independent

As a Python script, this runs on any platform that supports Python -- which is alot!

## Common file encodings

Supports UTF-8 and UTF-16; for other formats (including binary) fails if specified by path (even via wildcard) or ignoring if matched in directory search.

## Trailing whitespace trimming

Trims trailing whitespace.

## Detabbing

One mode, detabs indentation (leading) text only which is robust for any text file.

Another mode supports detabbing the entire content of a text file without special handling of source code string literals which is problematic for string literals that contains a tab characters. The tab characters will be replaced with spaces which affects the resulting behavior of the code. But, it's relatively rare for string literals to be programmed with tab characters. So, low likelihood of happening, but if it does then high likelihood of introducing a bug.

Another mode handles string literals with the commonly used syntax of C, C++, C#, Python and other languages with similar string literals. In this mode, a tab character is replaced with the tab escape sequence (\t).

## Entabbing

One mode supports entabbing indentation (leading) text which is robust for any text file.

Entabbing non-indentation text is not supported since that such internal tabbing is based the opinion of an author. For example, consider the following lines:

`int a;      // this is a`
`int b;      // this is b`
`short c;    // this is c`

Typically, an author would use tabs between each line's semi-colon and comment start so that the comments line up as a column. But, consider the space before 'a' and 'b'. An author typically would _not_ use a tab there, but an entabbing algorithm might since these variable names start at a tab stop (for 4-space tab stops). The algorithm could avoid replacing a single space with a tab, but is 2 spaces enough? Can contrive an example where 2 spaces as the same issue. 

Maybe only replace spaces with tabs if the number of spaces is greater than or equal to the tab size. This would probably result in code that is aligned the same as the code before modification. But, the result would be less than clean.

(for clarity spaces shown as dot (.) and tabs as 'T' and tab size is 4):

For example, this line would not be modified: `int a;..// this is a` even though the two spaces could be replaced with a tab.

For example, this line: `int a;......// this is a` would be modified to `int a;..T// this is a` even though it could be `int a;TT// this is a`.

Maybe the algorithm looks for column across multiple lines, but this is a much more complicated algorithm and also suffers from opinionated results.

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

# Use

Requires: Python 3; nothing else! no additional libraries.

See command-line help:

> python whitespace_formatter.py -h

By default, only prints changes that would be made. Some tools call this *dry-run* or *preview*. Include `--update` to overwrite files with modified content.

If you are not using source control (i.e. git), then you should backup your files before updating files.

# Use cases

This tool shines when formatting multiple files and especially many files such as a directory tree. It is great for a one-time, project-wide update. It is of course can be used for just one file too.

Other tools provide single file (and selection) whitespace conversion; some integrated into an editor such as VSCode and Notepad++. This is convenient since you don't have to leave the editor, but to date have not seen an editor-integrated feature that processes more than just one file at a time. To process many files, i.e. all of the files a project, would be tedious and error prone.

Other tools provide command-line and multiple file support. Seem to all be platform specific and tend to be cryptic or significantly less functional.

# Similar tools

A review of other tools with similar capabilities:

**Notepad++**: Ctrl+A, **Edit>Blank Operations>Tab to Spaces**, one file at a time (not dir/tree), not command line

**VSCode**: Command: **Convert indentation to Tabs**, one file at a time (not dir/tree), not command line

**Visual Studio**: File: Ctrl+K, Ctrl+D *indents* a file. Ctrl+K, Ctrl+F *indents* a selection, one file at a time; not project/directory/tree, 

**Eclipse**: Ctrl+Shift+F *formats* a file

**expand**: `expand -i -t 4 input | sponge output`, linux specific, flexible and powerful but high cognitive load

**vim**: `set ts=4, set expandtab, retab` flexible and powerful but high cognitive load

[**Artistic Style**](https://astyle.sourceforge.net/) ??

[**Tabs to Spaces** (online)](https://tabstospaces.com/), platform independent (since online), one chunk of code at a time (not dir/tree)

[**EnTabFile** - *a Windows tool to EnTab a source file*](https://www.matthew-jones.com/download/entab-windows.html) command line (how does it select fiels?) indentation only, Windows-specific what version of Windows?, handles string literals? Supports UTF8? UTF16? Can change indentation ("if there are 6 spaces and the tab setting is 4, then 2 tabs will be output")

[**tabs-to-spaces**](https://github.com/stephenmathieson/tabs-to-spaces) seems very limited functionality

# Changes

## Version 1

TBD

## TODO

Support en-tabbing code; with special handling for string literals. Probably just ignore string literals; don't replace spaces with tabs since that could change behavior of the code.

For detab, allow leaving tabs in string literals; ignoring the content of string literals

For entab (line), currently too aggressive in that any space that happens to fall at end of a tab stop is replaced with a tab. This is often not desirable such as in a comment string or even in a line of code that is not formatted as columnized multiple lines. Could ignore comment text but that requires parsing comments. Could ignore replacing spaces with tab if code is not-columnized, but that seems hard to detect.

Maybe: smart string literal handling based on file type. If file has certain extensions (.c, cpp, .cs and the many versions of C++ extensions) then use C-style string literal handling.

