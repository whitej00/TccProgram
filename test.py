import matplotlib.pyplot as plt
import math

EFFORT = 10000
X = list(range(1, 100))
# Y = list(map(lambda x : 10 * math.log2(x), X))
Y = list(map(lambda x : x ** 2, X))
Y2 = list(map(lambda y : EFFORT / y, Y))

plt.plot(X, Y, 'r--', X, Y2, 'b--')
plt.show()