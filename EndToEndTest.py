import shutil
import subprocess
import os
import unittest

class EndToEndTest(unittest.TestCase):
    def setUp(self):
        self.work_file_path = self.__get_test_path("test_file")
        self.tearDown()

    def tearDown(self):
        if os.path.isfile(self.work_file_path):
            os.remove(self.work_file_path)

    # NOTE: result.stdout and stderr may be interesting
    def __run_script(self, command):
        full_command = f"python whitespace_formatter.py {command}";
        result = subprocess.run(full_command, text=True, capture_output=True)
        if result.returncode != 0:
            raise RuntimeError(f"Error code ({result.returncode}) from command: {full_command}\r{result.stderr}")
        return result
    
    def __get_test_path(self, subpath):
        return os.path.join("test", subpath)
    
    def __read_file(self, path, encoding):
        with open(path, encoding=encoding) as f:
            return f.read()
        
    def __verify(self, src_file_name, expected_file_name, command, encoding):
        src_file = self.__get_test_path(src_file_name)
        shutil.copyfile(src_file, self.work_file_path)
        self.__run_script(command)
        expected = self.__read_file(self.__get_test_path(expected_file_name), encoding)
        actual = self.__read_file(self.work_file_path, encoding)
        self.assertEqual(actual, expected)

    def test_default_conform_utf8(self):
        self.__verify(
            "a-orig-utf8.h", 
            "a-leading_detabbed-and-trimmed-utf8.h", 
            f"--update {self.work_file_path}", 
            "utf-8")

    def test_default_conform_utf16(self):
        self.__verify(
            "a-orig-utf16.h", 
            "a-leading_detabbed-and-trimmed-utf16.h", 
            f"--update {self.work_file_path}", 
            "utf-16")

    def test_trim_trailing_utf8(self):
        self.__verify(
            "a-orig-utf8.h", 
            "a-trimmed-utf8.h", 
            f"--update --operation none {self.work_file_path}", 
            "utf-8")

    def test_trim_trailing_utf16(self):
        self.__verify(
            "a-orig-utf16.h", 
            "a-trimmed-utf16.h", 
            f"--update --operation none {self.work_file_path}", 
            "utf-16")

    def test_detab_code(self):
        self.__verify(
            "a-orig-utf8.h", 
            "a-detabbed-utf8.h", 
            f"--update --operation detab-code --leave-trailing {self.work_file_path}", 
            "utf-8")

    def test_entab_text(self):
        self.__verify(
            "a-orig-utf8.h", 
            "a-entabbed-utf8.h", 
            f"--update --operation entab-text --leave-trailing {self.work_file_path}", 
            "utf-8")

if __name__ == '__main__':
    unittest.main()