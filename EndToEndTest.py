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

    def __run_script(self, command):
        return subprocess.run(f"python whitespace_formatter.py {command}", text=True, capture_output=True)
    
    def __get_test_path(self, subpath):
        return os.path.join("test", subpath)
    
    def __read_file(self, path, encoding):
        with open(path, encoding=encoding) as f:
            return f.read()

    def test_foo(self):
        src_file = self.__get_test_path("a-utf8-orig.h")
        expected_file = self.__get_test_path("a-utf8-trimmed.h")
        work_file = self.__get_test_path("test_file")
        shutil.copyfile(src_file, work_file)
        result = self.__run_script(f"--update --operation none {work_file}")
        e = self.__read_file(expected_file, "utf-8")
        a = self.__read_file(work_file, "utf-8")
        self.assertEqual(a, e)

if __name__ == '__main__':
    unittest.main()