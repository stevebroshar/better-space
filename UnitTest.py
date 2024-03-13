import unittest
import whitespace_formatter
import shutil
import os

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

        self.assertEqual("    a", text)

    def test_detab_leading_replaces_tab_with_configured_number_of_spaces(self):
        text = self.conformer.detab_leading("\ta", 7)

        self.assertEqual("       a", text)

    def test_detab_leading_leaves_non_leading_tabs(self):
        text = self.conformer.detab_leading("a\tb\t", 4)

        self.assertEqual("a\tb\t", text)

    def test_detab_leading_adds_spaces_for_indent_that_is_spaces_and_tab(self):
        text = self.conformer.detab_leading(" \ta", 4)

        self.assertEqual("    a", text)

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

        self.conformer.load_from_file(self.test_file_path)

        self.assertEqual("Abc123\nDef456\n", self.conformer.text)

    def test_save_to_file_saves_to_file_loaded(self):
        with open(self.test_file_path, "w") as f: f.write("Abc123")
        self.conformer.load_from_file(self.test_file_path)
        self.conformer.text = "Def456"

        self.conformer.save_to_file()

        with open(self.test_file_path) as f: text = f.read()
        self.assertEqual("Def456", text)

    def test_is_modified_is_false_for_unmodified_text(self):
        with open(self.test_file_path, "w") as f: f.write("Abc123")
        self.conformer.load_from_file(self.test_file_path)

        self.assertEqual(False, self.conformer.is_modified)

    def test_is_modified_is_true_for_modified_text(self):
        with open(self.test_file_path, "w") as f: f.write("Abc123")
        self.conformer.load_from_file(self.test_file_path)

        self.conformer.text = "different"

        self.assertEqual(True, self.conformer.is_modified)

class FileProcessorUnitTest(unittest.TestCase):
    def setUp(self):
        self.processor = whitespace_formatter.FileProcessor(FakeLogger())
        self.test_dir_path = "__testdir"
        self.test_file_path = self.get_test_file_path("a")
        self.tearDown()
        os.mkdir(self.test_dir_path)

    def tearDown(self):
        if os.path.isdir(self.test_dir_path):
            shutil.rmtree(self.test_dir_path)

    def get_test_file_path(self, file_name):
        return os.path.join(self.test_dir_path, file_name)

    def test_is_binary_returns_true_for_content_with_null(self):
        with open(self.test_file_path, "w") as f: f.write("Abc\x00123")
        self.assertEqual(True, self.processor.is_binary(self.test_file_path))

    def test_is_binary_returns_false_for_content_with_no_null(self):
        with open(self.test_file_path, "w") as f: f.write("Abc123")
        self.assertEqual(False, self.processor.is_binary(self.test_file_path))

    def test_file_files_returns_empty_for_empty(self):
        file_paths = self.processor.find_files([], [])

        self.assertEqual(0, len(file_paths))

    def test_file_files_fails_for_no_match(self):
        self.assertRaises(whitespace_formatter.AppException, self.processor.find_files, ["notthere"], [])

    def test_file_files_finds_file_by_name(self):
        with open(self.test_file_path, "w") as f: f.write("xxx")
        
        file_paths = self.processor.find_files([self.test_file_path], [])

        self.assertEqual([self.test_file_path], file_paths)

    def test_file_files_finds_files_by_pattern(self):
        file_path_a = self.get_test_file_path("a.c")
        file_path_b = self.get_test_file_path("a.h")
        with open(file_path_a, "w") as f: f.write("a")
        with open(file_path_b, "w") as f: f.write("b")
        
        file_paths = self.processor.find_files([self.get_test_file_path("a.*")], [])

        self.assertCountEqual([file_path_a, file_path_b], file_paths)

    def test_file_files_finds_files_in_dir(self):
        file_path_a = self.get_test_file_path("a.c")
        file_path_b = self.get_test_file_path("a.h")
        with open(file_path_a, "w") as f: f.write("a")
        with open(file_path_b, "w") as f: f.write("b")
        
        file_paths = self.processor.find_files([self.test_dir_path], [])

        self.assertCountEqual([file_path_a, file_path_b], file_paths)

    def test_file_files_filters_dir_files(self):
        file_path_a = self.get_test_file_path("a.c")
        file_path_b = self.get_test_file_path("a.h")
        with open(file_path_a, "w") as f: f.write("a")
        with open(file_path_b, "w") as f: f.write("b")
        
        file_paths = self.processor.find_files([self.test_dir_path], ["*.c"])

        self.assertCountEqual([file_path_a], file_paths)

    def test_file_files_does_not_have_duplicates_for_overlapping_matching_patterns(self):
        file_path_a = self.get_test_file_path("a.c")
        file_path_b = self.get_test_file_path("a.h")
        with open(file_path_a, "w") as f: f.write("a")
        with open(file_path_b, "w") as f: f.write("b")
        
        file_paths = self.processor.find_files([self.test_dir_path], ["*.c", "a.*"])

        self.assertCountEqual([file_path_a, file_path_b], file_paths)

    def test_file_files_fails_for_binary_file(self):
        with open(self.test_file_path, "w") as f: f.write("a\x00a")
        
        self.assertRaises(whitespace_formatter.AppException, self.processor.find_files, [self.test_file_path], [])

    def test_file_files_does_not_match_binary_file(self):
        with open(self.test_file_path, "w") as f: f.write("x\x00x")
        
        file_paths = self.processor.find_files([self.test_dir_path], [])

        self.assertCountEqual([], file_paths)

    def test_file_files_recurses_dir_tree_by_default(self):
        file_path_a = self.get_test_file_path("a")
        file_dir_sub = self.get_test_file_path("sub")
        file_path_suba = self.get_test_file_path(os.path.join("sub", "suba"))
        with open(file_path_a, "w") as f: f.write("a")
        os.mkdir(file_dir_sub)
        with open(file_path_suba, "w") as f: f.write("suba")
        
        file_paths = self.processor.find_files([self.test_dir_path], [])

        self.assertCountEqual([file_path_a, file_path_suba], file_paths)

    def test_file_files_does_not_recurse_when_specified(self):
        file_path_a = self.get_test_file_path("a")
        file_dir_sub = self.get_test_file_path("sub")
        file_path_suba = self.get_test_file_path(os.path.join("sub", "suba"))
        with open(file_path_a, "w") as f: f.write("a")
        os.mkdir(file_dir_sub)
        with open(file_path_suba, "w") as f: f.write("suba")
        
        file_paths = self.processor.find_files([self.test_dir_path], [], False)

        self.assertCountEqual([file_path_a], file_paths)

if __name__ == '__main__':
    unittest.main()