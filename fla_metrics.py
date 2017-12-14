import math
import numpy as np


def compute_s(epsilon, walk_diff):
    """Computer the symbolic array {-1,0,1} for the FEM metrics."""
    conds = [walk_diff < -epsilon, (walk_diff >= -epsilon) & (walk_diff <= epsilon), walk_diff > epsilon]
    funcs = [-1, 0, 1]
    return np.piecewise(walk_diff, conds, funcs)


def compute_h(symbolic_s):
    """Computer the entropy of the three-point objects in symbolic array {-1,0,1}."""
    bin_count = [0., 0., 0., 0., 0., 0.]
    p = 0
    q = 1
    num_symbols = len(symbolic_s)
    while q < (num_symbols - 1):
        if symbolic_s[p] != symbolic_s[q]:
            if symbolic_s[p] == 0:
                if (symbolic_s[q] == 1):
                    bin_count[0] += 1
                else:
                    bin_count[1] += 1
            if symbolic_s[p] == 1:
                if (symbolic_s[q] == 0):
                    bin_count[2] += 1
                else:
                    bin_count[3] += 1
            if symbolic_s[p] == -1:
                if (symbolic_s[q] == 0):
                    bin_count[4] += 1
                else:
                    bin_count[5] += 1
        p += 1
        q += 1

    entropy = 0.
    for i in range(0, 5):
        if (bin_count[i] != 0):
            bin_count[i] = bin_count[i] / (num_symbols - 2.)
            entropy -= bin_count[i] * math.log(bin_count[i], 6)
    return entropy


def is_flat(s):
    """Given symbolic array S, return true is all symbols = 0, and false otherwise."""
    for i in range(0, len(s)):
        if s[i] != 0:
            return False
    return True


def get_epsilon_star(walk_diff):
    """Calculate epsilon* for the FEM metrics."""
    eps_base = 10.
    eps_step = 10.
    eps = 0.
    eps_order = 0.
    not_found = True
    # Quickly find the order:
    while (not_found):
        symbolic_s = compute_s(eps, walk_diff)
        if is_flat(symbolic_s):
            not_found = False
            eps_step = eps_step / eps_base
        else:
            eps = eps_step
            eps_order += 1
            eps_step *= eps_base
    small_step = 0.01 * (10 ** eps_order)
    not_found = True
    while (not_found):
        symbolic_s = compute_s(eps, walk_diff)
        if is_flat(symbolic_s):
            if eps_step <= small_step:
                not_found = False
            else:
                eps -= eps_step
                eps_step /= eps_base
                eps += eps_step
        else:
            eps += eps_step
    return eps  # this is epsilon*


def compute_fem(walk_diff):
    """Calculate the FEM metric."""
    eps_star = get_epsilon_star(walk_diff)
    incr = 0.05 * eps_star
    h_max = 0.
    for i in np.arange(0., eps_star, incr):
        cur_h = compute_h(compute_s(i, walk_diff))
        if cur_h > h_max: h_max = cur_h
    return h_max


def scale_walk(walk):
    """Scales the walk of arbitrary fitness range to [0,1]"""
    min_f = min(walk)
    max_f = max(walk)
    diff = max_f - min_f
    return (walk - min_f) / diff


def compute_m1(walk, epsilon):
    """Calculate the neutrality metric M1. Input: progressive random walk (fitness values scaled to [0,1])"""
    m1 = 0.
    len_3p_walk = len(walk) - 2
    for i in range(0, len_3p_walk):
        min_f = min(walk[i:i + 3])
        max_f = max(walk[i:i + 3])
        if max_f - min_f <= epsilon: m1 += 1.

    return m1 / len_3p_walk


def compute_m2(walk, epsilon):
    """Calculate the neutrality metric M2. Input: progressive random walk (fitness values scaled to [0,1])"""
    m2 = 0.
    temp = 0.
    len_3p_walk = len(walk) - 2
    for i in range(0, len_3p_walk):
        min_f = min(walk[i:i + 3])
        max_f = max(walk[i:i + 3])
        if max_f - min_f <= epsilon:  # is neutral
            temp += 1.0
        elif temp > 0:
            if temp > m2: m2 = temp
            temp = 0

    return m2 / len_3p_walk


def compute_grad(walk, n, step_size, bounds):
    # (1) calculate the fitness differences:
    err_diff = np.diff(walk)
    # (2) calculate the difference between max and min fitness:
    fit_diff = np.amax(walk) - np.amin(walk)
    # (3) calculate the total manhattan distance between the bounds of the search space
    manhattan_diff = n * 2 * bounds
    scaled_step = step_size / manhattan_diff
    # (4) calculate g(t) for t = 1..T
    g_t = (err_diff / fit_diff) / scaled_step
    # (5) calculate G_avg
    return np.mean(np.absolute(g_t)), np.std(np.absolute(g_t))


if __name__ == '__main__':
    my_walk = np.array([0.,1.,0.,1.,1.,1.,1.,0.,1.,0.,1]) # test
    print "M1: ", compute_m1(scale_walk(my_walk), 1e-8)
    print "M2: ", compute_m2(scale_walk(my_walk), 1e-8)
    print "FEM: ", compute_fem(np.diff(my_walk))
    print "Grad: ", compute_grad(my_walk, 1, 0.1, 0.5)