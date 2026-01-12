import sys
import random
from typing import List
import copy
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


def can_place(box: Box, cont: Container, x, y, rot, boxes) -> bool:
    w, h = (box.h, box.w) if rot else (box.w, box.h)

    if x + w > cont.W or y + h > cont.H:
        return False

    box.x, box.y, box.rotation = x, y, rot
    for bid in cont.boxes:
        if box_intersect(box, boxes[bid - 1]):
            return False
    return True


def insert_box(box: Box, cont: Container, x, y, rot):
    w, h = (box.h, box.w) if rot else (box.w, box.h)
    box.x, box.y, box.rotation = x, y, rot
    box.truck = cont.ID

    cont.boxes.append(box.ID)
    cont.boxes_pos.append((x, y + h))
    cont.boxes_pos.append((x + w, y))
    cont.used = True


# ===================== OBJECTIVE =====================
def init_cost(containers):
    return sum(c.cost for c in containers)
def total_cost(containers):
    return sum(c.cost for c in containers if c.used)


# ===================== GREEDY CONSTRUCTION =====================

def greedy_construct(boxes, containers):
    containers.sort(key=lambda c: (c.cost, c.ID))

    for box in boxes:
        placed = False
        for cont in containers:
            for (x, y) in cont.boxes_pos:
                for rot in (False, True):
                    if can_place(box, cont, x, y, rot, boxes):
                        insert_box(box, cont, x, y, rot)
                        cont.boxes_pos.remove((x, y))
                        placed = True
                        break
                if placed:
                    break
            if placed:
                break

        if not placed:
            raise RuntimeError(f"Cannot place box {box.ID}")


# ===================== DESTROY =====================

def destroy_solution(boxes, containers, destroy_rate=0.2):
    # 1. CHỈ lấy box đang được đặt
    active_boxes = [b for b in boxes if b.truck != -1]
    if not active_boxes:
        return []

    # 2. Cost-biased weights
    max_cost = max(containers[b.truck - 1].cost for b in active_boxes)
    # print("max_cost:", max_cost)
    weights = [
        containers[b.truck - 1].cost / max_cost
        for b in active_boxes
    ]

    # 3. Chọn box để destroy
    num_remove = max(1, int(len(active_boxes) * destroy_rate))
    removed = random.choices(active_boxes, weights=weights, k=num_remove)
    removed = list({b.ID: b for b in removed}.values())
    # print("destroyed boxes:", [b.ID for b in removed])
    
    # 4. Destroy = reset assignment (KHÔNG đụng container)
    for b in removed:
        b.truck = -1

    # 5. Rebuild container state từ box assignments

    for c in containers:
        c.boxes.clear()
        c.boxes_pos = [(0, 0)]
        c.used = False

    # Tạo dict để tìm container theo ID (vì containers đã sort)
    cont_by_id = {c.ID: c for c in containers}
    
    for b in boxes:
        if b.truck != -1:
            cont = cont_by_id[b.truck]  # Tìm đúng container theo ID
            insert_box(b, cont, b.x, b.y, b.rotation)
    return removed


# ===================== REPAIR =====================

def repair_solution(removed, boxes, containers):
    # QUAN TRỌNG: Sort theo diện tích giảm dần (đặt box lớn trước)
    removed_sorted = sorted(removed, key=lambda b: b.w * b.h, reverse=True)
    # print("repairing boxes:", [b.ID for b in removed_sorted])
    for b in removed_sorted:
        placed = False
        # Ưu tiên container đã used trước (để không mở thêm container mới)
        for cont in sorted(containers, key=lambda c: (0 if c.used else 1, c.cost, c.ID)):
            for (x, y) in cont.boxes_pos:
                for rot in (False, True):
                    if can_place(b, cont, x, y, rot, boxes):
                        insert_box(b, cont, x, y, rot)
                        cont.boxes_pos.remove((x, y))
                        placed = True
                        break
                if placed:
                    break
            if placed:
                break

        if not placed:
            raise RuntimeError(f"Repair failed for box {b.ID}")


# ===================== LNS =====================

def CB_LNS(boxes, containers, iters=100, destroy_rate=0.3):
    best_cost = total_cost(containers)
    current_container = copy.deepcopy(containers)
    current_boxes = copy.deepcopy(boxes)

    for _ in range(iters):
        removed = destroy_solution(boxes, containers, destroy_rate)
        repair_solution(removed, boxes, containers)

        c = total_cost(containers)
        
        if c < best_cost:
            best_cost = c
            return boxes, containers  # (boxes, containers)
        else:
            # rollback
            for b in boxes:
                b.truck = -1
            for cont in containers:
                cont.used = False
                cont.boxes = []
                cont.boxes_pos = [(0, 0)]
            containers = copy.deepcopy(current_container)
            boxes = copy.deepcopy(current_boxes)

    return current_boxes, current_container  # (boxes, containers) - FIX!


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
    # print("Initial cost:", total_cost(containers))
    for i in range(50):
        # print(f"--- LNS Iteration {i+1} ---")
        current_boxes, current_containers = CB_LNS(boxes, containers)
        print("Final cost:", total_cost(current_containers))
        containers = current_containers
        boxes = current_boxes
    # print("Final cost:", total_cost(containers))
    # for b in boxes:
    #     print(b.ID, b.truck, b.x, b.y, int(b.rotation))


if __name__ == "__main__":
    solve()
