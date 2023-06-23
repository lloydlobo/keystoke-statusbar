import timeit

"""
20230623 12:10pm zsh $ fd | entr -a python benchmarks/repeat_blinker.py
Timestamp: 2023-06-23 12:10pm

Benchmark Results:

Approach 1 execution time: 0.1358351930102799
Approach 2 execution time: 0.1464715600013733
Approach 1 execution time: 0.15091263700742275
Approach 2 execution time: 0.17113871900073718
Approach 1 execution time: 0.14487505500437692
Approach 2 execution time: 0.15307779899740126
Approach 1 execution time: 0.13119528599781916
Approach 2 execution time: 0.14762886799871922
Approach 1 execution time: 0.1345155849994626
Approach 2 execution time: 0.16528391500469297
Approach 1 execution time: 0.14086058299290016
Approach 2 execution time: 0.14593262600828893
Approach 1 execution time: 0.1390316269971663
Approach 2 execution time: 0.17395710000710096
Approach 1 execution time: 0.14983699499862269
Approach 2 execution time: 0.16607758001191542

Conclusion:
Based on the benchmark results, it can be observed that the execution
times for Approach 1 and Approach 2 are relatively close. There is
some variation in the execution times between different runs, but overall, the
difference in performance between the two approaches is not significant.
Therefore, in terms of performance, both approaches can be
considered comparable.
"""


class MyClass:
    def __init__(self):
        self.background = ['']  # Replace with the appropriate initialization
        self.repeat_blinker = 0

    def approach1(self):
        # First implementation using if-else statements
        match self.repeat_blinker:
            case 0:
                self.background[0] = '░'
            case 1:
                self.background[0] = '▓'
            case 2:
                self.background[0] = '█'
        self.repeat_blinker = (self.repeat_blinker + 1) % 3

        # self.repeat_blinker += 1
        # self.repeat_blinker %= 3

    def approach2(self):
        # Second implementation using a list and modulo arithmetic
        brightness_levels = ['░', '▓', '█']
        self.background[0] = brightness_levels[self.repeat_blinker %
                                               len(brightness_levels)]
        self.repeat_blinker += 1


# Create an instance of MyClass
my_object = MyClass()

# Measure execution time of approach 1
time1 = timeit.timeit(my_object.approach1, number=1_000_000)

# Measure execution time of approach 2
time2 = timeit.timeit(my_object.approach2, number=1_000_000)

print("Approach 1 execution time:", time1)
print("Approach 2 execution time:", time2)

"""
Timestamp: 12: 23pm

Benchmark Results:

Approach 1 mod execution time: 0.10104788100579754
Approach 2 mod execution time: 0.07497309299651533
Approach 1 mod execution time: 0.1052592949999962
Approach 2 mod execution time: 0.09829926800739486
Approach 1 mod execution time: 0.1202450900018448
Approach 2 mod execution time: 0.09305175200279336
Approach 1 mod execution time: 0.13630819699028507
Approach 2 mod execution time: 0.0821700980013702
Approach 1 mod execution time: 0.16806030299630947
Approach 2 mod execution time: 0.09783654000784736
Approach 1 mod execution time: 0.12246345700987149
Approach 2 mod execution time: 0.10021215899905656
Approach 1 mod execution time: 0.11530429699632805
Approach 2 mod execution time: 0.08205466400249861
Approach 1 mod execution time: 0.10933067300356925
Approach 2 mod execution time: 0.08002849700278603
Approach 1 mod execution time: 0.10363263900217135
Approach 2 mod execution time: 0.08499671999015845
Approach 1 mod execution time: 0.11571741300576832
Approach 2 mod execution time: 0.0796079880092293
Approach 1 mod execution time: 0.10989527399942745
Approach 2 mod execution time: 0.07559441099874675
Approach 1 mod execution time: 0.10029658600979019
Approach 2 mod execution time: 0.07436031500401441
Approach 1 mod execution time: 0.1026989060046617
Approach 2 mod execution time: 0.07470317800471094
Approach 1 mod execution time: 0.10441498999716714
Approach 2 mod execution time: 0.07603902999835555
Approach 1 mod execution time: 0.11532512100529857
Approach 2 mod execution time: 0.07396074899588712
Approach 1 mod execution time: 0.11176310900191311
Approach 2 mod execution time: 0.0784656489995541
Approach 1 mod execution time: 0.1006971229944611
Approach 2 mod execution time: 0.07436198998766486
Approach 1 mod execution time: 0.1000153799977852
Approach 2 mod execution time: 0.07569137000245973

Conclusion:
Based on the benchmark results, it can be concluded that Approach 2, which
uses the modulo operation directly in the assignment statement, is
consistently faster than Approach 1, which separately increments and
then performs the modulo operation. The execution times for Approach 2 are
consistently lower, indicating that it takes less time to execute compared
to Approach 1. Therefore, in terms of performance, Approach 2 is the
faster option.

"""

repeat_blinker = 0


def approach1():
    global repeat_blinker
    repeat_blinker += 1
    repeat_blinker %= 3


def approach2():
    global repeat_blinker
    repeat_blinker = (repeat_blinker + 1) % 3


# Measure execution time of approach 1
time1 = timeit.timeit(approach1, number=1000000)

# Measure execution time of approach 2
time2 = timeit.timeit(approach2, number=1000000)

print("Approach 1 mod execution time:", time1)
print("Approach 2 mod execution time:", time2)
