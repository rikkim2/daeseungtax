from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')
STATICFILES_DIRS = [
    STATIC_DIR,
    os.path.join(BASE_DIR,'static'),
    ]
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

# STATICFILES_DIRS = os.path.join(STATIC_DIR, 'debugtoolbar')
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-(5d_*k*!6*rk=g=+06jl+=u%d76p&2jps!!1zhf#lck(=lg*nx'
# 세션타임아웃시간 설정
SESSION_COOKIE_AGE = 60000
SESSION_SAVE_EVERY_REQUEST = True
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*','admin.daeseungtax.co.kr']

# 커스텀 사용자 모델을 지정하는 것 보다 OAuth를 일반 사용자와 함께 사용한다 tableName : auth_
# AUTH_USER_MODEL = 'admins.MemAdmin' #AUTH_USER_MODEL 설정을 사용하여 커스텀 사용자 모델을 지정
# # 커스텀 사용자 백엔드 생성
# AUTHENTICATION_BACKENDS = [
#     'django.contrib.auth.backends.ModelBackend',  # Keep the default model backend to authenticate regular users
#     'admins.adminAuth.customBackend.AdminBackend'
# ]

INSTALLED_APPS = [
    'channels',
    "daphne",
    'app',
    'chat',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
      # template에 3자리숫자 컴마 구현
    "django.contrib.humanize",

    'django_hosts',#django_hosts 설정 : 

    'corsheaders',
    'imagekit',
    'bootstrap4',
    # 'app.kakao',

    'admins',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',

    # 'django_apscheduler',
    # 'debug_toolbar',
]
CKEDITOR_UPLOAD_PATH = "uploads/"
ASGI_APPLICATION = 'noa.asgi.application'
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
        },
        "OPTIONS": {
            "timeout": 300  # 5 minutes
        }
    }
}
MIDDLEWARE = [
    'django_hosts.middleware.HostsRequestMiddleware',  # django-hosts 설정: 최상단
    'corsheaders.middleware.CorsMiddleware',  # CORS: 최상단

    # 'debug_toolbar.middleware.DebugToolbarMiddleware',  # 디버그 툴: 가능한 상단

    'django.middleware.common.CommonMiddleware',
    'htmlmin.middleware.HtmlMinifyMiddleware',
    'htmlmin.middleware.MarkRequestMiddleware',

    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',  # 중복 주의 (위에도 있음)
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    # 'allauth.account.middleware.AccountMiddleware',  # Django 4.1.8과 호환성 문제로 주석 처리
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    'noa.middleware.AllowIframeMiddleware',  # iframe 허용

    'django_hosts.middleware.HostsResponseMiddleware',  # django-hosts 설정: 최하단
]

CORS_ORIGIN_ALLOW_ALL = True     
CORS_ALLOWED_ORIGINS = ['http://daeseungtax.co.kr','https://daeseungtax.co.kr','https://admin.daeseungtax.co.kr','https://www.daeseungtax.co.kr','https://admin.daeseungtax.co.kr','http://admin.localhost:8000']   
CORS_ORIGIN_WHITELIST = ['http://daeseungtax.co.kr','https://daeseungtax.co.kr','https://admin.daeseungtax.co.kr','https://www.daeseungtax.co.kr' ,'http://127.0.0.1:8000','http://admin.127.0.0.1:8000' ]


CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = True
CORS_URLS_REGEX = r'^/media/upload/.*$'

DEFAULT_HOST = "www"#django_hosts 설정 : 
ROOT_HOSTCONF = 'noa.hosts'#django_hosts 설정 : 
ROOT_URLCONF = 'noa.urls'


CONTEXT_PROCESSORS = [
    'django.template.context_processors.debug',
    'django.template.context_processors.request',
    'django.contrib.auth.context_processors.auth',
    'django.contrib.messages.context_processors.messages',
        # 여기 아래에 새 context processor 추가
    'admins.app.context_processors.common_context',
]
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',

        'DIRS': [TEMPLATES_DIR],
        # 'DIRS': [os.path.join(BASE_DIR, "app", "templates")],  # 올바른 경로인지 확인
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors':CONTEXT_PROCESSORS,
            'debug':DEBUG,
            # 'context_processors': [
            #     'django.template.context_processors.debug',  # 디버깅 관련
            #     'django.template.context_processors.request',  # ✅ Admin 네비게이션 사용 필수
            #     'django.contrib.auth.context_processors.auth',  # ✅ Admin 및 인증 관련 필수
            #     'django.contrib.messages.context_processors.messages',  # ✅ 메시지 프레임워크 필수
            #     'django.template.context_processors.tz',  # ✅ 타임존 필터 사용 가능하게 설정
            # ],
        },

    },

]


WSGI_APPLICATION = 'noa.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

DATABASES = {
    # 'default': {
    #     'ENGINE': 'django.db.backends.sqlite3',
    #     'NAME': BASE_DIR / 'db.sqlite3',
    # }
    'default':{
        #'ENGINE':'sql_server.pyodbc',
        'ENGINE':'mssql',
        'NAME':'simplebook',
        'HOST':'211.63.194.154',
        'USER':'sa',
        'PASSWORD':'justaman@1928!'
    }
}
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/


USE_TZ = True

HTML_MINIFY = True

# 국제화 및 지역화 활성화
USE_I18N = True
USE_L10N = True

# 기본 언어를 한국어로 설정
LANGUAGE_CODE = 'ko-kr'
# LANGUAGE_CODE = 'en-us'
# 시간대 설정 (필요에 따라 조정)
TIME_ZONE = 'Asia/Seoul'
# TIME_ZONE = 'UTC'
# 사용 가능한 언어 목록 (필요에 따라 추가)
LANGUAGES = [
    ('ko', 'Korean'),
]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/
STATIC_URL = 'static/'
STATIC_ROOT = os.path.abspath(os.path.join(BASE_DIR,'noa','static'))


# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = "smtp.gmail.com"
EMAIL_HOST_USER = 'daeseung23@gmail.com'
EMAIL_HOST_PASSWORD = 'zrncmbdvtrphknoa'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER 

OPENAI_API_KEY='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'
CHATGPT_HOME = os.path.join(BASE_DIR, 'constructor')



LOGOUT_REDIRECT_URL = '/'

ACCOUNT_DEFAULT_HTTP_PROTOCOL='https'


#디버깅을 위해 필요 ==> admin에서 사용불가해서 삭제
# INTERNAL_IPS = [
#     '127.0.0.1','localhost'
# ]
# DEBUG_TOOLBAR_CONFIG = {
#     'SHOW_TOOLBAR_CALLBACK': 'app.utils.should_display_debug_toolbar',
# }

# 1. iframe 허용 설정
# X_FRAME_OPTIONS = 'SAMEORIGIN'  # 같은 도메인에서는 허용
