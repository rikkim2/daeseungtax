import os

from pyChatGPT import ChatGPT

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from app.models import MemUser
from django.http import HttpResponse
from django.views import View

# session_token = 'eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIn0..Yx_LARMQsk2D-qFV.PbnTHZArsQFskbkk_SSdzPUJzm2KBEUMRKevoMwSyandeVixuzoYJrzSPus1oU0i7ve0bvZ7ClthC5G7HiyRPaYlCp3FXxl805BiME-7aRYc5OttbugVNhKCnAYIYKh-nxJ0fw_fW2TkXmIB9a9He4HZjeRVe0ax7z85D-XE8fMMN9jobrCnEs6vbMXyUXtA4kuqfT2qPjhNRpVi8ZNy-7_Ph-CuGmIxNVNqlhwuw2C6qUJY9Zvzr1JIv6ATeI6TZRm_De9pRGShbH5o26yIrANjOyJ5U6LiiBBK5DM7QQhFAyRquM1a1HmKIaSh-XJmmbAqNxG5mZMYgX0UWVgRb4oVR0pKMImX9TZYomVHJp6vnioS0uAjoC_Ke1qKeFKhsOVj24jNB3G1h9PllP0HWSrbKPiT-v_dFYxz1g12uBYZ1jFgza19dNGm4mWCvY-8jKxJTtRkGotasdZ5I4D-MNwEEOGlS7snhaQf3VBzHYED0ywsl-W1x-KENL09Urvs0DsouZLV9tqSC-79RiSdIxxt3-gErjj_uF80V7QMmuZqmZVLw8ozMkY0P19rN4EkXcYCyhPHEUJ1uXHfshmlAefcAJfLBdCnvuB3QLokGTFY2Cyk1efwFDpE2XVc4j1Atm9W9_cU0g8-UZLNl6FosjB3UHMcqVezHc6Ejfq_1Gg_ydH2lTf4RCqqoLTEMzUevY6O7LkpTTEpYsnu2YkD-iSpqHB_TRV2rDCY2w5jlFe1yCrh-18D3-GVQ5NHleASEAutTkIhOpz0DEssL1U65SnhB7ppculf2lm0fKy6M8G2OciHAr4rxtD69CWUW4aCDnLVZcDs7Rg4ABmgoiTKLyEKpymSZHA7K6vVIzaHEW_i71pg6HD7VQw8zTsjluLojSf_AkBPEzw9SJjDzn-2v-IJ5IRXWrkpI-9uVHKvrJOCEPzgvYk6cxmiBuLGezvAvVx9gI2_UJ4hRECFaz9HRn47gRnZwsaW1gOb-hA9Z7H4O66qsNHSsQzv-ZdGX_K6y9n1dev5K6DVXQdqAyf-5f9N2ror1icAkVK9B2EBsfZmLa_wic1H4-9mduoW9hBLH9zY-jLH-3lp8jbutADcVr01CrAorSc1DJFeHmsVLBuvOTKPvBPzDjzXgLLx3nOLwluG79aNSkLTKfnbjMSCSIH1OBdMWICQ-oZbANIMiPY6spq5NebNnhIYrmVPLTudCkYh6EJ8xBifu7Pq98PRTsG9GCjoHA1l6JLMvNoF7PI9Xpq0A-nLGW5wji0zqnsz53g-KKEwVl7XZiJZN5MJqmlKwQdAqGnv10cQfZfnybH-B-Q-YtrJ1yWxmd-9JDoIzE6EFUpEe8Ns2Tt-Ss_v_PiC9EZeaDySSsbAiDXcbhi0WLyAOBqDk7KOPYcT5DXnXyWIb346plyd4Wm7vRRbhg3pNkatbEzq-Eqaw81xfqTCqFvORzT7B0tlS1JMDR1cvsqENf8u5HVDWoYpNUHPmAL6GQ4xQmzfsXx35mC6aAPIL6_YaAqtcfo8H_34DYffcrmKp_6TC2NnVHNu4_hTa9iaeGrUrnOBkASfHbqGChm69lh8nWOUCOpSu5P02bUlSaAXdf4EzXQGM6rNcKbmi4VvTT0wJEV6DwHGfcRUhEsO5ro-11lrps0Q-NrVVeTXHFW2Ohk7FBdhnEfvwQZCPEo1xa5fvXnEV4CrgtHtiLrLPzJZcqrn6b4pkaxCX4qqGnv0gRHkFtOmFeBsXFV6C0Pj1QaKPNtVeNIoMHM8VVp2tcenwTMFBgPChzMhlc_2yOY_wD5PCMf_Tuf2OUrv73cwKVPzerKAJIbh8ur6eDyIwg6effMD1H5mOD8nswC_3NgawX1NK-uL8bklDjRJglxAhvn74BxxX8USsoieo5sy7RfZunX2RIXYDpvVNBIKMmZKMXubMdPzTo9I90p5Uo5wnMQOEpIjj6Qx1IxVPhnPgJ6u9wxnOzXjCHVzL0yCnsCSYKZeYt5SI8s-OMhKNTU93OxFLRvqEOCgB65Sl-B94NJhHhdWzdarorVedebdGX1SI_yRbXMw_b6q3xFRLelvwMY2wGpw_KCvzUhcQJVf_i5-wXSbf5DDRsTRGwYR6ZXaXgw-si5LA_tvwdr-Mlc3pWrymgwEN0RVQP2OAGlzvrPCOBGGhrMIz_1W0PcHByvrdHKwFXWm5ZC2LUuEeKVMDqPgNAnxmC5tJd80STO6fRA63HWygO7aufZACC_Zeodu3J5pi7kF-rhKLH1E_ZGIjveviEOkd9OfeA.Y2W27j-XdaaO4pb4UH4xGA'
# api1 = ChatGPT(session_token)  # auth with session token
# api2 = ChatGPT(session_token, proxy='http://127.0.0.1:8000')  # specify proxy
# api3 = ChatGPT(auth_type='google', email='daeseung23@gmail.com', password='zrncmbdvtrphknoa')  # auth with google login
# api4 = ChatGPT(session_token, moderation=False)  # disable moderation
# api5 = ChatGPT(session_token, window_size=(1024, 768))  # specify window size
# api6 = ChatGPT(session_token, verbose=True)  # verbose mode (print debug messages)


# api7 = ChatGPT(auth_type='openai', email='daeseung23@gmail.com', password='zrncmbdvtrphknoa', verbose=True)

# api8 = ChatGPT(auth_type='openai', email='daeseung23@gmail.com', password='zrncmbdvtrphknoa',
#                twocaptcha_apikey='2captcha_apikey',
#                verbose=True)

# api9 = ChatGPT(auth_type='openai', email='daeseung23@gmail.com', password='zrncmbdvtrphknoa',
#                login_cookies_path='your_cookies_path',
#                verbose=True)

# resp = api1.send_message('Hello, world!')
# print(resp['message'])

# api1.reset_conversation()  # reset the conversation






@login_required(login_url="/login/")
def index(request):
  context = {}
  # chatbot_response("한국 종합소득세율은 몇퍼센트?")
  return render(request, "faq/faqAI.html",context)
