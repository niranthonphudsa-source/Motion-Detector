import math

def get_distance(p1, p2):
    if p1 is None or p2 is None: return 999999
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])