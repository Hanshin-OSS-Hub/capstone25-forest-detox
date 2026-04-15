from rest_framework import serializers


# ----------------------------------------------------
# 8-1 기록 탭 앱 Top5 응답용 Serializer
# ----------------------------------------------------
class DailyAppUsageTopSerializer(serializers.Serializer):
    """
    선택한 날짜에 가장 많이 사용한 앱 Top 5 를 응답할 때 사용하는 Serializer 입니다.
    """

    # 순위
    rank = serializers.IntegerField()

    # 앱 이름
    app_name = serializers.CharField()

    # 사용 시간(분)
    usage_minutes = serializers.IntegerField()


# ----------------------------------------------------
# 8-1 기록 탭 일간 챌린지 상태 응답용 Serializer
# ----------------------------------------------------
class DailyChallengeStatusSerializer(serializers.Serializer):
    """
    선택한 날짜의 일간 챌린지 상태를 내려줄 때 사용하는 Serializer 입니다.
    """

    # 챌린지 ID
    id = serializers.IntegerField()

    # 챌린지 제목
    title = serializers.CharField()

    # 챌린지 설명
    description = serializers.CharField(allow_blank=True, allow_null=True)

    # 챌린지 난이도
    difficulty = serializers.CharField()

    # 챌린지 상태
    status = serializers.CharField()

    # 보상 포인트
    reward_points = serializers.IntegerField()


# ----------------------------------------------------
# 8-1 기록 탭 날짜 상세 응답용 Serializer
# ----------------------------------------------------
class RecordDetailResponseSerializer(serializers.Serializer):
    """
    사용자가 기록 탭에서 특정 날짜를 눌렀을 때,
    그 날짜의 상세 데이터를 응답하는 Serializer 입니다.
    """

    # 선택한 날짜 문자열
    selected_date = serializers.CharField()

    # 그날 대표 감정
    # 감정 기록이 없으면 null 이 됩니다.
    emotion_label = serializers.CharField(allow_null=True)

    # 그날 총 사용시간(분)
    total_usage_minutes = serializers.IntegerField()

    # 그날 목표 시간(분)
    target_minutes = serializers.IntegerField()

    # 그날 목표 달성 여부
    goal_achieved = serializers.BooleanField()

    # 그날 기록 탭에 보여줄 안내 문구
    daily_feedback_message = serializers.CharField()

    # 그날 일간 챌린지 목록
    daily_challenges = DailyChallengeStatusSerializer(many=True)

    # 그날 가장 많이 사용한 앱 Top 5
    top_apps = DailyAppUsageTopSerializer(many=True)


# ----------------------------------------------------
# 8-1 월별 캘린더 응답용 Serializer
# ----------------------------------------------------
class CalendarDaySummarySerializer(serializers.Serializer):
    """
    기록 탭 캘린더에서 날짜마다 최소 표시 정보를 줄 때 사용하는 Serializer 입니다.

    예:
    - 감정 기록이 있었는지
    - 목표 달성 여부가 있었는지
    """

    # 날짜
    date = serializers.CharField()

    # 감정 기록 존재 여부
    has_emotion = serializers.BooleanField()

    # 목표 달성 여부
    goal_achieved = serializers.BooleanField()

    # 총 사용시간(분)
    total_usage_minutes = serializers.IntegerField()


class CalendarMonthResponseSerializer(serializers.Serializer):
    """
    월별 캘린더 응답 전체를 감싸는 Serializer 입니다.
    """

    # 조회한 연도
    year = serializers.IntegerField()

    # 조회한 월
    month = serializers.IntegerField()

    # 해당 월 날짜 요약 목록
    days = CalendarDaySummarySerializer(many=True)


# ----------------------------------------------------
# 10-1 사용량 업로드용 Serializer
# ----------------------------------------------------
class AppUsageUploadItemSerializer(serializers.Serializer):
    """
    Flutter/Android 에서 수집한 앱 사용 기록 1개를 검증하는 Serializer 입니다.
    """

    # 앱 이름
    app_name = serializers.CharField()

    # 앱 카테고리 이름
    # 예: Social, Video, Productivity
    category_name = serializers.CharField(required=False, allow_blank=True)

    # 사용 방식
    # foreground / background
    usage_type = serializers.CharField(required=False, allow_blank=True, default="foreground")

    # 사용 시작 시각
    # ISO 형식 문자열을 받습니다.
    start_time = serializers.DateTimeField()

    # 사용 종료 시각
    end_time = serializers.DateTimeField()


class AppUsageUploadRequestSerializer(serializers.Serializer):
    """
    앱 사용량 업로드 요청 전체를 검증하는 Serializer 입니다.
    """

    # 업로드 대상 사용자 ID
    user_id = serializers.IntegerField()

    # 여러 개의 사용량 레코드를 한 번에 받습니다.
    usage_logs = AppUsageUploadItemSerializer(many=True)


class AppUsageUploadResponseSerializer(serializers.Serializer):
    """
    앱 사용량 업로드 결과 응답용 Serializer 입니다.
    """

    # 성공 여부
    success = serializers.BooleanField()

    # 저장된 레코드 개수
    saved_count = serializers.IntegerField()

    # 응답 메시지
    message = serializers.CharField()