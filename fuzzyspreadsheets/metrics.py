#!/usr/bin/env python

"""
metric functions for fuzzy matching
"""


from .utils import check_types, check_empty_or_none, check_equivalence



def levenshtein_distance(s1, s2, replacement_cost=2):
    """Stanford's Percy Liang algorithm from lecture 1 (the fastest)"""
    
    # Cache for memoization
    cache = dict()
    
    # Inner recursive function
    def recurse(i, j, replacement_cost=2):
        # If cached - retrun from chache
        if (i,j) in cache: return cache[(i,j)]
        
        # Base case
        if i == 0: return j
        if j == 0: return i
        
        # If last letters are the same
        if s2[i-1] == s1[j-1]:
            ans = recurse(i-1, j-1, replacement_cost=replacement_cost)
            
        # If last letters differ
        else:
            sub_cost = recurse(i-1, j-1, replacement_cost=replacement_cost) + replacement_cost   # substitution cost
            ins_cost = recurse(i-1, j, replacement_cost=replacement_cost) + 1   # insertion cost
            del_cost = recurse(i, j-1, replacement_cost=replacement_cost) + 1   # deletion cost
            ans = min(sub_cost, ins_cost, del_cost)
        
        # Cache and return
        cache[(i,j)] = ans
        return ans
    return recurse(len(s2), len(s1), replacement_cost=replacement_cost)




@check_types(str, str)   # this will be checkd first
@check_empty_or_none     # this will be checked second
@check_equivalence       # this will be checked last
def levenshtein_ratio(s1, s2):
    """Levenshtein similarity ratio"""
    if not (s1 and s2):   # both strings must be > zero-length
        return None
    d = levenshtein_distance(s1, s2, replacement_cost=2)  # must be 2 here !!!
    return (len(s1) + len(s2) - d) / (len(s1) + len(s2))




def cosine_similarity(vector1, vector2):
    """cosine similarity of two vectors"""
    assert len(vector1) == len(vector2), "both vectors must be of equal length"
    return sum(c1*c2 for c1,c2 in zip(vector1, vector2)) / ( sum(v**2 for v in vector1) ** 0.5 * sum(v**2 for v in vector2) ** 0.5  )




@check_types(str, str)   # this will be checkd first
@check_empty_or_none     # this will be checked second
@check_equivalence       # this will be checked last
def token_set_ratio(s1, s2):
    """Roughly emulates the function by the same name from the fuzzywuzzy package"""
    s1,s2 = ([s.strip() for s in s.strip().replace(',', ' ').upper().split(' ') if s] for s in (s1,s2))
    s1,s2 = (s1,s2) if len(s1) <= len(s2) else (s2,s1)
    vectors1,vectors2 = ([(ord(s[0])-33, len(s)) for s in st] for st in (s1,s2))
    n = max(vectors1 + vectors2, key=lambda t: t[0])[0]
    vectors1,vectors2 = ([(c2, *([0,]*c1+[1,]+[0,]*(n-c1))) for c1,c2 in vectors] for vectors in (vectors1,vectors2))
    
    ll = []; [ll.append([]) for v in s1]
    ll = [[cosine_similarity(v1,v2) for v2 in vectors2] for v1 in vectors1]
    
    right_indeces = [t[0] for t in sorted([(i,max(l)) for i,l in enumerate(ll)], reverse=True, key=lambda t: t[-1])]
    left_indeces = list(range(len(s2)))
    fuzzy_set = list()
    
    for right_ix in right_indeces:
        left_ix = ll[right_ix].index(max(ll[right_ix]))
        if left_ix not in left_indeces: continue
        fuzzy_set.append((right_ix, left_ix))
        if left_ix in left_indeces: left_indeces.remove(left_ix)
        
    fuzzy_set = [(s1[ix_left], s2[ix_right]) for (ix_left, ix_right) in fuzzy_set]
    ratio = sum(levenshtein_ratio(s1,s2) for s1,s2 in fuzzy_set) / len(fuzzy_set)
    return ratio



@check_types(str, str)   # this will be checkd first
@check_empty_or_none     # this will be checked second
@check_equivalence       # this will be checked last
def n_grams_ratio(s1, s2, n=2):
    """as described in  https://www.youtube.com/watch?v=YhrKvEjpBYo"""
    n = min(len(s1), len(s2), n)
    s1, s2 = (str(s).strip().lower() for s in (s1,s2))
    S1, S2 = (frozenset(s[i:i+n] for i in range(len(s)-(n-1))) for s in (s1, s2))
    normalizer = len(S1.union(S2))
    if normalizer == 0: return 0
    return len(S1.intersection(S2)) / normalizer

