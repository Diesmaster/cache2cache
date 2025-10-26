"""
Basic usage example of my_library.

This demonstrates how to use the main features of the library.
"""

from my_library import main_function, AnotherClass
from my_library.submodule import submodule_function, SubmoduleClass


def main():
    # Using the main function
    print("Main function example:")
    result = main_function("hello")
    print(f"  Result: {result}")
    
    result_with_arg2 = main_function("hello", "world")
    print(f"  Result with second arg: {result_with_arg2}")
    
    # Using the AnotherClass
    print("\nClass example:")
    processor = AnotherClass("custom_value")
    result = processor.process("sample_data")
    print(f"  Result: {result}")
    
    # Using the submodule
    print("\nSubmodule examples:")
    sub_result = submodule_function("test_parameter")
    print(f"  Function result: {sub_result}")
    
    sub_processor = SubmoduleClass({"option1": "value1"})
    sub_class_result = sub_processor.run("test_input")
    print(f"  Class result: {sub_class_result}")


if __name__ == "__main__":
    main()
