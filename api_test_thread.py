from app_test import text_gen
from threading import Thread, Lock

if '__main__' == __name__:

    xlock = Lock()

    def run(i):
        xinput = f'上帝说的第{i}话是'
        print('<<<<', xinput)
        xoutput = text_gen(xinput)
        with xlock:
            print(xinput, '>>>>', xoutput)

    xpool = []
    for i in range(7):
        xthread = Thread(target=run, args=(i + 1, ))
        xthread.start()
        xpool.append(xthread)

    for xthread in xpool:
        xthread.join()

    print('-------------ALL OVER------------')
