import math

def poisson_probability(goals, xG):
    return (
        (xG**float(goals))*float((math.e**(-xG)))/(math.factorial(goals))
    )

# default max goals is 10, based on largest amt of goals scored by a team is 9
'''
    generates probability table of probability of goals scored example
    {
        [0] = 0.238231 -- 23.8%
        [1] = 0.3432 -- 34.2%
    }

'''
def goals_distribution(xG, max_goals=10):
    probs = {}

    for goal in range(max_goals + 1):
        probs[goal] = poisson_probability(goal, xG)

    return probs