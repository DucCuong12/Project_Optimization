import sys
import os
import time
import csv
import random
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

def total_cost(containers):
    return sum(c.cost for c in containers if c.used)


def count_used_trucks(containers):
    return sum(1 for c in containers if c.used)


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
    active_boxes = [b for b in boxes if b.truck != -1]
    if not active_boxes:
        return []

    max_cost = max(containers[b.truck - 1].cost for b in active_boxes)
    weights = [
        containers[b.truck - 1].cost / max_cost
        for b in active_boxes
    ]

    num_remove = max(1, int(len(active_boxes) * destroy_rate))
    removed = random.choices(active_boxes, weights=weights, k=num_remove)
    removed = list({b.ID: b for b in removed}.values())
    
    for b in removed:
        b.truck = -1

    for c in containers:
        c.boxes.clear()
        c.boxes_pos = [(0, 0)]
        c.used = False

    cont_by_id = {c.ID: c for c in containers}
    
    for b in boxes:
        if b.truck != -1:
            cont = cont_by_id[b.truck]
            insert_box(b, cont, b.x, b.y, b.rotation)
    return removed


# ===================== REPAIR =====================

def repair_solution(removed, boxes, containers):
    removed_sorted = sorted(removed, key=lambda b: b.w * b.h, reverse=True)
    
    for b in removed_sorted:
        placed = False
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
            current_container = copy.deepcopy(containers)
            current_boxes = copy.deepcopy(boxes)
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

    return current_boxes, current_container, best_cost


# ===================== SOLVE =====================

def solve_single(input_path, lns_rounds=50, iters_per_round=100, destroy_rate=0.3):
    with open(input_path, "r") as f:
        data = f.read().strip().split()

    it = iter(data)

    N = int(next(it))
    K = int(next(it))

    boxes = [Box(i + 1, int(next(it)), int(next(it))) for i in range(N)]
    containers = [
        Container(i + 1, int(next(it)), int(next(it)), int(next(it)))
        for i in range(K)
    ]

    start_time = time.time()
    
    greedy_construct(boxes, containers)
    
    for _ in range(lns_rounds):
        boxes, containers, _ = CB_LNS(boxes, containers, iters=iters_per_round, destroy_rate=destroy_rate)
    
    end_time = time.time()

    cost = total_cost(containers)
    n_used = count_used_trucks(containers)
    running_time = end_time - start_time

    return N, K, n_used, cost, running_time, boxes


def write_output(output_path, N, K, cost, running_time, boxes):
    with open(output_path, "w") as f:
        for b in sorted(boxes, key=lambda x: x.ID):
            f.write(f"{b.ID} {b.truck} {b.x} {b.y} {int(b.rotation)}\n")
        f.write(f"{N} {K} {cost} {running_time:.6f}\n")


# ===================== MAIN =====================

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    test_dir = os.path.join(base_dir, "Test_case")
    output_base = os.path.dirname(os.path.abspath(__file__))

    results = []

    phases = [
        (1, 1, 40),
        (2, 0, 59),
        (3, 0, 59)
    ]

    for phase, start, end in phases:
        for test_num in range(start, end + 1):
            test_str = f"{test_num:02d}"
            input_path = os.path.join(test_dir, f"Phase_{phase}", f"input{test_str}.txt")
            output_path = os.path.join(output_base, f"Phase_{phase}", f"output{test_str}.txt")

            if not os.path.exists(input_path):
                print(f"Skip: {input_path} not found")
                results.append({
                    'n_items': 'N/A',
                    'n_trucks': 'N/A',
                    'n_trucks_used': 'N/A',
                    'cost': 'N/A',
                    'running_time': 'N/A'
                })
                continue

            try:
                N, K, n_used, cost, running_time, boxes = solve_single(
                    input_path, lns_rounds=50, iters_per_round=100, destroy_rate=0.3
                )
                write_output(output_path, N, K, cost, running_time, boxes)
                
                results.append({
                    'n_items': N,
                    'n_trucks': K,
                    'n_trucks_used': n_used,
                    'cost': cost,
                    'running_time': f"{running_time:.6f}"
                })
                print(f"Phase {phase} - Test {test_str}: Cost={cost}, Time={running_time:.6f}s")
            except Exception as e:
                print(f"Error Phase {phase} - Test {test_str}: {e}")
                results.append({
                    'n_items': 'N/A',
                    'n_trucks': 'N/A',
                    'n_trucks_used': 'N/A',
                    'cost': 'N/A',
                    'running_time': 'N/A'
                })

    # Write CSV
    csv_path = os.path.join(output_base, "result_CBGLS.csv")
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['n_items', 'n_trucks', 'n_trucks_used', 'cost', 'running_time'])
        writer.writeheader()
        writer.writerows(results)
    
    print(f"\nResults saved to {csv_path}")


if __name__ == "__main__":
    main()
