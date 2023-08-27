import sys
import re
import matplotlib.pyplot as plt

xregex_values = re.compile(r'^epoch\#(\d+):\s+loss\s+\=\s+([\.0-9]+)\s+acc\s+\=\s+\{\'top1\'\:\s+([\.0-9]+)', re.IGNORECASE)

xregex_paths = re.compile(r'saving to (.+)$', re.IGNORECASE)

if '__main__' == __name__:
    # 从命令行拿到日志路径
    argc = len(sys.argv)
    if argc <= 1:
        print('Please provide the log path!')
        sys.exit(1)
    log_path = sys.argv[1]

    # 读取日志
    xloss_list = []
    xtop1_list = []
    xepoch2path = dict()
    xepoch = 0
    with open(log_path, 'r',encoding='utf8') as xfin:
        while True:
            xline = xfin.readline()
            if not xline:
                break
            if '\r\n' == xline[-2:]:
                xline = xline[:-2]
            else:
                xline = xline[:-1]
            xmatches = xregex_values.search(xline)
            xmatches_path = xregex_paths.search(xline)
            if xmatches is None and xmatches_path is None:
                continue
            if xmatches is not None:
                xepoch = int(xmatches[1])
                xloss = float(xmatches[2])
                xtop1 = float(xmatches[3])
                print(xepoch, xloss, xtop1)
                xloss_list.append(xloss)
                xtop1_list.append(xtop1)
            else:
                xpath = xmatches_path[1]
                # print(xpath)
                xepoch2path[xepoch] = xpath

    plt.subplot(1, 2, 1)
    plt.plot(xloss_list)

    plt.subplot(1, 2, 2)
    plt.plot(xtop1_list)

    print(xepoch2path)

    plt.show()
