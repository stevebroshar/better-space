import argparse
import glob
import os

# Provides for editing the content of a file
class FileConformer(object):
    __slots__ = "__file_text", "__text", "__file_path"

    def __init__(self):
        self.__text = ""

    # Cached file content
    @property
    def text(self):
        return self.__text
    @text.setter
    def text(self, to):
        self.__text = to

    # Loads and caches the content of a file
    def load_from_file(self, file_path):
        self.__file_path = file_path
        with open(file_path, "r") as f:
            self.__file_text = self.__text = f.read()

    # Saves the cached file content to the file from which it was loaded
    def save_to_file(self):
        if not self.__file_path:
            raise RuntimeError("Must load file first")
        if self.__text != self.__file_text:
            with open(self.__file_path, "w") as f:
                f.write(self.__text)

    def __apply_operations(self, line, operations):
        for operation in operations:
            line = operation(line)
        return line

    # Applies a series of operations to the lines of the loaded cached content
    def conform_lines(self, operations):
        lines = self.__text.split("\n")
        lines = [self.__apply_operations(line, operations) for line in lines]
        self.__text = "\n".join(lines)
    
# Utilities for editing lines of code
class LineConformer(object):
    def __find_first_non_whitespace(self, line):
        for i, c in enumerate(line):
            if c != ' ' and c != '\t': return i
        return -1
    
    def __split_leading(self, line):
        nonWsPos = self.__find_first_non_whitespace(line)
        if (nonWsPos == -1):
            return line, ""
        return line[:nonWsPos], line[nonWsPos:]

    # Removes tailing whitespace
    def trim_trailing(self, line):
        return line.rstrip()

    # Replaces tabs in leading whitespace with spaces
    # An indentation can consist of both spaces and a tab and if each tab was simply replaced with
    # a number of spaces equal to tab_size, then the resulting text would not neccsarily line up
    # like it did with the tabs. Therefore, this replaces each tab with the number of spaces that
    # results in an indentation sized to tab_size.
    def detab_leading(self, line, tab_size):
        leading, body = self.__split_leading(line)
        if "\t" in leading:
            new_leading = ""
            for c in leading:
                if c == "\t":
                    new_leading += " " * (tab_size - len(new_leading) % tab_size)
                else:
                    new_leading += c
            return new_leading + body
        return line
    
class File(object):
    pass

class FileProcessor(object):
    __slots__ = "__none"

    def __find_matching_files(self, pattern):
        return glob.glob(pattern)
    
    # Finds files based on input
    # path_specs: list of path patterns to select files and directories
    # match_patterns: list of patterns to filter items in a directory
    # recurse_depth: 
    #   None: recurse to bottom
    #   False|1: processes files and files in directories specified by path_specs
    #   0: process no directories
    #   >0: number of directory levels to process
    def find_files(self, path_specs, match_patterns, recurse_depth=None):
        if recurse_depth == False: recurse_depth = 1
        next_recursive_depth = recurse_depth
        if not next_recursive_depth == None:
            next_recursive_depth =- 1
        file_paths = set()
        for path_spec in path_specs:
            paths = self.__find_matching_files(path_spec)
            if len(paths) == 0:
                raise FileNotFoundError(f"No files selected by '{path_spec}'")
            for path in paths:
                if os.path.isfile(path):
                    if self.is_binary(path):
                        raise ValueError(f"Binary file '{path}'")
                        #print(f"Skipping binary file '{path}'")
                    else:
                        file_paths.add(path)
                elif os.path.isdir(path):
                    if recurse_depth == None or recurse_depth > 0:
                        if len(match_patterns) == 0:
                            match_patterns = ["*"]
                        for match_pattern in match_patterns:
                            sub_pattern = os.path.join(path, match_pattern)
                            sub_paths = glob.glob(sub_pattern)
                            non_binary_sub_paths = []
                            for sub_path in sub_paths:
                                if os.path.isfile(sub_path) and self.is_binary(sub_path):
                                    pass #print(f"Ignoring binary file '{sub_path}'")
                                else:
                                    non_binary_sub_paths.append(sub_path)
                            inner_paths = self.find_files(non_binary_sub_paths, match_patterns, next_recursive_depth)
                            file_paths.update(inner_paths)
                else:
                    raise RuntimeError("Unexpected")
        return list(file_paths)

    # Indicates whether a file has binary content based on whether it contains a null char
    def is_binary(self, file_path):
        with open(file_path,'r') as f:
            file_bytes = f.read(512)
        return "\x00" in file_bytes
    
if __name__ == '__main__':
    script_name = os.path.splitext(os.path.basename(os.path.abspath(__file__)))[0]
    supported_feature_names = ["conform-whitespace", "detab-leading", "trim-trailing", "detab-strings"]
    default_features = ["conform-whitespace", "trim-trailing"]

    #c_extentions = "c;cc;cpp;cs;cxx;h;hpp;hxx"

    parser = argparse.ArgumentParser(
        #formatter_class=argparse.RawTextHelpFormatter,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Modifies text files to replace tabs with spaces (or vise versa), trims whitespace from the end of each line and replace tabs in string literals",
        epilog=f"""
Note: Fails for a binary file that is specified directly; binary files found by matching are ignored

Examples

> {script_name} src --modify
For directory src, replaces tabs with spaces and trims whitespace from end of lines for each matching file in the directory tree.
Since --strings is not used, sting literals are not modified.

> {script_name} src --modify --pattern *.js --pattern *.html
Processes files in src matching *.js or *.html instead of all text files
Since --strings is not used, sting literals are not modified.

> {script_name} --modify a.cpp b.cpp *.h
Replaces tabs with spaces and trims whitespace from end of lines for files a.cpp, b.cpp and files matching *.h

> {script_name} --modify --to-tabs abc.cpp
Replaces spaces with tabs and trims whitespace from the end of each line.

> {script_name} --modify --feature conform-whitespace abc.cpp
Replaces tabs with spaces but leaves end-of-line whitespace

> {script_name} --modify --feature detab-leading --feature trim-trailing abc.cpp
Replaces tabs used for indenting code (leaving other tabs) and trims end-of-line whitespace

> {script_name} --modify a.html --feature detab-strings
Replaces tabs in double-quoted string literals with '\\t'. Does not replace other tabs or trim end-of-line.

> {script_name} --modify a.html --feature detab-strings --string-literal-tab "&#9;" --string-literal-delimiter "'"
Finds string literals as text between matching single quotes and replaces each tab with "&#9;"
""")
    parser.add_argument("-m", "--modify", action="store_true", 
                        help="modify files instead of only logging changes")
    parser.add_argument("-t", "--to-tabs", action="store_true", 
                        help="convert spaces to tabs instead of tabs to spaces")
    parser.add_argument("-s", "--tab-size", type=int, metavar="SIZE", 
                        help="number of spaces for a tab")
    parser.add_argument("-f", "--feature", action='append', metavar="FEATURE", 
                        help=f"selects a feature: {', '.join(supported_feature_names)}; default when none specified: {', '.join(default_features)}; ")
    parser.add_argument("--string-tab", metavar="TEXT",
                        help="text to replace a string literal tab with; defaults to '\\t' which is valid for many languages include C/C++")
    parser.add_argument("--string-delimiter", metavar="DELIM", 
                        help="text that delimits a string literal; defaults to double-quote (\")")
    #parser.add_argument("--ignore-eol", action="store_true", 
    #                    help="leaves remove end-of-line whitespace")
    parser.add_argument("-p", "--pattern", metavar="PATTERN", action='append',
                        help="pattern to match files in a directory")
    #parser.add_argument("--ignore-files", action="store_true", 
    #                    help="semi-colon separated list of files to exclude from file matching in a directory")
    parser.add_argument("path", nargs="+", 
                        help="file or directory to process")
    args = parser.parse_args()

    feature_names = default_features
    if args.feature:
        feature_names = args.feature
    for feature_name in feature_names:
        if not feature_name in supported_feature_names:
            exit(f"Unknown feature: '{feature_name}'")

    print(f"Selected features: {', '.join(feature_names)}")

    tab_size = args.tab_size if args.tab_size else 4
    string_literal_delim_text = args.string_delimiter if args.string_delimiter else '"'
    string_literal_tab_text = args.string_tab if args.string_tab else '\\t'

    line_conformer = LineConformer()
    operations = []
    # if "conform-whitespace" in args.feature:
    #     operations.append(line_conformer.detab)
    if "trim-trailing" in args.feature:
        operations.append(line_conformer.trim_trailing)
    if "detab-leading" in args.feature:
        operations.append(line_conformer.detab_leading)
    # if "detab-strings" in args.feature:
    #     operations.append(lambda: line_conformer.detab_strings(string_literal_delim_text, string_literal_tab_text))

    file_processor = FileProcessor()
    file_paths = file_processor.find_files(args.path, args.pattern)
    
    file_conformer = FileConformer()
    for file_path in file_paths:
        file_conformer.load_from_file(file_path)
        file_conformer.conform_lines(operations)
        if args.modify:
            file_conformer.save_to_file(file_path)
