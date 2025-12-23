from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import PageNumberPagination
from rest_framework import filters
from .models import FCMToken, Parent, Student, AttendanceLog, StudentBusPass, BusPassRequest
from .serializers import (
    ParentRegistrationSerializer,
    ParentProfileSerializer,
    StudentProfileSerializer,
    StudentScheduleSerializer,
    StudentBusPassSerializer,
    AttendanceLogSerializer,
    CustomTokenObtainPairSerializer,
    CustomTokenRefreshSerializer,
    ParentBasicProfileSerializer,
    BusPassRequestSerializer,
    AdminStudentDetailSerializer,
    AdminParentDetailSerializer
)
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from datetime import timedelta 
from django.conf import settings
import pandas as pd
import os
from django.contrib.auth.models import User
from django.db import transaction, IntegrityError
from django.utils import timezone
from datetime import datetime, time
from .permissions import APIKeyCheck
from .schedule_utils import get_student_schedule_by_id, get_all_schedules
from django_filters.rest_framework import DjangoFilterBackend
from firebase_admin import messaging
from .models import FCMToken
from django.core.mail import send_mail


def set_auth_cookies(response, access_token, refresh_token=None):
    
    access_lifetime = settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME']
    
    response.set_cookie(
        key='access_token',
        value=access_token,
        httponly=True,
        secure=settings.CSRF_COOKIE_SECURE, 
        samesite=settings.CSRF_COOKIE_SAMESITE,
        max_age=access_lifetime.total_seconds(),
        path='/'
    )
    
    if refresh_token:
        refresh_lifetime = settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME']
        response.set_cookie(
            key='refresh_token',
            value=refresh_token,
            httponly=True,
            secure=settings.CSRF_COOKIE_SECURE,
            samesite=settings.CSRF_COOKIE_SAMESITE,
            max_age=refresh_lifetime.total_seconds(),
            path='/' 
        )
    return response

class Paginator(PageNumberPagination):
    page_size = 10
    page_size_query_params = 'page_size'
    max_page_size = 100

class CustomTokenObtainPairView(TokenObtainPairView):
   
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        response_data = serializer.validated_data
        
        access_token = serializer.context['access_token']
        refresh_token = serializer.context['refresh_token']
        
        response = Response(response_data, status=status.HTTP_200_OK)
        
        set_auth_cookies(response, access_token, refresh_token)
        
        return response

class CustomTokenRefreshView(TokenRefreshView):
    
    serializer_class = CustomTokenRefreshSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        access_token = serializer.context['access_token']
        
        response = Response({"message": "Token refreshed successfully"}, status=status.HTTP_200_OK)
        
        set_auth_cookies(
            response, 
            access_token, 
            serializer.context.get('refresh_token') 
        )
        
        return response
    

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:

            refresh_token = request.COOKIES.get('refresh_token')
            
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
        except Exception as e:
            pass

        response = Response({"message": "Logged out successfully"}, status=status.HTTP_200_OK)
    
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        
        return response


class ParentRegistrationView(APIView):
    permission_classes = [AllowAny] 

    def post(self, request, *args, **kwargs):
        serializer = ParentRegistrationSerializer(data=request.data)
        
        if serializer.is_valid():
            parent_profile = serializer.save()
            user = parent_profile.user
            
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)
            
            user_data = {
                "user_id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name
            }
            
            response_data = {
                "message": "Parent account created successfully.",
                "user": user_data
            }

            response = Response(response_data, status=status.HTTP_201_CREATED)
            
            set_auth_cookies(response, access_token, refresh_token)
            return response
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ParentProfileView(APIView):
    serializer_class = ParentProfileSerializer
    permission_classes = [IsAuthenticated] 

    def get(self, request, *args, **kwargs):
        try:
            profile = self.request.user.parent_profile
            serializer = self.serializer_class(profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Parent.DoesNotExist:
            return Response({"error": "Profile does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ParentChildrenListView(APIView):
    serializer_class = StudentScheduleSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            profile = self.request.user.parent_profile
            children_queryset = profile.children.all()
            serializer = self.serializer_class(children_queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Parent.DoesNotExist:
            return Response({"error": "Parent profile not found for this user."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class LinkChildView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            parent_profile = request.user.parent_profile
        except Parent.DoesNotExist:
            return Response({"error": "Parent profile not found for this user."}, status=status.HTTP_404_NOT_FOUND)

        university_id = request.data.get('child_university_id')
        reg_code = request.data.get('child_registration_code')

        if not university_id or not reg_code:
            return Response({"error": "child_university_id and child_registration_code are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            student = Student.objects.get(university_id=university_id)
        except Student.DoesNotExist:
            return Response({"error": "No student found with this University ID."}, status=status.HTTP_404_NOT_FOUND)

        if student.registration_code != reg_code:
            return Response({"error": "The Registration Code is incorrect for this student."}, status=status.HTTP_400_BAD_REQUEST)

        if parent_profile.children.filter(university_id=university_id).exists():
            return Response({"error": "This student is already linked to your account."}, status=status.HTTP_400_BAD_REQUEST)

        parent_profile.children.add(student)
        serializer = StudentProfileSerializer(student)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class ParentChildLogView(APIView):
    serializer_class = AttendanceLogSerializer
    permission_classes = [IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        'status': ['exact'],
        'bus_number': ['exact'],
        'timestamp': ['date'],
        'direction': ['exact']
    }

    def filter_queryset(self, queryset):
        for backend in list(self.filter_backends):
            queryset = backend().filter_queryset(self.request, queryset, self)
        return queryset

    def get(self, request, *args, **kwargs):
        child_university_id = self.kwargs.get('university_id')

        try:
            parent_profile = self.request.user.parent_profile
            student = Student.objects.get(university_id=child_university_id)

            if not parent_profile.children.filter(pk=student.pk).exists():
                raise PermissionDenied("You do not have permission to view this student's logs.")

            queryset = AttendanceLog.objects.filter(student=student).order_by('-timestamp')
            
            filtered_queryset = self.filter_queryset(queryset)
            
            if not filtered_queryset.exists():
                return Response({"message": "No scan logs found matching your criteria."}, status=status.HTTP_200_OK)

            serializer = self.serializer_class(filtered_queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Parent.DoesNotExist:
            return Response({"error": "Parent profile not found."}, status=status.HTTP_404_NOT_FOUND)
        except Student.DoesNotExist:
            return Response({"error": "Student not found."}, status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            return Response({"error": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StudentProfileView(APIView):
    serializer_class = StudentProfileSerializer
    permission_classes = [IsAuthenticated] 

    def get(self, request, *args, **kwargs):
        try:
            profile = self.request.user.student_profile
            serializer = self.serializer_class(profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Student.DoesNotExist:
            return Response({"error": "Profile does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class StudentScheduleView(APIView):
    serializer_class = StudentScheduleSerializer
    permission_classes = [IsAuthenticated] 

    def get(self, request, *args, **kwargs):
        try:
            student_profile = self.request.user.student_profile
            serializer = self.serializer_class(student_profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Student.DoesNotExist:
            return Response(
                {"error": "Student profile not found for this user."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response({"error": f"Could not generate schedule: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DemoStudentLoginView(APIView):
    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        if not email:
             return Response({"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)
        email = email.lower()
        
        csv_file_path = os.path.join(settings.BASE_DIR, 'students.csv')
        
        try:
            df = pd.read_csv(csv_file_path, dtype=str)
            student_data = df[df['university_email'].str.lower() == email]
            
            if student_data.empty:
                return Response({"error": "Email not found in student directory (students.csv)."}, status=status.HTTP_404_NOT_FOUND)
            
            student_row = student_data.iloc[0].to_dict()
            
            student_profile, created_student = Student.objects.get_or_create(
                university_id=str(student_row['university_id']),
                defaults={
                    'university_email': student_row['university_email'],
                    'personal_email': student_row.get('personal_email', ''),
                    'schedule_id': student_row.get('schedule_id')
                }
            )
            
            user, created_user = User.objects.get_or_create(
                username=email, 
                defaults={
                    'email': email,
                    'first_name': student_row.get('first_name'),
                    'last_name': student_row.get('last_name')
                }
            )

            if not student_profile.user:
                student_profile.user = user
                student_profile.save() 
            
            student_profile.schedule_id = student_row.get('schedule_id')
            student_profile.save() 

            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)
            
            response_data = {
                "message": "Student login successful.",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name
                }
            }
            
            response = Response(response_data, status=status.HTTP_200_OK)
            
            set_auth_cookies(response, access_token, refresh_token)
            return response

        except FileNotFoundError:
            return Response({"error": "Server configuration error: students.csv not found."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except IntegrityError:
            return Response({"error": "Database conflict. Please try again."}, status=status.HTTP_409_CONFLICT)
        except Exception as e:
            return Response({"error": f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ScanLogView(APIView):
    permission_classes = [APIKeyCheck]

    def _is_time_in_slot(self, scan_time, start_str, end_str, buffer_minutes=30):
        try:
            start_time = datetime.strptime(start_str, '%H:%M').time()
            end_time = datetime.strptime(end_str, '%H:%M').time()

            start_dt = datetime.combine(datetime.today(), start_time)
            end_dt = datetime.combine(datetime.today(), end_time)
            
            valid_start = (start_dt - timedelta(minutes=buffer_minutes)).time()
            valid_end = (end_dt + timedelta(minutes=buffer_minutes)).time()

            return valid_start <= scan_time <= valid_end
        except Exception:
            return False

    def _send_firebase_notification(self, student, log_entry):
        try:
            parents = student.parents.all()
            if not parents.exists():
                return

            tokens_queryset = FCMToken.objects.filter(user__parent_profile__in=parents)
            if not tokens_queryset.exists():
                return
            
            registration_tokens = [t.token for t in tokens_queryset]

            title = "Bus Activity Update"
            body = f"{student.user.first_name} scanned {log_entry.direction} on {log_entry.bus_number}. Status: {log_entry.status}"

            success_count = 0
            
            for token_str in registration_tokens:
                try:
                    message = messaging.Message(
                        notification=messaging.Notification(
                            title=title,
                            body=body,
                        ),
                        android=messaging.AndroidConfig(
                            priority='high',
                            notification=messaging.AndroidNotification(
                                channel_id='default',
                                sound='default',
                                default_sound=True,
                            ),
                        ),
                        data={
                            "student_id": str(student.university_id),
                            "scan_id": str(log_entry.id),
                            "status": log_entry.status,
                        },
                        token=token_str,
                    )
                    
                    messaging.send(message)
                    success_count += 1
                    
                except Exception as e:
                    print(f"FCM Send Failed: {e}")
                    if 'Requested entity was not found' in str(e) or 'registration-token-not-registered' in str(e):
                        FCMToken.objects.filter(token=token_str).delete()

        except Exception as e:
            print(f"FCM General Error: {str(e)}")

    def _send_email_notifications(self, student, log_entry):
        print(f"DEBUG: Starting email notification for {student.university_id}")
        try:
            timestamp_str = log_entry.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            subject = f"Bus Scan: {student.user.first_name} {student.user.last_name} ({log_entry.status})"
            
            parents = student.parents.all()
            parent_emails = [p.user.email for p in parents if p.user.email]
            
            if parent_emails:
                message = (
                    f"Student: {student.user.first_name} {student.user.last_name}\n"
                    f"Time: {timestamp_str}\n"
                    f"Bus: {log_entry.bus_number}\n"
                    f"Direction: {log_entry.direction}\n"
                    f"Status: {log_entry.status}\n\n"
                    f"This is an automated notification from the Bus System."
                )
                
                print(f"DEBUG: Sending Parent Email to {len(parent_emails)} recipients...")
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    parent_emails,
                    fail_silently=False
                )
                print("EMAIL: Parent notification sent successfully.")
            else:
                print("DEBUG: No parent emails found for this student.")

            if log_entry.status == 'INVALID':
                admins = User.objects.filter(is_staff=True)
                admin_emails = [a.email for a in admins if a.email]
                
                if admin_emails:
                    admin_subject = f"ALERT: Invalid Scan for {student.university_id}"
                    admin_message = (
                        f"ALERT: INVALID SCAN DETECTED\n\n"
                        f"Student ID: {student.university_id}\n"
                        f"Name: {student.user.first_name} {student.user.last_name}\n"
                        f"Status: {log_entry.status}\n"
                        f"Bus: {log_entry.bus_number}\n"
                        f"Time: {timestamp_str}\n\n"
                        f"Please check the system logs for details."
                    )
                    
                    print(f"DEBUG: Sending Admin Alert to {len(admin_emails)} admins...")
                    send_mail(
                        admin_subject,
                        admin_message,
                        settings.DEFAULT_FROM_EMAIL,
                        admin_emails,
                        fail_silently=False
                    )
                    print("EMAIL: Admin alert sent successfully.")
                else:
                    print("DEBUG: Scan was INVALID, but no Admin emails found to alert.")

        except Exception as e:
            print(f"EMAIL CRASH: {e}")

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        student_rfid = request.data.get('student_rfid')
        bus_number = request.data.get('bus_number')
        scan_timestamp_str = request.data.get('scan_timestamp')

        if not all([student_rfid, scan_timestamp_str]):
            return Response({"error": "student_rfid and scan_timestamp are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            scan_timestamp = datetime.fromisoformat(scan_timestamp_str.replace('Z', '+00:00'))
        except ValueError:
            return Response({"error": "Invalid timestamp format. Must be ISO 8601."}, status=status.HTTP_400_BAD_REQUEST)

        server_now = timezone.now()
        time_difference = abs(server_now - scan_timestamp)

        if time_difference > timedelta(minutes=5):
            return Response({"error": "Invalid timestamp (Clock Skew > 5 mins)."}, status=status.HTTP_400_BAD_REQUEST)
        
        direction_input = request.data.get('direction')
        
        if not direction_input:
            uae_tz = timezone.get_current_timezone()
            scan_local = scan_timestamp.astimezone(uae_tz)
            
            if scan_local.hour < 12:
                direction_input = 'INBOUND'
            else:
                direction_input = 'OUTBOUND'
        
        direction_input = direction_input.upper()

        try:
            student = Student.objects.get(university_id=student_rfid)
        except Student.DoesNotExist:
            return Response({"error": "Student ID not found."}, status=status.HTTP_404_NOT_FOUND)

        active_pass = StudentBusPass.objects.filter(
            student=student,
            valid_from__lte=scan_timestamp,
            valid_until__gte=scan_timestamp,
            used_at__isnull=True
        ).first()

        if active_pass:
            active_pass.used_at = scan_timestamp
            active_pass.save()

            log = AttendanceLog.objects.create(
                student=student,
                timestamp=scan_timestamp,
                bus_number=bus_number,
                status=AttendanceLog.ScanStatus.OVERRIDE,
                direction=direction_input
            )
            
            self._send_firebase_notification(student, log)
            self._send_email_notifications(student, log)

            return Response({"status": "VALID", "reason": "Admin Pass Used"}, status=status.HTTP_200_OK)

        try:
            schedule_data = get_student_schedule_by_id(student.schedule_id)
            valid_days_list = schedule_data.get('days_list', [])
        except Exception as e:
            print(f"Error building schedule for {student_rfid}: {e}")
            return Response({"error": f"Could not validate schedule: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        scan_day_short = scan_timestamp.strftime("%a")[:2]
        is_valid_schedule = (scan_day_short in valid_days_list)

        if is_valid_schedule:
            log = AttendanceLog.objects.create(
                student=student,
                timestamp=scan_timestamp,
                bus_number=bus_number,
                status=AttendanceLog.ScanStatus.VALID,
                direction=direction_input
            )
            
            self._send_firebase_notification(student, log)
            self._send_email_notifications(student, log)
            
            return Response({"status": "VALID", "reason": "Schedule Matched"}, status=status.HTTP_200_OK)
        else:
            log = AttendanceLog.objects.create(
                student=student,
                timestamp=scan_timestamp,
                bus_number=bus_number,
                status=AttendanceLog.ScanStatus.INVALID,
                direction=direction_input
            )
            
            self._send_firebase_notification(student, log)
            self._send_email_notifications(student, log)
            
            return Response({"status": "INVALID", "reason": "Not on Schedule"}, status=status.HTTP_403_FORBIDDEN)

class CreateBusPassView(generics.CreateAPIView):
    queryset = StudentBusPass.objects.all()
    serializer_class = StudentBusPassSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def perform_create(self, serializer):
        serializer.save(admin_who_granted=self.request.user)

class AdminScanLogView(generics.ListAPIView):
    serializer_class = AttendanceLogSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        'student__university_id': ['exact'],
        'status': ['exact'],
        'bus_number': ['exact'],
        'timestamp': ['date'],
        'direction': ['exact']
    }

    def get_queryset(self):
        params = self.request.query_params
       
        if params:
            return AttendanceLog.objects.all().order_by('-timestamp')
        
        today = timezone.now().date()
        return AttendanceLog.objects.filter(timestamp__date=today).order_by('-timestamp')

class StudentScheduleReportView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request, *args, **kwargs):
        report_time = timezone.now()
        
        day_query = request.query_params.get('day')
        
        if not day_query:
            day_name = report_time.strftime("%A")
        else:
            day_name = day_query
        
        day_query_short = day_name[:2].title()
        
        try:
            all_schedules = get_all_schedules()
            all_students = Student.objects.select_related('user').all()
            report = []

            for student in all_students:
                is_valid_today = False
                
            
                has_active_pass = StudentBusPass.objects.filter(
                    student=student,
                    valid_from__lte=report_time,
                    valid_until__gte=report_time,
                    used_at__isnull=True
                ).exists()

                if has_active_pass:
                    is_valid_today = True
                else:
                    if student.schedule_id:
                        student_schedule_info = all_schedules.get(str(student.schedule_id))
                        
                        if student_schedule_info:
                            valid_days = student_schedule_info.get('days_list', [])
                            if day_query_short in valid_days:
                                is_valid_today = True
                
                if is_valid_today:
                    student_data = {
                        "university_id": student.university_id,
                        "full_name": student.user.get_full_name() if student.user else "N/A",
                        "schedule_id": student.schedule_id
                    }
                    report.append(student_data)

            return Response(report, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": f"Could not generate report: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class StudentAttendanceLogHistoryView(ListAPIView):
    serializer_class = AttendanceLogSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'bus_number', 'direction']

    def get_queryset(self):
        try:
            student = self.request.user.student_profile
        except Student.DoesNotExist:
            return AttendanceLog.objects_none()

        queryset = AttendanceLog.objects.filter(student=student)
        from_date = self.request.query_params.get('from_date')
        to_date = self.request.query_params.get('to_date')

        if from_date:
            queryset = queryset.filter(timestamp__date__gte=from_date)
            if to_date:
                queryset = queryset.filter(timestamp__date__lte=to_date)
        else:
            thirty_days_ago = timezone.now() - timedelta(days=30)
            queryset = queryset.filter(timestamp__gte=thirty_days_ago)

        return queryset.order_by('-timestamp')
    

class StudentParentListView(generics.ListAPIView):
    serializer_class =  ParentBasicProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        try:
            student = self.request.user.student_profile
            return student.parents.all()
        except Student.DoesNotExist:
            return Parent.objects.none()


class StudentPassRequestView(generics.ListCreateAPIView):
    
    serializer_class = BusPassRequestSerializer
    permission_classes = [IsAuthenticated]

    pagination_class = Paginator

    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        'status': ['exact'],
        'request_date': ['date', 'gte', 'lte']
    }


    def get_queryset(self):
        try:
            student = self.request.user.student_profile
        except Student.DoesNotExist:
            return BusPassRequest.objects.none()
        
        queryset = BusPassRequest.objects.filter(student=student).order_by('-request_date')

        params = self.request.query_params

        has_filters = 'status' in params or 'request_date' in params

        if not has_filters:
            thirty_days_ago = timezone.now() - timedelta(days=30)
            queryset = queryset.filter(request_date__gte=thirty_days_ago)

        return queryset

    def perform_create(self, serializer):
        try:
            serializer.save(student=self.request.user.student_profile)
        except Student.DoesNotExist:
             pass 

class AdminPassRequestListView(generics.ListAPIView):

    serializer_class = BusPassRequestSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'student__university_id']

    def get_queryset(self):
        queryset = BusPassRequest.objects.all()
        status_param = self.request.query_params.get('status')
        if not status_param:
            queryset = queryset.filter(status=BusPassRequest.RequestStatus.PENDING)
        return queryset

class AdminApprovePassView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    @transaction.atomic
    def post(self, request, pk, *args, **kwargs):
        try:
            pass_request = BusPassRequest.objects.get(pk=pk)
        except BusPassRequest.DoesNotExist:
            return Response({"error": "Request not found"}, status=status.HTTP_404_NOT_FOUND)

        if pass_request.status != BusPassRequest.RequestStatus.PENDING:
             return Response({"error": "This request has already been processed."}, status=status.HTTP_400_BAD_REQUEST)
        
        final_valid_from = request.data.get('valid_from', pass_request.requested_valid_from)
        
        final_valid_until = request.data.get('valid_until', pass_request.requested_valid_until)

        StudentBusPass.objects.create(
            student=pass_request.student,
            admin_who_granted=request.user,
            reason=f"Approved Request: {pass_request.reason}",
            valid_from=final_valid_from,
            valid_until=final_valid_until
        )

        pass_request.status = BusPassRequest.RequestStatus.APPROVED
        pass_request.admin_notes = request.data.get('admin_notes', 'Approved by admin.')
        pass_request.approved_valid_from = final_valid_from
        pass_request.approved_valid_until = final_valid_until
        pass_request.save()

        return Response({
            "message": "Pass approved and created.",
            "valid_from": final_valid_from,
            "valid_until": final_valid_until
        }, status=status.HTTP_200_OK)

class AdminRejectPassView(APIView):

    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, pk, *args, **kwargs):
        try:
            pass_request = BusPassRequest.objects.get(pk=pk)
        except BusPassRequest.DoesNotExist:
            return Response({"error": "Request not found"}, status=status.HTTP_404_NOT_FOUND)
            
        if pass_request.status != BusPassRequest.RequestStatus.PENDING:
             return Response({"error": "This request has already been processed."}, status=status.HTTP_400_BAD_REQUEST)

        pass_request.status = BusPassRequest.RequestStatus.REJECTED
        pass_request.admin_notes = request.data.get('admin_notes', 'Rejected by admin.')
        pass_request.save()

        return Response({"message": "Request rejected."}, status=status.HTTP_200_OK)
    


class AdminGetStudentInfo(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request, university_id, *args, **kwargs):
        try:
            student = Student.objects.get(university_id=university_id)
            
            serializer = AdminStudentDetailSerializer(student)
            
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Student.DoesNotExist:
            return Response(
                {"error": f"Student with ID {university_id} not found."}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class AdminGetParentInfo(APIView):

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request, pk, *args, **kwargs):
        try:
            parent = Parent.objects.get(pk=pk)
           
            serializer = AdminParentDetailSerializer(parent)
            
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Parent.DoesNotExist:
            return Response(
                {"error": f"Parent with ID {pk} not found."}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class AdminStudentListView(generics.ListAPIView):
    queryset = Student.objects.all().order_by('university_id')
    serializer_class = AdminStudentDetailSerializer 
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    filter_backends = [filters.SearchFilter]
    search_fields = ['university_id', 'university_email', 'user__first_name', 'user__last_name']

class AdminParentListView(generics.ListAPIView):
    queryset = Parent.objects.all().order_by('id')
    serializer_class = AdminParentDetailSerializer 
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    filter_backends = [filters.SearchFilter]
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'phone_number']

class UpdateFCMTokenView(APIView):
    """
    Endpoint for the Frontend to register a device for push notifications.
    Frontend sends the token, Backend saves it linked to the user.
    """
    permission_classes = [IsAuthenticated] # User must be logged in

    def post(self, request, *args, **kwargs):
        fcm_token = request.data.get('fcm_token')
        
        if not fcm_token:
            return Response({"error": "fcm_token is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        # Update existing or create new token record for this user
        # We use update_or_create to ensure one token per device/user combo if needed,
        # but here we simply ensure the token exists for the user.
        # A simple approach is to delete if it exists elsewhere and create new.
        
        # 1. Clean up: If this token was assigned to another user, remove it
        FCMToken.objects.filter(token=fcm_token).exclude(user=request.user).delete()
        
        # 2. Save the token for the current user
        FCMToken.objects.get_or_create(
            user=request.user,
            token=fcm_token
        )
        
        return Response({"message": "Device registered for notifications."}, status=status.HTTP_200_OK)