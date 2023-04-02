# Python Style Guide

This document outlines the guidelines for writing Python code for our project. Following these guidelines helps ensure that the code is consistent and easy to read.

## Code Formatting

- Use 4 spaces for indentation.
- Use a space after the # for inline comments.
- Use blank lines to separate logical sections of code.

```python
if x > 0:
    print('x is positive')
else:
    print('x is non-positive')

# This is an inline comment.

def function_name(parameter):
    # Code inside function.
```

## Naming Conventions

### Variables

- Use descriptive names that accurately reflect the purpose of the variable.
- Use snake_case for variable names.

```python
number_of_items = 5
total_price = 10.50
```

### Functions

- Use descriptive names that accurately reflect the purpose of the function.
- Use snake_case for function names.

```python
def calculate_total_price(quantity, price):
    return quantity * price
````

### Classes

- Use PascalCase for class names.

```python
class User:
    # ...
````

### File Names

- Use snake_case for file names.

```
main_script.py
user_profile.py
```

### Comments

- Use comments to explain non-obvious or complex code.
- Use complete sentences and proper grammar.
- Begin comments with a capital letter.
- Use one space after the # for inline comments.
- Use multi-line comments for longer explanations.

```python
# Add the value to the list.
my_list.append(value)

"""
This function takes two parameters:
- name: a string representing the name of the user
- age: an integer representing the age of the user

It returns a greeting message.
"""
def greet(name, age):
    # ...
```

### Miscellaneous

- Use double quotes for strings.
- Use parentheses for tuple packing and unpacking.
- Always use is or is not to compare with None.
- Use a blank line before and after a return statement.
- Use None instead of '' or [] for default values of function arguments.

```python
message = "Hello, world!"
print(message)

a, b, c = (1, 2, 3)

if x is None:
    # ...

def my_function(arg1, arg2=None):
    # ...
    
def my_other_function(arg1, arg2=[]):
    # This is bad.
    
def my_good_function(arg1, arg2=None):
    if arg2 is None:
        arg2 = []
    # ...
````

## Resources

[PEP 8 -- Style Guide for Python Code](https://www.python.org/dev/peps/pep-0008/)\
[Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)\
[Python Code Style: A Guide to Writing Readable Code](https://realpython.com/python-code-style/)
