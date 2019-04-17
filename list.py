"""TODO."""


def chunk_list(list_, numChunks):
    """TODO."""
    chunks = []
    length = len(list_)
    numChunks = int(numChunks)
    previous = 0

    for num in range(numChunks):
        num += 1
        current = int(float(num) / numChunks * length)
        chunks.append(list_[previous:current])
        previous = current

    return chunks


def group_list_to_dict(rows, groupingKey):
    """TODO."""
    result = {}

    for row in rows:
        key = row.pop(groupingKey)
        if key not in result:
            result[key] = []
        result[key].append(row)

    return result
