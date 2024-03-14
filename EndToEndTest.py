import shutil
import subprocess
import os
import unittest

class EndToEndTest(unittest.TestCase):
    # def setUp(self):
    #     self.processor = whitespace_formatter.FileProcessor(FakeLogger())
    #     self.test_dir_path = "__testdir"
    #     self.test_file_path = self.__get_test_file_path("a")
    #     self.tearDown()
    #     os.mkdir(self.test_dir_path)

    # def tearDown(self):
    #     if os.path.isdir(self.test_dir_path):
    #         shutil.rmtree(self.test_dir_path)

    def __run_script(self, command):
        return subprocess.run(f"python whitespace_formatter.py {command}", text=True, capture_output=True)

    def test_foo(self):
        r = self.__run_script("-h")
        src_file = os.path.join("test", "testclass1.h")
        expected_file = os.path.join("test", "testclass1_endspace.h")
        tmp_file = os.path.join("test", "test_file")
        shutil.copyfile()
        # copy testclass1.h to testfile
        # script --update --operation none testfile
        # load testfile
        # load testclass_endspace.h
        # verify equal
        #print(r.stdout)

if __name__ == '__main__':
    unittest.main()