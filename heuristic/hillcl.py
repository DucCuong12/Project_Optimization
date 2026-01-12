import sys
import copy
from typing import List

INF = 10**9


# ===================== DATA STRUCTURES =====================

class Box:
    def __init__(self, ID, w, h):
        self.ID = ID
        self.w = w
        self.h = h
        self.truck = -1
        self.x = 0
        self.y = 0
        self.rotation = False


class Container:
    def __init__(self, ID, W, H, cost):
        self.ID = ID
        self.W = W
        self.H = H
        self.cost = cost
        self.used = False
        self.boxes = []
        self.boxes_pos = [(0, 0)]


# ===================== GEOMETRY =====================

def box_intersect(b1: Box, b2: Box) -> bool:
    w1, h1 = (b1.h, b1.w) if b1.rotation else (b1.w, b1.h)
    w2, h2 = (b2.h, b2.w) if b2.rotation else (b2.w, b2.h)

    if max(b1.x, b2.x) >= min(b1.x + w1, b2.x + w2):
        return False
    if max(b1.y, b2.y) >= min(b1.y + h1, b2.y + h2):
        return False
    return True


def can_place(box: Box, container: Container, x, y, rotation, boxes: List[Box]) -> bool:
    w, h = (box.h, box.w) if rotation else (box.w, box.h)

    if x + w > container.W or y + h > container.H:
        return False

    box.x, box.y, box.rotation = x, y, rotation
    for bid in container.boxes:
        if box_intersect(box, boxes[bid - 1]):
            return False

    return True


def insert_box(box: Box, container: Container, x, y, rotation):
    w, h = (box.h, box.w) if rotation else (box.w, box.h)

    box.x = x
    box.y = y
    box.rotation = rotation
    box.truck = container.ID

    container.boxes.append(box.ID)
    container.boxes_pos.append((x, y + h))
    container.boxes_pos.append((x + w, y))
    container.used = True


# ===================== CONSTRUCTIVE =====================

def find_best_container(box: Box, containers, boxes, used_flag):
    best = None
    min_cost = INF
    best_sum = INF

    for i, cont in enumerate(containers):
        if cont.used != used_flag:
            continue

        for pos in cont.boxes_pos:
            for rot in (False, True):
                if can_place(box, cont, pos[0], pos[1], rot, boxes):
                    s = pos[0] + pos[1]
                    if cont.cost < min_cost or (cont.cost == min_cost and s < best_sum):
                        min_cost = cont.cost
                        best_sum = s
                        best = (i, pos, rot)

        if cont.cost >= min_cost:
            break

    if best is not None:
        return best

    return find_best_container(box, containers, boxes, False)


def construct_initial_solution(boxes, containers):
    for box in boxes:
        ci, pos, rot = find_best_container(box, containers, boxes, True)
        containers[ci].boxes_pos.remove(pos)
        insert_box(box, containers[ci], pos[0], pos[1], rot)


# ===================== COST =====================

def compute_cost(containers):
    return sum(c.cost for c in containers if c.used)


# ===================== HILL CLIMBING =====================

def find_container_of_box(box_id, containers):
    for c in containers:
        if box_id in c.boxes:
            return c
    return None


def hill_climbing(boxes, containers):
    """
    Hill Climbing using RELOCATION move:
    Move one box from its current container to another container
    if total cost is reduced.
    """

    best_cost = compute_cost(containers)
    improved = True

    while improved:
        improved = False

        # iterate over boxes by ID (stable)
        for box in boxes:

            # find source container (DO NOT trust box.truck)
            src = find_container_of_box(box.ID, containers)
            if src is None:
                continue

            # try moving box to another container
            for dst in containers:
                if dst is src:
                    continue

                # try all extreme points
                for pos in dst.boxes_pos:
                    for rot in (False, True):

                        # --- copy whole state ---
                        boxes_cp = copy.deepcopy(boxes)
                        conts_cp = copy.deepcopy(containers)

                        b = boxes_cp[box.ID - 1]
                        src_cp = find_container_of_box(b.ID, conts_cp)
                        dst_cp = conts_cp[dst.ID - 1]

                        if src_cp is None:
                            continue

                        # remove from source
                        src_cp.boxes.remove(b.ID)
                        if not src_cp.boxes:
                            src_cp.used = False

                        # try place in destination
                        if not can_place(b, dst_cp, pos[0], pos[1], rot, boxes_cp):
                            continue

                        insert_box(b, dst_cp, pos[0], pos[1], rot)

                        new_cost = compute_cost(conts_cp)

                        # hill climbing: accept ONLY improvement
                        if new_cost < best_cost:
                            boxes[:] = boxes_cp
                            containers[:] = conts_cp
                            best_cost = new_cost
                            improved = True
                            break

                    if improved:
                        break
                if improved:
                    break
            if improved:
                break

    return boxes, containers

# ===================== MAIN =====================

def solve():
    data = sys.stdin.read().strip().split()
    it = iter(data)

    N = int(next(it))
    K = int(next(it))

    boxes = [Box(i + 1, int(next(it)), int(next(it))) for i in range(N)]
    containers = [
        Container(i + 1, int(next(it)), int(next(it)), int(next(it)))
        for i in range(K)
    ]

    containers.sort(key=lambda c: (c.cost, c.ID))

    # 1️⃣ Construct
    construct_initial_solution(boxes, containers)

    # 2️⃣ Hill Climbing
    boxes, containers = hill_climbing(boxes, containers)

    # Output
    for box in boxes:
        print(box.ID, box.truck, box.x, box.y, int(box.rotation))


if __name__ == "__main__":
    solve()
