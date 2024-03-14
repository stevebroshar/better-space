import whitespace_formatter
import shutil
import os
import unittest

class FakeLogger(whitespace_formatter.Logger):
    def __init__(self):
        super().__init__()
        self.entries = []

    def log(self, message):
        self.entries.append(message)

class LineConformerUnitTest(unittest.TestCase):
    def setUp(self):
        self.conformer = whitespace_formatter.LineConformer(FakeLogger())

    def test_trim_trailing_removes_whitespace_from_eol(self):
        text = self.conformer.trim_trailing("  abc \t")

        self.assertEqual("  abc", text)

    def test_detab_leading_replaces_tab_with_4_spaces(self):
        text = self.conformer.detab_leading("\ta", 4)

        self.assertEqual(" "*4 + "a", text)

    def test_detab_leading_leaves_non_leading_tabs(self):
        text = self.conformer.detab_leading("a\tb\t", 4)

        self.assertEqual("a\tb\t", text)

    def test_detab_leading_adds_spaces_for_indent_that_is_space_and_tab(self):
        text = self.conformer.detab_leading(" \ta", 4)

        self.assertEqual(" "*4 + "a", text)

    def test_detab_leading_adds_spaces_for_indent_that_is_tab_width_minus_one_spaces_and_tab(self):
        text = self.conformer.detab_leading("   \ta", 4)

        self.assertEqual(" "*4 + "a", text)

    def test_detab_text_replaces_all_tabs_in_line(self):
        text = self.conformer.detab_text("\ta\tb\t", 4)

        self.assertEqual(" "*4 + "a" + " "*3 + "b" + " "*3, text)

    def test_detab_text_replaces_tabs_with_spaces_to_tab_stops(self):
        text = self.conformer.detab_text(" \ta  \tb  \t", 4)

        self.assertEqual(" "*4 + "a" + " "*3 + "b" + " "*3, text)

class FileConformerUnitTest(unittest.TestCase):
    def setUp(self):
        self.conformer = whitespace_formatter.FileConformer(FakeLogger())
        self.test_file_path = "__testfile"

    def tearDown(self):
        if os.path.isfile(self.test_file_path):
            os.remove(self.test_file_path)

    def test_conform_lines_performs_operation(self):
        self.conformer.text = "a\nb\nc"

        self.conformer.conform_lines([lambda line : "==>" + line + "<=="])

        self.assertEqual("==>a<==\n==>b<==\n==>c<==", self.conformer.text)

    def test_conform_lines_performs_each_operation(self):
        self.conformer.text = "ab"

        self.conformer.conform_lines([lambda line : line.replace("a", "x"), lambda line : line.replace("b", "y")])

        self.assertEqual("xy", self.conformer.text)

    def test_conform_lines_preserves_empty_last_line(self):
        self.conformer.text = "a\nb\nc\n"

        self.conformer.conform_lines([lambda line : line.replace("b", "x")])

        self.assertEqual("a\nx\nc\n", self.conformer.text)

    def test_load_from_file_loads_text_from_file(self):
        with open(self.test_file_path, "w") as f: f.write("Abc123\nDef456\n")

        self.conformer.load_from_file(self.test_file_path, "utf-8")

        self.assertEqual("Abc123\nDef456\n", self.conformer.text)

    def test_save_to_file_saves_to_file_loaded(self):
        with open(self.test_file_path, "w") as f: f.write("Abc123")
        self.conformer.load_from_file(self.test_file_path, "utf-8")
        self.conformer.text = "Def456"

        self.conformer.save_to_file()

        with open(self.test_file_path) as f: text = f.read()
        self.assertEqual("Def456", text)

    def test_is_modified_is_false_for_unmodified_text(self):
        with open(self.test_file_path, "w") as f: f.write("Abc123")
        self.conformer.load_from_file(self.test_file_path, "utf-8")

        self.assertEqual(False, self.conformer.is_modified)

    def test_is_modified_is_true_for_modified_text(self):
        with open(self.test_file_path, "w") as f: f.write("Abc123")
        self.conformer.load_from_file(self.test_file_path, "utf-8")

        self.conformer.text = "different"

        self.assertEqual(True, self.conformer.is_modified)

class FileProcessorUnitTest(unittest.TestCase):
    def setUp(self):
        self.processor = whitespace_formatter.FileProcessor(FakeLogger())
        self.test_dir_path = "__testdir"
        self.test_file_path = self.__get_test_file_path("a")
        self.tearDown()
        os.mkdir(self.test_dir_path)

    def tearDown(self):
        if os.path.isdir(self.test_dir_path):
            shutil.rmtree(self.test_dir_path)

    def __write_binary_file(self, path):
        with open(path, "wb") as f:
            for byte in [123, 3, 255, 0, 100]:
                f.write(byte.to_bytes(1))

    def __get_test_file_path(self, file_name):
        return os.path.join(self.test_dir_path, file_name)

    def test_detect_encoding_returns_utf8_for_utf8_content(self):
        with open(self.test_file_path, "w", encoding="utf-8") as f: f.write("Abc123")
        self.assertEqual("utf-8", self.processor.detect_encoding(self.test_file_path))

    def test_detect_encoding_returns_utf16_for_utf16_content(self):
        with open(self.test_file_path, "w", encoding="utf-16") as f: f.write("Abc123")
        self.assertEqual("utf-16", self.processor.detect_encoding(self.test_file_path))

    def test_detect_encoding_returns_None_for_binary_content(self):
        self.__write_binary_file(self.test_file_path)
        self.assertEqual(None, self.processor.detect_encoding(self.test_file_path))

    def test_file_files_returns_empty_for_empty(self):
        file_paths = self.processor.find_files([], [])

        self.assertEqual(0, len(file_paths))

    def test_file_files_fails_for_no_match(self):
        self.assertRaises(whitespace_formatter.AppException, self.processor.find_files, ["notthere"], [])

    def test_file_files_finds_file_by_name(self):
        with open(self.test_file_path, "w", encoding="utf-8") as f: f.write("xxx")
        
        file_paths = self.processor.find_files([self.test_file_path], [])

        self.assertEqual({self.test_file_path: "utf-8"}, file_paths)

    def test_file_files_finds_files_by_pattern(self):
        file_path_a = self.__get_test_file_path("a.c")
        file_path_b = self.__get_test_file_path("a.h")
        with open(file_path_a, "w") as f: f.write("a")
        with open(file_path_b, "w") as f: f.write("b")
        
        file_paths = self.processor.find_files([self.__get_test_file_path("a.*")], [])

        self.assertCountEqual([file_path_a, file_path_b], file_paths)

    def test_file_files_finds_files_in_dir(self):
        file_path_a = self.__get_test_file_path("a.c")
        file_path_b = self.__get_test_file_path("a.h")
        with open(file_path_a, "w") as f: f.write("a")
        with open(file_path_b, "w") as f: f.write("b")
        
        file_paths = self.processor.find_files([self.test_dir_path], [])

        self.assertCountEqual([file_path_a, file_path_b], file_paths)

    def test_file_files_filters_dir_files(self):
        file_path_a = self.__get_test_file_path("a.c")
        file_path_b = self.__get_test_file_path("a.h")
        with open(file_path_a, "w") as f: f.write("a")
        with open(file_path_b, "w") as f: f.write("b")
        
        file_paths = self.processor.find_files([self.test_dir_path], ["*.c"])

        self.assertCountEqual([file_path_a], file_paths)

    def test_file_files_does_not_have_duplicates_for_overlapping_matching_patterns(self):
        file_path_a = self.__get_test_file_path("a.c")
        file_path_b = self.__get_test_file_path("a.h")
        with open(file_path_a, "w") as f: f.write("a")
        with open(file_path_b, "w") as f: f.write("b")
        
        file_paths = self.processor.find_files([self.test_dir_path], ["*.c", "a.*"])

        self.assertCountEqual([file_path_a, file_path_b], file_paths)

    def test_file_files_fails_for_binary_file(self):
        self.__write_binary_file(self.test_file_path)
        
        self.assertRaises(whitespace_formatter.AppException, self.processor.find_files, [self.test_file_path], [])

    def test_file_files_does_not_match_binary_file(self):
        self.__write_binary_file(self.test_file_path)
    
        file_paths = self.processor.find_files([self.test_dir_path], [])

        self.assertCountEqual([], file_paths)

    def test_file_files_recurses_dir_tree_by_default(self):
        file_path_a = self.__get_test_file_path("a")
        file_dir_sub = self.__get_test_file_path("sub")
        file_path_suba = self.__get_test_file_path(os.path.join("sub", "suba"))
        with open(file_path_a, "w") as f: f.write("a")
        os.mkdir(file_dir_sub)
        with open(file_path_suba, "w") as f: f.write("suba")
        
        file_paths = self.processor.find_files([self.test_dir_path], [])

        self.assertCountEqual([file_path_a, file_path_suba], file_paths)

    def test_file_files_does_not_recurse_when_specified(self):
        file_path_a = self.__get_test_file_path("a")
        file_dir_sub = self.__get_test_file_path("sub")
        file_path_suba = self.__get_test_file_path(os.path.join("sub", "suba"))
        with open(file_path_a, "w") as f: f.write("a")
        os.mkdir(file_dir_sub)
        with open(file_path_suba, "w") as f: f.write("suba")
        
        file_paths = self.processor.find_files([self.test_dir_path], [], False)

        self.assertCountEqual([file_path_a], file_paths)

if __name__ == '__main__':
    unittest.main()