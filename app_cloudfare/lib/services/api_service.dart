import 'dart:convert';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:http/http.dart' as http;

class ApiException implements Exception {
  final String message;
  final int? statusCode;
  ApiException(this.message, {this.statusCode});
  @override
  String toString() => 'ApiException: $message';
}

class ApiService {
  static const Duration _timeout = Duration(seconds: 15);

  static String get _baseUrl {
    if (kIsWeb) return Uri.base.origin;
    return 'https://queensgame-2fk.pages.dev';
  }

  static Future<Map<String, dynamic>> _request(
    String method,
    String path, {
    Map<String, dynamic>? body,
  }) async {
    final uri = Uri.parse('$_baseUrl$path');
    http.Response response;
    final headers = {'Content-Type': 'application/json'};

    try {
      if (method == 'GET') {
        response = await http.get(uri, headers: headers).timeout(_timeout);
      } else if (method == 'POST') {
        response = await http
            .post(uri, headers: headers, body: body != null ? jsonEncode(body) : null)
            .timeout(_timeout);
      } else if (method == 'PUT') {
        response = await http
            .put(uri, headers: headers, body: body != null ? jsonEncode(body) : null)
            .timeout(_timeout);
      } else {
        throw ApiException('Unsupported HTTP method: $method');
      }
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException('Network error: ${e.toString()}');
    }

    dynamic decoded;
    try {
      decoded = jsonDecode(response.body);
    } on FormatException {
      throw ApiException(
        'El servidor devolvió una respuesta que no es JSON '
        '(HTTP ${response.statusCode}).',
        statusCode: response.statusCode,
      );
    }

    if (response.statusCode >= 200 && response.statusCode < 300) {
      if (decoded is Map<String, dynamic>) return decoded;
      throw ApiException(
        'El servidor devolvió una respuesta JSON inesperada.',
        statusCode: response.statusCode,
      );
    }
    final detail = decoded is Map
        ? (decoded['detail'] ?? decoded['error'] ?? 'Error desconocido')
        : 'Error desconocido';
    throw ApiException(detail.toString(), statusCode: response.statusCode);
  }

  /// Starts a new game with the given board size.
  static Future<Map<String, dynamic>> createGame(int size) async {
    return _request('POST', '/api/games', body: {'size': size});
  }

  /// Fetches current game state.
  static Future<Map<String, dynamic>> getGame(String id) async {
    return _request('GET', '/api/games/$id');
  }

  /// Places or removes a queen/cross on a cell.
  /// [action]: "queen", "cross", "empty"
  static Future<Map<String, dynamic>> updateCell(
      String id, int row, int col, String action) async {
    return _request('POST', '/api/games/$id/cells',
        body: {'row': row, 'col': col, 'action': action});
  }

  /// Undoes the last move.
  static Future<Map<String, dynamic>> undo(String id) async {
    return _request('POST', '/api/games/$id/undo');
  }

  /// Resets the board (keeps the same map).
  static Future<Map<String, dynamic>> reset(String id) async {
    return _request('POST', '/api/games/$id/reset');
  }

  /// Places a hint queen.
  static Future<Map<String, dynamic>> hint(String id) async {
    return _request('POST', '/api/games/$id/hint');
  }

  /// Toggles auto-cross mode.
  static Future<Map<String, dynamic>> setAutoCross(
      String id, bool enabled) async {
    return _request('PUT', '/api/games/$id/settings/auto-cross',
        body: {'enabled': enabled});
  }

  /// Top 10 scoreboard for a given size.
  static Future<Map<String, dynamic>> getRecords(int size) async {
    return _request('GET', '/api/scoreboard?size=$size');
  }

  /// Game rules.
  static Future<Map<String, dynamic>> getRules() async {
    return _request('GET', '/api/rules');
  }
}
