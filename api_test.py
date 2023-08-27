from app_test import text_gen

if '__main__' == __name__:

    for i in range(3):
        xinput = f'上帝说的第{i}话是'
        xoutput = text_gen(xinput)
        print(xinput, '>>>>', xoutput)
