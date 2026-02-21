import random

def gaussian_sample(min_val, max_val, median=None):
    """
    Generate random samples from a normal distribution.
    
    - If median is not provided, it's calculated as midpoint of min and max
    - σ = (max_val - min_val) / 6
    - Samples are clamped to [min_val, max_val]
    - Returns a single float if n=1, otherwise a list
    """
    mu = median if median is not None else (min_val + max_val) / 2
    sigma = (max_val - min_val) / 6

    res = 0
    value = random.gauss(mu, sigma)
    value = max(min_val, min(max_val, value))
    res = value

    return res

sample = gaussian_sample(2, 10, 4.5)
for i in range(0, 7):
    print(sample / 7 < random.uniform(0,1))