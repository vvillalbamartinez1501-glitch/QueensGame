import 'dart:convert';

import 'package:http/http.dart' as http;

const _defaultApiBaseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: '',
);

class ApiException implements Exception {
  const ApiException(this.message);

  final String message;

  @override
  String toString() => message;
}

class ApiService {
  ApiService({http.Client? client, String? baseUrl})
      : _client = client ?? http.Client(),
        _baseUrl = (baseUrl ?? _defaultApiBaseUrl).replaceFirst(
          RegExp(r'/$'),
          '',
        );

  final http.Client _client;
  final String _baseUrl;

  Uri _uri(String path) => _baseUrl.isEmpty
      ? Uri.base.resolve(path)
      : Uri.parse('$_baseUrl$path');

  Future<Map<String, dynamic>> _request(
    String method,
    String path, {
    Map<String, Object?>? body,
  }) async {
    try {
      final uri = _uri(path);
      final headers = {'Content-Type': 'application/json'};
      const timeout = Duration(seconds: 12);
      late final http.Response response;
      if (method == 'GET') {
        response = await _client.get(uri, headers: headers).timeout(timeout);
      } else if (method == 'POST') {
        response = await _client.post(
          uri,
          headers: headers,
          body: jsonEncode(body ?? const {}),
        ).timeout(timeout);
      } else if (method == 'PUT') {
        response = await _client.put(
          uri,
          headers: headers,
          body: jsonEncode(body ?? const {}),
        ).timeout(timeout);
      } else {
        throw ApiException('Método HTTP no soportado: $method');
      }
      final decoded = jsonDecode(response.body);
      if (response.statusCode < 200 || response.statusCode >= 300) {
        final detail = decoded is Map<String, dynamic>
            ? decoded['detail']?.toString()
            : null;
        throw ApiException(detail ?? 'Error del servidor (${response.statusCode}).');
      }
      if (decoded is! Map<String, dynamic>) {
        throw const ApiException('El servidor devolvió una respuesta inválida.');
      }
      return decoded;
    } on ApiException {
      rethrow;
    } on FormatException {
      throw const ApiException('El servidor devolvió JSON inválido.');
    } catch (error) {
      throw ApiException('No se pudo conectar con el servidor: $error');
    }
  }

  Future<Map<String, dynamic>> createGame(int size, bool autoCross) =>
      _request('POST', '/api/games', body: {
        'size': size,
        'auto_cross': autoCross,
      });

  Future<Map<String, dynamic>> getGame(String id) =>
      _request('GET', '/api/games/$id');

  Future<Map<String, dynamic>> updateCell(
    String id,
    int row,
    int col,
    String action,
  ) =>
      _request('POST', '/api/games/$id/cells', body: {
        'row': row,
        'col': col,
        'action': action,
      });

  Future<Map<String, dynamic>> undo(String id) =>
      _request('POST', '/api/games/$id/undo');

  Future<Map<String, dynamic>> reset(String id) =>
      _request('POST', '/api/games/$id/reset');

  Future<Map<String, dynamic>> hint(String id) =>
      _request('POST', '/api/games/$id/hint');

  Future<Map<String, dynamic>> setAutoCross(String id, bool enabled) =>
      _request('PUT', '/api/games/$id/settings/auto-cross', body: {
        'enabled': enabled,
      });

  Future<List<dynamic>> getRecords(int size) async {
    final result = await _request('GET', '/api/scoreboard?size=$size');
    return result['records'] as List<dynamic>;
  }

  Future<Map<String, dynamic>> getRules() =>
      _request('GET', '/api/rules');

  void close() => _client.close();
}
