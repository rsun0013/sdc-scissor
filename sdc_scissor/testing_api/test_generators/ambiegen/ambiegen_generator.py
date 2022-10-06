# from code_pipeline.tests_generation import RoadTestFactory
from time import sleep
import logging as log

from pymoo.optimize import minimize

from sdc_scissor.testing_api.test_generators.ambiegen.Utils.test_case_problem import TestCaseProblem
from sdc_scissor.testing_api.test_generators.ambiegen.Utils.test_case_mutation import TestCaseMutation
from sdc_scissor.testing_api.test_generators.ambiegen.Utils.test_case_crossover import TestCaseCrossover
from sdc_scissor.testing_api.test_generators.ambiegen.Utils.duplicate_elimination import DuplicateElimination
from sdc_scissor.testing_api.test_generators.ambiegen.Utils.generate_test_case_sampling import GenerateTestCaseSampling
import time
from pymoo.algorithms.nsga2 import NSGA2
import sdc_scissor.testing_api.test_generators.ambiegen.config as cf


class CustomAmbieGenGenerator:
    """
    This test generator creates road points using affine tratsformations to vectors.
    Initially generated test cases are optimized by NSGA2 algorithm with two objectives:
    fault revealing power and diversity. We use a simplified model of a vehicle to
    estimate the fault revealing power (as the maximum deviation from the road center).
    We use 100 generations and 100 population size. In each iteration of the generator
    the Pareto optimal solutions are provided and executed. Then the algorithm is launched again.
    """

    def __init__(self, time_budget=None, executor=None, map_size=200):
        self.map_size = cf.model["map_size"]
        self.time_budget = time_budget
        self.executor = executor

    def start(self):
        """
        In this function the algorithm is launched and
        the Pareto optimal solutions are returned
        """

        log.info("Test generation ambiegen.")
        algorithm = NSGA2(
            n_offsprings=50,
            pop_size=cf.ga["population"],
            sampling=GenerateTestCaseSampling(),
            crossover=TestCaseCrossover(cf.ga["cross_rate"]),
            mutation=TestCaseMutation(cf.ga["mut_rate"]),
            eliminate_duplicates=DuplicateElimination(),
        )

        t = int(time.time() * 1000)
        seed = ((t & 0xFF000000) >> 24) + ((t & 0x00FF0000) >> 8) + ((t & 0x0000FF00) << 8) + ((t & 0x000000FF) << 24)

        res = minimize(
            TestCaseProblem(),
            algorithm,
            ("n_gen", cf.ga["n_gen"]),
            seed=seed,
            verbose=False,
            save_history=True,
            eliminate_duplicates=True,
        )

        # print("Best solution found: \nF = %s" % (res.F))
        gen = len(res.history) - 1
        test_cases = []
        i = 0
        log.info(res)
        existing_points = set()
        for gen1 in range(0,len(res.history)):
            i = 0
            while i < len(res.F):
                result = res.history[gen1].pop.get("X")[i]
                road_points = result[0].intp_points
                result[0].calcTurns()
                if tuple(road_points) not in existing_points:
                    test_cases.append((tuple(road_points),result[0].uturns))
                existing_points.add(tuple(road_points))
                i += 1
        #test_cases = list(dict.fromkeys(test_cases))
        return test_cases
