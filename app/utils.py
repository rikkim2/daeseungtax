import os
from uuid import uuid4

def rename_imagefile_to_uuid(instance, filename):
  upload_to = f'{instance}'
  ext = filename.split('.')[-1]
  uuid = uuid4().hex

  if instance:
      filename = '{}_{}.{}'.format(uuid, instance, ext)
  else:
      filename = '{}.{}'.format(uuid, ext)
  
  return os.path.join(upload_to, filename)


# def should_display_debug_toolbar(request):
#     """admin.localhost 도메인에서 온 요청에 대해 Debug Toolbar를 표시합니다."""
#     return request.get_host().startswith('admin.localhost')