#put in organisms.py?
#to stop the numbers of certain values exceeding a certain range and becoming unrealistic.
def clamp(value, minimum, maximum):
    return min(
        maximum,
        max(minimum, value)
    )