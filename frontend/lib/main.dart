import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

void main() {
  runApp(const ForestDetoxApp());
}

class ForestDetoxApp extends StatelessWidget {
  const ForestDetoxApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Forest Detox',
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.green),
      ),
      home: const LoginPage(),
    );
  }
}

class LoginPage extends StatelessWidget {
  const LoginPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      // 배경색을 일단 초록색 계열로 깔아둬서 이미지가 로딩 중일 때도 이질감이 없게 했어
      backgroundColor: const Color(0xFFE8F5E9),
      body: Container(
        width: double.infinity,
        height: double.infinity,
        decoration: const BoxDecoration(
          image: DecorationImage(
            // ⚠️ 여기서 파일 이름('home_screen.png')이 assets 폴더와 정확히 일치해야 해!
            image: AssetImage('assets/home_screen.png'),
            fit: BoxFit.cover,
          ),
        ),
        child: SafeArea(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.end,
            children: [
              Padding(
                padding: const EdgeInsets.only(bottom: 80.0), // 버튼 위치를 살짝 더 올렸어
                child: GestureDetector(
                  onTap: () async {
                    // ignore: avoid_print
                    print('🚀 백엔드(Django)로 카카오 로그인 요청 시도 중...');

                    try {
                      final response = await http.post(
                        Uri.parse(
                          'http://127.0.0.1:8000/api/v1/auth/kakao/login/',
                        ),
                      );

                      if (response.statusCode == 200) {
                        // ignore: avoid_print
                        print('✅ 연동 성공! 서버 응답: ${response.body}');
                      } else {
                        // ignore: avoid_print
                        print('⚠️ 연동 실패: 상태 코드 ${response.statusCode}');
                      }
                    } catch (e) {
                      // ignore: avoid_print
                      print('🚨 서버 통신 확인 완료 (서버 미가동 상태): $e');
                    }
                  },
                  child: Container(
                    width: 320, // 버튼 가로 길이를 살짝 늘려 안정감을 줬어
                    height: 56,
                    decoration: BoxDecoration(
                      color: const Color(0xFFFEE500),
                      borderRadius: BorderRadius.circular(12),
                      boxShadow: [
                        BoxShadow(
                          // 최신 버전 문법으로 수정해서 노란 줄을 없앴어
                          color: Colors.black.withValues(alpha: 0.15),
                          blurRadius: 10,
                          offset: const Offset(0, 4),
                        ),
                      ],
                    ),
                    child: const Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.chat_bubble, color: Colors.black, size: 20),
                        SizedBox(width: 12),
                        Text(
                          '카카오로 시작하기 (API 연동)',
                          style: TextStyle(
                            color: Colors.black,
                            fontWeight: FontWeight.bold,
                            fontSize: 16,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
