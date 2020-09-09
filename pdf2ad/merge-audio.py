from pydub import AudioSegment

sound = AudioSegment.from_mp3("TOC__Training_.mp3")
sound_1 = AudioSegment.from_mp3("TOC__Training_.mp3")
sound_2 = AudioSegment.from_mp3("TOC__Training_.mp3")
sound_3 = sound+sound_1+sound_2
sound_3.export("sound_3_merged.mp3", format="mp3")
