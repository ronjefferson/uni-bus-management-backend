from django.urls import path
from .views import ParentRegistrationView, ParentProfileView, DemoStudentLoginView, StudentProfileView, StudentScheduleView, ScanLogView, CreateBusPassView, AdminScanLogView, StudentScheduleReportView, ParentChildrenListView, LinkChildView, ParentChildLogView, CustomTokenObtainPairView, CustomTokenRefreshView, LogoutView, StudentAttendanceLogHistoryView, StudentParentListView, StudentPassRequestView, AdminPassRequestListView, AdminApprovePassView, AdminRejectPassView, AdminGetStudentInfo, AdminGetParentInfo, AdminStudentListView, AdminParentListView, UpdateFCMTokenView
from rest_framework_simplejwt.views import (
    TokenObtainPairView, TokenRefreshView
)

urlpatterns = [
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('token/logout/', LogoutView.as_view(), name='token_logout'),
    path('notifications/register-device/', UpdateFCMTokenView.as_view(), name='fcm-register-device'),

    path('parents/register/', ParentRegistrationView.as_view(), name='parent-register'),
    path('parents/me/', ParentProfileView.as_view(), name='parent-profile'),
    path('parents/me/children/', ParentChildrenListView.as_view(), name='parent-children-list'),
    path('parents/me/link-child/', LinkChildView.as_view(), name='parent-link-child'),
    path('parents/me/children/<str:university_id>/logs/', ParentChildLogView.as_view(), name='parent-child-logs'),
    
    path('students/demo-login/', DemoStudentLoginView.as_view(), name='demo-student-login'),
    path('students/me/', StudentProfileView.as_view(), name='student-profile'),
    path('students/schedule/', StudentScheduleView.as_view(), name='student-schedule'),
    path('students/me/logs/', StudentAttendanceLogHistoryView.as_view(), name='student-scan-log-history'),
    path('students/me/parents/', StudentParentListView.as_view(), name='student-parents-list'),
    path('students/requests/', StudentPassRequestView.as_view(), name='student-pass-requests'),

    path('logs/scan/', ScanLogView.as_view(), name='scan-log'),
    

    path('admin/bus-pass/create/', CreateBusPassView.as_view(), name='admin-create-pass'),
    path('admin/scan-logs/', AdminScanLogView.as_view(), name='admin-scan-logs'),
    path('admin/student-report/', StudentScheduleReportView.as_view(), name='admin-student-report'),
    path('admin/requests/', AdminPassRequestListView.as_view(), name='admin-request-list'),
    path('admin/requests/<int:pk>/approve/', AdminApprovePassView.as_view(), name='admin-request-approve'),
    path('admin/requests/<int:pk>/reject/', AdminRejectPassView.as_view(), name='admin-request-reject'),
    path('admin/students/<str:university_id>/', AdminGetStudentInfo.as_view(), name='admin-student-info'),
    path('admin/parents/<int:pk>/', AdminGetParentInfo.as_view(), name='admin-parent-info'),
    path('admin/students/', AdminStudentListView.as_view(), name='admin-student-list'),
    path('admin/parents/', AdminParentListView.as_view(), name='admin-parent-list'),
]
