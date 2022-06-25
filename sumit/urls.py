
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # transfering all url routing data to authentication app
    path('', include('authentication.urls'))
]
