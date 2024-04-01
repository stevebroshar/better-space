import argparse
import glob
import io
import sys
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

    @property
    def is_verbose_enabled(self):
        return self.__text
    @is_verbose_enabled.setter
    def is_verbose_enabled(self, to):
        self.__is_verbose_enabled = bool(to)

    def log(self, message):
        print(message)

    def log_verbose(self, message):
        if self.__is_verbose_enabled:
            self.log(message)

class FileConformer(object):
    '''Provides for editing the content of a file'''
    
    __slots__ = "__file_text", "__text", "__file_path", "__logger", "__encoding"

    def __init__(self, logger):
        self.__logger = logger
        self.__text = ""

    @property
    def text(self):
        '''Cached file content'''
        return self.__text
    @text.setter
    def text(self, to):
        self.__text = str(to)

    @property
    def is_modified(self):
        return self.__text != self.__file_text

    def load_from_file(self, file_path, encoding):
        '''Loads and caches the content of a file'''
        self.__file_path = file_path
        self.__encoding = encoding
        with open(file_path, "r", encoding=encoding) as f:
            self.__file_text = self.__text = f.read()

    def save_to_file(self):
        '''Saves the cached file content to the file from which it was loaded using the same encoding'''
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

    def conform_lines(self, operations):
        '''
        Applies a series of operations to the lines of the loaded cached content
        An operation is a function that accepts a line of text and returns the conformed text
        '''
        change_count = 0
        lines = self.__text.split("\n")
        conformed_lines = []
        for count, line in enumerate(lines):
            conformed_line, line_change_count = self.__apply_operations(line, count, operations)
            change_count += line_change_count
            conformed_lines.append(conformed_line)
        self.__text = "\n".join(conformed_lines)
        return change_count
    
class LineConformer(object):
    '''Utilities for editing lines of code'''

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
    
    def trim_trailing(self, line, log_change):
        '''Removes tailing whitespace'''
        result = line.rstrip()
        if result != line:
            log_change("Trimmed trailing whitespace")
        return result
    
    def detab_leading(self, line, log_change, tab_size):
        '''Replaces tabs in indentation text of a line with spaces aligned with tab stops equally spaced by tab_size.'''
        leading_whitespace, post_leading = self.__split_leading_whitespace(line)
        detabbed_leading = self.detab_line(leading_whitespace, log_change, tab_size)
        return detabbed_leading + post_leading
    
    def detab_line(self, line, log_change, tab_size):
        '''
        Replaces tabs in text with spaces aligned with tab stops equally spaced by tab_size.
        No special handling of string literals which is problematic for source code.
        '''
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
    
    def detab_code_line(self, line, log_change, tab_size):
        '''
        Replaces tabs in text with spaces aligned with tab stops equally spaced by tab_size.
        Attempts to handle string literals for programming languages such as C, C++, C#, Python
        and languages with similar string literal syntax.
        A string literal beginning is either a single or double quote and then ends when the same
        quote char is found later but not escaped with backslash.
        The non-starting quote char is ignored inside a string literal like in Python.
        This logic also allows for C/C++ literals; both string (double-quoted) and char (single-quoted)

        ### Known limitation
        Does _not_ handle raw literals (marked with r in Python and R in C++)
        '''
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
    
    def entab_leading(self, line, log_change, tab_size):
        '''Replaces spaces in leading whitespace with tabs according to tab stops spaced equally by tab_size'''
        leading_whitespace, post_leading = self.__split_leading_whitespace(line)
        new_leading = self.entab_line(leading_whitespace, log_change, tab_size)
        return new_leading + post_leading
    
    def entab_line(self, line, log_change, tab_size):
        '''Replaces spaces with tabs according to tab stops spaced equally by tab_size'''
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
    
class FileSelect(object):
    '''
    Specifies file selection criteria.
    Defaults to selecting all files of a directoy and all levels of sub-directories.
    '''

    __slots__ = ["__depth_limit", "__match_patterns"]

    def __init__(self):
        self.__match_patterns = ["*"]
        self.__depth_limit = sys.maxsize

    @property
    def match_patterns(self):
        '''Filter patterns to select files in a directory; can contain path wildcards'''
        return self.__match_patterns
    @match_patterns.setter
    def match_patterns(self, to):
        self.__match_patterns = list(to)

    @property
    def depth_limit(self):
        '''
        Number of subdirectory levels to process.
        Value 0 selects to only process specified files and files in specified directories
        '''
        return self.__depth_limit
    @depth_limit.setter
    def depth_limit(self, to):
        if to < 0:
            raise AppException("Depth limit minimum is 0")
        self.__depth_limit = bool(to)

    def __str__(self):
        return f"{{match_patterns:{self.match_patterns} depth_limit:{self.depth_limit}}}"

class FileProcessor(object):
    __slots__ = "__logger"

    def __init__(self, logger):
        self.__logger = logger

    def __find_files_in_tree(self, selected_files_by_path, dir_path, file_select, depth):
        '''
        Finds files in a directory tree based on selection criteria

        ### Parameters
        selected_files_by_path (dict): Selected files by path
        dir_path (string): Directory path
        file_select (FileSelect): Selection criteria
        depth (number): Current depth of search
        '''
        if depth <= file_select.depth_limit:
            for match_pattern in file_select.match_patterns:
                sub_pattern = os.path.join(dir_path, match_pattern)
                matching_sub_paths = glob.glob(sub_pattern)
                for sub_path in matching_sub_paths:
                    encoding = self.detect_encoding_or_none(sub_path)
                    if os.path.isfile(sub_path):
                        if not encoding:
                            self.__logger.log(f"{sub_path}: ignoring file since is unsupported text encoding or binary")
                        else:
                            selected_files_by_path[sub_path] = encoding
            # search sub-dirs
            sub_paths = glob.glob(os.path.join(dir_path, "*"))
            for sub_path in sub_paths:
                if os.path.isdir(sub_path):
                    self.__find_files_in_tree(selected_files_by_path, sub_path, file_select, depth + 1)

    def find_files(self, path_specs, file_select=FileSelect()):
        '''
        Finds files based on selection criteria

        ### Parameters
        path_specs (string[]): Path patterns to select files and directories; can contain path wildcards
        file_select (FileSelect): Selection criteria
        '''
        selected_files_by_path = dict()
        for path_spec in path_specs:
            paths = glob.glob(path_spec)
            if len(paths) == 0:
                raise AppException(f"No files selected by '{path_spec}'")
            for path in paths:
                if os.path.isfile(path):
                    encoding = self.detect_encoding_or_none(path)
                    if not encoding:
                        raise AppException(f"File is unsupported text encoding or binary '{path}'")
                    selected_files_by_path[path] = encoding
                elif os.path.isdir(path):
                    self.__find_files_in_tree(selected_files_by_path, path, file_select, 0)
                else:
                    raise RuntimeError(f"INTERNAL ERROR: Path is neither file nor dir: {path}")
        return selected_files_by_path

    def detect_encoding_or_none(self, file_path):
        '''
        Returns the first supported encoding that works for the file or None if none work which 
        means the file is either unsupported text encoding or binary.
        '''
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
            description="Modifies text files to replace tabs with spaces (or vise versa), trims whitespace from the end of each line and replaces tabs in string literals",
            epilog=f"""
tab operations:
  none              Use to _only_ remove trailing whitespace
  detab-leading     Replace tabs with spaces before the first non-whitespace character
  detab-text        Replace tabs with spaces throughout; no special handing for string literals
  detab-code        Replace tabs with spaces throughout; replace tabs in string literals with markup
  entab-leading     Replace spaces with tabs before first non-whitespace character
  entab-text        Replace spaces with tabls throughout; no special handing for string literals
  entab-code        FUTURE: Replace spaces with tabs throughout while ignoring string literals

note:
  Files with an unsupported encoding (such as binary files) result in failure when
  specified via path, but ignored when matching (--match)

examples:

  > {script_name} --update a.cpp *.h

  For file a.cpp and files matching *.h, replace leading tabs with spaces and trim whitespace
  from the end of each line. Fails if a.cpp not found or no files matching *.h.
  Overwrites modified files.

  > {script_name} --update src

  For each text file in the directory tree src, replace leading tabs with spaces and trim
  whitespace from the end of each line. Fails if src not found, but not if it is an empty
  directory. Overwrites modified files.

  > {script_name} --match *.js --match *.html src

  Process files in src matching *.js or *.html instead of all text files

  > {script_name} --tab-operation none *.c

  Only remove trailing whitespace from matching files.

  > {script_name} a.c --tab-operation detab-text

  Replace tabs with spaces throughout the file. Tabs in source code string literals are replaced
  with spaces -- which is probably not desirable.

  > {script_name} a.c --tab-operation detab-code

  Replace tabs with spaces throughout the file except for string literals where tabs are replaced
  with markup (\\t by default).

  > {script_name} a.c --tab-operation entab-leading

  Replace leading spaces with tabs and trim whitespace from the end of each line.
    """)
        parser.add_argument("path", nargs="+", 
                            help="file or directory to process")
        parser.add_argument("-u", "--update", action="store_true", 
                            help="save modified files; not saved by default")
        parser.add_argument("-v", "--verbose", action="store_true", 
                            help="verbose logging")
        parser.add_argument("--leave-trailing", action="store_true", 
                            help="leave any trailing whitespace; default is to trim")
        parser.add_argument("-o", "--tab-operation", metavar="OPERATION", default="detab-leading",
                            help=f"detab/entab operation; default: detab-leading; supported: {', '.join(supported_operations)}")
        parser.add_argument("-t", "--tab-size", type=int, metavar="SIZE", default=4,
                            help="number of spaces for a tab")
        parser.add_argument("-m", "--match", metavar="PATTERN", action='append',
                            help="pattern to match files in a directory; default is all files")
        parser.add_argument("-d", "--depth-limit", type=int, metavar="LIMIT",
                            help="limit to directory level searching; default is unlimited")

        args = parser.parse_args()

        logger = Logger()
        logger.is_verbose_enabled = args.verbose

        line_conformer = LineConformer()
        operations = []
        if not args.leave_trailing:
            operations.append(line_conformer.trim_trailing)
        if not args.tab_operation in supported_operations:
            exit(f"Unknown operation '{args.tab_operation}', supported operations: {', '.join(supported_operations)}")
        if args.tab_operation == "none":
            pass
        elif args.tab_operation == "detab-leading":
            operations.append(lambda line, log: line_conformer.detab_leading(line, log, args.tab_size))
        elif args.tab_operation == "detab-text":
            operations.append(lambda line, log: line_conformer.detab_line(line, log, args.tab_size))
        elif args.tab_operation == "detab-code":
            operations.append(lambda line, log: line_conformer.detab_code_line(line, log, args.tab_size))
        elif args.tab_operation == "entab-leading":
            operations.append(lambda line, log: line_conformer.entab_leading(line, log, args.tab_size))
        elif args.tab_operation == "entab-text":
            operations.append(lambda line, log: line_conformer.entab_line(line, log, args.tab_size))
        else:
            exit(f"Operation '{args.tab_operation}' is not supported")

        file_select = FileSelect()
        if args.match != None:
            file_select.match_patterns = args.match
        if args.depth_limit != None:
            file_select.depth_limit = args.depth_limit
        file_processor = FileProcessor(logger)
        selected_files_by_path = file_processor.find_files(args.path, file_select)

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