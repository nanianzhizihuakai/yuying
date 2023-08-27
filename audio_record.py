import time
import redis
import pyaudio

FORMAT = pyaudio.paInt16  # 音频格式
CHANNELS = 1  # 声道数
RATE = 16000  # 采样率
LEN_MS = 40  # 40ms一段
N_CHUNK_SAMPLES = RATE // 1000 * LEN_MS  # 每段录制采样数
print('N_CHUNK_SAMPLES', N_CHUNK_SAMPLES)

rdb = redis.Redis('127.0.0.1', 6379, 0)

if '__main__' == __name__:

    # 使用pyaudio录音
    p = pyaudio.PyAudio()
    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=N_CHUNK_SAMPLES
    )

    REC_TIME_S = 5
    print(f'录制{REC_TIME_S}秒，请ctrl+C终止……')
    for i in range(REC_TIME_S * 1000 // LEN_MS):
        print('.', end='')
        chunk = stream.read(N_CHUNK_SAMPLES)
        rdb.lpush('audio_stream_user001', chunk)
    print()

    print('录制完毕！')
    stream.stop_stream()
    stream.close()
    p.terminate()
