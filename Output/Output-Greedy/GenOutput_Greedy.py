import sys
import os
import time
import csv
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
    w, h = (box.h, box.w) if rot else (box.w, box.h)

    if x + w > cont.W or y + h > cont.H:
        return False
    if x < 0 or y < 0:
        return False

    old_x, old_y, old_rot = box.x, box.y, box.rotation
    box.x, box.y, box.rotation = x, y, rot
    
    for bid in cont.boxes:
        if box_intersect(box, boxes[bid - 1]):
            box.x, box.y, box.rotation = old_x, old_y, old_rot
            return False
    
    box.x, box.y, box.rotation = old_x, old_y, old_rot
    return True


def get_candidate_positions(cont: Container, boxes) -> List[tuple]:
    positions = set()
    positions.add((0, 0))
    
    for bid in cont.boxes:
        b = boxes[bid - 1]
        w, h = (b.h, b.w) if b.rotation else (b.w, b.h)
        positions.add((b.x + w, b.y))
        positions.add((b.x, b.y + h))
    
    return sorted(positions, key=lambda p: (p[1], p[0]))


def place_box(box: Box, cont: Container, x, y, rot):
    box.x, box.y, box.rotation = x, y, rot
    box.truck = cont.ID
    cont.boxes.append(box.ID)
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


# ===================== SOLVE =====================

def solve_single(input_path):
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
    end_time = time.time()

    cost = total_cost(containers)
    n_used = count_used_trucks(containers)
    running_time = end_time - start_time

    return N, K, n_used, cost, running_time, boxes


def write_output(output_path, N, K, cost, running_time, boxes):
    with open(output_path, "w") as f:
        # Write box placements
        for b in sorted(boxes, key=lambda x: x.ID):
            f.write(f"{b.ID} {b.truck} {b.x} {b.y} {int(b.rotation)}\n")
        # Write summary
        f.write(f"{N} {K} {cost} {running_time:.6f}\n")


# ===================== MAIN =====================

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    test_dir = os.path.join(base_dir, "Test_case")
    output_base = os.path.dirname(os.path.abspath(__file__))

    results = []

    # Phase 1: test 01-40
    # Phase 2: test 00-59
    # Phase 3: test 00-59
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
                N, K, n_used, cost, running_time, boxes = solve_single(input_path)
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
    csv_path = os.path.join(output_base, "result_Greedy.csv")
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['n_items', 'n_trucks', 'n_trucks_used', 'cost', 'running_time'])
        writer.writeheader()
        writer.writerows(results)
    
    print(f"\nResults saved to {csv_path}")


if __name__ == "__main__":
    main()
