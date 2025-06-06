def getNumNodes(move_log):
    nodes = set()
    for (old_pos, new_pos, is_capture) in move_log:
        nodes.add(old_pos)
        nodes.add(new_pos)

    return nodes

def compareMoves(move_log, move_list):
    nodes = getNodes(move_log)
    graph = dict()
    for n in nodes:
        graph[n] = defaultdict(int)
    capture_set = set()

    for (old_pos, new_pos, is_capture) in move_list:
        graph[old_pos][new_pos] += 1
        if is_capture:
            capture_set.add(new_pos)

    res = []
    def dfs(curr, path, volume):
        for key in graph[curr]:
            if 
