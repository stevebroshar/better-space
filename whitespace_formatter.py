import argparse
import glob
import os

class AppException(Exception):
    __slots__ = []

class Logger(object):
    __slots__ = ["__is_verbose_enabled", "__is_debug_enabled"]

    def __init__(self):
        self.__is_verbose_enabled = False
        self.__is_debug_enabled = False

    @property
    def is_verbose_enabled(self):
        return self.__text
    @is_verbose_enabled.setter
    def is_verbose_enabled(self, to):
        self.__is_verbose_enabled = to
        
    def log(self, message):
        print(message)

    def log_verbose(self, message):
        if self.__is_verbose_enabled:
            self.log(message)

    def log_debug(self, message):
        if self.__is_debug_enabled:
            self.log("DEBUG: " +message)

# Provides for editing the content of a file
class FileConformer(object):
    __slots__ = "__file_text", "__text", "__file_path", "__logger", "__encoding"

    def __init__(self, logger):
        self.__logger = logger
        self.__text = ""

    # Cached file content
    @property
    def text(self):
        return self.__text
    @text.setter
    def text(self, to):
        self.__text = to

    @property
    def is_modified(self):
        return self.__text != self.__file_text

    # Loads and caches the content of a file
    def load_from_file(self, file_path, encoding):
        self.__file_path = file_path
        self.__encoding = encoding
        with open(file_path, "r", encoding=encoding) as f:
            self.__file_text = self.__text = f.read()

    # Saves the cached file content to the file from which it was loaded using the same encoding
    def save_to_file(self):
        if not self.__file_path:
            raise RuntimeError("Must load file first")
        self.__logger.log_debug(f"Saving {self.__file_path} encoding:{self.__encoding}")
        with open(self.__file_path, "w", encoding=self.__encoding) as f:
            f.write(self.__text)

    def __apply_operations(self, line, operations):
        for operation in operations:
            line = operation(line)
        return line

    # Applies a series of operations to the lines of the loaded cached content
    # An operation is a function that accepts a line of text and returns the conformed text
    def conform_lines(self, operations):
        lines = self.__text.split("\n")
        lines = [self.__apply_operations(line, operations) for line in lines]
        self.__text = "\n".join(lines)
    
# Utilities for editing lines of code
class LineConformer(object):
    __slots__ = ["__logger"]

    def __init__(self, logger):
        self.__logger = logger;

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
        result = line.rstrip()
        if result != line:
            self.__logger.log_debug("Trimmed line")
        return result

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
    
class FileProcessor(object):
    __slots__ = "__logger"

    def __init__(self, logger):
        self.__logger = logger

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
        selected_files_by_path = dict()
        for path_spec in path_specs:
            paths = glob.glob(path_spec)
            if len(paths) == 0:
                raise AppException(f"No files selected by '{path_spec}'")
            for path in paths:
                if os.path.isfile(path):
                    encoding = self.detect_encoding(path)
                    if not encoding:
                        raise AppException(f"File is not readable text '{path}'; is binary or an unknown text encoding")
                    selected_files_by_path[path] = encoding
                elif os.path.isdir(path):
                    if recurse_depth == None or recurse_depth > 0:
                        if match_patterns == None or len(match_patterns) == 0:
                            match_patterns = ["*"]
                        for match_pattern in match_patterns:
                            sub_pattern = os.path.join(path, match_pattern)
                            sub_paths = glob.glob(sub_pattern)
                            non_binary_sub_paths = []
                            for sub_path in sub_paths:
                                if os.path.isfile(sub_path) and not self.detect_encoding(sub_path):
                                    self.__logger.log(f"{sub_path}: ignoring since is not readabile text; is binary or an unknown text encoding")
                                else:
                                    non_binary_sub_paths.append(sub_path)
                            decendent_files = self.find_files(non_binary_sub_paths, match_patterns, next_recursive_depth)
                            selected_files_by_path.update(decendent_files)
                else:
                    raise RuntimeError("Unexpected")
        return selected_files_by_path
    
    # Returns the first encoding that works for the file or None if none work which means the file is probably binary.
    def detect_encoding(self, file_path):
        encodings = ["utf-16", "utf-8"]
        for encoding in encodings:
            try:
                with open(file_path, encoding=encoding) as f:
                    f.read(512)
                return encoding
            except:
                pass
        return None
    
if __name__ == '__main__':
    try:
        script_name = os.path.splitext(os.path.basename(os.path.abspath(__file__)))[0]
        parser = argparse.ArgumentParser(
            #formatter_class=argparse.RawTextHelpFormatter,
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description="Modifies text files to replace tabs with spaces (or vise versa), trims whitespace from the end of each line and replace tabs in string literals",
            epilog=f"""
    Notes
     o Fails for a binary file that is specified directly (path); ignores binary files when matching (--pattern)
     o Trims trailing whitespace unless specify --leave-trailing

    Terms
     o detab: replace tabs with spaces
     o entab: replace spaces with tabs
     o leading: whitespace before first non-whitespace char of a line
     o trailing: whitespace after last non-whitespace char of a line
     o text: a flat text file
     o code: source code; also a flat text file

    Operations
     o detab-leading: Replaces tabs with spaces before the first non-whitespace character
     o detab-text: Replaces tabs with spaces after the first and before the last non-whitespace character; no special treament for string literals
     o detab-code: Replaces tabs with spaces after the first and before the last non-whitespace character with special handing for string literals
        Requires: [pattern: ([quote-char, [quote-escape]], [line-comment], [comment-start, comment-end])]

     > script detab-leading paths
     > script detab-text paths
     > script detab-code --quote-char DQ --quote-escape BS --line-comment // --comment-start /* --comment-end */ paths
     > script --ignore-trailing

    Examples

    > {script_name} --modify a.cpp *.h
    For file a.cpp and files matching *.h, replaces leading tabs with spaces and trims whitespace from the end of each line.
    Processes file a.cpp and files matching *.h.
    Fails if a.cpp not found or no files matching *.h.
    Will update modified files.

    > {script_name} --modify src
    For each text file in the directory tree src, replaces leading tabs with spaces and trims whitespace from the end of each line.
    Ignores binary files in the directory tree.
    Fails if src not found, but not if it is an empty directory.
    Will update modified files.

    > {script_name} --pattern *.js --pattern *.html src
    Processes files in src matching *.js or *.html instead of all text files

    FUTURE
    > {script_name} a.c detab-text
    Replaces tabs with spaces throughout the file.
    If the input is source code, tabs in string literals are replaced with spaces which is probably not desirable.

    FUTURE
    > {script_name} a.c detab-code --string-tab \\t --string-delimiter DQ --string-escape BS --line-comment // --comment-start /* --comment-end */
    Replaces tabs with spaces throughout the file except for string literals where tabs are replaced with the value of string-tab.

    FUTURE
    > {script_name} abc.cpp entab-leading
    Replaces leading spaces with tabs and trims whitespace from the end of each line.
    """)
        parser.add_argument("-m", "--modify", action="store_true", 
                            help="save modified files; not saved by default")
        parser.add_argument("-v", "--verbose", action="store_true", 
                            help="verbose logging")
        parser.add_argument("--leave-trailing", action="store_true", 
                            help="leave any trailing whitespace")
        parser.add_argument("-s", "--tab-size", type=int, metavar="SIZE", 
                            help="number of spaces for a tab")
        parser.add_argument("--string-tab", metavar="TEXT",
                            help="text to replace a string literal tab with; defaults to '\\t' which is valid for many languages include C/C++")
        parser.add_argument("--string-delimiter", metavar="DELIM", 
                            help="text that delimits a string literal; defaults to double-quote (\")")
        parser.add_argument("-p", "--pattern", metavar="PATTERN", action='append',
                            help="pattern to match files in a directory")
        parser.add_argument("path", nargs="+", 
                            help="file or directory to process")

        subparsers = parser.add_subparsers(required=False, dest="command")
        detab_leading_parser = subparsers.add_parser('detab-leading')
        detab_text_parser = subparsers.add_parser('detab-text')
        detab_code_parser = subparsers.add_parser('detab-code')
        entab_leading_parser = subparsers.add_parser('entab-leading')
        entab_text_parser = subparsers.add_parser('entab-text')
        entab_code_parser = subparsers.add_parser('entab-code')

        args = parser.parse_args()

        logger = Logger()
        logger.is_verbose_enabled = args.verbose

        tab_size = args.tab_size if args.tab_size else 4
        string_literal_delim_text = args.string_delimiter if args.string_delimiter else '"'
        string_literal_tab_text = args.string_tab if args.string_tab else '\\t'

        line_conformer = LineConformer(logger)
        operations = []
        if not args.leave_trailing:
            operations.append(line_conformer.trim_trailing)
        if not args.command or args.command == "detab-leading":
            operations.append(lambda line: line_conformer.detab_leading(line, tab_size))
        else:
            exit(f"Command '{args.command}' is not supported")
        # if args.command == "detab-text":
        #     operations.append(lambda line: line_conformer.detab_text(line, tab_size))
        # if args.command == "detab-code":
        #     operations.append(lambda line: line_conformer.detab_code(line, tab_size, string_literal_delim_text, string_literal_tab_text, line_comment, comment_start, comment_end))

        file_processor = FileProcessor(logger)
        selected_files_by_path = file_processor.find_files(args.path, args.pattern)

        modified_count = 0
        file_conformer = FileConformer(logger)
        for file_path,encoding in selected_files_by_path.items():
            logger.log_debug(f"Start: {file_path}")
            file_conformer.load_from_file(file_path, encoding)
            file_conformer.conform_lines(operations)
            if file_conformer.is_modified:
                modified_count += 1
                if args.modify:
                    logger.log(f"{file_path}: updated")
                    file_conformer.save_to_file()
                else:
                    logger.log(f"{file_path}: content modified but save not enabled")
            else:
                logger.log(f"{file_path}: no changes")
            logger.log_debug(f"End: {file_path}")

        logger.log(f"\nFiles processed: {len(selected_files_by_path)}; with changes: {modified_count}")
    except AppException as e:
        exit(e)