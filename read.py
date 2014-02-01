from matplotlib import pyplot as plt
from tsdb.reader import read_all

df = read_all('410730')
plt.plot(df.index, df['value'])
plt.show()


