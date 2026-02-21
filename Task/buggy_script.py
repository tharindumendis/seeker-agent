def calculate_average(numbers):
    # This function has a bug - it doesn't handle empty lists
    total = 0
    for num in numbers:
        total += num
    average = total / len(numbers)  # Bug: division by zero when numbers is empty
    return average

# Test the function
test_numbers = []
result = calculate_average(test_numbers)
print(f"Average: {result}")