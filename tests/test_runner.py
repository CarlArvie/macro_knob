import unittest
import os
import sys

def main():
    # Ensure the 'tests' directory is in python path
    tests_dir = os.path.dirname(os.path.abspath(__file__))
    if tests_dir not in sys.path:
        sys.path.insert(0, tests_dir)

    # Setup test discovery in the test_cases directory
    loader = unittest.TestLoader()
    start_dir = os.path.join(tests_dir, 'test_cases')
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Run test suite
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code (0 for success, 1 for failure)
    sys.exit(not result.wasSuccessful())

if __name__ == '__main__':
    main()
