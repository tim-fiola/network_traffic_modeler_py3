
def find_end_index(start_index, lines):
    """
    Given a start index and lines of data, finds the first line that
    contains only '' and returns the index for that line.
    """
    end_index = None
    for line in lines[start_index:]:
        if line == '':
            end_index = lines.index(line, start_index)
            break
    return end_index
