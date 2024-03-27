import argparse
import glob
import io
import os

SPACE = " "
TAB = "\t"
ESCAPE = "\\"
SglQuote = "'"
DblQuote = '"'

class AppException(Exception):
    __slots__ = []

class Logger(object):
    __slots__ = ["__is_verbose_enabled", "__is_debug_enabled"]

    def __init__(self):
        self.__is_verbose_enabled = False
        # self.__is_debug_enabled = False

    @property
    def is_verbose_enabled(self):
        return self.__text
    @is_verbose_enabled.setter
    def is_verbose_enabled(self, to):
        self.__is_verbose_enabled = to
        
    # @property
    # def is_debug_enabled(self):
    #     return self.__text
    # @is_debug_enabled.setter
    # def is_debug_enabled(self, to):
    #     self.__is_debug_enabled = to
        
    def log(self, message):
        print(message)

    def log_verbose(self, message):
        if self.__is_verbose_enabled:
            self.log(message)

    # def log_debug(self, message):
    #     if self.__is_debug_enabled:
    #         self.log(message)

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
        self.__logger.log_verbose(f"Saving {self.__file_path} encoding:{self.__encoding}")
        with open(self.__file_path, "w", encoding=self.__encoding) as f:
            f.write(self.__text)

    class FileContext(object):
        __slots__ = ["__line_number", "__log_change", "__change_count"]

        def __init__(self, log_change):
            self.__change_count = 0
            self.__log_change = log_change

        def set_line_number(self, to):
            self.__line_number = to

        def get_change_count(self):
            return self.__change_count

        def log(self, message):
            self.__change_count +=1
            self.__log_change(self.__line_number, message)

    def __log_change(self, line_number, message):
        self.__logger.log_verbose(f"{self.__file_path}:{line_number + 1}: {message}")

    def __apply_operations(self, line_text, line_number, operations):
        context = self.FileContext(self.__log_change)
        for operation in operations:
            context.set_line_number(line_number)
            line_text = operation(line_text, context.log)
        return line_text, context.get_change_count()

    # Applies a series of operations to the lines of the loaded cached content
    # An operation is a function that accepts a line of text and returns the conformed text
    def conform_lines(self, operations):
        change_count = 0
        lines = self.__text.split("\n")
        conformed_lines = []
        for count, line in enumerate(lines):
            conformed_line, line_change_count = self.__apply_operations(line, count, operations)
            change_count += line_change_count
            conformed_lines.append(conformed_line)
        self.__text = "\n".join(conformed_lines)
        return change_count
    
# Utilities for editing lines of code
class LineConformer(object):
    __slots__ = ["__logger", "__debugging"]

    def __init__(self):
        self.__debugging = False
    
    def __log_debug(self, message):
        print(f"\n {message}")

    def __find_first_non_whitespace(self, line):
        for i, c in enumerate(line):
            if c != SPACE and c != TAB: return i
        return -1
    
    def __split_leading_whitespace(self, line):
        nonWsPos = self.__find_first_non_whitespace(line)
        if nonWsPos == -1:
            return line, ""
        return line[:nonWsPos], line[nonWsPos:]

    def __get_spaces_to_next_tab_stop(self, line_len, tab_size):
        return SPACE * (tab_size - line_len % tab_size)
    
    # Removes tailing whitespace
    def trim_trailing(self, line, log_change):
        result = line.rstrip()
        if result != line:
            log_change("Trimmed trailing whitespace")
        return result
    
    # Replaces tabs in indentation text of a line with spaces aligned with tab stops equally spaced by tab_size.
    def detab_leading(self, line, log_change, tab_size):
        leading_whitespace, post_leading = self.__split_leading_whitespace(line)
        detabbed_leading = self.detab_line(leading_whitespace, log_change, tab_size)
        return detabbed_leading + post_leading
    
    # Replaces tabs in text with spaces aligned with tab stops equally spaced by tab_size.
    # No special handling of string literals which is problematic for source code.
    def detab_line(self, line, log_change, tab_size):
        if not TAB in line:
            return line
        out_line = io.StringIO()
        for c in line:
            if c == TAB:
                out_line.write(self.__get_spaces_to_next_tab_stop(out_line.tell(), tab_size))
                log_change(f"Replaced tab with spaces")
            else:
                out_line.write(c)
        return out_line.getvalue()
    
    # Replaces tabs in text with spaces aligned with tab stops equally spaced by tab_size.
    # Attempts to handle string literals for programming languages such as C, C++, C#, Python
    # and languages with similar string literal syntax.
    # A string literal beginning is either a single or double quote and then ends when the same
    # quote char is found later but not escaped with backslash.
    # The non-starting quote char is ignored inside a string literal like in Python.
    # This logic also allows for C/C++ literals; both string (double-quoted) and char (single-quoted)
    # Does _not_ handle raw literals (marked with r in Python and R in C++)
    def detab_code_line(self, line, log_change, tab_size):
        if not TAB in line:
            return line
        out_line = io.StringIO()
        literalTabSpecifier = r"\t"
        inStringLiteral = False
        startLiteralQuote = None
        escapeNext = False
        for c in line:
            if self.__debugging: self.__log_debug(f"char: '{c}'")
            if c == ESCAPE:
                if inStringLiteral:
                    if escapeNext:
                        if self.__debugging: self.__log_debug(r"escaped escape: \\")
                    else:
                        if self.__debugging: self.__log_debug("escape (without preceding escape)")
                        escapeNext = True
                        out_line.write(c)
                        continue
                out_line.write(c)
            elif c == SglQuote or c == DblQuote:
                if not escapeNext:
                    if inStringLiteral:
                        if c == startLiteralQuote:
                            inStringLiteral = False
                            startLiteralQuote = None
                            if self.__debugging: self.__log_debug("end string literal")
                    else:
                        inStringLiteral = True
                        startLiteralQuote = c
                        if self.__debugging: self.__log_debug("start string literal")
                out_line.write(c)
            elif c == TAB:
                if inStringLiteral:
                    out_line.write(literalTabSpecifier)
                    msg = f"Replaced tab with {literalTabSpecifier} in string literal"
                    log_change(msg)
                    if self.__debugging: self.__log_debug(msg)
                else:
                    out_line.write(self.__get_spaces_to_next_tab_stop(out_line.tell(), tab_size))
                    msg = "Replaced tab with spaces"
                    log_change(msg)
                    if self.__debugging: self.__log_debug(msg)
            else:
                out_line.write(c)
            escapeNext = False
        if inStringLiteral:
            msg = f"Warning: Unmatched string delim ({startLiteralQuote}) in line: '{line}'"
            if self.__debugging: self.__log_debug(msg)
            log_change(msg)
        return out_line.getvalue()
    
    # Replaces spaces in leading whitespace with tabs according to tab stops spaced equally by tab_size.
    def entab_leading(self, line, log_change, tab_size):
        leading_whitespace, post_leading = self.__split_leading_whitespace(line)
        new_leading = self.entab_line(leading_whitespace, log_change, tab_size)
        return new_leading + post_leading
    
    # Replaces spaces with tabs according to tab stops spaced equally by tab_space.
    def entab_line(self, line, log_change, tab_size):
        out_line = io.StringIO()
        logical_len = 0
        space_count = 0
        in_tab_whitespace = False
        for c in line:
            if self.__debugging: self.__log_debug(f"logical length: {logical_len}")
            if c == SPACE:
                at_tab_stop = logical_len % tab_size == tab_size - 1
                if at_tab_stop: # and (in_tab_whitespace or space_count > tab_size - 1):
                    msg = f"Replaced {space_count + 1} space(s) with tab"
                    log_change(msg)
                    if self.__debugging: self.__log_debug(msg)
                    out_line.write(TAB)
                    space_count = 0
                    logical_len += 1
                else:
                    if self.__debugging: self.__log_debug(f"space")
                    space_count += 1
                    logical_len += 1
            elif c == TAB:
                if space_count > 0:
                    msg = f"Dropping {space_count} space(s) for existing tab"
                    log_change(msg)
                    if self.__debugging: self.__log_debug(msg)
                else:
                    if self.__debugging: self.__log_debug(f"tab")
                out_line.write(c)
                space_count = 0
                spaces_to_next_tab_stop = tab_size - logical_len % tab_size
                logical_len += spaces_to_next_tab_stop
                in_tab_whitespace = True
            else:
                if self.__debugging: self.__log_debug(f"char '{c}'")
                out_line.write(SPACE*space_count)
                out_line.write(c)
                space_count = 0
                logical_len += 1
                in_tab_whitespace = False
        return out_line.getvalue()
    
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
    supported_operations = [
        "none",
        "detab-leading",
        "detab-text",
        "detab-code",
        "entab-leading",
        "entab-text",
        # "entab-code"]
    ]
    script_name = os.path.splitext(os.path.basename(os.path.abspath(__file__)))[0]
    try:
        parser = argparse.ArgumentParser(
            #formatter_class=argparse.RawTextHelpFormatter,
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description="Modifies text files to replace tabs with spaces (or vise versa), trims whitespace from the end of each line and replace tabs in string literals",
            epilog=f"""
    Note: Fails for binary files specified via path; ignores binary files when matching (--match)

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

    Examples

    > {script_name} --update a.cpp *.h

    For file a.cpp and files matching *.h, replace leading tabs with spaces and trim whitespace from the end of each line.
    Fails if a.cpp not found or no files matching *.h.
    Overwrites modified files.

    > {script_name} --update src

    For each text file in the directory tree src, replace leading tabs with spaces and trim whitespace from the end of each line.
    Fails if src not found, but not if it is an empty directory.
    Overwrites modified files.

    > {script_name} --match *.js --match *.html src

    Process files in src matching *.js or *.html instead of all text files

    > {script_name} --tab-operation none *.c

    Only remove trailing whitespace from matching files.

    > {script_name} a.c --tab-operation detab-text

    Replace tabs with spaces throughout the file.
    If the input is source code, tabs in string literals are replaced with spaces which is probably not desirable.

    > {script_name} a.c --tab-operation detab-code

    Replace tabs with spaces throughout the file except for string literals where tabs are replaced with the value of string-tab.

    > {script_name} a.c --tab-operation entab-leading
        
    Replace leading spaces with tabs and trims whitespace from the end of each line.
    """)
        parser.add_argument("path", nargs="+", 
                            help="file or directory to process")
        parser.add_argument("-u", "--update", action="store_true", 
                            help="save modified files; not saved by default")
        parser.add_argument("-v", "--verbose", action="store_true", 
                            help="verbose logging")
        # parser.add_argument("-D", "--DEBUG", action="store_true", 
        #                     help="debug logging")
        parser.add_argument("--leave-trailing", action="store_true", 
                            help="leave any trailing whitespace; default is to trim")
        parser.add_argument("-o", "--tab-operation", metavar="NAME", default="detab-leading",
                            help=f"detab/entab operation; default: detab-leading; supported: {', '.join(supported_operations)}")
        parser.add_argument("-t", "--tab-size", type=int, metavar="SIZE", 
                            help="number of spaces for a tab")
        parser.add_argument("-m", "--match", metavar="PATTERN", action='append',
                            help="pattern to match files in a directory")

        # parser.add_argument("--string-delimiter", metavar="TEXT", 
        #                     help="text that delimits a string literal; defaults to double-quote (\")")
        # parser.add_argument("--string-delimiter-escape", metavar="TEXT", 
        #                     help="text that marks a string-delimiter character as _not_ a delimitor in a string literal; defaults to backslash (\\)")
        # parser.add_argument("--string-tab", metavar="TEXT",
        #                     help="text to replace tabs in string literals; defaults to '\\t'")
        # parser.add_argument("--line-comment", metavar="TEXT", 
        #                     help="text marks the start of a line comment; to the end of the line; defaults to '//'")
        # parser.add_argument("--start-comment", metavar="TEXT", 
        #                     help="text that delimits the start of a potentially multi-line comment; defaults to '/*'")
        # parser.add_argument("--end-comment", metavar="TEXT", 
        #                     help="text that delimits the end of a potentially multi-line comment; defaults to '*/'")

        args = parser.parse_args()

        logger = Logger()
        logger.is_verbose_enabled = args.verbose
        # logger.is_debug_enabled = args.DEBUG

        tab_size = args.tab_size if args.tab_size else 4

        line_conformer = LineConformer()
        operations = []
        if not args.leave_trailing:
            operations.append(line_conformer.trim_trailing)
        if not args.tab_operation in supported_operations:
            exit(f"Unknown operation '{args.tab_operation}', supported operations: {', '.join(supported_operations)}")
        if args.tab_operation == "none":
            pass
        elif args.tab_operation == "detab-leading":
            operations.append(lambda line, log: line_conformer.detab_leading(line, log, tab_size))
        elif args.tab_operation == "detab-text":
            operations.append(lambda line, log: line_conformer.detab_line(line, log, tab_size))
        elif args.tab_operation == "detab-code":
            operations.append(lambda line, log: line_conformer.detab_code_line(line, log, tab_size))
        elif args.tab_operation == "entab-leading":
            operations.append(lambda line, log: line_conformer.entab_leading(line, log, tab_size))
        elif args.tab_operation == "entab-text":
            operations.append(lambda line, log: line_conformer.entab_line(line, log, tab_size))
        else:
            exit(f"Operation '{args.tab_operation}' is not supported")

        file_processor = FileProcessor(logger)
        selected_files_by_path = file_processor.find_files(args.path, args.match)

        file_change_count = 0
        file_error_count = 0
        file_conformer = FileConformer(logger)
        for file_path,encoding in selected_files_by_path.items():
            try:
                file_conformer.load_from_file(file_path, encoding)
                change_count = file_conformer.conform_lines(operations)
                if file_conformer.is_modified:
                    file_change_count += 1
                    if args.update:
                        logger.log(f"{file_path}: updated")
                        file_conformer.save_to_file()
                    else:
                        logger.log(f"{file_path}: changes: {change_count}")
                else:
                    logger.log(f"{file_path}: no changes")
            except Exception as e:
                file_error_count += 1
                logger.log(f"{file_path}: ERROR {e}")

        message = f"\nFiles processed: {len(selected_files_by_path)}; with changes: {file_change_count}"
        if file_error_count > 0:
            message += f" failed: {file_error_count}"
        logger.log(message)
        if file_change_count > 0 and not args.update:
            logger.log(f"Hint: Include --update to save changes")
    except AppException as e:
        exit(e)