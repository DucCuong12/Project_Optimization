import sys
import random
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
        self.boxes = []  # list of box IDs


# ===================== GEOMETRY =====================

def box_intersect(b1: Box, b2: Box) -> bool:
    w1, h1 = (b1.h, b1.w) if b1.rotation else (b1.w, b1.h)
    w2, h2 = (b2.h, b2.w) if b2.rotation else (b2.w, b2.h)

    if max(b1.x, b2.x) >= min(b1.x + w1, b2.x + w2):
        return False
    if max(b1.y, b2.y) >= min(b1.y + h1, b2.y + h2):
        return False
    return True


def can_place_at(box: Box, cont: Container, x, y, rot, boxes) -> bool:
    """Kiểm tra có thể đặt box tại (x,y) với rotation rot không"""
    w, h = (box.h, box.w) if rot else (box.w, box.h)

    if x + w > cont.W or y + h > cont.H:
        return False
    if x < 0 or y < 0:
        return False

    # Tạm set để check intersection
    old_x, old_y, old_rot = box.x, box.y, box.rotation
    box.x, box.y, box.rotation = x, y, rot
    
    for bid in cont.boxes:
        if box_intersect(box, boxes[bid - 1]):
            box.x, box.y, box.rotation = old_x, old_y, old_rot
            return False
    
    box.x, box.y, box.rotation = old_x, old_y, old_rot
    return True


def get_candidate_positions(cont: Container, boxes) -> List[tuple]:
    """
    Tính tất cả candidate positions trong container.
    Sử dụng Bottom-Left heuristic: các điểm góc của boxes + (0,0)
    """
    positions = set()
    positions.add((0, 0))
    
    for bid in cont.boxes:
        b = boxes[bid - 1]
        w, h = (b.h, b.w) if b.rotation else (b.w, b.h)
        # Góc trên-trái và góc phải-dưới của mỗi box
        positions.add((b.x + w, b.y))  # phải của box
        positions.add((b.x, b.y + h))  # trên của box
    
    return sorted(positions, key=lambda p: (p[1], p[0]))  


def place_box(box: Box, cont: Container, x, y, rot):
    """Đặt box vào container tại vị trí (x, y)"""
    box.x, box.y, box.rotation = x, y, rot
    box.truck = cont.ID
    cont.boxes.append(box.ID)
    cont.used = True


# ===================== OBJECTIVE =====================

def total_cost(containers):
    return sum(c.cost for c in containers if c.used)


# ===================== GREEDY CONSTRUCTION =====================

def greedy_construct(boxes, containers):
    """Greedy: đặt từng box vào container có cost thấp nhất mà fit được"""
    containers.sort(key=lambda c: (c.cost, c.ID))

    for box in boxes:
        placed = False
        for cont in containers:
            # Tính candidate positions động
            positions = get_candidate_positions(cont, boxes)
            for (x, y) in positions:
                for rot in (False, True):
                    if can_place_at(box, cont, x, y, rot, boxes):
                        place_box(box, cont, x, y, rot)
                        placed = True
                        break
                if placed:
                    break
            if placed:
                break

        if not placed:
            raise RuntimeError(f"Cannot place box {box.ID}")


# ===================== DESTROY =====================

def rebuild_container_state(boxes, containers):
    """Rebuild container.boxes từ thông tin boxes"""
    for c in containers:
        c.boxes.clear()
        c.used = False

    for b in boxes:
        if b.truck != -1:
            cont = containers[b.truck - 1]
            cont.boxes.append(b.ID)
            cont.used = True


def random_destroy(boxes, containers, destroy_rate=0.2):
    """Randomly remove some boxes from solution"""
    active_boxes = [b for b in boxes if b.truck != -1]
    if not active_boxes:
        return []

    num_remove = max(1, int(len(active_boxes) * destroy_rate))
    removed = random.sample(active_boxes, num_remove)

    # Reset assignment cho các boxes bị remove
    for b in removed:
        b.truck = -1

    # Rebuild container state
    rebuild_container_state(boxes, containers)

    return removed


# ===================== REPAIR =====================

def repair_solution(removed, boxes, containers):
    """Repair: đặt lại các boxes đã bị remove"""
    # Sort removed boxes theo diện tích giảm dần (đặt box lớn trước)
    removed_sorted = sorted(removed, key=lambda b: b.w * b.h, reverse=True)
    
    for b in removed_sorted:
        placed = False
        # Ưu tiên đặt vào containers đã used (cost thấp) trước
        for cont in sorted(containers, key=lambda c: (0 if c.used else 1, c.cost, c.ID)):
            positions = get_candidate_positions(cont, boxes)
            for (x, y) in positions:
                for rot in (False, True):
                    if can_place_at(b, cont, x, y, rot, boxes):
                        place_box(b, cont, x, y, rot)
                        placed = True
                        break
                if placed:
                    break
            if placed:
                break

        if not placed:
            raise RuntimeError(f"Repair failed for box {b.ID}")

# ===================== IO =====================

def solve():
    with open("example.txt", "r") as f:
        data = f.read().strip().split()

    it = iter(data)

    N = int(next(it))
    K = int(next(it))

    boxes = [Box(i + 1, int(next(it)), int(next(it))) for i in range(N)]
    containers = [
        Container(i + 1, int(next(it)), int(next(it)), int(next(it)))
        for i in range(K)
    ]

    containers.sort(key=lambda c: (c.cost, c.ID))

    greedy_construct(boxes, containers)
    print("After greedy - Cost:", total_cost(containers))
    
    # random_LNS(boxes, containers, iters=100, destroy_rate=0.3)
    
    # print("Final cost:", total_cost(containers))


if __name__ == "__main__":
    solve()
