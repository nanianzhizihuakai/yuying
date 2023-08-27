import time
import redis
import pyaudio
from audio_record import (
    FORMAT,
    CHANNELS,
    RATE,
    LEN_MS,
    N_CHUNK_SAMPLES,
)

rdb = redis.Redis('127.0.0.1', 6379, 0)

if '__main__' == __name__:

    # 使用pyaudio录音
    p = pyaudio.PyAudio()
    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        output=True
    )

    print('播放中，请ctrl+C终止……')
    while True:
        chunk = rdb.rpop('audio_stream_user001')
        if chunk is None:
            time.sleep(0.001)  # 重要
            continue
        print('.', end='')
        stream.write(chunk)
    print()

    print('播放完毕！')
    stream.stop_stream()
    stream.close()
    p.terminate()
